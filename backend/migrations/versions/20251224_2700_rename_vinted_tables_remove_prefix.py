"""Rename vinted tables - remove vinted_ prefix

Revision ID: 20251224_2700
Revises: 20251224_2600
Create Date: 2025-12-24

Renames tables in vinted schema to remove redundant vinted_ prefix:
- vinted.vinted_action_types → vinted.action_types
- vinted.vinted_categories → vinted.categories
- vinted.vinted_mapping → vinted.mapping
- vinted.vinted_orders → vinted.orders
- vinted.vinted_order_products → vinted.order_products
- vinted.vinted_deletions → vinted.deletions
"""

from alembic import op

revision = "20251224_2700"
down_revision = "20251224_2600"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename tables
    op.execute("ALTER TABLE vinted.vinted_action_types RENAME TO action_types")
    print("  ✓ Renamed vinted_action_types → action_types")
    
    op.execute("ALTER TABLE vinted.vinted_categories RENAME TO categories")
    print("  ✓ Renamed vinted_categories → categories")
    
    op.execute("ALTER TABLE vinted.vinted_mapping RENAME TO mapping")
    print("  ✓ Renamed vinted_mapping → mapping")
    
    op.execute("ALTER TABLE vinted.vinted_orders RENAME TO orders")
    print("  ✓ Renamed vinted_orders → orders")
    
    op.execute("ALTER TABLE vinted.vinted_order_products RENAME TO order_products")
    print("  ✓ Renamed vinted_order_products → order_products")
    
    op.execute("ALTER TABLE vinted.vinted_deletions RENAME TO deletions")
    print("  ✓ Renamed vinted_deletions → deletions")
    
    # Rename sequences
    op.execute("ALTER SEQUENCE IF EXISTS vinted.vinted_action_types_id_seq RENAME TO action_types_id_seq")
    op.execute("ALTER SEQUENCE IF EXISTS vinted.vinted_categories_id_seq RENAME TO categories_id_seq")
    op.execute("ALTER SEQUENCE IF EXISTS vinted.vinted_mapping_id_seq RENAME TO mapping_id_seq")
    op.execute("ALTER SEQUENCE IF EXISTS vinted.vinted_deletions_id_seq RENAME TO deletions_id_seq")
    op.execute("ALTER SEQUENCE IF EXISTS vinted.vinted_order_products_id_seq RENAME TO order_products_id_seq")
    print("  ✓ Renamed sequences")
    
    # Rename indexes
    op.execute("ALTER INDEX IF EXISTS vinted.idx_vinted_mapping_default RENAME TO idx_mapping_default")
    op.execute("ALTER INDEX IF EXISTS vinted.idx_vinted_mapping_lookup RENAME TO idx_mapping_lookup")
    op.execute("ALTER INDEX IF EXISTS vinted.idx_vinted_orders_buyer_id RENAME TO idx_orders_buyer_id")
    op.execute("ALTER INDEX IF EXISTS vinted.idx_vinted_orders_status RENAME TO idx_orders_status")
    op.execute("ALTER INDEX IF EXISTS vinted.idx_vinted_orders_created_at_vinted RENAME TO idx_orders_created_at_vinted")
    op.execute("ALTER INDEX IF EXISTS vinted.idx_vinted_order_products_transaction_id RENAME TO idx_order_products_transaction_id")
    op.execute("ALTER INDEX IF EXISTS vinted.idx_vinted_order_products_vinted_item_id RENAME TO idx_order_products_vinted_item_id")
    op.execute("ALTER INDEX IF EXISTS vinted.idx_vinted_order_products_product_id RENAME TO idx_order_products_product_id")
    op.execute("ALTER INDEX IF EXISTS vinted.idx_vinted_deletions_id_vinted RENAME TO idx_deletions_id_vinted")
    op.execute("ALTER INDEX IF EXISTS vinted.idx_vinted_deletions_id_site RENAME TO idx_deletions_id_site")
    op.execute("ALTER INDEX IF EXISTS vinted.idx_vinted_deletions_date_deleted RENAME TO idx_deletions_date_deleted")
    op.execute("ALTER INDEX IF EXISTS vinted.idx_vinted_deletions_days_active RENAME TO idx_deletions_days_active")
    print("  ✓ Renamed indexes")
    
    # Update FK constraint names
    op.execute("ALTER TABLE vinted.mapping DROP CONSTRAINT IF EXISTS vinted_mapping_my_category_fkey")
    op.execute("""
        ALTER TABLE vinted.mapping 
        ADD CONSTRAINT mapping_my_category_fkey 
        FOREIGN KEY (my_category) REFERENCES product_attributes.categories(name_en)
    """)
    
    op.execute("ALTER TABLE vinted.order_products DROP CONSTRAINT IF EXISTS vinted_order_products_transaction_id_fkey")
    op.execute("""
        ALTER TABLE vinted.order_products 
        ADD CONSTRAINT order_products_transaction_id_fkey 
        FOREIGN KEY (transaction_id) REFERENCES vinted.orders(transaction_id) ON DELETE CASCADE
    """)
    print("  ✓ Updated FK constraints")


def downgrade() -> None:
    # Rename tables back
    op.execute("ALTER TABLE vinted.action_types RENAME TO vinted_action_types")
    op.execute("ALTER TABLE vinted.categories RENAME TO vinted_categories")
    op.execute("ALTER TABLE vinted.mapping RENAME TO vinted_mapping")
    op.execute("ALTER TABLE vinted.orders RENAME TO vinted_orders")
    op.execute("ALTER TABLE vinted.order_products RENAME TO vinted_order_products")
    op.execute("ALTER TABLE vinted.deletions RENAME TO vinted_deletions")
