"""
Plugin Task Helper - Utilitaires pour orchestration synchrone des tâches plugin

Inspiré de l'architecture pythonApiWOO où le backend garde le contrôle
du flux d'exécution via des appels synchrones.

Business Rules (2025-12-12):
- Le backend orchestre step-by-step comme avec requests.post()
- wait_for_task_completion() attend qu'une tâche soit complétée
- Le backend garde le contexte, pas besoin de TaskType pour routing
- Timeout configurable par tâche (défaut: 60s)
- Rate limiting avec délais aléatoires pour éviter détection bot

Architecture:
- Crée tâche → Attend completion → Traite résultat → Étape suivante
- Poll DB toutes les 1s (configurable)
- Pas de callback async, juste await synchrone

Author: Claude
Date: 2025-12-12
"""

import asyncio
import random
import re
import time
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from models.user.plugin_task import PluginTask, TaskStatus
from shared.logging_setup import get_logger

logger = get_logger(__name__)


def _get_current_schema(db: Session) -> Optional[str]:
    """
    Récupère le schéma utilisateur actuel depuis le search_path.

    Returns:
        str ou None: Le nom du schéma user_X ou None si non trouvé
    """
    result = db.execute(text("SHOW search_path"))
    path = result.scalar()
    if path:
        # Chercher un schéma user_X dans le path
        for schema in path.split(","):
            schema = schema.strip().strip('"')
            if schema.startswith("user_"):
                return schema
    return None


def _restore_search_path(db: Session, schema_name: str) -> None:
    """
    Restaure le search_path après un commit.

    SET LOCAL ne persiste que pendant une transaction.
    Après db.commit(), on doit reconfigurer le search_path.
    """
    db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))


def _commit_and_restore_path(db: Session) -> None:
    """
    Fait un commit et restaure le search_path.

    Pattern pour éviter que SET LOCAL soit perdu après commit.
    """
    # Capturer le schema avant le commit
    schema = _get_current_schema(db)

    # Commit
    db.commit()

    # Restaurer le search_path
    if schema:
        _restore_search_path(db, schema)


# =============================================================================
# RATE LIMITER - Anti-bot detection
# =============================================================================

class VintedRateLimiter:
    """
    Rate limiter avec délais aléatoires pour éviter la détection bot.

    Configuration:
    - Délais différents selon le type d'opération
    - Randomisation pour simuler comportement humain
    - Tracking du dernier appel pour espacement minimum
    """

    # Configuration des délais par pattern d'URL (min_delay, max_delay en secondes)
    DELAY_CONFIG = {
        # Opérations sensibles - délais longs
        'item_upload': (3.0, 6.0),       # Création de produit
        'items/.*/delete': (2.5, 5.0),   # Suppression
        'photos': (2.0, 4.0),            # Upload d'images

        # Opérations de lecture - délais courts
        'wardrobe': (0.5, 1.5),          # Liste produits
        'my_orders': (0.5, 1.5),         # Commandes
        'users': (0.3, 1.0),             # Info utilisateur

        # Par défaut
        'default': (0.3, 1.0),
    }

    # Multiplicateur pour les opérations d'écriture (PUT/DELETE)
    WRITE_MULTIPLIER = 1.8

    # Espacement minimum entre requêtes (en secondes)
    MIN_SPACING = 0.5

    _last_request_time: float = 0
    _request_count: int = 0

    @classmethod
    def _get_delay_config(cls, path: str) -> tuple[float, float]:
        """Retourne (min_delay, max_delay) pour une URL donnée."""
        for pattern, delays in cls.DELAY_CONFIG.items():
            if pattern == 'default':
                continue
            if re.search(pattern, path, re.IGNORECASE):
                return delays
        return cls.DELAY_CONFIG['default']

    @classmethod
    async def wait_before_request(cls, path: str, http_method: str = 'GET') -> float:
        """
        Attend un délai aléatoire avant d'exécuter une requête.

        Args:
            path: URL de la requête
            http_method: GET, POST, PUT, DELETE

        Returns:
            float: Délai effectif appliqué en secondes
        """
        min_delay, max_delay = cls._get_delay_config(path)

        # Augmenter le délai pour les opérations d'écriture
        if http_method in ('POST', 'PUT', 'DELETE'):
            min_delay *= cls.WRITE_MULTIPLIER
            max_delay *= cls.WRITE_MULTIPLIER

        # Calculer délai aléatoire
        delay = random.uniform(min_delay, max_delay)

        # Assurer espacement minimum depuis la dernière requête
        time_since_last = time.time() - cls._last_request_time
        if time_since_last < cls.MIN_SPACING:
            extra_wait = cls.MIN_SPACING - time_since_last
            delay = max(delay, extra_wait)

        # Ajouter une variation supplémentaire tous les 10 appels
        cls._request_count += 1
        if cls._request_count % 10 == 0:
            # Pause plus longue périodiquement (simule une pause humaine)
            delay += random.uniform(1.0, 3.0)
            logger.debug(f"[RateLimiter] Pause périodique ajoutée (requête #{cls._request_count})")

        if delay > 0:
            logger.debug(f"[RateLimiter] Attente {delay:.2f}s avant {http_method} {path[:50]}...")
            await asyncio.sleep(delay)

        cls._last_request_time = time.time()
        return delay

    @classmethod
    def reset(cls):
        """Reset le compteur (utile pour les tests)."""
        cls._last_request_time = 0
        cls._request_count = 0


