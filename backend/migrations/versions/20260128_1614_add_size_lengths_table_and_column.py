"""add size_lengths table and product.size_length column

Creates the size_lengths reference table in product_attributes schema
and adds size_length column to all tenant products tables.

Phase 1A of size system refactoring:
- Separate waist (W32) from leg length (L34) for bottoms
- size_lengths stores standard leg lengths: 26, 28, 30, 32, 34, 36, 38

Revision ID: e1f2a3b4c5d6
Revises: dd45dbbb6368
Create Date: 2026-01-28
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = 'e1f2a3b4c5d6'
down_revision: Union[str, None] = 'dd45dbbb6368'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Standard leg length values (in inches)
STANDARD_LENGTHS = [
    ('26', 26),
    ('28', 28),
    ('30', 30),
    ('32', 32),
    ('34', 34),
    ('36', 36),
    ('38', 38),
]


def _get_tenant_schemas(conn) -> list[str]:
    """Get all tenant schemas (user_X) + template_tenant."""
    result = conn.execute(text(
        "SELECT schema_name FROM information_schema.schemata "
        "WHERE schema_name LIKE 'user_%' OR schema_name = 'template_tenant' "
        "ORDER BY schema_name"
    ))
    return [row[0] for row in result]


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Create size_lengths table in product_attributes schema
    table_exists = conn.execute(text(
        "SELECT EXISTS ("
        "  SELECT 1 FROM information_schema.tables "
        "  WHERE table_schema = 'product_attributes' AND table_name = 'size_lengths'"
        ")"
    )).scalar()

    if not table_exists:
        conn.execute(text("""
            CREATE TABLE product_attributes.size_lengths (
                name_en VARCHAR(20) PRIMARY KEY,
                equivalent_inches INTEGER
            )
        """))

        # Create index
        conn.execute(text(
            "CREATE INDEX idx_size_lengths_name_en ON product_attributes.size_lengths(name_en)"
        ))

        # Seed standard values
        for name, inches in STANDARD_LENGTHS:
            conn.execute(text(
                "INSERT INTO product_attributes.size_lengths (name_en, equivalent_inches) "
                "VALUES (:name, :inches)"
            ), {"name": name, "inches": inches})

    # 2. Add size_length column to all tenant products tables
    schemas = _get_tenant_schemas(conn)

    for schema in schemas:
        # Check if products table exists
        products_exists = conn.execute(text(
            "SELECT EXISTS ("
            "  SELECT 1 FROM information_schema.tables "
            "  WHERE table_schema = :schema AND table_name = 'products'"
            ")"
        ), {"schema": schema}).scalar()

        if not products_exists:
            continue

        # Check if column already exists (idempotent)
        col_exists = conn.execute(text(
            "SELECT EXISTS ("
            "  SELECT 1 FROM information_schema.columns "
            "  WHERE table_schema = :schema "
            "    AND table_name = 'products' "
            "    AND column_name = 'size_length'"
            ")"
        ), {"schema": schema}).scalar()

        if col_exists:
            continue

        # Add column
        conn.execute(text(
            f'ALTER TABLE "{schema}".products '
            f'ADD COLUMN size_length VARCHAR(20)'
        ))

        # Add FK constraint
        conn.execute(text(
            f'ALTER TABLE "{schema}".products '
            f'ADD CONSTRAINT fk_products_size_length '
            f'FOREIGN KEY (size_length) REFERENCES product_attributes.size_lengths(name_en) '
            f'ON UPDATE CASCADE ON DELETE SET NULL'
        ))


def downgrade() -> None:
    conn = op.get_bind()
    schemas = _get_tenant_schemas(conn)

    # 1. Remove size_length column from all tenant products tables
    for schema in schemas:
        # Check if column exists
        col_exists = conn.execute(text(
            "SELECT EXISTS ("
            "  SELECT 1 FROM information_schema.columns "
            "  WHERE table_schema = :schema "
            "    AND table_name = 'products' "
            "    AND column_name = 'size_length'"
            ")"
        ), {"schema": schema}).scalar()

        if col_exists:
            # Drop FK constraint first
            conn.execute(text(
                f'ALTER TABLE "{schema}".products DROP CONSTRAINT IF EXISTS fk_products_size_length'
            ))
            # Drop column
            conn.execute(text(
                f'ALTER TABLE "{schema}".products DROP COLUMN size_length'
            ))

    # 2. Drop size_lengths table
    conn.execute(text("DROP TABLE IF EXISTS product_attributes.size_lengths"))
