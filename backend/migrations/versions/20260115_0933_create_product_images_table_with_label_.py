"""create product_images table with label flag

Revision ID: 077dc55ef8d0
Revises: 78c0a01b2a38
Create Date: 2026-01-15 09:33:45.836153+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '077dc55ef8d0'
down_revision: Union[str, None] = '78c0a01b2a38'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_user_schemas(conn) -> list[str]:
    """Get all user schemas (user_*)."""
    result = conn.execute(
        text("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name LIKE 'user_%'
            ORDER BY schema_name
        """)
    )
    return [row[0] for row in result.fetchall()]


def table_exists(conn, schema: str, table: str) -> bool:
    """Check if table exists in schema."""
    result = conn.execute(
        text("""
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = :schema
                AND table_name = :table
            )
        """),
        {"schema": schema, "table": table}
    )
    return result.scalar()


def upgrade() -> None:
    conn = op.get_bind()

    # Get all user schemas + template
    user_schemas = get_user_schemas(conn)
    if "template_tenant" not in user_schemas:
        user_schemas.append("template_tenant")

    for schema in user_schemas:
        # Check if table already exists (idempotent)
        if table_exists(conn, schema, "product_images"):
            print(f"✓ Table {schema}.product_images already exists, skipping")
            continue

        print(f"Creating {schema}.product_images table...")

        # Create table
        conn.execute(text(f"""
            CREATE TABLE {schema}.product_images (
                id SERIAL PRIMARY KEY,
                product_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                "order" INTEGER NOT NULL,

                -- Critical flag for label distinction
                is_label BOOLEAN NOT NULL DEFAULT FALSE,

                -- SEO and metadata
                alt_text TEXT,
                tags TEXT[],

                -- File metadata
                mime_type VARCHAR(100),
                file_size INTEGER,
                width INTEGER,
                height INTEGER,

                -- Timestamps
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

                -- Constraints
                CONSTRAINT fk_product_images_product_id
                    FOREIGN KEY (product_id)
                    REFERENCES {schema}.products(id)
                    ON DELETE CASCADE,

                CONSTRAINT uq_product_images_product_order
                    UNIQUE (product_id, "order")
            )
        """))

        # Create indexes
        conn.execute(text(f"""
            CREATE INDEX idx_product_images_product_id
            ON {schema}.product_images(product_id)
        """))

        conn.execute(text(f"""
            CREATE INDEX idx_product_images_is_label
            ON {schema}.product_images(is_label)
        """))

        conn.execute(text(f"""
            CREATE INDEX idx_product_images_order
            ON {schema}.product_images(product_id, "order")
        """))

        print(f"✓ Created {schema}.product_images with indexes")


def downgrade() -> None:
    conn = op.get_bind()

    # Get all user schemas + template
    user_schemas = get_user_schemas(conn)
    if "template_tenant" not in user_schemas:
        user_schemas.append("template_tenant")

    for schema in user_schemas:
        if not table_exists(conn, schema, "product_images"):
            print(f"✓ Table {schema}.product_images doesn't exist, skipping")
            continue

        print(f"Dropping {schema}.product_images table...")

        # Drop table (cascade drops indexes automatically)
        conn.execute(text(f"""
            DROP TABLE IF EXISTS {schema}.product_images CASCADE
        """))

        print(f"✓ Dropped {schema}.product_images")
