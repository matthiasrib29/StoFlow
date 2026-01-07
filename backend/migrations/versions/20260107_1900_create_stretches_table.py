"""create stretches table

Revision ID: a1b2c3d4e5f6
Revises: 9c7c0b878bb4
Create Date: 2026-01-07 19:00:00.000000+01:00

Purpose:
    Create product_attributes.stretches table with multilingual support (7 languages).
    Seed table with 4 standard stretch levels:
    - No Stretch
    - Slight Stretch
    - Moderate Stretch
    - Super Stretch
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '9c7c0b878bb4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create stretches table and seed initial values."""
    conn = op.get_bind()

    print("\n" + "=" * 70)
    print("📊 CREATING STRETCHES TABLE")
    print("=" * 70 + "\n")

    # Create table
    conn.execute(text("""
        CREATE TABLE product_attributes.stretches (
            name_en VARCHAR(100) PRIMARY KEY,
            name_fr VARCHAR(100),
            name_de VARCHAR(100),
            name_it VARCHAR(100),
            name_es VARCHAR(100),
            name_nl VARCHAR(100),
            name_pl VARCHAR(100)
        );
    """))

    # Create index
    conn.execute(text("""
        CREATE INDEX idx_stretches_name_en
        ON product_attributes.stretches(name_en);
    """))

    print("✅ Created stretches table with 7 languages support")

    # Seed data (Title Case)
    stretches = [
        ("No Stretch", "Aucun Stretch", "Kein Stretch", "Nessun Stretch",
         "Sin Elasticidad", "Geen Stretch", "Bez Rozciągliwości"),
        ("Slight Stretch", "Léger Stretch", "Leichter Stretch", "Leggero Stretch",
         "Elasticidad Ligera", "Lichte Stretch", "Lekka Rozciągliwość"),
        ("Moderate Stretch", "Stretch Modéré", "Mäßiger Stretch", "Stretch Moderato",
         "Elasticidad Moderada", "Matige Stretch", "Umiarkowana Rozciągliwość"),
        ("Super Stretch", "Super Stretch", "Super Stretch", "Super Stretch",
         "Super Elasticidad", "Super Stretch", "Super Rozciągliwość")
    ]

    for name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl in stretches:
        conn.execute(text("""
            INSERT INTO product_attributes.stretches
            (name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl)
            VALUES (:name_en, :name_fr, :name_de, :name_it, :name_es, :name_nl, :name_pl)
            ON CONFLICT (name_en) DO NOTHING;
        """), {
            "name_en": name_en, "name_fr": name_fr, "name_de": name_de,
            "name_it": name_it, "name_es": name_es, "name_nl": name_nl, "name_pl": name_pl
        })

    print(f"✅ Seeded {len(stretches)} stretch values")
    print("\nStretch values added:")
    for name_en, name_fr, *_ in stretches:
        print(f"  - {name_en} / {name_fr}")

    print("\n" + "=" * 70)
    print("✅ STRETCHES TABLE CREATED")
    print("=" * 70)


def downgrade() -> None:
    """Drop stretches table."""
    conn = op.get_bind()

    print("\n⚠️  Dropping stretches table...")

    conn.execute(text("DROP TABLE IF EXISTS product_attributes.stretches CASCADE;"))

    print("✅ Stretches table dropped")
