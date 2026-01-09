"""emergency: create condition_sups table for prod

Revision ID: 20260109_1319
Revises: d4d7725adb3a
Create Date: 2026-01-09 13:19

Emergency fix for production deployment:
- Production branch never had 20260105_0001 which creates product_attributes.condition_sups
- Migration 20260107_1705 tries to reference this table but it doesn't exist
- This emergency migration creates the table if it doesn't exist

Safe to run on both dev (where table exists) and prod (where it doesn't).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

from logging import getLogger

logger = getLogger(__name__)


# revision identifiers, used by Alembic.
revision: str = '20260109_1319'
down_revision: Union[str, None] = 'd4d7725adb3a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(conn, schema, table):
    """Check if a table exists."""
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = :schema AND table_name = :table
        )
    """), {"schema": schema, "table": table})
    return result.scalar()


def upgrade() -> None:
    """Create product_attributes.condition_sups table if it doesn't exist."""
    conn = op.get_bind()

    logger.info("\n" + "=" * 70)
    logger.info("🚨 EMERGENCY: Creating condition_sups table")
    logger.info("=" * 70 + "\n")

    # Check if table already exists (dev has it, prod doesn't)
    if table_exists(conn, 'product_attributes', 'condition_sups'):
        logger.info("✅ Table product_attributes.condition_sups already exists")
        logger.info("   (probably in dev - skipping creation)")
        return

    logger.info("📋 Creating product_attributes.condition_sups table...")

    # Create the table
    conn.execute(text("""
        CREATE TABLE product_attributes.condition_sups (
            name_en VARCHAR(255) NOT NULL PRIMARY KEY,
            name_fr VARCHAR(255),
            name_de VARCHAR(255),
            name_it VARCHAR(255),
            name_es VARCHAR(255),
            name_nl VARCHAR(255),
            name_pl VARCHAR(255)
        )
    """))

    logger.info("✅ Table created successfully")

    # Seed with basic values (will be completed by later migrations)
    logger.info("📝 Seeding with basic values...")
    basic_values = [
        ('Faded', 'Délavé', 'Verblasst', 'Sbiadito', 'Desvanecido', 'Vervaagd', 'Wyblakły'),
        ('Vintage wear', 'Usure vintage', 'Vintage-Verschleiß', 'Usura vintage', 'Desgaste vintage', 'Vintage slijtage', 'Zużycie vintage'),
        ('General wear', 'Usure générale', 'Allgemeiner Verschleiß', 'Usura generale', 'Desgaste general', 'Algemene slijtage', 'Ogólne zużycie'),
        ('Single stain', 'Tache unique', 'Einzelner Fleck', 'Singola macchia', 'Mancha única', 'Enkele vlek', 'Pojedyncza plama'),
        ('Multiple stains', 'Plusieurs taches', 'Mehrere Flecken', 'Macchie multiple', 'Manchas múltiples', 'Meerdere vlekken', 'Wiele plam'),
        ('Small hole', 'Petit trou', 'Kleines Loch', 'Piccolo buco', 'Agujero pequeño', 'Klein gat', 'Mała dziura'),
        ('Frayed hems', 'Ourlets effilochés', 'Ausgefranste Säume', 'Orli sfilacciati', 'Dobladillos deshilachados', 'Gerafelde zomen', 'Postrzępione brzegi'),
    ]

    for values in basic_values:
        conn.execute(text("""
            INSERT INTO product_attributes.condition_sups
            (name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl)
            VALUES (:en, :fr, :de, :it, :es, :nl, :pl)
            ON CONFLICT (name_en) DO NOTHING
        """), {
            "en": values[0], "fr": values[1], "de": values[2],
            "it": values[3], "es": values[4], "nl": values[5], "pl": values[6]
        })

    logger.info(f"✅ Seeded {len(basic_values)} basic values")
    logger.info("\n" + "=" * 70)
    logger.info("✅ EMERGENCY FIX COMPLETE")
    logger.info("=" * 70)


def downgrade() -> None:
    """Drop condition_sups table."""
    conn = op.get_bind()

    if table_exists(conn, 'product_attributes', 'condition_sups'):
        conn.execute(text("DROP TABLE product_attributes.condition_sups CASCADE"))
        logger.info("✅ Dropped product_attributes.condition_sups table")
