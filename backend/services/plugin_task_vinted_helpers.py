"""
Plugin Task Vinted Helpers - Vinted-specific helper functions for plugin tasks.

Contains specialized functions for Vinted operations:
- Connection verification (DOM and API-based)
- Session refresh handling
- 401 error handling with automatic retry

Author: Claude
Date: 2025-12-12
Refactored: 2026-01-05
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from models.user.plugin_task import PluginTask, TaskStatus
from services.plugin_task_rate_limiter import VintedRateLimiter
from shared.logging_setup import get_logger
from shared.schema_utils import commit_and_restore_path

logger = get_logger(__name__)


async def verify_vinted_connection(db: Session, timeout: int = 30) -> dict[str, Any]:
    """
    Vérifie que le plugin est connecté à Vinted (legacy - DOM parsing only).

    Crée une tâche spéciale get_vinted_user_info qui demande au plugin
    d'extraire userId/login depuis le DOM de Vinted.

    Args:
        db: Session SQLAlchemy
        timeout: Timeout en secondes (défaut: 30s)

    Returns:
        dict: {
            "connected": bool,
            "userId": int | None,
            "login": str | None,
            "timestamp": str
        }

    Raises:
        TimeoutError: Si le plugin ne répond pas
        Exception: Si erreur d'extraction

    Example:
        result = await verify_vinted_connection(db)
        if not result['connected']:
            raise HTTPException(400, "Plugin non connecté à Vinted")
    """
    # Import here to avoid circular dependency
    from services.plugin_task_helper import PluginTaskHelper

    helper = PluginTaskHelper()
    task = helper.create_special_task(db, "get_vinted_user_info", platform="vinted")
    return await helper.wait_for_task_completion(db, task.id, timeout)


async def verify_vinted_connection_with_profile(
    db: Session, timeout: int = 30
) -> dict[str, Any]:
    """
    Vérifie la connexion Vinted et récupère le profil complet avec stats vendeur.

    Crée une tâche get_vinted_user_profile qui demande au plugin de :
    1. Appeler l'API /api/v2/users/current pour récupérer le profil complet
    2. Si l'API échoue, fallback sur l'extraction DOM

    Args:
        db: Session SQLAlchemy
        timeout: Timeout en secondes (défaut: 30s)

    Returns:
        dict: {
            "connected": bool,
            "userId": int | None,
            "login": str | None,
            "source": "api" | "dom",
            "stats": {
                "item_count": int,
                "total_items_count": int,
                "given_item_count": int,
                "taken_item_count": int,
                "followers_count": int,
                "feedback_count": int,
                "feedback_reputation": float,
                "positive_feedback_count": int,
                "negative_feedback_count": int,
                "is_business": bool,
                "is_on_holiday": bool
            } | None,
            "timestamp": str
        }

    Raises:
        TimeoutError: Si le plugin ne répond pas
        Exception: Si erreur d'extraction

    Example:
        result = await verify_vinted_connection_with_profile(db)
        if result['connected'] and result.get('stats'):
            # Save stats to database
            connection.update_seller_stats(result['stats'])
    """
    # Import here to avoid circular dependency
    from services.plugin_task_helper import PluginTaskHelper

    helper = PluginTaskHelper()
    task = helper.create_special_task(db, "get_vinted_user_profile", platform="vinted")
    return await helper.wait_for_task_completion(db, task.id, timeout)


async def refresh_vinted_session(
    db: Session, job_id: Optional[int] = None, timeout: int = 30
) -> dict[str, Any]:
    """
    Rafraîchit la session Vinted via /web/api/auth/refresh.

    Crée une tâche refresh_vinted_session qui demande au plugin de :
    1. Appeler /web/api/auth/refresh pour régénérer les cookies de session
    2. Réinitialiser l'instance Axios de Vinted

    Utilisé par le job processor quand une tâche retourne 401 (session expirée).

    Args:
        db: Session SQLAlchemy
        job_id: ID du job parent (optionnel, pour logs)
        timeout: Timeout en secondes (défaut: 30s)

    Returns:
        dict: {
            "success": bool,
            "refreshed": bool,
            "timestamp": str
        }

    Raises:
        TimeoutError: Si le plugin ne répond pas
        Exception: Si le refresh échoue (401 = session vraiment expirée)

    Example:
        result = await refresh_vinted_session(db, job_id=job.id)
        if result['success']:
            # Session refreshed, retry la tâche originale
            pass
        else:
            # Session vraiment expirée, demander reconnexion
            raise Exception("Vinted session expired, please reconnect")
    """
    # Import here to avoid circular dependency
    from services.plugin_task_helper import PluginTaskHelper

    logger.info(
        f"[PluginTaskHelper] Refreshing Vinted session"
        f"{f' (job_id={job_id})' if job_id else ''}"
    )

    helper = PluginTaskHelper()
    task = helper.create_special_task(
        db, "refresh_vinted_session", platform="vinted", job_id=job_id
    )
    return await helper.wait_for_task_completion(db, task.id, timeout)


async def create_and_wait_with_401_handling(
    db: Session,
    http_method: str,
    path: str,
    payload: Optional[dict] = None,
    timeout: int = 60,
    max_refresh_attempts: int = 1,
    rate_limit: bool = True,
    job_id: Optional[int] = None,
    **kwargs,
) -> dict[str, Any]:
    """
    Like create_and_wait but with automatic 401 handling and session refresh.

    If the task fails with 401 (session expired):
    1. Creates a refresh_vinted_session task
    2. If refresh succeeds, retries the original task
    3. If refresh fails, raises exception

    This is the BACKEND-DRIVEN approach: the plugin just reports 401,
    the backend decides when to refresh and retry.

    Args:
        db: Session SQLAlchemy
        http_method: GET, POST, PUT, DELETE
        path: URL complète
        payload: Body de la requête
        timeout: Timeout en secondes
        max_refresh_attempts: Max number of session refresh attempts (default: 1)
        rate_limit: Si True, applique un délai aléatoire (défaut: True)
        job_id: ID du job parent (optionnel, pour logs)
        **kwargs: Arguments supplémentaires pour create_http_task

    Returns:
        dict: Task result (data)

    Raises:
        Exception: If task fails after all retry attempts
        TimeoutError: If timeout exceeded

    Example:
        # Will automatically retry once if 401 is received:
        result = await create_and_wait_with_401_handling(
            db, "GET", "/api/v2/users/current",
            max_refresh_attempts=1
        )
    """
    # Import here to avoid circular dependency
    from services.plugin_task_helper import PluginTaskHelper

    refresh_attempts = 0
    helper = PluginTaskHelper()

    while True:
        # Apply rate limiting if enabled
        if rate_limit:
            await VintedRateLimiter.wait_before_request(path, http_method)

        # Create the HTTP task
        task = helper.create_http_task(
            db, http_method, path, payload, job_id=job_id, **kwargs
        )

        logger.debug(
            f"[401Handler] Created task #{task.id} - {http_method} {path[:50]}..."
            f" (refresh_attempts={refresh_attempts})"
        )

        # Wait for completion (polling manually to get task object)
        start_time = time.time()
        poll_interval = 1.0

        while time.time() - start_time < timeout:
            db.expire_all()
            task = db.query(PluginTask).filter(PluginTask.id == task.id).first()

            if not task:
                raise ValueError(f"Task #{task.id} not found")

            if task.status == TaskStatus.SUCCESS:
                # Success - return data
                logger.debug(f"[401Handler] Task #{task.id} succeeded")
                if task.result and "data" in task.result:
                    return task.result["data"]
                return task.result or {}

            elif task.status == TaskStatus.FAILED:
                # Check if this is a 401 requiring refresh
                requires_refresh = task.result and task.result.get(
                    "requires_refresh", False
                )

                if requires_refresh and refresh_attempts < max_refresh_attempts:
                    refresh_attempts += 1
                    logger.warning(
                        f"[401Handler] Task #{task.id} failed with 401 - "
                        f"Attempting session refresh ({refresh_attempts}/{max_refresh_attempts})"
                    )

                    try:
                        # Call refresh_vinted_session
                        refresh_result = await refresh_vinted_session(
                            db, job_id=job_id, timeout=30
                        )

                        if refresh_result.get("success"):
                            logger.info(
                                f"[401Handler] Session refreshed, retrying task"
                            )
                            break  # Break inner while to retry outer while
                        else:
                            raise Exception(
                                "Vinted session refresh failed: "
                                f"{refresh_result.get('error', 'Unknown error')}"
                            )

                    except Exception as refresh_error:
                        logger.error(
                            f"[401Handler] Session refresh failed: {refresh_error}"
                        )
                        raise Exception(
                            f"Vinted session expired and refresh failed: {refresh_error}"
                        )

                elif requires_refresh:
                    # Max refresh attempts reached
                    raise Exception(
                        f"Task #{task.id} failed with 401: max refresh attempts "
                        f"({max_refresh_attempts}) reached"
                    )
                else:
                    # Normal failure (not 401)
                    error_msg = task.error_message or "Unknown error"
                    raise Exception(f"Task #{task.id} failed: {error_msg}")

            elif task.status == TaskStatus.TIMEOUT:
                raise TimeoutError(f"Task #{task.id} timeout (marked by plugin)")

            elif task.status == TaskStatus.CANCELLED:
                raise Exception(f"Task #{task.id} cancelled")

            await asyncio.sleep(poll_interval)

        else:
            # Timeout reached (while loop completed without break)
            elapsed = time.time() - start_time
            try:
                db.expire_all()
                task = db.query(PluginTask).filter(PluginTask.id == task.id).first()
                if task and task.status in (TaskStatus.PENDING, TaskStatus.PROCESSING):
                    task.status = TaskStatus.CANCELLED
                    task.error_message = f"Backend timeout after {elapsed:.2f}s"
                    task.completed_at = datetime.now(timezone.utc)
                    commit_and_restore_path(db)
            except Exception as e:
                logger.error(f"[401Handler] Error cancelling task #{task.id}: {e}")

            raise TimeoutError(f"Task #{task.id} timeout after {elapsed:.2f}s")

        # If we broke out of inner while (after refresh), continue outer while to retry
        continue


__all__ = [
    "verify_vinted_connection",
    "verify_vinted_connection_with_profile",
    "refresh_vinted_session",
    "create_and_wait_with_401_handling",
]
