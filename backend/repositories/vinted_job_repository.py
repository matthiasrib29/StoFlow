"""
Vinted Job Repository

Repository pour la gestion des VintedJob et VintedActionType.
Responsabilité: Accès données pour vinted_jobs (schema user_{id})
et action_types (schema vinted).

Architecture:
- Repository pattern pour isolation DB
- Opérations CRUD standards
- Queries optimisées avec indexes
- Filtres par status, date, etc.

Created: 2026-01-06
Author: Claude
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from models.user.vinted_job import VintedJob, JobStatus
from models.vinted.vinted_action_type import VintedActionType
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class VintedJobRepository:
    """
    Repository pour la gestion des VintedJob.

    Fournit toutes les opérations CRUD et queries spécialisées.
    """

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    @staticmethod
    def create(db: Session, job: VintedJob) -> VintedJob:
        """
        Crée un nouveau VintedJob.

        Args:
            db: Session SQLAlchemy
            job: Instance VintedJob à créer

        Returns:
            VintedJob: Instance créée avec ID assigné
        """
        db.add(job)
        db.commit()
        db.refresh(job)

        logger.info(
            f"[VintedJobRepository] Job created: id={job.id}, "
            f"action_type_id={job.action_type_id}, status={job.status.value}"
        )

        return job

    @staticmethod
    def get_by_id(db: Session, job_id: int) -> Optional[VintedJob]:
        """
        Récupère un VintedJob par son ID.

        Args:
            db: Session SQLAlchemy
            job_id: ID du job

        Returns:
            VintedJob si trouvé, None sinon
        """
        return db.query(VintedJob).filter(VintedJob.id == job_id).first()

    @staticmethod
    def update(db: Session, job: VintedJob) -> VintedJob:
        """
        Met à jour un VintedJob existant.

        Args:
            db: Session SQLAlchemy
            job: Instance VintedJob modifiée

        Returns:
            VintedJob: Instance mise à jour
        """
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def delete(db: Session, job_id: int) -> bool:
        """
        Supprime un VintedJob.

        Args:
            db: Session SQLAlchemy
            job_id: ID du job à supprimer

        Returns:
            True si supprimé, False si non trouvé
        """
        job = db.query(VintedJob).filter(VintedJob.id == job_id).first()
        if not job:
            return False

        db.delete(job)
        db.commit()

        logger.info(f"[VintedJobRepository] Job deleted: id={job_id}")
        return True

    # =========================================================================
    # Status Management
    # =========================================================================

    @staticmethod
    def update_status(
        db: Session,
        job_id: int,
        status: JobStatus,
        error_message: Optional[str] = None
    ) -> Optional[VintedJob]:
        """
        Met à jour le status d'un job.

        Args:
            db: Session SQLAlchemy
            job_id: ID du job
            status: Nouveau status
            error_message: Message d'erreur (optionnel)

        Returns:
            VintedJob mis à jour ou None si non trouvé
        """
        job = db.query(VintedJob).filter(VintedJob.id == job_id).first()
        if not job:
            return None

        job.status = status

        if error_message:
            job.error_message = error_message

        # Set timestamps based on status
        now = datetime.now(timezone.utc)
        if status == JobStatus.RUNNING and not job.started_at:
            job.started_at = now
        elif status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED, JobStatus.EXPIRED):
            job.completed_at = now

        db.commit()
        db.refresh(job)

        logger.info(
            f"[VintedJobRepository] Job status updated: id={job_id}, "
            f"status={status.value}"
        )

        return job

    # =========================================================================
    # Query Methods
    # =========================================================================

    @staticmethod
    def get_pending_jobs(
        db: Session,
        limit: int = 10,
        priority_order: bool = True
    ) -> List[VintedJob]:
        """
        Récupère les jobs en attente.

        Args:
            db: Session SQLAlchemy
            limit: Nombre max de résultats
            priority_order: Trier par priorité (1=highest first)

        Returns:
            Liste de VintedJob pending
        """
        query = db.query(VintedJob).filter(VintedJob.status == JobStatus.PENDING)

        if priority_order:
            query = query.order_by(VintedJob.priority.asc(), VintedJob.created_at.asc())
        else:
            query = query.order_by(VintedJob.created_at.asc())

        return query.limit(limit).all()

    @staticmethod
    def get_by_status(
        db: Session,
        status: JobStatus,
        limit: int = 100
    ) -> List[VintedJob]:
        """
        Récupère les jobs par status.

        Args:
            db: Session SQLAlchemy
            status: Status à filtrer
            limit: Nombre max de résultats

        Returns:
            Liste de VintedJob
        """
        return (
            db.query(VintedJob)
            .filter(VintedJob.status == status)
            .order_by(VintedJob.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_by_product_id(
        db: Session,
        product_id: int,
        status: Optional[JobStatus] = None
    ) -> List[VintedJob]:
        """
        Récupère les jobs pour un produit donné.

        Args:
            db: Session SQLAlchemy
            product_id: ID du produit
            status: Filtrer par status (optionnel)

        Returns:
            Liste de VintedJob
        """
        query = db.query(VintedJob).filter(VintedJob.product_id == product_id)

        if status:
            query = query.filter(VintedJob.status == status)

        return query.order_by(VintedJob.created_at.desc()).all()

    @staticmethod
    def get_by_batch_id(db: Session, batch_id: str) -> List[VintedJob]:
        """
        Récupère les jobs d'un batch.

        Args:
            db: Session SQLAlchemy
            batch_id: ID du batch

        Returns:
            Liste de VintedJob du batch
        """
        return (
            db.query(VintedJob)
            .filter(VintedJob.batch_id == batch_id)
            .order_by(VintedJob.created_at.asc())
            .all()
        )

    @staticmethod
    def get_active_jobs(db: Session, limit: int = 100) -> List[VintedJob]:
        """
        Récupère les jobs actifs (pending, running, paused).

        Args:
            db: Session SQLAlchemy
            limit: Nombre max de résultats

        Returns:
            Liste de VintedJob actifs
        """
        active_statuses = [JobStatus.PENDING, JobStatus.RUNNING, JobStatus.PAUSED]
        return (
            db.query(VintedJob)
            .filter(VintedJob.status.in_(active_statuses))
            .order_by(VintedJob.priority.asc(), VintedJob.created_at.asc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_expired_jobs(db: Session, limit: int = 100) -> List[VintedJob]:
        """
        Récupère les jobs expirés (pending avec expires_at passé).

        Args:
            db: Session SQLAlchemy
            limit: Nombre max de résultats

        Returns:
            Liste de VintedJob expirés
        """
        now = datetime.now(timezone.utc)
        return (
            db.query(VintedJob)
            .filter(
                and_(
                    VintedJob.status == JobStatus.PENDING,
                    VintedJob.expires_at.isnot(None),
                    VintedJob.expires_at < now
                )
            )
            .limit(limit)
            .all()
        )

    # =========================================================================
    # Statistics
    # =========================================================================

    @staticmethod
    def count_by_status(db: Session, status: JobStatus) -> int:
        """
        Compte les jobs par status.

        Args:
            db: Session SQLAlchemy
            status: Status à compter

        Returns:
            Nombre de jobs avec ce status
        """
        return db.query(func.count(VintedJob.id)).filter(
            VintedJob.status == status
        ).scalar() or 0

    @staticmethod
    def count_by_action_type(db: Session, action_type_id: int) -> int:
        """
        Compte les jobs par type d'action.

        Args:
            db: Session SQLAlchemy
            action_type_id: ID du type d'action

        Returns:
            Nombre de jobs
        """
        return db.query(func.count(VintedJob.id)).filter(
            VintedJob.action_type_id == action_type_id
        ).scalar() or 0

    @staticmethod
    def get_stats(db: Session) -> dict:
        """
        Récupère les statistiques globales des jobs.

        Args:
            db: Session SQLAlchemy

        Returns:
            Dict avec les stats par status
        """
        stats = {}
        for status in JobStatus:
            stats[status.value] = VintedJobRepository.count_by_status(db, status)
        return stats

    # =========================================================================
    # Action Types (vinted schema)
    # =========================================================================

    @staticmethod
    def get_action_types(db: Session) -> List[VintedActionType]:
        """
        Récupère tous les types d'actions Vinted.

        Args:
            db: Session SQLAlchemy

        Returns:
            Liste de VintedActionType
        """
        return db.query(VintedActionType).order_by(VintedActionType.priority.asc()).all()

    @staticmethod
    def get_action_type_by_code(db: Session, code: str) -> Optional[VintedActionType]:
        """
        Récupère un type d'action par son code.

        Args:
            db: Session SQLAlchemy
            code: Code de l'action (ex: 'publish', 'sync')

        Returns:
            VintedActionType ou None
        """
        return db.query(VintedActionType).filter(VintedActionType.code == code).first()

    @staticmethod
    def get_action_type_by_id(db: Session, action_type_id: int) -> Optional[VintedActionType]:
        """
        Récupère un type d'action par son ID.

        Args:
            db: Session SQLAlchemy
            action_type_id: ID du type d'action

        Returns:
            VintedActionType ou None
        """
        return db.query(VintedActionType).filter(VintedActionType.id == action_type_id).first()
