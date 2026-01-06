"""
Plugin Task Repository

Repository pour la gestion des PluginTask.
Responsabilité: Accès données pour plugin_tasks (schema user_{id}).

Architecture:
- Repository pattern pour isolation DB
- Opérations CRUD standards
- Queries optimisées avec indexes
- Filtres par status, job_id, etc.

Created: 2026-01-06
Author: Claude
"""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from models.user.plugin_task import PluginTask, TaskStatus
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class PluginTaskRepository:
    """
    Repository pour la gestion des PluginTask.

    Fournit toutes les opérations CRUD et queries spécialisées.
    """

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    @staticmethod
    def create(db: Session, task: PluginTask) -> PluginTask:
        """
        Crée une nouvelle PluginTask.

        Args:
            db: Session SQLAlchemy
            task: Instance PluginTask à créer

        Returns:
            PluginTask: Instance créée avec ID assigné
        """
        db.add(task)
        db.commit()
        db.refresh(task)

        logger.info(
            f"[PluginTaskRepository] Task created: id={task.id}, "
            f"method={task.http_method}, path={task.path}"
        )

        return task

    @staticmethod
    def get_by_id(db: Session, task_id: int) -> Optional[PluginTask]:
        """
        Récupère une PluginTask par son ID.

        Args:
            db: Session SQLAlchemy
            task_id: ID de la task

        Returns:
            PluginTask si trouvée, None sinon
        """
        return db.query(PluginTask).filter(PluginTask.id == task_id).first()

    @staticmethod
    def update(db: Session, task: PluginTask) -> PluginTask:
        """
        Met à jour une PluginTask existante.

        Args:
            db: Session SQLAlchemy
            task: Instance PluginTask modifiée

        Returns:
            PluginTask: Instance mise à jour
        """
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def delete(db: Session, task_id: int) -> bool:
        """
        Supprime une PluginTask.

        Args:
            db: Session SQLAlchemy
            task_id: ID de la task à supprimer

        Returns:
            True si supprimée, False si non trouvée
        """
        task = db.query(PluginTask).filter(PluginTask.id == task_id).first()
        if not task:
            return False

        db.delete(task)
        db.commit()

        logger.info(f"[PluginTaskRepository] Task deleted: id={task_id}")
        return True

    # =========================================================================
    # Status Management
    # =========================================================================

    @staticmethod
    def update_status(
        db: Session,
        task_id: int,
        status: TaskStatus,
        result: Optional[dict] = None,
        error_message: Optional[str] = None
    ) -> Optional[PluginTask]:
        """
        Met à jour le status d'une task.

        Args:
            db: Session SQLAlchemy
            task_id: ID de la task
            status: Nouveau status
            result: Résultat JSON (optionnel)
            error_message: Message d'erreur (optionnel)

        Returns:
            PluginTask mise à jour ou None si non trouvée
        """
        task = db.query(PluginTask).filter(PluginTask.id == task_id).first()
        if not task:
            return None

        task.status = status

        if result is not None:
            task.result = result

        if error_message:
            task.error_message = error_message

        # Set timestamps based on status
        now = datetime.now(timezone.utc)
        if status == TaskStatus.PROCESSING and not task.started_at:
            task.started_at = now
        elif status in (TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.TIMEOUT, TaskStatus.CANCELLED):
            task.completed_at = now

        db.commit()
        db.refresh(task)

        logger.info(
            f"[PluginTaskRepository] Task status updated: id={task_id}, "
            f"status={status.value}"
        )

        return task

    @staticmethod
    def increment_retry(db: Session, task_id: int) -> Optional[PluginTask]:
        """
        Incrémente le compteur de retry d'une task.

        Args:
            db: Session SQLAlchemy
            task_id: ID de la task

        Returns:
            PluginTask mise à jour ou None si non trouvée
        """
        task = db.query(PluginTask).filter(PluginTask.id == task_id).first()
        if not task:
            return None

        task.retry_count += 1
        db.commit()
        db.refresh(task)
        return task

    # =========================================================================
    # Query Methods
    # =========================================================================

    @staticmethod
    def get_pending(db: Session, limit: int = 10) -> List[PluginTask]:
        """
        Récupère les tasks en attente.

        Args:
            db: Session SQLAlchemy
            limit: Nombre max de résultats

        Returns:
            Liste de PluginTask pending
        """
        return (
            db.query(PluginTask)
            .filter(PluginTask.status == TaskStatus.PENDING)
            .order_by(PluginTask.created_at.asc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_by_status(
        db: Session,
        status: TaskStatus,
        limit: int = 100
    ) -> List[PluginTask]:
        """
        Récupère les tasks par status.

        Args:
            db: Session SQLAlchemy
            status: Status à filtrer
            limit: Nombre max de résultats

        Returns:
            Liste de PluginTask
        """
        return (
            db.query(PluginTask)
            .filter(PluginTask.status == status)
            .order_by(PluginTask.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_by_job_id(db: Session, job_id: int) -> List[PluginTask]:
        """
        Récupère les tasks associées à un job.

        Args:
            db: Session SQLAlchemy
            job_id: ID du job parent

        Returns:
            Liste de PluginTask du job
        """
        return (
            db.query(PluginTask)
            .filter(PluginTask.job_id == job_id)
            .order_by(PluginTask.created_at.asc())
            .all()
        )

    @staticmethod
    def get_by_product_id(
        db: Session,
        product_id: int,
        status: Optional[TaskStatus] = None
    ) -> List[PluginTask]:
        """
        Récupère les tasks pour un produit donné.

        Args:
            db: Session SQLAlchemy
            product_id: ID du produit
            status: Filtrer par status (optionnel)

        Returns:
            Liste de PluginTask
        """
        query = db.query(PluginTask).filter(PluginTask.product_id == product_id)

        if status:
            query = query.filter(PluginTask.status == status)

        return query.order_by(PluginTask.created_at.desc()).all()

    @staticmethod
    def get_processing(db: Session, limit: int = 50) -> List[PluginTask]:
        """
        Récupère les tasks en cours d'exécution.

        Args:
            db: Session SQLAlchemy
            limit: Nombre max de résultats

        Returns:
            Liste de PluginTask en processing
        """
        return (
            db.query(PluginTask)
            .filter(PluginTask.status == TaskStatus.PROCESSING)
            .order_by(PluginTask.started_at.asc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_retryable(db: Session, limit: int = 50) -> List[PluginTask]:
        """
        Récupère les tasks qui peuvent être retentées.

        Args:
            db: Session SQLAlchemy
            limit: Nombre max de résultats

        Returns:
            Liste de PluginTask retryable (failed avec retry_count < max_retries)
        """
        return (
            db.query(PluginTask)
            .filter(
                and_(
                    PluginTask.status == TaskStatus.FAILED,
                    PluginTask.retry_count < PluginTask.max_retries
                )
            )
            .order_by(PluginTask.created_at.asc())
            .limit(limit)
            .all()
        )

    # =========================================================================
    # Bulk Operations
    # =========================================================================

    @staticmethod
    def cancel_by_job_id(db: Session, job_id: int) -> int:
        """
        Annule toutes les tasks pending d'un job.

        Args:
            db: Session SQLAlchemy
            job_id: ID du job

        Returns:
            Nombre de tasks annulées
        """
        count = (
            db.query(PluginTask)
            .filter(
                and_(
                    PluginTask.job_id == job_id,
                    PluginTask.status == TaskStatus.PENDING
                )
            )
            .update({
                PluginTask.status: TaskStatus.CANCELLED,
                PluginTask.completed_at: datetime.now(timezone.utc)
            })
        )
        db.commit()

        if count > 0:
            logger.info(
                f"[PluginTaskRepository] Cancelled {count} pending tasks for job_id={job_id}"
            )

        return count

    @staticmethod
    def delete_completed_older_than(db: Session, days: int = 7) -> int:
        """
        Supprime les tasks terminées plus anciennes que N jours.

        Args:
            db: Session SQLAlchemy
            days: Nombre de jours de rétention

        Returns:
            Nombre de tasks supprimées
        """
        from datetime import timedelta

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        terminal_statuses = [
            TaskStatus.SUCCESS,
            TaskStatus.FAILED,
            TaskStatus.TIMEOUT,
            TaskStatus.CANCELLED
        ]

        count = (
            db.query(PluginTask)
            .filter(
                and_(
                    PluginTask.status.in_(terminal_statuses),
                    PluginTask.completed_at < cutoff
                )
            )
            .delete(synchronize_session=False)
        )
        db.commit()

        if count > 0:
            logger.info(
                f"[PluginTaskRepository] Deleted {count} old completed tasks (> {days} days)"
            )

        return count

    # =========================================================================
    # Statistics
    # =========================================================================

    @staticmethod
    def count_by_status(db: Session, status: TaskStatus) -> int:
        """
        Compte les tasks par status.

        Args:
            db: Session SQLAlchemy
            status: Status à compter

        Returns:
            Nombre de tasks avec ce status
        """
        return db.query(func.count(PluginTask.id)).filter(
            PluginTask.status == status
        ).scalar() or 0

    @staticmethod
    def count_by_job_id(db: Session, job_id: int) -> dict:
        """
        Compte les tasks par status pour un job.

        Args:
            db: Session SQLAlchemy
            job_id: ID du job

        Returns:
            Dict avec le compte par status
        """
        results = (
            db.query(PluginTask.status, func.count(PluginTask.id))
            .filter(PluginTask.job_id == job_id)
            .group_by(PluginTask.status)
            .all()
        )
        return {status.value: count for status, count in results}

    @staticmethod
    def get_stats(db: Session) -> dict:
        """
        Récupère les statistiques globales des tasks.

        Args:
            db: Session SQLAlchemy

        Returns:
            Dict avec les stats par status
        """
        stats = {}
        for status in TaskStatus:
            stats[status.value] = PluginTaskRepository.count_by_status(db, status)
        return stats
