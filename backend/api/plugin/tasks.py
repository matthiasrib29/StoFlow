"""
Plugin Task Queue Routes

Routes for task queue management (long polling, task results).

Business Rules (Updated: 2025-12-18):
- Long Polling: la requête reste ouverte jusqu'à ce qu'une tâche soit disponible
- Le backend orchestre step-by-step avec async/await
- Tasks marquées PROCESSING pour éviter les doublons
- Rate Limiting: execute_delay_ms indique au plugin d'attendre avant exécution

Author: Claude
Date: 2025-12-17
Updated: 2025-12-18 - Added execute_delay_ms for rate limiting
"""

import asyncio
import json
import logging
import random
import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_user_db
from models.user.plugin_task import PluginTask, TaskStatus
from shared.datetime_utils import utc_now

from .schemas import PendingTasksResponse, PluginTaskResponse, TaskResultRequest

router = APIRouter()
logger = logging.getLogger(__name__)


# ===== LONG POLLING CONFIG =====
LONG_POLL_TIMEOUT_SEC = 30  # Timeout max pour le long polling (30 secondes)
LONG_POLL_CHECK_INTERVAL = 1  # Vérifier la DB toutes les 1 seconde


# ===== RATE LIMITING CONFIG (2025-12-18) =====
# Délais en millisecondes que le plugin doit attendre AVANT d'exécuter une tâche
# CRITIQUE: Ces délais évitent le flood des APIs externes et le risque de ban
# Configuré: 1-2s entre chaque requête

# Configuration par pattern d'URL (min_delay_ms, max_delay_ms)
# UPDATED 2025-12-22: Increased delays to avoid DataDome 403 errors
RATE_LIMIT_DELAYS = {
    # Opérations sensibles - délais plus longs
    'item_upload': (3000, 5000),        # Création de produit: 3-5s
    'items/.*/delete': (3000, 5000),    # Suppression: 3-5s
    'photos': (3000, 5000),             # Upload d'images: 3-5s

    # Opérations de lecture - délais 2-4s (increased from 1-2s)
    'wardrobe': (2000, 4000),           # Liste produits: 2-4s
    'my_orders': (2000, 4000),          # Commandes: 2-4s
    'items/': (2500, 4500),             # Détail produit (HTML): 2.5-4.5s (most sensitive)

    # Par défaut: 2-3s (increased from 1-2s)
    'default': (2000, 3000),
}

# Multiplicateur pour les opérations d'écriture (POST/PUT/DELETE)
WRITE_MULTIPLIER = 1.5

# Délai minimum absolu (en ms)
MIN_ABSOLUTE_DELAY_MS = 1000


def _calculate_execute_delay(path: str | None, http_method: str | None) -> int:
    """
    Calcule le délai d'exécution en ms pour une tâche.

    Le plugin DOIT attendre ce délai avant d'exécuter la requête.
    Cela évite le flood des APIs externes (Vinted, eBay, etc.).

    Args:
        path: URL de la tâche
        http_method: Méthode HTTP (GET, POST, etc.)

    Returns:
        int: Délai en millisecondes
    """
    if not path:
        return MIN_ABSOLUTE_DELAY_MS

    # Trouver le pattern correspondant
    min_delay, max_delay = RATE_LIMIT_DELAYS['default']
    for pattern, delays in RATE_LIMIT_DELAYS.items():
        if pattern == 'default':
            continue
        if re.search(pattern, path, re.IGNORECASE):
            min_delay, max_delay = delays
            break

    # Calculer délai aléatoire
    delay = random.randint(min_delay, max_delay)

    # Augmenter pour les opérations d'écriture
    if http_method and http_method.upper() in ('POST', 'PUT', 'DELETE'):
        delay = int(delay * WRITE_MULTIPLIER)

    return max(delay, MIN_ABSOLUTE_DELAY_MS)