# =============================================================================
# PLUGIN TASK HELPER
# =============================================================================

class PluginTaskHelper:
    """
    Helper pour orchestration synchrone des tâches plugin.

    Permet au backend de contrôler le flux d'exécution comme avec pythonApiWOO :

    Example:
        # Au lieu de :
        response = requests.post("/api/vinted/photos", files=...)
        photo_id = response.json()['id']

        # On fait :
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
        description: Optional[str] = None
    ) -> PluginTask:
        """
        Crée une tâche HTTP simple pour le plugin.

        Args:
            db: Session SQLAlchemy (user schema)
            http_method: GET, POST, PUT, DELETE
            path: URL complète (ex: "https://www.vinted.fr/api/v2/photos")
            payload: Body de la requête (optionnel)
            platform: Plateforme cible (défaut: vinted)
            product_id: ID produit associé (optionnel)
            job_id: ID du job parent (optionnel, pour orchestration)
            description: Description pour logs (optionnel)

        Returns:
            PluginTask créée et persistée en DB

        Example:
            task = create_http_task(
                db, "POST", "https://www.vinted.fr/api/v2/photos",
                payload={"body": photo_data},
                job_id=job.id
            )
        """
        task = PluginTask(
            platform=platform,
            task_type=None,  # Pas de task_type, juste HTTP
            status=TaskStatus.PENDING,
            http_method=http_method,
            path=path,
            payload=payload or {},
            product_id=product_id,
            job_id=job_id,
            created_at=datetime.now(timezone.utc)
        )

        db.add(task)
        _commit_and_restore_path(db)  # Commit + restaure search_path
        db.refresh(task)

        logger.debug(
            f"[PluginTaskHelper] Tâche créée #{task.id} - "
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
        job_id: Optional[int] = None
    ) -> PluginTask:
        """
        Crée une tâche spéciale non-HTTP pour le plugin.

        Utilisé pour les opérations qui ne sont pas des requêtes HTTP :
        - get_vinted_user_info: Extraction userId/login depuis DOM

        Args:
            db: Session SQLAlchemy (user schema)
            task_type: Type de tâche spéciale (ex: "get_vinted_user_info")
            platform: Plateforme cible (défaut: vinted)
            payload: Données additionnelles (optionnel)
            product_id: ID produit associé (optionnel)
            job_id: ID du job parent (optionnel, pour orchestration)

        Returns:
            PluginTask créée et persistée en DB

        Example:
            task = create_special_task(db, "get_vinted_user_info")
            result = await wait_for_task_completion(db, task.id)
            if result['connected']:
                print(f"Connecté: {result['login']}")
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
            created_at=datetime.now(timezone.utc)
        )

        db.add(task)
        _commit_and_restore_path(db)  # Commit + restaure search_path
        db.refresh(task)

        logger.debug(f"[PluginTaskHelper] Tâche spéciale créée #{task.id} - {task_type}")

        return task

    @staticmethod
    async def wait_for_task_completion(
        db: Session,
        task_id: int,
        timeout: int = 60,
        poll_interval: float = 1.0
    ) -> dict[str, Any]:
        """
        Attend qu'une tâche soit complétée (comme requests.post() bloque).

        Args:
            db: Session SQLAlchemy
            task_id: ID de la tâche à attendre
            timeout: Timeout en secondes (défaut: 60s)
            poll_interval: Intervalle de polling en secondes (défaut: 1s)

        Returns:
            dict: task.result['data'] si succès

        Raises:
            TimeoutError: Si timeout dépassé
            Exception: Si la tâche échoue (avec task.error_message)

        Example:
            task = create_http_task(db, "POST", "/api/v2/photos", ...)
            result = await wait_for_task_completion(db, task.id, timeout=30)
            photo_id = result['id']
        """
        start_time = time.time()

        logger.debug(
            f"[PluginTaskHelper] Attente tâche #{task_id} "
            f"(timeout: {timeout}s, poll: {poll_interval}s)"
        )

        while time.time() - start_time < timeout:
            # Refresh task depuis DB
            db.expire_all()  # Force refresh
            task = db.query(PluginTask).filter(PluginTask.id == task_id).first()

            if not task:
                raise ValueError(f"Tâche #{task_id} introuvable")

            # Vérifier status
            if task.status == TaskStatus.SUCCESS:
                elapsed = time.time() - start_time
                logger.debug(
                    f"[PluginTaskHelper] Tâche #{task_id} complétée "
                    f"(elapsed: {elapsed:.2f}s)"
                )

                # Retourner juste la data (comme response.json())
                if task.result and 'data' in task.result:
                    return task.result['data']
                else:
                    return task.result or {}

            elif task.status == TaskStatus.FAILED:
                error_msg = task.error_message or "Erreur inconnue"
                logger.error(
                    f"[PluginTaskHelper] Tâche #{task_id} échouée: {error_msg}"
                )
                raise Exception(f"Task #{task_id} failed: {error_msg}")

            elif task.status == TaskStatus.TIMEOUT:
                raise TimeoutError(f"Task #{task_id} timeout (marquée par le plugin)")

            elif task.status == TaskStatus.CANCELLED:
                raise Exception(f"Task #{task_id} cancelled")

            # Attendre avant retry
            await asyncio.sleep(poll_interval)

        # Timeout dépassé - MARQUER LA TÂCHE COMME CANCELLED
        # CRITICAL (2025-12-18): Évite que la tâche reste PENDING et soit
        # récupérée au prochain poll du plugin → flood Vinted
        elapsed = time.time() - start_time

        # Annuler la tâche en BDD
        try:
            db.expire_all()
            task = db.query(PluginTask).filter(PluginTask.id == task_id).first()
            if task and task.status in (TaskStatus.PENDING, TaskStatus.PROCESSING):
                task.status = TaskStatus.CANCELLED
                task.error_message = f"Backend timeout after {elapsed:.2f}s"
                task.completed_at = datetime.now(timezone.utc)
                _commit_and_restore_path(db)
                logger.warning(
                    f"[PluginTaskHelper] Tâche #{task_id} ANNULÉE après timeout "
                    f"(elapsed: {elapsed:.2f}s, http_method={task.http_method}, "
                    f"path={task.path[:100] if task.path else 'N/A'})"
                )
        except Exception as e:
            logger.error(
                f"[PluginTaskHelper] Erreur annulation tâche #{task_id}: {e}",
                exc_info=True
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
    **kwargs
) -> dict[str, Any]:
    """
    Helper all-in-one : crée une tâche et attend son résultat.

    Équivalent de requests.post() mais via plugin.
    Inclut rate limiting automatique pour éviter détection bot.

    Args:
        db: Session SQLAlchemy
        http_method: GET, POST, PUT, DELETE
        path: URL complète
        payload: Body de la requête
        timeout: Timeout en secondes
        rate_limit: Si True, applique un délai aléatoire (défaut: True)
        **kwargs: Arguments supplémentaires pour create_http_task

    Example:
        # Au lieu de :
        response = requests.post(url, json=data)
        result = response.json()

        # Faire :
        result = await create_and_wait(db, "POST", url, payload={"body": data})
    """
    # Appliquer rate limiting si activé
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
    **kwargs
) -> dict[str, Any]:
    """
    Comme create_and_wait mais SANS rate limiting.

    Utile pour les requêtes internes ou urgentes.
    """
    return await create_and_wait(
        db, http_method, path, payload, timeout,
        rate_limit=False, **kwargs
    )


async def verify_vinted_connection(
    db: Session,
    timeout: int = 30
) -> dict[str, Any]:
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
    helper = PluginTaskHelper()
    task = helper.create_special_task(db, "get_vinted_user_info", platform="vinted")
    return await helper.wait_for_task_completion(db, task.id, timeout)


async def verify_vinted_connection_with_profile(
    db: Session,
    timeout: int = 30
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
    helper = PluginTaskHelper()
    task = helper.create_special_task(db, "get_vinted_user_profile", platform="vinted")
    return await helper.wait_for_task_completion(db, task.id, timeout)
