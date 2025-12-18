"""replace_condition_letter_codes_with_explicit_names

Revision ID: 24d10525915b
Revises: 7c235d5f635c
Create Date: 2025-12-09 11:34:33.497874+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '24d10525915b'
down_revision: Union[str, None] = '7c235d5f635c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Replace letter-based condition codes (a, b, c, d) with explicit names (EXCELLENT, GOOD, FAIR, POOR).

    Steps:
    1. Insert new conditions with explicit names
    2. Update all products in all user schemas to use new condition codes
    3. Delete old letter-based conditions
    """

    # Step 1: Insert new conditions with explicit names
    op.execute("""
        INSERT INTO product_attributes.conditions (name, coefficient, vinted_id, ebay_condition, description_fr, description_en, description_de, description_it, description_es, description_nl, description_pl)
        VALUES
            ('EXCELLENT', 1.0, 2, 'PRE_OWNED_EXCELLENT', 'Très bon état', 'Excellent', 'Ausgezeichnet', 'Eccellente', 'Excelente', 'Uitstekend', 'Doskonały'),
            ('GOOD', 0.85, 3, 'PRE_OWNED_GOOD', 'Bon état', 'Good', 'Gut', 'Buono', 'Bueno', 'Goed', 'Dobry'),
            ('FAIR', 0.6, 4, 'PRE_OWNED_FAIR', 'État usé', 'Fair', 'Akzeptabel', 'Discreto', 'Aceptable', 'Redelijk', 'Zadowalający'),
            ('POOR', 0.5, 4, 'PRE_OWNED_POOR', 'État très usé', 'Poor', 'Schlecht', 'Scarso', 'Malo', 'Slecht', 'Zły')
        ON CONFLICT (name) DO NOTHING;
    """)

    # Step 2: Get all user schemas and update products in each schema
    connection = op.get_bind()

    # Get all user schemas (schemas starting with 'user_')
    result = connection.execute(sa.text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
    """))

    user_schemas = [row[0] for row in result]

    # Update products in each user schema
    for schema in user_schemas:
        # Update condition codes: a -> EXCELLENT, b -> GOOD, c -> FAIR, d -> POOR
        op.execute(sa.text(f"""
            UPDATE {schema}.products
            SET condition = CASE
                WHEN condition = 'a' THEN 'EXCELLENT'
                WHEN condition = 'b' THEN 'GOOD'
                WHEN condition = 'c' THEN 'FAIR'
                WHEN condition = 'd' THEN 'POOR'
                ELSE condition
            END
            WHERE condition IN ('a', 'b', 'c', 'd')
        """))

    # Step 3: Delete old letter-based conditions
    op.execute("""
        DELETE FROM product_attributes.conditions
        WHERE name IN ('a', 'b', 'c', 'd')
    """)


def downgrade() -> None:
    """
    Rollback: Restore letter-based condition codes.
    """

    # Step 1: Re-insert old letter-based conditions
    op.execute("""
        INSERT INTO product_attributes.conditions (name, coefficient, vinted_id, ebay_condition, description_fr, description_en, description_de, description_it, description_es, description_nl, description_pl)
        VALUES
            ('a', 1.0, 2, 'PRE_OWNED_EXCELLENT', 'Très bon état', 'Excellent', 'Ausgezeichnet', 'Eccellente', 'Excelente', 'Uitstekend', 'Doskonały'),
            ('b', 0.85, 3, 'PRE_OWNED_GOOD', 'Bon état', 'Good', 'Gut', 'Buono', 'Bueno', 'Goed', 'Dobry'),
            ('c', 0.6, 4, 'PRE_OWNED_FAIR', 'État usé', 'Fair', 'Akzeptabel', 'Discreto', 'Aceptable', 'Redelijk', 'Zadowalający'),
            ('d', 0.5, 4, 'PRE_OWNED_POOR', 'État très usé', 'Poor', 'Schlecht', 'Scarso', 'Malo', 'Slecht', 'Zły')
        ON CONFLICT (name) DO NOTHING;
    """)

    # Step 2: Update all products in all user schemas back to letter codes
    connection = op.get_bind()

    result = connection.execute(sa.text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
    """))

    user_schemas = [row[0] for row in result]

    for schema in user_schemas:
        op.execute(sa.text(f"""
            UPDATE {schema}.products
            SET condition = CASE
                WHEN condition = 'EXCELLENT' THEN 'a'
                WHEN condition = 'GOOD' THEN 'b'
                WHEN condition = 'FAIR' THEN 'c'
                WHEN condition = 'POOR' THEN 'd'
                ELSE condition
            END
            WHERE condition IN ('EXCELLENT', 'GOOD', 'FAIR', 'POOR')
        """))

    # Step 3: Delete new explicit-name conditions
    op.execute("""
        DELETE FROM product_attributes.conditions
        WHERE name IN ('EXCELLENT', 'GOOD', 'FAIR', 'POOR')
    """)
