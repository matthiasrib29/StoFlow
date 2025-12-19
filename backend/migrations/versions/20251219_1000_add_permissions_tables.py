"""Add permissions and role_permissions tables for RBAC

Revision ID: 20251219_1000
Revises: 20251218_2400
Create Date: 2025-12-19

Business Rules:
- Permissions stored in database (modifiable without code change)
- RolePermission links roles to permissions
- Seed default permissions for ADMIN, USER, SUPPORT roles
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20251219_1000'
down_revision: Union[str, None] = '20251218_2400'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create permissions table
    op.create_table(
        'permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(100), nullable=False, comment="Unique permission code (e.g., 'products:create')"),
        sa.Column('name', sa.String(255), nullable=False, comment="Human-readable permission name"),
        sa.Column('description', sa.String(500), nullable=True, comment="Description of what this permission allows"),
        sa.Column('category', sa.String(50), nullable=False, comment="Permission category for grouping"),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment="Whether this permission is active"),
        sa.PrimaryKeyConstraint('id'),
        schema='public'
    )
    op.create_index('ix_public_permissions_id', 'permissions', ['id'], unique=False, schema='public')
    op.create_index('ix_public_permissions_code', 'permissions', ['code'], unique=True, schema='public')

    # Create role_permissions table
    op.create_table(
        'role_permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('role', sa.Enum('admin', 'user', 'support', name='userrole', schema='public', create_type=False), nullable=False, comment="User role"),
        sa.Column('permission_id', sa.Integer(), nullable=False, comment="Permission ID"),
        sa.ForeignKeyConstraint(['permission_id'], ['public.permissions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('role', 'permission_id', name='uq_role_permission'),
        schema='public'
    )
    op.create_index('ix_public_role_permissions_id', 'role_permissions', ['id'], unique=False, schema='public')
    op.create_index('ix_public_role_permissions_role', 'role_permissions', ['role'], unique=False, schema='public')
    op.create_index('ix_public_role_permissions_permission_id', 'role_permissions', ['permission_id'], unique=False, schema='public')

    # Seed default permissions
    permissions_table = sa.table(
        'permissions',
        sa.column('id', sa.Integer),
        sa.column('code', sa.String),
        sa.column('name', sa.String),
        sa.column('description', sa.String),
        sa.column('category', sa.String),
        sa.column('is_active', sa.Boolean),
        schema='public'
    )

    default_permissions = [
        # Products
        {"id": 1, "code": "products:read", "name": "View products", "category": "products", "description": "View product list and details", "is_active": True},
        {"id": 2, "code": "products:create", "name": "Create products", "category": "products", "description": "Create new products", "is_active": True},
        {"id": 3, "code": "products:update", "name": "Update products", "category": "products", "description": "Modify existing products", "is_active": True},
        {"id": 4, "code": "products:delete", "name": "Delete products", "category": "products", "description": "Delete products", "is_active": True},

        # Publications
        {"id": 5, "code": "publications:read", "name": "View publications", "category": "publications", "description": "View publication list and status", "is_active": True},
        {"id": 6, "code": "publications:create", "name": "Publish products", "category": "publications", "description": "Publish products to marketplaces", "is_active": True},
        {"id": 7, "code": "publications:delete", "name": "Unpublish products", "category": "publications", "description": "Remove products from marketplaces", "is_active": True},

        # Integrations
        {"id": 8, "code": "integrations:read", "name": "View integrations", "category": "integrations", "description": "View connected platforms", "is_active": True},
        {"id": 9, "code": "integrations:vinted:connect", "name": "Connect Vinted", "category": "integrations", "description": "Connect Vinted account", "is_active": True},
        {"id": 10, "code": "integrations:vinted:disconnect", "name": "Disconnect Vinted", "category": "integrations", "description": "Disconnect Vinted account", "is_active": True},
        {"id": 11, "code": "integrations:ebay:connect", "name": "Connect eBay", "category": "integrations", "description": "Connect eBay account", "is_active": True},
        {"id": 12, "code": "integrations:ebay:disconnect", "name": "Disconnect eBay", "category": "integrations", "description": "Disconnect eBay account", "is_active": True},
        {"id": 13, "code": "integrations:etsy:connect", "name": "Connect Etsy", "category": "integrations", "description": "Connect Etsy account", "is_active": True},
        {"id": 14, "code": "integrations:etsy:disconnect", "name": "Disconnect Etsy", "category": "integrations", "description": "Disconnect Etsy account", "is_active": True},

        # Stats
        {"id": 15, "code": "stats:read", "name": "View statistics", "category": "stats", "description": "View sales and performance stats", "is_active": True},
        {"id": 16, "code": "stats:export", "name": "Export statistics", "category": "stats", "description": "Export stats to CSV/Excel", "is_active": True},

        # Account
        {"id": 17, "code": "account:read", "name": "View account", "category": "account", "description": "View own account settings", "is_active": True},
        {"id": 18, "code": "account:update", "name": "Update account", "category": "account", "description": "Modify own account settings", "is_active": True},
        {"id": 19, "code": "subscription:read", "name": "View subscription", "category": "account", "description": "View subscription details", "is_active": True},
        {"id": 20, "code": "subscription:manage", "name": "Manage subscription", "category": "account", "description": "Change subscription plan", "is_active": True},

        # Admin
        {"id": 21, "code": "admin:users:read", "name": "View all users", "category": "admin", "description": "View all users in the system", "is_active": True},
        {"id": 22, "code": "admin:users:update", "name": "Update users", "category": "admin", "description": "Modify any user's data", "is_active": True},
        {"id": 23, "code": "admin:users:delete", "name": "Delete users", "category": "admin", "description": "Delete any user", "is_active": True},
        {"id": 24, "code": "admin:users:role", "name": "Change user roles", "category": "admin", "description": "Change any user's role", "is_active": True},
        {"id": 25, "code": "admin:permissions:manage", "name": "Manage permissions", "category": "admin", "description": "Modify role permissions", "is_active": True},
    ]

    op.bulk_insert(permissions_table, default_permissions)

    # Seed role_permissions
    role_permissions_table = sa.table(
        'role_permissions',
        sa.column('role', sa.Enum),
        sa.column('permission_id', sa.Integer),
        schema='public'
    )

    # ADMIN: all permissions (1-25)
    admin_permissions = [{"role": "admin", "permission_id": i} for i in range(1, 26)]

    # USER: products, publications, integrations, stats, account (1-20)
    user_permissions = [{"role": "user", "permission_id": i} for i in range(1, 21)]

    # SUPPORT: read-only (1, 5, 8, 15, 17, 18, 19, 21)
    support_permission_ids = [1, 5, 8, 15, 17, 18, 19, 21]
    support_permissions = [{"role": "support", "permission_id": i} for i in support_permission_ids]

    op.bulk_insert(role_permissions_table, admin_permissions + user_permissions + support_permissions)

    # Reset sequence for permissions table
    op.execute("SELECT setval('public.permissions_id_seq', (SELECT MAX(id) FROM public.permissions))")


def downgrade() -> None:
    # Drop role_permissions table
    op.drop_index('ix_public_role_permissions_permission_id', table_name='role_permissions', schema='public')
    op.drop_index('ix_public_role_permissions_role', table_name='role_permissions', schema='public')
    op.drop_index('ix_public_role_permissions_id', table_name='role_permissions', schema='public')
    op.drop_table('role_permissions', schema='public')

    # Drop permissions table
    op.drop_index('ix_public_permissions_code', table_name='permissions', schema='public')
    op.drop_index('ix_public_permissions_id', table_name='permissions', schema='public')
    op.drop_table('permissions', schema='public')
