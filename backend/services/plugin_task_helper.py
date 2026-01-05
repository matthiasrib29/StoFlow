"""
Plugin Task Helper - Utilities for synchronous plugin task orchestration.

Inspired by pythonApiWOO architecture where the backend keeps control
of the execution flow via synchronous calls.

Business Rules (2025-12-12):
- Backend orchestrates step-by-step like with requests.post()
- wait_for_task_completion() waits for a task to complete
- Backend keeps context, no need for TaskType routing
- Configurable timeout per task (default: 60s)
- Rate limiting with random delays to avoid bot detection

Architecture:
- Create task → Wait completion → Process result → Next step
- Poll DB every 1s (configurable)
- No async callback, just synchronous await

Author: Claude
Date: 2025-12-12
Refactored: 2026-01-05 - Split into multiple modules
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from models.user.plugin_task import PluginTask, TaskStatus
from shared.logging_setup import get_logger
from shared.schema_utils import (
    get_current_schema,
    restore_search_path,
    commit_and_restore_path,
)

# Import from split modules
from services.plugin_task_rate_limiter import VintedRateLimiter
from services.plugin_task_vinted_helpers import (
    verify_vinted_connection,
    verify_vinted_connection_with_profile,
    refresh_vinted_session,
    create_and_wait_with_401_handling,
)

logger = get_logger(__name__)

# Re-export for backward compatibility (deprecated, use shared.schema_utils instead)
_get_current_schema = get_current_schema
_restore_search_path = restore_search_path
_commit_and_restore_path = commit_and_restore_path


# =============================================================================
# PLUGIN TASK HELPER
# =============================================================================


class PluginTaskHelper:
    """
    Helper for synchronous plugin task orchestration.

    Allows the backend to control execution flow like with pythonApiWOO:

    Example:
        # Instead of:
        response = requests.post("/api/vinted/photos", files=...)
        photo_id = response.json()['id']

        # Do:
        task = create_http_task("POST", "/api/v2/photos", body=...)
        result = await wait_for_task_completion(task.id)
        photo_id = result['id']
    """

    @staticmethod
    def create_http_task(
        db: Session,
        http_method: str,
        path: str,
        payload: Optional[dict] = None,
        platform: str = "vinted",
        product_id: Optional[int] = None,
        job_id: Optional[int] = None,
        description: Optional[str] = None,
    ) -> PluginTask:
        """
        Create a simple HTTP task for the plugin.

        Args:
            db: SQLAlchemy session (user schema)
            http_method: GET, POST, PUT, DELETE
            path: Full URL (e.g., "https://www.vinted.fr/api/v2/photos")
            payload: Request body (optional)
            platform: Target platform (default: vinted)
            product_id: Associated product ID (optional)
            job_id: Parent job ID (optional, for orchestration)
            description: Description for logs (optional)

        Returns:
            PluginTask created and persisted in DB

        Example:
            task = create_http_task(
                db, "POST", "https://www.vinted.fr/api/v2/photos",
                payload={"body": photo_data},
                job_id=job.id
            )
        """
        task = PluginTask(
            platform=platform,
            task_type=None,  # No task_type, just HTTP
            status=TaskStatus.PENDING,
            http_method=http_method,
            path=path,
            payload=payload or {},
            product_id=product_id,
            job_id=job_id,
            created_at=datetime.now(timezone.utc),
        )

        db.add(task)
        commit_and_restore_path(db)  # Commit + restore search_path
        db.refresh(task)

        logger.debug(
            f"[PluginTaskHelper] Task created #{task.id} - "
            f"{http_method} {path[:50]}... "
            f"{description or ''}"
        )

        return task

    @staticmethod
    def create_special_task(
        db: Session,
        task_type: str,
        platform: str = "vinted",
        payload: Optional[dict] = None,
        product_id: Optional[int] = None,
        job_id: Optional[int] = None,
    ) -> PluginTask:
        """
        Create a special non-HTTP task for the plugin.

        Used for operations that are not HTTP requests:
        - get_vinted_user_info: Extract userId/login from DOM
        - get_vinted_user_profile: Get full profile via API
        - refresh_vinted_session: Refresh session cookies

        Args:
            db: SQLAlchemy session (user schema)
            task_type: Special task type (e.g., "get_vinted_user_info")
            platform: Target platform (default: vinted)
            payload: Additional data (optional)
            product_id: Associated product ID (optional)
            job_id: Parent job ID (optional, for orchestration)

        Returns:
            PluginTask created and persisted in DB

        Example:
            task = create_special_task(db, "get_vinted_user_info")
            result = await wait_for_task_completion(db, task.id)
            if result['connected']:
                print(f"Connected: {result['login']}")
        """
        task = PluginTask(
            platform=platform,
            task_type=task_type,
            status=TaskStatus.PENDING,
            http_method=None,
            path=None,
            payload=payload or {},
            product_id=product_id,
            job_id=job_id,
            created_at=datetime.now(timezone.utc),
        )

        db.add(task)
        commit_and_restore_path(db)  # Commit + restore search_path
        db.refresh(task)

        logger.debug(
            f"[PluginTaskHelper] Special task created #{task.id} - {task_type}"
        )

        return task

    @staticmethod
    async def wait_for_task_completion(
        db: Session, task_id: int, timeout: int = 60, poll_interval: float = 1.0
    ) -> dict[str, Any]:
        """
        Wait for a task to complete (like requests.post() blocks).

        Args:
            db: SQLAlchemy session
            task_id: ID of the task to wait for
            timeout: Timeout in seconds (default: 60s)
            poll_interval: Polling interval in seconds (default: 1s)

        Returns:
            dict: task.result['data'] if success

        Raises:
            TimeoutError: If timeout exceeded
            Exception: If task fails (with task.error_message)

        Example:
            task = create_http_task(db, "POST", "/api/v2/photos", ...)
            result = await wait_for_task_completion(db, task.id, timeout=30)
            photo_id = result['id']
        """
        start_time = time.time()

        logger.debug(
            f"[PluginTaskHelper] Waiting for task #{task_id} "
            f"(timeout: {timeout}s, poll: {poll_interval}s)"
        )

        while time.time() - start_time < timeout:
            # Refresh task from DB
            db.expire_all()  # Force refresh
            task = db.query(PluginTask).filter(PluginTask.id == task_id).first()

            if not task:
                raise ValueError(f"Task #{task_id} not found")

            # Check status
            if task.status == TaskStatus.SUCCESS:
                elapsed = time.time() - start_time
                logger.debug(
                    f"[PluginTaskHelper] Task #{task_id} completed "
                    f"(elapsed: {elapsed:.2f}s)"
                )

                # Return just the data (like response.json())
                if task.result and "data" in task.result:
                    return task.result["data"]
                else:
                    return task.result or {}

            elif task.status == TaskStatus.FAILED:
                error_msg = task.error_message or "Unknown error"
                logger.error(
                    f"[PluginTaskHelper] Task #{task_id} failed: {error_msg}"
                )
                raise Exception(f"Task #{task_id} failed: {error_msg}")

            elif task.status == TaskStatus.TIMEOUT:
                raise TimeoutError(f"Task #{task_id} timeout (marked by plugin)")

            elif task.status == TaskStatus.CANCELLED:
                raise Exception(f"Task #{task_id} cancelled")

            # Wait before retry
            await asyncio.sleep(poll_interval)

        # Timeout exceeded - MARK TASK AS CANCELLED
        # CRITICAL (2025-12-18): Prevents task from staying PENDING and being
        # picked up on next plugin poll → flood Vinted
        elapsed = time.time() - start_time

        # Cancel task in DB
        try:
            db.expire_all()
            task = db.query(PluginTask).filter(PluginTask.id == task_id).first()
            if task and task.status in (TaskStatus.PENDING, TaskStatus.PROCESSING):
                task.status = TaskStatus.CANCELLED
                task.error_message = f"Backend timeout after {elapsed:.2f}s"
                task.completed_at = datetime.now(timezone.utc)
                commit_and_restore_path(db)
                logger.warning(
                    f"[PluginTaskHelper] Task #{task_id} CANCELLED after timeout "
                    f"(elapsed: {elapsed:.2f}s, http_method={task.http_method}, "
                    f"path={task.path[:100] if task.path else 'N/A'})"
                )
        except Exception as e:
            logger.error(
                f"[PluginTaskHelper] Error cancelling task #{task_id}: {e}",
                exc_info=True,
            )

        raise TimeoutError(
            f"Task #{task_id} timeout after {elapsed:.2f}s (status: {task.status})"
        )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


async def create_and_wait(
    db: Session,
    http_method: str,
    path: str,
    payload: Optional[dict] = None,
    timeout: int = 60,
    rate_limit: bool = True,
    **kwargs,
) -> dict[str, Any]:
    """
    All-in-one helper: create a task and wait for its result.

    Equivalent of requests.post() but via plugin.
    Includes automatic rate limiting to avoid bot detection.

    Args:
        db: SQLAlchemy session
        http_method: GET, POST, PUT, DELETE
        path: Full URL
        payload: Request body
        timeout: Timeout in seconds
        rate_limit: If True, apply random delay (default: True)
        **kwargs: Additional arguments for create_http_task

    Example:
        # Instead of:
        response = requests.post(url, json=data)
        result = response.json()

        # Do:
        result = await create_and_wait(db, "POST", url, payload={"body": data})
    """
    # Apply rate limiting if enabled
    if rate_limit:
        await VintedRateLimiter.wait_before_request(path, http_method)

    helper = PluginTaskHelper()
    task = helper.create_http_task(db, http_method, path, payload, **kwargs)
    return await helper.wait_for_task_completion(db, task.id, timeout)


async def create_and_wait_no_limit(
    db: Session,
    http_method: str,
    path: str,
    payload: Optional[dict] = None,
    timeout: int = 60,
    **kwargs,
) -> dict[str, Any]:
    """
    Like create_and_wait but WITHOUT rate limiting.

    Useful for internal or urgent requests.
    """
    return await create_and_wait(
        db, http_method, path, payload, timeout, rate_limit=False, **kwargs
    )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Main class
    "PluginTaskHelper",
    # Rate limiter (re-export)
    "VintedRateLimiter",
    # Helper functions
    "create_and_wait",
    "create_and_wait_no_limit",
    # Vinted-specific helpers (re-export)
    "verify_vinted_connection",
    "verify_vinted_connection_with_profile",
    "refresh_vinted_session",
    "create_and_wait_with_401_handling",
    # Deprecated (use shared.schema_utils)
    "_get_current_schema",
    "_restore_search_path",
    "_commit_and_restore_path",
]
