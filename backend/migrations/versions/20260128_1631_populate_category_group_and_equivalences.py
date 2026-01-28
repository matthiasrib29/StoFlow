"""populate category_group and equivalences in sizes_normalized

Data migration to set:
- category_group based on size patterns
- International equivalences (FR/US/IT)

Category groups:
- letter: XXS, XS, S, M, L, XL, XXL, XXXL, 4XL, 5XL
- numeric_eu: 34, 36, 38, 40, 42, 44, 46, 48, 50, 52
- waist: W24, W26, W28, W30, W32, W34, W36, W38, W40, W42, W44, W46
- one_size: One Size, Unique, TAILLE UNIQUE

Revision ID: sz_catgrp_002
Revises: sz_catgrp_001
Create Date: 2026-01-28
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = 'sz_catgrp_002'
down_revision: Union[str, None] = 'sz_catgrp_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Category group patterns
LETTER_SIZES = ['XXS', 'XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL', '3XL', '4XL', '5XL']
NUMERIC_EU_SIZES = ['32', '34', '36', '38', '40', '42', '44', '46', '48', '50', '52', '54', '56']
ONE_SIZE_PATTERNS = ['One Size', 'Unique', 'TAILLE UNIQUE', 'OS', 'U', 'TU']

# Size equivalences (unified, not gender-specific)
# Format: name_en -> (fr, us, it)
SIZE_EQUIVALENCES = {
    # Letter sizes
    'XXS': ('32', '0-2', '36'),
    'XS': ('34', '2-4', '38'),
    'S': ('36', '4-6', '40'),
    'M': ('38-40', '8-10', '42-44'),
    'L': ('42-44', '12-14', '46-48'),
    'XL': ('46-48', '16-18', '50-52'),
    'XXL': ('50-52', '20-22', '54-56'),
    'XXXL': ('54-56', '24-26', '58-60'),
    '3XL': ('54-56', '24-26', '58-60'),
    '4XL': ('58-60', '28-30', '62-64'),
    '5XL': ('62-64', '32-34', '66-68'),

    # Numeric EU sizes (women's clothing typically)
    '32': ('32', '0', '36'),
    '34': ('34', '2', '38'),
    '36': ('36', '4', '40'),
    '38': ('38', '6', '42'),
    '40': ('40', '8', '44'),
    '42': ('42', '10', '46'),
    '44': ('44', '12', '48'),
    '46': ('46', '14', '50'),
    '48': ('48', '16', '52'),
    '50': ('50', '18', '54'),
    '52': ('52', '20', '56'),
    '54': ('54', '22', '58'),
    '56': ('56', '24', '60'),

    # One size
    'One Size': (None, None, None),
    'Unique': (None, None, None),
    'TAILLE UNIQUE': (None, None, None),
}


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Set category_group for letter sizes
    letter_list = "'" + "','".join(LETTER_SIZES) + "'"
    conn.execute(text(f"""
        UPDATE product_attributes.sizes_normalized
        SET category_group = 'letter'
        WHERE name_en IN ({letter_list})
          AND category_group IS NULL
    """))

    # 2. Set category_group for numeric EU sizes
    numeric_list = "'" + "','".join(NUMERIC_EU_SIZES) + "'"
    conn.execute(text(f"""
        UPDATE product_attributes.sizes_normalized
        SET category_group = 'numeric_eu'
        WHERE name_en IN ({numeric_list})
          AND category_group IS NULL
    """))

    # 3. Set category_group for waist sizes (W24, W26, etc.)
    conn.execute(text("""
        UPDATE product_attributes.sizes_normalized
        SET category_group = 'waist'
        WHERE name_en ~ '^W\\d{2}'
          AND category_group IS NULL
    """))

    # 4. Set category_group for one_size
    one_size_list = "'" + "','".join(ONE_SIZE_PATTERNS) + "'"
    conn.execute(text(f"""
        UPDATE product_attributes.sizes_normalized
        SET category_group = 'one_size'
        WHERE name_en IN ({one_size_list})
          AND category_group IS NULL
    """))

    # 5. Set equivalences for known sizes
    for name_en, (fr, us, it) in SIZE_EQUIVALENCES.items():
        # Build SET clause dynamically
        set_parts = []
        params = {"name_en": name_en}

        if fr is not None:
            set_parts.append("equivalent_fr = :fr")
            params["fr"] = fr
        if us is not None:
            set_parts.append("equivalent_us = :us")
            params["us"] = us
        if it is not None:
            set_parts.append("equivalent_it = :it")
            params["it"] = it

        if set_parts:
            set_clause = ", ".join(set_parts)
            conn.execute(text(f"""
                UPDATE product_attributes.sizes_normalized
                SET {set_clause}
                WHERE name_en = :name_en
            """), params)


def downgrade() -> None:
    conn = op.get_bind()

    # Reset all category_group and equivalences to NULL
    conn.execute(text("""
        UPDATE product_attributes.sizes_normalized
        SET category_group = NULL,
            equivalent_fr = NULL,
            equivalent_us = NULL,
            equivalent_it = NULL
    """))
