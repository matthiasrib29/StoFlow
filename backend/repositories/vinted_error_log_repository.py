"""
Vinted Error Log Repository

Repository pour la gestion des logs d'erreurs Vinted (CRUD operations).
Responsabilité: Accès données pour vinted_error_logs (schema user_{id}).

Architecture:
- Repository pattern pour isolation DB
- Opérations CRUD standards
- Queries optimisées avec indexes
- Filtres par product_id, error_type, operation

Created: 2024-12-10
Author: Claude
"""

from datetime import timedelta
from typing import List, Optional

from sqlalchemy import and_, delete, func, select
from sqlalchemy.orm import Session

from models.user.vinted_error_log import VintedErrorLog
from shared.datetime_utils import utc_now


class VintedErrorLogRepository:
    """
    Repository pour la gestion des VintedErrorLog.

    Fournit toutes les opérations CRUD et queries spécialisées pour les logs d'erreurs.
    """

    @staticmethod
    def create(db: Session, error_log: VintedErrorLog) -> VintedErrorLog:
        """
        Crée un nouveau VintedErrorLog.

        Args:
            db: Session SQLAlchemy
            error_log: Instance VintedErrorLog à créer

        Returns:
            VintedErrorLog: Instance créée avec ID assigné

        Example:
            >>> error = VintedErrorLog(
            ...     product_id=123,
            ...     operation='publish',
            ...     error_type='mapping_error',
            ...     error_message='Brand not mapped'
            ... )
            >>> created = VintedErrorLogRepository.create(db, error)
            >>> print(created.id)
            1
        """
        db.add(error_log)
        db.commit()
        db.refresh(error_log)
        return error_log

    @staticmethod
    def get_by_id(db: Session, error_log_id: int) -> Optional[VintedErrorLog]:
        """
        Récupère un VintedErrorLog par son ID.

        Args:
            db: Session SQLAlchemy
            error_log_id: ID du VintedErrorLog

        Returns:
            VintedErrorLog si trouvé, None sinon
        """
        stmt = select(VintedErrorLog).where(VintedErrorLog.id == error_log_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_all_by_product_id(db: Session, product_id: int, limit: int = 50) -> List[VintedErrorLog]:
        """
        Récupère tous les logs d'erreurs pour un produit.

        Args:
            db: Session SQLAlchemy
            product_id: ID du Product
            limit: Nombre maximum de résultats (défaut: 50)

        Returns:
            Liste de VintedErrorLog triés par date décroissante

        Example:
            >>> errors = VintedErrorLogRepository.get_all_by_product_id(db, 123)
            >>> print(len(errors))
            3
            >>> for error in errors:
            ...     print(f"{error.operation}: {error.error_message}")
            publish: Brand not mapped
            publish: Image upload failed
        """
        stmt = (
            select(VintedErrorLog)
            .where(VintedErrorLog.product_id == product_id)
            .order_by(VintedErrorLog.created_at.desc())
            .limit(limit)
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def get_latest_by_product_id(db: Session, product_id: int) -> Optional[VintedErrorLog]:
        """
        Récupère la dernière erreur pour un produit.

        Args:
            db: Session SQLAlchemy
            product_id: ID du Product

        Returns:
            VintedErrorLog le plus récent si trouvé, None sinon

        Example:
            >>> latest_error = VintedErrorLogRepository.get_latest_by_product_id(db, 123)
            >>> if latest_error:
            ...     print(latest_error.error_message)
            'Brand not mapped'
        """
        stmt = (
            select(VintedErrorLog)
            .where(VintedErrorLog.product_id == product_id)
            .order_by(VintedErrorLog.created_at.desc())
        )
        return db.execute(stmt).scalars().first()

    @staticmethod
    def get_all_by_error_type(
        db: Session,
        error_type: str,
        limit: int = 100
    ) -> List[VintedErrorLog]:
        """
        Récupère tous les logs par type d'erreur.

        Args:
            db: Session SQLAlchemy
            error_type: Type d'erreur ('mapping_error', 'api_error', 'image_error', 'validation_error')
            limit: Nombre maximum de résultats

        Returns:
            Liste de VintedErrorLog

        Example:
            >>> mapping_errors = VintedErrorLogRepository.get_all_by_error_type(db, 'mapping_error')
            >>> print(len(mapping_errors))
            15
        """
        stmt = (
            select(VintedErrorLog)
            .where(VintedErrorLog.error_type == error_type)
            .order_by(VintedErrorLog.created_at.desc())
            .limit(limit)
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def get_all_by_operation(
        db: Session,
        operation: str,
        limit: int = 100
    ) -> List[VintedErrorLog]:
        """
        Récupère tous les logs par type d'opération.

        Args:
            db: Session SQLAlchemy
            operation: Type d'opération ('publish', 'update', 'delete')
            limit: Nombre maximum de résultats

        Returns:
            Liste de VintedErrorLog

        Example:
            >>> publish_errors = VintedErrorLogRepository.get_all_by_operation(db, 'publish')
            >>> print(len(publish_errors))
            42
        """
        stmt = (
            select(VintedErrorLog)
            .where(VintedErrorLog.operation == operation)
            .order_by(VintedErrorLog.created_at.desc())
            .limit(limit)
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def get_recent_errors(db: Session, hours: int = 24, limit: int = 100) -> List[VintedErrorLog]:
        """
        Récupère les erreurs récentes (dernières X heures).

        Args:
            db: Session SQLAlchemy
            hours: Nombre d'heures dans le passé (défaut: 24)
            limit: Nombre maximum de résultats

        Returns:
            Liste de VintedErrorLog des dernières X heures

        Example:
            >>> recent = VintedErrorLogRepository.get_recent_errors(db, hours=12)
            >>> print(len(recent))
            8
        """
        cutoff_time = utc_now() - timedelta(hours=hours)
        stmt = (
            select(VintedErrorLog)
            .where(VintedErrorLog.created_at >= cutoff_time)
            .order_by(VintedErrorLog.created_at.desc())
            .limit(limit)
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def get_errors_by_product_and_operation(
        db: Session,
        product_id: int,
        operation: str
    ) -> List[VintedErrorLog]:
        """
        Récupère les erreurs pour un produit et une opération spécifiques.

        Args:
            db: Session SQLAlchemy
            product_id: ID du Product
            operation: Type d'opération ('publish', 'update', 'delete')

        Returns:
            Liste de VintedErrorLog

        Example:
            >>> errors = VintedErrorLogRepository.get_errors_by_product_and_operation(
            ...     db, 123, 'publish'
            ... )
            >>> print(len(errors))
            2
        """
        stmt = (
            select(VintedErrorLog)
            .where(
                and_(
                    VintedErrorLog.product_id == product_id,
                    VintedErrorLog.operation == operation
                )
            )
            .order_by(VintedErrorLog.created_at.desc())
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def delete(db: Session, error_log_id: int) -> bool:
        """
        Supprime un VintedErrorLog.

        Args:
            db: Session SQLAlchemy
            error_log_id: ID du VintedErrorLog à supprimer

        Returns:
            bool: True si supprimé, False si non trouvé

        Example:
            >>> success = VintedErrorLogRepository.delete(db, 1)
            >>> print(success)
            True
        """
        error_log = VintedErrorLogRepository.get_by_id(db, error_log_id)
        if not error_log:
            return False

        db.delete(error_log)
        db.commit()
        return True

    @staticmethod
    def delete_by_product_id(db: Session, product_id: int) -> int:
        """
        Supprime tous les logs d'erreurs pour un produit.

        Args:
            db: Session SQLAlchemy
            product_id: ID du Product

        Returns:
            int: Nombre de logs supprimés

        Example:
            >>> count = VintedErrorLogRepository.delete_by_product_id(db, 123)
            >>> print(count)
            5
        """
        stmt = delete(VintedErrorLog).where(VintedErrorLog.product_id == product_id)
        result = db.execute(stmt)
        deleted_count = result.rowcount
        db.commit()
        return deleted_count

    @staticmethod
    def delete_old_errors(db: Session, days: int = 30) -> int:
        """
        Supprime les logs d'erreurs plus anciens que X jours.

        Args:
            db: Session SQLAlchemy
            days: Nombre de jours dans le passé (défaut: 30)

        Returns:
            int: Nombre de logs supprimés

        Example:
            >>> count = VintedErrorLogRepository.delete_old_errors(db, days=90)
            >>> print(f"{count} erreurs supprimées")
            142 erreurs supprimées
        """
        cutoff_time = utc_now() - timedelta(days=days)
        stmt = delete(VintedErrorLog).where(VintedErrorLog.created_at < cutoff_time)
        result = db.execute(stmt)
        deleted_count = result.rowcount
        db.commit()
        return deleted_count

    @staticmethod
    def count_by_error_type(db: Session) -> dict:
        """
        Compte le nombre d'erreurs par type.

        Args:
            db: Session SQLAlchemy

        Returns:
            dict: Mapping error_type → count

        Example:
            >>> counts = VintedErrorLogRepository.count_by_error_type(db)
            >>> print(counts)
            {
                'mapping_error': 42,
                'api_error': 15,
                'image_error': 8,
                'validation_error': 23
            }
        """
        stmt = (
            select(
                VintedErrorLog.error_type,
                func.count(VintedErrorLog.id).label('count')
            )
            .group_by(VintedErrorLog.error_type)
        )
        results = db.execute(stmt).all()

        return {result.error_type: result.count for result in results}

    @staticmethod
    def count_by_operation(db: Session) -> dict:
        """
        Compte le nombre d'erreurs par opération.

        Args:
            db: Session SQLAlchemy

        Returns:
            dict: Mapping operation → count

        Example:
            >>> counts = VintedErrorLogRepository.count_by_operation(db)
            >>> print(counts)
            {
                'publish': 68,
                'update': 12,
                'delete': 5
            }
        """
        stmt = (
            select(
                VintedErrorLog.operation,
                func.count(VintedErrorLog.id).label('count')
            )
            .group_by(VintedErrorLog.operation)
        )
        results = db.execute(stmt).all()

        return {result.operation: result.count for result in results}

    @staticmethod
    def get_error_summary(db: Session) -> dict:
        """
        Récupère un résumé complet des erreurs.

        Args:
            db: Session SQLAlchemy

        Returns:
            dict: Résumé avec total, par type, par opération, et erreurs récentes

        Example:
            >>> summary = VintedErrorLogRepository.get_error_summary(db)
            >>> print(summary)
            {
                'total_errors': 88,
                'by_type': {'mapping_error': 42, 'api_error': 15, ...},
                'by_operation': {'publish': 68, 'update': 12, ...},
                'last_24h': 8,
                'last_7d': 25
            }
        """
        stmt_total = select(func.count(VintedErrorLog.id))
        total = db.execute(stmt_total).scalar_one()

        # Erreurs dernières 24h
        cutoff_24h = utc_now() - timedelta(hours=24)
        stmt_24h = (
            select(func.count(VintedErrorLog.id))
            .where(VintedErrorLog.created_at >= cutoff_24h)
        )
        last_24h = db.execute(stmt_24h).scalar_one()

        # Erreurs derniers 7 jours
        cutoff_7d = utc_now() - timedelta(days=7)
        stmt_7d = (
            select(func.count(VintedErrorLog.id))
            .where(VintedErrorLog.created_at >= cutoff_7d)
        )
        last_7d = db.execute(stmt_7d).scalar_one()

        return {
            'total_errors': total or 0,
            'by_type': VintedErrorLogRepository.count_by_error_type(db),
            'by_operation': VintedErrorLogRepository.count_by_operation(db),
            'last_24h': last_24h or 0,
            'last_7d': last_7d or 0
        }
