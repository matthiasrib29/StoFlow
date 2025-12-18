"""
Plugin Task Service

Gere les taches a executer par le plugin browser.

Business Rules (2025-12-06):
- Le backend cree des taches (PENDING)
- Le plugin poll GET /api/plugin/tasks toutes les 5s
- Le plugin execute et retourne le resultat
- Les taches expirent apres 1h (TIMEOUT)

Author: Claude
Date: 2025-12-06
"""

from datetime import datetime, timedelta, timezone
from sqlalchemy import func
from sqlalchemy.orm import Session

from models.user.plugin_task import PluginTask, TaskStatus


class PluginTaskService:
    """
    Service pour gerer les taches du plugin.

    DEPRECATED: Préférer PluginTaskHelper pour créer des tâches :
    - create_http_task() pour les requêtes HTTP
    - create_special_task() pour les tâches non-HTTP
    - verify_vinted_connection() pour vérifier la connexion
    """

    @staticmethod
    def get_pending_tasks(
        db: Session,
        limit: int = 10
    ) -> list[PluginTask]:
        """
        Recupere les taches en attente pour le plugin.

        Business Rules:
        - Retourne seulement les taches PENDING
        - Trie par date de creation (FIFO)
        - Limite configurable (defaut 10)
        - Marque automatiquement les taches expirees comme TIMEOUT

        Args:
            db: Session DB
            limit: Nombre max de taches a retourner

        Returns:
            Liste des taches PENDING
        """
        # Marquer les taches expirees (> 1h) comme TIMEOUT
        timeout_threshold = datetime.now(timezone.utc) - timedelta(hours=1)

        db.query(PluginTask).filter(
            PluginTask.status == TaskStatus.PENDING,
            PluginTask.created_at < timeout_threshold
        ).update({
            "status": TaskStatus.TIMEOUT,
            "error_message": "Task expired after 1 hour",
            "completed_at": func.now()
        })
        db.commit()

        # Recuperer les taches PENDING
        tasks = db.query(PluginTask).filter(
            PluginTask.status == TaskStatus.PENDING
        ).order_by(
            PluginTask.created_at.asc()
        ).limit(limit).all()

        return tasks

    @staticmethod
    def mark_task_processing(
        db: Session,
        task_id: int
    ) -> PluginTask | None:
        """
        Marque une tache comme en cours d'execution.

        Business Rules:
        - Change status: PENDING -> PROCESSING
        - Enregistre started_at

        Args:
            db: Session DB
            task_id: ID de la tache

        Returns:
            Tache mise a jour ou None si introuvable
        """
        task = db.query(PluginTask).filter(PluginTask.id == task_id).first()

        if not task:
            return None

        task.status = TaskStatus.PROCESSING
        task.started_at = func.now()

        db.commit()
        db.refresh(task)

        return task

    @staticmethod
    def complete_task_success(
        db: Session,
        task_id: int,
        result: dict
    ) -> PluginTask | None:
        """
        Marque une tache comme reussie.

        Business Rules:
        - Change status: PROCESSING -> SUCCESS
        - Enregistre le resultat retourne par le plugin
        - Enregistre completed_at

        Args:
            db: Session DB
            task_id: ID de la tache
            result: Resultat retourne par le plugin

        Returns:
            Tache mise a jour ou None si introuvable
        """
        task = db.query(PluginTask).filter(PluginTask.id == task_id).first()

        if not task:
            return None

        task.status = TaskStatus.SUCCESS
        task.result = result
        task.completed_at = func.now()

        db.commit()
        db.refresh(task)

        return task

    @staticmethod
    def complete_task_failed(
        db: Session,
        task_id: int,
        error_message: str,
        error_details: dict | None = None
    ) -> PluginTask | None:
        """
        Marque une tache comme echouee.

        Business Rules:
        - Incremente retry_count
        - Si retry_count < max_retries: status = PENDING (retry)
        - Si retry_count >= max_retries: status = FAILED (abandon)
        - Enregistre l'erreur

        Args:
            db: Session DB
            task_id: ID de la tache
            error_message: Message d'erreur
            error_details: Details supplementaires (optionnel)

        Returns:
            Tache mise a jour ou None si introuvable
        """
        task = db.query(PluginTask).filter(PluginTask.id == task_id).first()

        if not task:
            return None

        task.retry_count += 1
        task.error_message = error_message

        if error_details:
            task.result = error_details

        # Retry ou abandon
        if task.retry_count < task.max_retries:
            task.status = TaskStatus.PENDING  # Retry
        else:
            task.status = TaskStatus.FAILED  # Abandon
            task.completed_at = func.now()

        db.commit()
        db.refresh(task)

        return task

    @staticmethod
    def cancel_task(
        db: Session,
        task_id: int
    ) -> PluginTask | None:
        """
        Annule une tache.

        Business Rules:
        - Change status -> CANCELLED
        - Enregistre completed_at

        Args:
            db: Session DB
            task_id: ID de la tache

        Returns:
            Tache mise a jour ou None si introuvable
        """
        task = db.query(PluginTask).filter(PluginTask.id == task_id).first()

        if not task:
            return None

        task.status = TaskStatus.CANCELLED
        task.completed_at = func.now()

        db.commit()
        db.refresh(task)

        return task

    @staticmethod
    def get_task_by_id(
        db: Session,
        task_id: int
    ) -> PluginTask | None:
        """
        Recupere une tache par ID.

        Args:
            db: Session DB
            task_id: ID de la tache

        Returns:
            Tache ou None si introuvable
        """
        return db.query(PluginTask).filter(PluginTask.id == task_id).first()

