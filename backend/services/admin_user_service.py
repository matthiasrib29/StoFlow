"""
Admin User Service

Service for managing users (admin only).
Provides CRUD operations for user management.

Business Rules:
- Only ADMIN users can access these operations
- Hard delete removes user and their PostgreSQL schema
- Password changes require rehashing
- Email changes require uniqueness check
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import text, or_

from models.public.user import User, UserRole, SubscriptionTier
from models.public.subscription_quota import SubscriptionQuota
from services.auth_service import AuthService
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class AdminUserService:
    """Service for admin user management operations."""

    @staticmethod
    def list_users(
        db: Session,
        skip: int = 0,
        limit: int = 50,
        search: Optional[str] = None,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[List[User], int]:
        """
        List all users with optional filtering and pagination.

        Args:
            db: SQLAlchemy session
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return
            search: Search term for email or full_name
            role: Filter by role
            is_active: Filter by active status

        Returns:
            Tuple of (list of users, total count)
        """
        query = db.query(User)

        # Apply filters
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    User.email.ilike(search_term),
                    User.full_name.ilike(search_term),
                    User.business_name.ilike(search_term),
                )
            )

        if role is not None:
            query = query.filter(User.role == role)

        if is_active is not None:
            query = query.filter(User.is_active == is_active)

        # Get total count before pagination
        total = query.count()

        # Apply pagination and ordering
        users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()

        logger.info(f"Admin list_users: found {total} users, returning {len(users)}")
        return users, total

    @staticmethod
    def get_user(db: Session, user_id: int) -> Optional[User]:
        """
        Get a user by ID.

        Args:
            db: SQLAlchemy session
            user_id: User ID

        Returns:
            User if found, None otherwise
        """
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            logger.debug(f"Admin get_user: found user_id={user_id}")
        else:
            logger.warning(f"Admin get_user: user_id={user_id} not found")
        return user

    @staticmethod
    def create_user(
        db: Session,
        email: str,
        password: str,
        full_name: str,
        role: UserRole = UserRole.USER,
        is_active: bool = True,
        subscription_tier: SubscriptionTier = SubscriptionTier.FREE,
        business_name: Optional[str] = None,
    ) -> User:
        """
        Create a new user (admin operation).

        Args:
            db: SQLAlchemy session
            email: User email (must be unique)
            password: Plain text password (will be hashed)
            full_name: User's full name
            role: User role (default: USER)
            is_active: Active status (default: True)
            subscription_tier: Subscription tier (default: FREE)
            business_name: Optional business name

        Returns:
            Created User

        Raises:
            ValueError: If email already exists
        """
        # Check email uniqueness
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            raise ValueError(f"Email already exists: {email}")

        # Get subscription quota
        quota = db.query(SubscriptionQuota).filter(
            SubscriptionQuota.tier == subscription_tier
        ).first()

        if not quota:
            raise ValueError(f"Subscription quota not found for tier: {subscription_tier}")

        # Create user
        user = User(
            email=email,
            hashed_password=AuthService.hash_password(password),
            full_name=full_name,
            role=role,
            is_active=is_active,
            subscription_tier=subscription_tier,
            subscription_tier_id=quota.id,
            subscription_status="active",
            business_name=business_name,
            email_verified=True,  # Admin-created users are pre-verified
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        # Create user schema
        from services.user_schema_service import UserSchemaService
        try:
            schema_name = UserSchemaService.create_user_schema(db, user.id)
            logger.info(f"Admin create_user: user_id={user.id}, schema={schema_name}")
        except Exception as e:
            # Rollback user creation if schema fails
            db.delete(user)
            db.commit()
            raise ValueError(f"Failed to create user schema: {e}")

        return user

    @staticmethod
    def update_user(
        db: Session,
        user_id: int,
        email: Optional[str] = None,
        full_name: Optional[str] = None,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
        subscription_tier: Optional[SubscriptionTier] = None,
        business_name: Optional[str] = None,
        password: Optional[str] = None,
    ) -> Optional[User]:
        """
        Update a user (admin operation).

        Args:
            db: SQLAlchemy session
            user_id: User ID to update
            email: New email (optional, checked for uniqueness)
            full_name: New full name (optional)
            role: New role (optional)
            is_active: New active status (optional)
            subscription_tier: New subscription tier (optional)
            business_name: New business name (optional)
            password: New password (optional, will be hashed)

        Returns:
            Updated User or None if not found

        Raises:
            ValueError: If new email already exists
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        # Check email uniqueness if changing
        if email and email != user.email:
            existing = db.query(User).filter(User.email == email).first()
            if existing:
                raise ValueError(f"Email already exists: {email}")
            user.email = email

        if full_name is not None:
            user.full_name = full_name

        if role is not None:
            user.role = role

        if is_active is not None:
            user.is_active = is_active
            # Reset failed login attempts when reactivating
            if is_active:
                user.failed_login_attempts = 0
                user.locked_until = None

        if subscription_tier is not None:
            # Update quota reference
            quota = db.query(SubscriptionQuota).filter(
                SubscriptionQuota.tier == subscription_tier
            ).first()
            if quota:
                user.subscription_tier = subscription_tier
                user.subscription_tier_id = quota.id

        if business_name is not None:
            user.business_name = business_name

        if password:
            user.hashed_password = AuthService.hash_password(password)

        db.commit()
        db.refresh(user)

        logger.info(f"Admin update_user: user_id={user_id} updated")
        return user

    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        """
        Delete a user and their PostgreSQL schema (hard delete).

        Args:
            db: SQLAlchemy session
            user_id: User ID to delete

        Returns:
            True if deleted, False if not found
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        schema_name = user.schema_name

        # Delete user schema first
        try:
            db.execute(text(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE"))
            logger.info(f"Admin delete_user: dropped schema {schema_name}")
        except Exception as e:
            logger.error(f"Admin delete_user: failed to drop schema {schema_name}: {e}")
            # Continue with user deletion even if schema drop fails

        # Delete AI credits if exists
        if user.ai_credit:
            db.delete(user.ai_credit)

        # Delete user
        db.delete(user)
        db.commit()

        logger.info(f"Admin delete_user: user_id={user_id} deleted (hard delete)")
        return True

    @staticmethod
    def toggle_active(db: Session, user_id: int) -> Optional[User]:
        """
        Toggle user active status.

        Args:
            db: SQLAlchemy session
            user_id: User ID

        Returns:
            Updated User or None if not found
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        user.is_active = not user.is_active

        # Reset failed login if reactivating
        if user.is_active:
            user.failed_login_attempts = 0
            user.locked_until = None

        db.commit()
        db.refresh(user)

        logger.info(f"Admin toggle_active: user_id={user_id}, is_active={user.is_active}")
        return user

    @staticmethod
    def unlock_user(db: Session, user_id: int) -> Optional[User]:
        """
        Unlock a locked user account.

        Args:
            db: SQLAlchemy session
            user_id: User ID

        Returns:
            Updated User or None if not found
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        user.failed_login_attempts = 0
        user.locked_until = None

        db.commit()
        db.refresh(user)

        logger.info(f"Admin unlock_user: user_id={user_id} unlocked")
        return user
