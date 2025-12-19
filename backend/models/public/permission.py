"""
Permission Models for RBAC System

Business Rules (2025-12-19):
- Permissions are stored in database (modifiable without code change)
- RolePermission links roles to permissions
- 3 roles: ADMIN, USER, SUPPORT
- ADMIN: full access
- USER: access to own data only
- SUPPORT: read-only on all data

Author: Claude
Date: 2025-12-19
"""

from enum import Enum
from sqlalchemy import Column, Integer, String, Boolean, Enum as SQLEnum, UniqueConstraint, ForeignKey
from sqlalchemy.orm import relationship

from shared.database import Base
from models.public.user import UserRole


class PermissionCategory(str, Enum):
    """Categories of permissions for grouping."""
    PRODUCTS = "products"
    PUBLICATIONS = "publications"
    INTEGRATIONS = "integrations"
    STATS = "stats"
    ACCOUNT = "account"
    ADMIN = "admin"


class Permission(Base):
    """
    Permission model.

    Stores all available permissions in the system.
    Permissions are identified by a unique code (e.g., "products:create").
    """
    __tablename__ = "permissions"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True, index=True)
    code = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique permission code (e.g., 'products:create')"
    )
    name = Column(
        String(255),
        nullable=False,
        comment="Human-readable permission name"
    )
    description = Column(
        String(500),
        nullable=True,
        comment="Description of what this permission allows"
    )
    category = Column(
        String(50),
        nullable=False,
        comment="Permission category for grouping"
    )
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether this permission is active"
    )

    # Relationships
    role_permissions = relationship("RolePermission", back_populates="permission")

    def __repr__(self):
        return f"<Permission(code={self.code}, name={self.name})>"


class RolePermission(Base):
    """
    Role-Permission mapping.

    Links roles to their permissions.
    Stored in database for easy modification.
    """
    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint('role', 'permission_id', name='uq_role_permission'),
        {"schema": "public"}
    )

    id = Column(Integer, primary_key=True, index=True)
    role = Column(
        SQLEnum(UserRole, name="userrole", schema="public", create_type=False),
        nullable=False,
        index=True,
        comment="User role"
    )
    permission_id = Column(
        Integer,
        ForeignKey("public.permissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Permission ID"
    )

    # Relationships
    permission = relationship("Permission", back_populates="role_permissions")

    def __repr__(self):
        return f"<RolePermission(role={self.role.value}, permission_id={self.permission_id})>"


# Default permissions to seed
DEFAULT_PERMISSIONS = [
    # Products
    {"code": "products:read", "name": "View products", "category": "products", "description": "View product list and details"},
    {"code": "products:create", "name": "Create products", "category": "products", "description": "Create new products"},
    {"code": "products:update", "name": "Update products", "category": "products", "description": "Modify existing products"},
    {"code": "products:delete", "name": "Delete products", "category": "products", "description": "Delete products"},

    # Publications
    {"code": "publications:read", "name": "View publications", "category": "publications", "description": "View publication list and status"},
    {"code": "publications:create", "name": "Publish products", "category": "publications", "description": "Publish products to marketplaces"},
    {"code": "publications:delete", "name": "Unpublish products", "category": "publications", "description": "Remove products from marketplaces"},

    # Integrations
    {"code": "integrations:read", "name": "View integrations", "category": "integrations", "description": "View connected platforms"},
    {"code": "integrations:vinted:connect", "name": "Connect Vinted", "category": "integrations", "description": "Connect Vinted account"},
    {"code": "integrations:vinted:disconnect", "name": "Disconnect Vinted", "category": "integrations", "description": "Disconnect Vinted account"},
    {"code": "integrations:ebay:connect", "name": "Connect eBay", "category": "integrations", "description": "Connect eBay account"},
    {"code": "integrations:ebay:disconnect", "name": "Disconnect eBay", "category": "integrations", "description": "Disconnect eBay account"},
    {"code": "integrations:etsy:connect", "name": "Connect Etsy", "category": "integrations", "description": "Connect Etsy account"},
    {"code": "integrations:etsy:disconnect", "name": "Disconnect Etsy", "category": "integrations", "description": "Disconnect Etsy account"},

    # Stats
    {"code": "stats:read", "name": "View statistics", "category": "stats", "description": "View sales and performance stats"},
    {"code": "stats:export", "name": "Export statistics", "category": "stats", "description": "Export stats to CSV/Excel"},

    # Account
    {"code": "account:read", "name": "View account", "category": "account", "description": "View own account settings"},
    {"code": "account:update", "name": "Update account", "category": "account", "description": "Modify own account settings"},
    {"code": "subscription:read", "name": "View subscription", "category": "account", "description": "View subscription details"},
    {"code": "subscription:manage", "name": "Manage subscription", "category": "account", "description": "Change subscription plan"},

    # Admin
    {"code": "admin:users:read", "name": "View all users", "category": "admin", "description": "View all users in the system"},
    {"code": "admin:users:update", "name": "Update users", "category": "admin", "description": "Modify any user's data"},
    {"code": "admin:users:delete", "name": "Delete users", "category": "admin", "description": "Delete any user"},
    {"code": "admin:users:role", "name": "Change user roles", "category": "admin", "description": "Change any user's role"},
    {"code": "admin:permissions:manage", "name": "Manage permissions", "category": "admin", "description": "Modify role permissions"},
]

# Default role-permission mappings
DEFAULT_ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        # All permissions
        "products:read", "products:create", "products:update", "products:delete",
        "publications:read", "publications:create", "publications:delete",
        "integrations:read",
        "integrations:vinted:connect", "integrations:vinted:disconnect",
        "integrations:ebay:connect", "integrations:ebay:disconnect",
        "integrations:etsy:connect", "integrations:etsy:disconnect",
        "stats:read", "stats:export",
        "account:read", "account:update",
        "subscription:read", "subscription:manage",
        "admin:users:read", "admin:users:update", "admin:users:delete", "admin:users:role",
        "admin:permissions:manage",
    ],
    UserRole.USER: [
        # Own data only
        "products:read", "products:create", "products:update", "products:delete",
        "publications:read", "publications:create", "publications:delete",
        "integrations:read",
        "integrations:vinted:connect", "integrations:vinted:disconnect",
        "integrations:ebay:connect", "integrations:ebay:disconnect",
        "integrations:etsy:connect", "integrations:etsy:disconnect",
        "stats:read", "stats:export",
        "account:read", "account:update",
        "subscription:read", "subscription:manage",
    ],
    UserRole.SUPPORT: [
        # Read-only on all data
        "products:read",
        "publications:read",
        "integrations:read",
        "stats:read",
        "account:read", "account:update",  # Can update own account
        "subscription:read",
        "admin:users:read",  # Can view all users
    ],
}


__all__ = [
    "Permission",
    "RolePermission",
    "PermissionCategory",
    "DEFAULT_PERMISSIONS",
    "DEFAULT_ROLE_PERMISSIONS",
]
