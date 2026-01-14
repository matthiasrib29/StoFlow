"""
Vinted Job Repository

Repository pour la gestion des MarketplaceJob et VintedActionType.
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

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from models.user.marketplace_job import MarketplaceJob, JobStatus
from models.vinted.vinted_action_type import VintedActionType
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class VintedJobRepository:
    """
    Repository pour la gestion des MarketplaceJob.

    Fournit toutes les opérations CRUD et queries spécialisées.
    """

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    @staticmethod
    def create(db: Session, job: MarketplaceJob) -> MarketplaceJob:
        """
        Crée un nouveau MarketplaceJob.

        Args:
            db: Session SQLAlchemy
            job: Instance MarketplaceJob à créer

        Returns:
            MarketplaceJob: Instance créée avec ID assigné
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
    def get_by_id(db: Session, job_id: int) -> Optional[MarketplaceJob]:
        """
        Récupère un MarketplaceJob par son ID.

        Args:
            db: Session SQLAlchemy
            job_id: ID du job

        Returns:
            MarketplaceJob si trouvé, None sinon
        """
        stmt = select(MarketplaceJob).where(MarketplaceJob.id == job_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def update(db: Session, job: MarketplaceJob) -> MarketplaceJob:
        """
        Met à jour un MarketplaceJob existant.

        Args:
            db: Session SQLAlchemy
            job: Instance MarketplaceJob modifiée

        Returns:
            MarketplaceJob: Instance mise à jour
        """
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def delete(db: Session, job_id: int) -> bool:
        """
        Supprime un MarketplaceJob.

        Args:
            db: Session SQLAlchemy
            job_id: ID du job à supprimer

        Returns:
            True si supprimé, False si non trouvé
        """
        stmt = select(MarketplaceJob).where(MarketplaceJob.id == job_id)
        job = db.execute(stmt).scalar_one_or_none()
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
    ) -> Optional[MarketplaceJob]:
        """
        Met à jour le status d'un job.

        Args:
            db: Session SQLAlchemy
            job_id: ID du job
            status: Nouveau status
            error_message: Message d'erreur (optionnel)

        Returns:
            MarketplaceJob mis à jour ou None si non trouvé
        """
        stmt = select(MarketplaceJob).where(MarketplaceJob.id == job_id)
        job = db.execute(stmt).scalar_one_or_none()
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
    ) -> List[MarketplaceJob]:
        """
        Récupère les jobs en attente.

        Args:
            db: Session SQLAlchemy
            limit: Nombre max de résultats
            priority_order: Trier par priorité (1=highest first)

        Returns:
            Liste de MarketplaceJob pending
        """
        stmt = select(MarketplaceJob).where(MarketplaceJob.status == JobStatus.PENDING)

        if priority_order:
            stmt = stmt.order_by(MarketplaceJob.priority.asc(), MarketplaceJob.created_at.asc())
        else:
            stmt = stmt.order_by(MarketplaceJob.created_at.asc())

        stmt = stmt.limit(limit)
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def get_by_status(
        db: Session,
        status: JobStatus,
        limit: int = 100
    ) -> List[MarketplaceJob]:
        """
        Récupère les jobs par status.

        Args:
            db: Session SQLAlchemy
            status: Status à filtrer
            limit: Nombre max de résultats

        Returns:
            Liste de MarketplaceJob
        """
        stmt = (
            select(MarketplaceJob)
            .where(MarketplaceJob.status == status)
            .order_by(MarketplaceJob.created_at.desc())
            .limit(limit)
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def get_by_product_id(
        db: Session,
        product_id: int,
        status: Optional[JobStatus] = None
    ) -> List[MarketplaceJob]:
        """
        Récupère les jobs pour un produit donné.

        Args:
            db: Session SQLAlchemy
            product_id: ID du produit
            status: Filtrer par status (optionnel)

        Returns:
            Liste de MarketplaceJob
        """
        stmt = select(MarketplaceJob).where(MarketplaceJob.product_id == product_id)

        if status:
            stmt = stmt.where(MarketplaceJob.status == status)

        stmt = stmt.order_by(MarketplaceJob.created_at.desc())
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def get_by_batch_id(db: Session, batch_id: str) -> List[MarketplaceJob]:
        """
        Récupère les jobs d'un batch.

        Args:
            db: Session SQLAlchemy
            batch_id: ID du batch

        Returns:
            Liste de MarketplaceJob du batch
        """
        stmt = (
            select(MarketplaceJob)
            .where(MarketplaceJob.batch_id == batch_id)
            .order_by(MarketplaceJob.created_at.asc())
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def get_active_jobs(db: Session, limit: int = 100) -> List[MarketplaceJob]:
        """
        Récupère les jobs actifs (pending, running, paused).

        Args:
            db: Session SQLAlchemy
            limit: Nombre max de résultats

        Returns:
            Liste de MarketplaceJob actifs
        """
        active_statuses = [JobStatus.PENDING, JobStatus.RUNNING, JobStatus.PAUSED]
        stmt = (
            select(MarketplaceJob)
            .where(MarketplaceJob.status.in_(active_statuses))
            .order_by(MarketplaceJob.priority.asc(), MarketplaceJob.created_at.asc())
            .limit(limit)
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def get_expired_jobs(db: Session, limit: int = 100) -> List[MarketplaceJob]:
        """
        Récupère les jobs expirés (pending avec expires_at passé).

        Args:
            db: Session SQLAlchemy
            limit: Nombre max de résultats

        Returns:
            Liste de MarketplaceJob expirés
        """
        now = datetime.now(timezone.utc)
        stmt = (
            select(MarketplaceJob)
            .where(
                and_(
                    MarketplaceJob.status == JobStatus.PENDING,
                    MarketplaceJob.expires_at.isnot(None),
                    MarketplaceJob.expires_at < now
                )
            )
            .limit(limit)
        )
        return list(db.execute(stmt).scalars().all())

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
        stmt = select(func.count(MarketplaceJob.id)).where(
            MarketplaceJob.status == status
        )
        return db.execute(stmt).scalar_one() or 0

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
        stmt = select(func.count(MarketplaceJob.id)).where(
            MarketplaceJob.action_type_id == action_type_id
        )
        return db.execute(stmt).scalar_one() or 0

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
        stmt = select(VintedActionType).order_by(VintedActionType.priority.asc())
        return list(db.execute(stmt).scalars().all())

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
        stmt = select(VintedActionType).where(VintedActionType.code == code)
        return db.execute(stmt).scalar_one_or_none()

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
        stmt = select(VintedActionType).where(VintedActionType.id == action_type_id)
        return db.execute(stmt).scalar_one_or_none()