def _fetch_pending_tasks(db: Session, limit: int) -> list:
    """
    Helper: Récupère les tâches PENDING depuis la DB.
    Filtre pour ne garder qu'une tâche par plateforme (FIFO).
    """
    # Expirer le cache SQLAlchemy pour avoir des données fraîches
    db.expire_all()

    tasks = (
        db.query(PluginTask)
        .filter(PluginTask.status == TaskStatus.PENDING, PluginTask.platform.isnot(None))
        .order_by(PluginTask.created_at)
        .limit(limit)
        .all()
    )

    # Filtrer pour ne garder qu'une task par plateforme (FIFO)
    seen_platforms = set()
    filtered_tasks = []
    for task in tasks:
        if task.platform not in seen_platforms:
            seen_platforms.add(task.platform)
            filtered_tasks.append(task)

    return filtered_tasks


def _build_task_response(task: PluginTask) -> PluginTaskResponse:
    """
    Helper: Construit une PluginTaskResponse depuis une PluginTask.
    Doit être appelé AVANT le commit (search_path perdu après).

    Rate Limiting (2025-12-18):
    - Calcule execute_delay_ms pour chaque tâche
    - Le plugin DOIT attendre ce délai avant d'exécuter
    """
    params = None
    payload = task.payload or {}
    if "params" in payload:
        params = payload.get("params")
        payload = {k: v for k, v in payload.items() if k != "params"}

    # Calculer le délai d'exécution pour rate limiting
    execute_delay = _calculate_execute_delay(task.path, task.http_method)

    return PluginTaskResponse(
        id=task.id,
        platform=task.platform,
        http_method=task.http_method,
        path=task.path,
        params=params,
        payload=payload,
        task_type=task.task_type,
        execute_delay_ms=execute_delay,
        created_at=task.created_at,
    )


@router.get("/tasks", response_model=PendingTasksResponse, status_code=status.HTTP_200_OK)
async def get_tasks_with_long_polling(
    user_db: tuple = Depends(get_user_db),
    timeout: int = 30,
    limit: int = 10,
):
    """
    Récupère les tâches en attente avec LONG POLLING.

    Business Rules (2025-12-17):
    - Long Polling: la requête reste ouverte jusqu'à ce qu'une tâche soit disponible
    - Timeout par défaut: 30 secondes
    - Si tâches disponibles → retour immédiat
    - Si pas de tâches → attente jusqu'à timeout ou nouvelle tâche
    - Le plugin doit relancer immédiatement une nouvelle requête après réponse

    Args:
        user_db: Tuple (db, current_user) avec search_path configuré
        timeout: Timeout en secondes (default 30, max 60)
        limit: Nombre max de tâches (default 10)

    Returns:
        PendingTasksResponse: Tâches trouvées (ou vide si timeout)
    """
    db, current_user = user_db

    # Limiter le timeout à la config max
    timeout = min(timeout, LONG_POLL_TIMEOUT_SEC)
    elapsed = 0

    # Long Polling loop: attendre jusqu'à avoir des tâches ou timeout
    filtered_tasks = []
    while elapsed < timeout:
        filtered_tasks = _fetch_pending_tasks(db, limit)

        if filtered_tasks:
            # Tâches trouvées → sortir de la boucle
            logger.debug(
                f"[Long Polling] User {current_user.id}: {len(filtered_tasks)} tâche(s) trouvée(s) après {elapsed}s"
            )
            break

        # Pas de tâches → attendre 1 seconde et réessayer
        await asyncio.sleep(LONG_POLL_CHECK_INTERVAL)
        elapsed += LONG_POLL_CHECK_INTERVAL

    # Construire la liste des tasks AVANT le commit
    # (après commit, le search_path est perdu et SQLAlchemy ne peut plus charger les attributs)
    task_responses = [_build_task_response(task) for task in filtered_tasks]

    # Marquer les tâches comme PROCESSING pour éviter les doublons
    for task in filtered_tasks:
        task.status = TaskStatus.PROCESSING
        task.started_at = utc_now()

    if filtered_tasks:
        db.commit()

    has_tasks = len(task_responses) > 0

    if not has_tasks:
        logger.debug(f"[Long Polling] User {current_user.id}: timeout après {timeout}s, aucune tâche")

    return PendingTasksResponse(
        tasks=task_responses,
        next_poll_interval_ms=0,  # Long polling: relancer immédiatement
        has_pending_tasks=has_tasks,
    )


