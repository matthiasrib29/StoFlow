"""
User Repository

Repository pour la gestion des utilisateurs (CRUD operations).
Responsabilité: Accès données pour users (schema public).

Architecture:
- Repository pattern pour isolation DB
- Opérations CRUD standards
- Queries pour authentification et gestion utilisateurs

Created: 2026-01-06
Author: Claude
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.public.user import User, UserRole, SubscriptionTier
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class UserRepository:
    """
    Repository pour la gestion des User.

    Fournit toutes les opérations CRUD et queries spécialisées.
    Toutes les méthodes sont statiques pour faciliter l'utilisation.
    """

    @staticmethod
    def create(db: Session, user: User) -> User:
        """
        Crée un nouveau User.

        Args:
            db: Session SQLAlchemy
            user: Instance User à créer

        Returns:
            User: Instance créée avec ID assigné
        """
        db.add(user)
        db.flush()  # Get ID without committing (caller manages transaction)

        logger.info(
            f"[UserRepository] User created: id={user.id}, email={user.email}"
        )

        return user

    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        """
        Récupère un User par son ID.

        Args:
            db: Session SQLAlchemy
            user_id: ID de l'utilisateur

        Returns:
            User si trouvé, None sinon
        """
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        """
        Récupère un User par son email.

        Args:
            db: Session SQLAlchemy
            email: Email de l'utilisateur

        Returns:
            User si trouvé, None sinon
        """
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def exists_by_email(db: Session, email: str) -> bool:
        """
        Vérifie si un email existe déjà.

        Args:
            db: Session SQLAlchemy
            email: Email à vérifier

        Returns:
            bool: True si l'email existe
        """
        return (
            db.query(func.count(User.id))
            .filter(User.email == email)
            .scalar()
            or 0
        ) > 0

    @staticmethod
    def update(db: Session, user: User) -> User:
        """
        Met à jour un User existant.

        Args:
            db: Session SQLAlchemy
            user: Instance User modifiée

        Returns:
            User: Instance mise à jour
        """
        db.flush()  # Caller manages transaction

        logger.debug(f"[UserRepository] User updated: id={user.id}")

        return user

    @staticmethod
    def update_login_stats(
        db: Session,
        user: User,
        failed_attempts: Optional[int] = None,
        locked_until: Optional[datetime] = None,
        last_login: Optional[datetime] = None,
        last_failed_login: Optional[datetime] = None,
    ) -> User:
        """
        Met à jour les statistiques de login d'un User.

        Args:
            db: Session SQLAlchemy
            user: Instance User à modifier
            failed_attempts: Nombre de tentatives échouées (None = ne pas modifier)
            locked_until: Date de déverrouillage (None = ne pas modifier)
            last_login: Date de dernière connexion (None = ne pas modifier)
            last_failed_login: Date de dernière tentative échouée (None = ne pas modifier)

        Returns:
            User: Instance mise à jour
        """
        if failed_attempts is not None:
            user.failed_login_attempts = failed_attempts
        if locked_until is not None:
            user.locked_until = locked_until
        if last_login is not None:
            user.last_login = last_login
        if last_failed_login is not None:
            user.last_failed_login = last_failed_login

        db.flush()

        logger.debug(
            f"[UserRepository] Login stats updated: user_id={user.id}, "
            f"failed_attempts={user.failed_login_attempts}"
        )

        return user

    @staticmethod
    def reset_login_failures(db: Session, user: User) -> User:
        """
        Réinitialise le compteur de login échoués.

        Args:
            db: Session SQLAlchemy
            user: Instance User

        Returns:
            User: Instance mise à jour
        """
        user.failed_login_attempts = 0
        user.last_failed_login = None
        user.locked_until = None
        db.flush()

        return user

    @staticmethod
    def increment_failed_login(db: Session, user: User) -> User:
        """
        Incrémente le compteur de login échoués.

        Args:
            db: Session SQLAlchemy
            user: Instance User

        Returns:
            User: Instance mise à jour
        """
        from shared.datetime_utils import utc_now

        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        user.last_failed_login = utc_now()
        db.flush()

        return user

    @staticmethod
    def lock_account(db: Session, user: User, lock_until: datetime) -> User:
        """
        Verrouille un compte utilisateur.

        Args:
            db: Session SQLAlchemy
            user: Instance User
            lock_until: Date jusqu'à laquelle verrouiller

        Returns:
            User: Instance mise à jour
        """
        user.locked_until = lock_until
        db.flush()

        logger.warning(f"[UserRepository] Account locked: user_id={user.id}, until={lock_until}")

        return user

    @staticmethod
    def list_active(db: Session, limit: int = 100) -> List[User]:
        """
        Liste les utilisateurs actifs.

        Args:
            db: Session SQLAlchemy
            limit: Nombre max de résultats

        Returns:
            Liste de User actifs
        """
        return (
            db.query(User)
            .filter(User.is_active == True)  # noqa: E712
            .order_by(User.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def list_by_role(db: Session, role: UserRole, limit: int = 100) -> List[User]:
        """
        Liste les utilisateurs par rôle.

        Args:
            db: Session SQLAlchemy
            role: Rôle à filtrer
            limit: Nombre max de résultats

        Returns:
            Liste de User avec ce rôle
        """
        return (
            db.query(User)
            .filter(User.role == role)
            .order_by(User.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def list_by_subscription(
        db: Session, tier: SubscriptionTier, limit: int = 100
    ) -> List[User]:
        """
        Liste les utilisateurs par tier d'abonnement.

        Args:
            db: Session SQLAlchemy
            tier: Tier d'abonnement
            limit: Nombre max de résultats

        Returns:
            Liste de User avec ce tier
        """
        return (
            db.query(User)
            .filter(User.subscription_tier == tier)
            .order_by(User.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def count(db: Session, active_only: bool = False) -> int:
        """
        Compte le nombre total d'utilisateurs.

        Args:
            db: Session SQLAlchemy
            active_only: Si True, compte uniquement les actifs

        Returns:
            int: Nombre d'utilisateurs
        """
        query = db.query(func.count(User.id))

        if active_only:
            query = query.filter(User.is_active == True)  # noqa: E712

        return query.scalar() or 0

    @staticmethod
    def count_by_subscription(db: Session, tier: SubscriptionTier) -> int:
        """
        Compte les utilisateurs par tier d'abonnement.

        Args:
            db: Session SQLAlchemy
            tier: Tier d'abonnement

        Returns:
            int: Nombre d'utilisateurs avec ce tier
        """
        return (
            db.query(func.count(User.id))
            .filter(User.subscription_tier == tier)
            .scalar()
            or 0
        )

    @staticmethod
    def exists(db: Session, user_id: int) -> bool:
        """
        Vérifie si un utilisateur existe.

        Args:
            db: Session SQLAlchemy
            user_id: ID de l'utilisateur

        Returns:
            bool: True si existe
        """
        return (
            db.query(func.count(User.id))
            .filter(User.id == user_id)
            .scalar()
            or 0
        ) > 0

    @staticmethod
    def get_by_stripe_customer_id(db: Session, stripe_customer_id: str) -> Optional[User]:
        """
        Récupère un User par son Stripe customer ID.

        Args:
            db: Session SQLAlchemy
            stripe_customer_id: ID Stripe du customer

        Returns:
            User si trouvé, None sinon
        """
        return db.query(User).filter(User.stripe_customer_id == stripe_customer_id).first()

    @staticmethod
    def search(db: Session, query_text: str, limit: int = 50) -> List[User]:
        """
        Recherche des utilisateurs par email ou nom.

        Args:
            db: Session SQLAlchemy
            query_text: Texte de recherche
            limit: Nombre max de résultats

        Returns:
            Liste de User correspondants
        """
        search_pattern = f"%{query_text}%"

        return (
            db.query(User)
            .filter(
                (User.email.ilike(search_pattern))
                | (User.full_name.ilike(search_pattern))
            )
            .order_by(User.created_at.desc())
            .limit(limit)
            .all()
        )


__all__ = ["UserRepository"]
