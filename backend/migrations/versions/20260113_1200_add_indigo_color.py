"""add: Indigo color with translations and Blue parent

Revision ID: 20260113_1200
Revises: 20260113_1100
Create Date: 2026-01-13

Adds the Indigo color to product_attributes.colors with:
- All 7 language translations (EN, FR, DE, IT, ES, NL, PL)
- Parent color: Blue
- Hex code: #4B0082
"""
from alembic import op
from sqlalchemy import text
from logging import getLogger

logger = getLogger(__name__)

# revision identifiers, used by Alembic.
revision = '20260113_1200'
down_revision = '20260113_1100'
branch_labels = None
depends_on = None


# Indigo color data with translations
INDIGO_COLOR = {
    'name_en': 'Indigo',
    'name_fr': 'Indigo',
    'name_de': 'Indigo',
    'name_it': 'Indaco',
    'name_es': 'Indigo',
    'name_nl': 'Indigo',
    'name_pl': 'Indygo',
    'hex_code': '#4B0082',
    'parent_color': 'Blue',
    'vinted_id': None,  # No Vinted mapping yet
}


def upgrade() -> None:
    """Add Indigo color to product_attributes.colors."""
    connection = op.get_bind()

    # Insert Indigo color with ON CONFLICT to be idempotent
    connection.execute(
        text("""
            INSERT INTO product_attributes.colors (
                name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl,
                hex_code, parent_color, vinted_id
            ) VALUES (
                :name_en, :name_fr, :name_de, :name_it, :name_es, :name_nl, :name_pl,
                :hex_code, :parent_color, :vinted_id
            )
            ON CONFLICT (name_en) DO UPDATE SET
                name_fr = EXCLUDED.name_fr,
                name_de = EXCLUDED.name_de,
                name_it = EXCLUDED.name_it,
                name_es = EXCLUDED.name_es,
                name_nl = EXCLUDED.name_nl,
                name_pl = EXCLUDED.name_pl,
                hex_code = EXCLUDED.hex_code,
                parent_color = EXCLUDED.parent_color
        """),
        INDIGO_COLOR
    )
    logger.info("  - Added Indigo color with Blue parent and translations")


def downgrade() -> None:
    """Remove Indigo color from product_attributes.colors."""
    connection = op.get_bind()

    connection.execute(
        text("""
            DELETE FROM product_attributes.colors
            WHERE name_en = 'Indigo'
        """)
    )
    logger.info("  - Removed Indigo color")