@router.get(
    "/tasks/pending",
    response_model=list[PluginTaskResponse],
    status_code=status.HTTP_200_OK,
    deprecated=True,
)
async def get_pending_tasks(
    user_db: tuple = Depends(get_user_db),
    limit: int = 10,
):
    """
    [DEPRECATED] Utiliser GET /tasks à la place.

    Récupère les tâches en attente (format legacy sans polling adaptatif).
    """
    db, current_user = user_db

    tasks = (
        db.query(PluginTask)
        .filter(PluginTask.status == TaskStatus.PENDING, PluginTask.platform.isnot(None))
        .order_by(PluginTask.created_at)
        .limit(limit)
        .all()
    )

    seen_platforms = set()
    filtered_tasks = []
    for task in tasks:
        if task.platform not in seen_platforms:
            seen_platforms.add(task.platform)
            filtered_tasks.append(task)

    # Construire les réponses AVANT le commit
    result = [_build_task_response(task) for task in filtered_tasks]

    # Marquer les tâches comme PROCESSING pour éviter les doublons
    for task in filtered_tasks:
        task.status = TaskStatus.PROCESSING
        task.started_at = utc_now()

    if filtered_tasks:
        db.commit()

    return result


@router.post("/tasks/{task_id}/result", status_code=status.HTTP_200_OK)
async def submit_task_result(
    task_id: int,
    result: TaskResultRequest,
    user_db: tuple = Depends(get_user_db),
):
    """
    Soumet le resultat d'execution d'une tache.

    Architecture simplifiée (2025-12-12):
    - Le backend orchestre step-by-step avec create_and_wait()
    - Cet endpoint fait JUSTE: marquer SUCCESS/FAILED + stocker résultat
    - create_and_wait() détecte automatiquement le changement de status
    - Pas de Queue, pas de génération de next step ici

    Args:
        task_id: ID de la tache
        result: Resultat d'execution
        user_db: Tuple (db, current_user) avec search_path configuré

    Returns:
        dict: Confirmation du traitement
    """
    db, current_user = user_db

    # DEBUG: Log what we receive from plugin (sans exposer tokens/secrets)
    logger.debug(f"[submit_task_result] Task {task_id} - success={result.success}")
    if result.result:
        # Ne logger que les clés, pas les valeurs (risque tokens/secrets)
        safe_keys = list(result.result.keys()) if isinstance(result.result, dict) else None
        logger.debug(f"[submit_task_result] Result keys: {safe_keys}")

    # Récupérer la task
    task = db.query(PluginTask).filter(PluginTask.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )

    # Sauvegarder les valeurs AVANT le commit (search_path perdu après commit)
    task_id_val = task.id
    task_http_method = task.http_method
    task_path = task.path

    if result.success:
        # ===== SUCCÈS =====
        task.status = TaskStatus.SUCCESS
        task.result = result.result or {}
        task.completed_at = utc_now()

        db.commit()

        logger.info(f"Task #{task_id_val} SUCCESS - {task_http_method} {task_path}")

        return {
            "success": True,
            "task_id": task_id_val,
            "status": TaskStatus.SUCCESS.value,
            "message": f"Task {task_id} completed successfully",
        }

    else:
        # ===== ÉCHEC =====
        error_message = result.error_message or "Unknown error"
        error_details = result.error_details or {}
        http_status = error_details.get("status_code") or error_details.get("status")

        # Marquer comme FAILED (pas de retry pour Vinted API errors)
        task.status = TaskStatus.FAILED
        task.error_message = error_message
        task.result = error_details
        task.completed_at = utc_now()

        db.commit()

        logger.warning(
            f"Task #{task_id_val} FAILED - {task_http_method} {task_path} - "
            f"HTTP {http_status}: {error_message}"
        )

        return {
            "success": False,
            "task_id": task_id_val,
            "status": TaskStatus.FAILED.value,
            "message": f"Task {task_id} failed: {error_message}",
            "error": {
                "message": error_message,
                "http_status": http_status,
                "details": error_details,
            },
        }
