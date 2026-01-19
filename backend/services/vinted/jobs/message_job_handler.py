"""
Message Job Handler - Synchronisation des conversations/messages Vinted

Thin handler that delegates to VintedMessageService.

Modes:
- Sync inbox (all conversations)
- Sync specific conversation (messages)

Author: Claude
Date: 2025-12-19
Updated: 2026-01-15 - Refactored to follow standard pattern
"""

from typing import Any

from sqlalchemy.orm import Session

from models.user.marketplace_job import MarketplaceJob
from services.vinted.vinted_message_service import VintedMessageService
from .base_job_handler import BaseJobHandler


class MessageJobHandler(BaseJobHandler):
    """
    Handler for synchronizing Vinted conversations/messages.

    Delegates all business logic to VintedMessageService.
    """

    ACTION_CODE = "message"

    def create_tasks(self, job: MarketplaceJob) -> list[str]:
        """
        Define task steps for message synchronization.

        Args:
            job: MarketplaceJob

        Returns:
            List of task step descriptions
        """
        params = job.result_data if isinstance(job.result_data, dict) else {}
        conversation_id = params.get('conversation_id')

        if conversation_id:
            return [
                "Fetch conversation from Vinted",
                "Sync messages to database",
                "Update conversation status"
            ]
        else:
            return [
                "Fetch inbox from Vinted",
                "Sync conversations to database",
                "Update conversation counters"
            ]

    def get_service(self) -> VintedMessageService:
        """
        Get service instance for message operations.

        Returns:
            VintedMessageService instance
        """
        return VintedMessageService(self.db)

    async def execute(self, job: MarketplaceJob) -> dict[str, Any]:
        """
        Execute message synchronization by delegating to service.

        Args:
            job: MarketplaceJob with optional result_data:
                - {} or None: sync inbox (all conversations)
                - {"conversation_id": int}: sync specific conversation
                - {"sync_all": bool}: sync all inbox pages
                - {"page": int, "per_page": int}: pagination

        Returns:
            dict: {
                "success": bool,
                "message_handled": bool,
                "mode": "inbox" | "conversation",
                "synced": int,
                "created": int,
                "updated": int,
                "error": str | None
            }
        """
        # Extract parameters from job
        params = job.result_data if isinstance(job.result_data, dict) else {}
        conversation_id = params.get('conversation_id')

        try:
            mode = "conversation" if conversation_id else "inbox"
            self.log_start(f"Sync messages ({mode})")

            # Delegate to service
            service = self.get_service()
            result = await service.handle_message(
                message_id=conversation_id,
                user_id=self.user_id,
                shop_id=self.shop_id or 0,
                params=params
            )

            if result.get("success"):
                synced = result.get("synced", 0)
                self.log_success(f"{synced} {mode}(s) synced")
            else:
                self.log_error(f"Sync failed: {result.get('error')}")

            return result

        except Exception as e:
            self.log_error(f"Message sync error: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
