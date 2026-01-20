"""
Vinted Job Bridge Service - Bridge Celery -> MarketplaceJob for Vinted.

Celery workers cannot execute Vinted jobs directly (WebSocket required).
This bridge creates MarketplaceJobs that the frontend executes via Plugin.

Architecture:
    Celery Task -> VintedJobBridgeService -> MarketplaceJob -> WebSocket notify
                                                                    |
                                                          Frontend executes via Plugin

Author: Claude
Date: 2026-01-20
"""

from typing import Any

from sqlalchemy.orm import Session

from services.marketplace.marketplace_job_service import MarketplaceJobService
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class VintedJobBridgeService:
    """
    Bridge service that creates MarketplaceJobs for Vinted operations.

    Since Celery workers run in separate processes without WebSocket access,
    Vinted jobs cannot be executed directly. Instead, we create a MarketplaceJob
    and notify the frontend to execute it via the browser plugin.

    Usage:
        bridge = VintedJobBridgeService(db)

        # From Celery task
        result = bridge.queue_publish(product_id=123, user_id=1, shop_id=456)

        # Result contains job_id for tracking
        # Frontend receives WebSocket notification and executes the job
    """

    def __init__(self, db: Session):
        self.db = db
        self.job_service = MarketplaceJobService(db)

    def queue_publish(
        self,
        product_id: int,
        user_id: int,
        shop_id: int | None = None,
    ) -> dict[str, Any]:
        """
        Queue a publish job for frontend execution.

        Args:
            product_id: Product ID to publish
            user_id: User ID for notifications
            shop_id: Optional Vinted shop ID

        Returns:
            Dict with job_id and status
        """
        job = self.job_service.create_job(
            marketplace="vinted",
            action_code="publish",
            product_id=product_id,
            priority=2,  # HIGH priority for publish
            input_data={"shop_id": shop_id, "user_id": user_id},
        )

        self.db.commit()

        logger.info(
            f"[VintedJobBridge] Created publish job #{job.id} "
            f"for product {product_id} (user={user_id})"
        )

        # Notify frontend via WebSocket
        self._notify_frontend(user_id, job)

        return {
            "success": True,
            "job_id": job.id,
            "status": "queued_for_frontend",
            "message": "Vinted job created - awaiting frontend execution",
        }

    def queue_update(
        self,
        product_id: int,
        user_id: int,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Queue an update job for frontend execution.

        Args:
            product_id: Product ID to update
            user_id: User ID for notifications
            **kwargs: Additional update parameters (price, title, etc.)

        Returns:
            Dict with job_id and status
        """
        input_data = {"user_id": user_id, **kwargs}

        job = self.job_service.create_job(
            marketplace="vinted",
            action_code="update",
            product_id=product_id,
            priority=3,  # NORMAL priority for updates
            input_data=input_data,
        )

        self.db.commit()

        logger.info(
            f"[VintedJobBridge] Created update job #{job.id} "
            f"for product {product_id} (user={user_id})"
        )

        self._notify_frontend(user_id, job)

        return {
            "success": True,
            "job_id": job.id,
            "status": "queued_for_frontend",
            "message": "Vinted update job created - awaiting frontend execution",
        }

    def queue_delete(
        self,
        product_id: int,
        user_id: int,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Queue a delete job for frontend execution.

        Args:
            product_id: Product ID to delete from Vinted
            user_id: User ID for notifications
            **kwargs: Additional delete parameters

        Returns:
            Dict with job_id and status
        """
        input_data = {"user_id": user_id, **kwargs}

        job = self.job_service.create_job(
            marketplace="vinted",
            action_code="delete",
            product_id=product_id,
            priority=2,  # HIGH priority for deletes
            input_data=input_data,
        )

        self.db.commit()

        logger.info(
            f"[VintedJobBridge] Created delete job #{job.id} "
            f"for product {product_id} (user={user_id})"
        )

        self._notify_frontend(user_id, job)

        return {
            "success": True,
            "job_id": job.id,
            "status": "queued_for_frontend",
            "message": "Vinted delete job created - awaiting frontend execution",
        }

    def queue_sync(
        self,
        user_id: int,
        shop_id: int | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Queue a sync job for frontend execution.

        Args:
            user_id: User ID for notifications and sync
            shop_id: Optional Vinted shop ID
            **kwargs: Additional sync parameters

        Returns:
            Dict with job_id and status
        """
        input_data = {"user_id": user_id, "shop_id": shop_id, **kwargs}

        job = self.job_service.create_job(
            marketplace="vinted",
            action_code="sync",
            product_id=None,  # Sync is not product-specific
            priority=3,  # NORMAL priority for sync
            input_data=input_data,
        )

        self.db.commit()

        logger.info(
            f"[VintedJobBridge] Created sync job #{job.id} (user={user_id})"
        )

        self._notify_frontend(user_id, job)

        return {
            "success": True,
            "job_id": job.id,
            "status": "queued_for_frontend",
            "message": "Vinted sync job created - awaiting frontend execution",
        }

    def _notify_frontend(self, user_id: int, job) -> None:
        """
        Send WebSocket notification to frontend about pending job.

        The frontend should:
        1. Listen for 'vinted_job_pending' events
        2. Fetch job details if needed
        3. Execute the job via the browser plugin
        4. Call PATCH /api/vinted/jobs/{job_id}/complete or /fail

        Args:
            user_id: User ID for room targeting
            job: MarketplaceJob instance
        """
        try:
            import asyncio
            from services.websocket_service import sio

            room = f"user_{user_id}"

            # Get action code from job
            action_code = None
            if job.action_type_id:
                action_type = self.job_service.get_action_type_by_id(job.action_type_id)
                if action_type:
                    action_code = action_type.code

            data = {
                "job_id": job.id,
                "action": action_code,
                "product_id": job.product_id,
                "priority": job.priority,
                "input_data": job.input_data,
            }

            # Send async emit from sync context
            # This is safe because we're just queuing a message
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If there's already a running loop (e.g., in FastAPI async context)
                    asyncio.create_task(sio.emit("vinted_job_pending", data, room=room))
                else:
                    loop.run_until_complete(sio.emit("vinted_job_pending", data, room=room))
            except RuntimeError:
                # No event loop - create one (typical for Celery workers)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(sio.emit("vinted_job_pending", data, room=room))
                finally:
                    loop.close()

            logger.debug(
                f"[VintedJobBridge] Sent notification for job #{job.id} to room {room}"
            )

        except Exception as e:
            # Log but don't fail - job is created regardless of notification
            logger.warning(
                f"[VintedJobBridge] Failed to notify frontend for job #{job.id}: {e}"
            )
