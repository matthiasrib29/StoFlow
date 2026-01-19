"""add_hex_codes_to_colors

Revision ID: 8f3a2b1c9d0e
Revises: c4ce5f067571
Create Date: 2026-01-19 13:20:00.000000+01:00

Adds hex color codes to product_attributes.colors table for UI display.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8f3a2b1c9d0e'
down_revision: Union[str, None] = 'c4ce5f067571'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Color to hex code mapping
COLOR_HEX_CODES = {
    'Beige': '#F5F5DC',
    'Black': '#000000',
    'Blue': '#0066CC',
    'Blush': '#DE5D83',
    'Bronze': '#CD7F32',
    'Brown': '#8B4513',
    'Burgundy': '#800020',
    'Burnt orange': '#CC5500',
    'Butter yellow': '#FFFACD',
    'Camel': '#C19A6B',
    'Charcoal': '#36454F',
    'Cherry red': '#DE3163',
    'Chocolate': '#7B3F00',
    'Cinnamon': '#D2691E',
    'Cobalt': '#0047AB',
    'Cognac': '#9A463D',
    'Coral': '#FF7F50',
    'Cream': '#FFFDD0',
    'Dusty pink': '#D4A5A5',
    'Eggplant': '#614051',
    'Emerald': '#50C878',
    'Espresso': '#3C2415',
    'Forest green': '#228B22',
    'Fuchsia': '#FF00FF',
    'Gold': '#FFD700',
    'Gray': '#808080',
    'Green': '#228B22',
    'Hot pink': '#FF69B4',
    'Indigo': '#4B0082',
    'Ivory': '#FFFFF0',
    'Khaki': '#C3B091',
    'Klein blue': '#002FA7',
    'Lavender': '#E6E6FA',
    'Light-blue': '#ADD8E6',
    'Lilac': '#C8A2C8',
    'Mauve': '#E0B0FF',
    'Metallic': '#AAA9AD',
    'Mint': '#98FB98',
    'Mocha': '#967969',
    'Multicolor': None,  # Special case - no single hex
    'Mustard': '#FFDB58',
    'Navy': '#000080',
    'Nude': '#E3BC9A',
    'Off-white': '#FAF9F6',
    'Olive': '#808000',
    'Orange': '#FFA500',
    'Peach': '#FFCBA4',
    'Pink': '#FFC0CB',
    'Plum': '#8E4585',
    'Powder blue': '#B0E0E6',
    'Purple': '#800080',
    'Red': '#FF0000',
    'Rose gold': '#B76E79',
    'Rust': '#B7410E',
    'Sage': '#9DC183',
    'Sand': '#C2B280',
    'Silver': '#C0C0C0',
    'Slate': '#708090',
    'Tan': '#D2B48C',
    'Taupe': '#483C32',
    'Teal': '#008080',
    'Terracotta': '#E2725B',
    'Turquoise': '#40E0D0',
    'Vanilla yellow': '#F3E5AB',
    'White': '#FFFFFF',
    'Wine': '#722F37',
    'Yellow': '#FFFF00',
}


def upgrade() -> None:
    """Add hex codes to all colors."""
    conn = op.get_bind()

    updated = 0
    for color_name, hex_code in COLOR_HEX_CODES.items():
        if hex_code is None:
            continue
        result = conn.execute(sa.text("""
            UPDATE product_attributes.colors
            SET hex_code = :hex_code
            WHERE name_en = :name
            AND (hex_code IS NULL OR hex_code = '')
        """), {'hex_code': hex_code, 'name': color_name})
        updated += result.rowcount

    print(f"  Updated {updated} colors with hex codes")


def downgrade() -> None:
    """Remove hex codes from colors."""
    conn = op.get_bind()

    conn.execute(sa.text("""
        UPDATE product_attributes.colors
        SET hex_code = NULL
    """))

    print("  Removed hex codes from colors")
