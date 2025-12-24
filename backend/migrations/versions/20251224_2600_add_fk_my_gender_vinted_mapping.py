"""Add FK on my_gender in vinted_mapping

Revision ID: 20251224_2600
Revises: 20251224_2500
Create Date: 2025-12-24

Adds foreign key constraint on my_gender referencing product_attributes.genders(name_en)
"""

from alembic import op

revision = "20251224_2600"
down_revision = "20251224_2500"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE vinted.vinted_mapping
        ADD CONSTRAINT fk_vinted_mapping_gender
        FOREIGN KEY (my_gender) 
        REFERENCES product_attributes.genders(name_en)
        ON UPDATE CASCADE
        ON DELETE SET NULL
    """)
    print("  ✓ Added FK constraint on my_gender")


def downgrade() -> None:
    op.execute("""
        ALTER TABLE vinted.vinted_mapping
        DROP CONSTRAINT IF EXISTS fk_vinted_mapping_gender
    """)
    print("  ✓ Dropped FK constraint on my_gender")
