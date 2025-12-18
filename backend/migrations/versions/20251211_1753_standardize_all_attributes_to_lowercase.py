"""standardize_all_attributes_to_lowercase

Revision ID: 2l3m4n5o6p7q
Revises: 1k2l3m4n5o6p
Create Date: 2025-12-11 17:53:00.000000+01:00

Cette migration standardise toutes les valeurs name_en en minuscules (lowercase)
pour assurer la cohérence entre toutes les tables product_attributes.

Business Rule (Validé 2025-12-11):
- Toutes les valeurs name_en doivent être en minuscules pour cohérence
- Format standardisé : lowercase pour les IDs internes
- Les traductions (name_fr, etc.) gardent leur casse originale

Tables affectées:
- lengths: "Cropped" → "cropped", "Ankle" → "ankle", etc.
- necklines: "Boat Neck" → "boat neck", "Round Neck" → "round neck", etc.
- patterns: "Abstract" → "abstract", "Animal Print" → "animal print", etc.
- sports: "Baseball" → "baseball", "American Football" → "american football", etc.
- conditions: "EXCELLENT" → "excellent", "FAIR" → "fair", etc.

Actions:
1. Pour chaque table, convertir name_en en minuscules
2. Mettre à jour les références dans products (template_tenant + user schemas)

Author: Claude
Date: 2025-12-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2l3m4n5o6p7q'
down_revision: Union[str, None] = '1k2l3m4n5o6p'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Tables à standardiser avec leur colonne de référence dans products
# Format: (table_name, product_column, pk_column_name)
# pk_column_name: 'name_en' pour la plupart, 'name' pour conditions/sizes/brands
TABLES_TO_STANDARDIZE = [
    ('lengths', 'length', 'name_en'),
    ('necklines', 'neckline', 'name_en'),
    ('patterns', 'pattern', 'name_en'),
    ('sports', 'sport', 'name_en'),
    ('conditions', 'condition', 'name'),  # Note: uses 'name' not 'name_en'
]


def upgrade() -> None:
    """
    Convertit toutes les valeurs name_en en minuscules.
    """
    connection = op.get_bind()

    total_updated = 0

    for table_name, product_column, pk_column in TABLES_TO_STANDARDIZE:
        print(f"\n  🔄 Processing {table_name.upper()}...")

        # 1. Récupérer toutes les valeurs actuelles
        result = connection.execute(sa.text(f"""
            SELECT {pk_column} FROM product_attributes.{table_name}
            WHERE {pk_column} != LOWER({pk_column})
        """))

        values_to_update = [row[0] for row in result]

        if not values_to_update:
            print(f"  ⏭️  {table_name}: already lowercase, skipping")
            continue

        print(f"  ℹ️  Found {len(values_to_update)} values to convert")

        # 2. Pour chaque valeur, créer la version lowercase et mettre à jour les références
        for old_value in values_to_update:
            new_value = old_value.lower()

            # Vérifier si la nouvelle valeur existe déjà
            result = connection.execute(sa.text(f"""
                SELECT EXISTS (
                    SELECT FROM product_attributes.{table_name}
                    WHERE {pk_column} = :new_value
                )
            """), {"new_value": new_value})

            new_exists = result.scalar()

            if new_exists and new_value != old_value:
                # Conflit : la version lowercase existe déjà
                print(f"  ⚠️  '{old_value}' → '{new_value}' (conflict: lowercase version exists)")
                # Mettre à jour les références pour pointer vers la version lowercase
                # puis supprimer l'ancienne

                # Mettre à jour template_tenant
                connection.execute(sa.text(f"""
                    UPDATE template_tenant.products
                    SET {product_column} = :new_value
                    WHERE {product_column} = :old_value
                """), {"new_value": new_value, "old_value": old_value})

                # Mettre à jour tous les user schemas
                result = connection.execute(sa.text("""
                    SELECT DISTINCT table_schema
                    FROM information_schema.tables
                    WHERE table_schema LIKE 'user_%'
                    AND table_name = 'products'
                """))
                user_schemas = [row[0] for row in result]

                for schema in user_schemas:
                    connection.execute(sa.text(f"""
                        UPDATE {schema}.products
                        SET {product_column} = :new_value
                        WHERE {product_column} = :old_value
                    """), {"new_value": new_value, "old_value": old_value})

                # Supprimer l'ancienne valeur
                connection.execute(sa.text(f"""
                    DELETE FROM product_attributes.{table_name}
                    WHERE {pk_column} = :old_value
                """), {"old_value": old_value})

                print(f"  ✓ Merged '{old_value}' into '{new_value}' and updated references")

            else:
                # Pas de conflit, on peut simplement UPDATE la PK
                # D'abord mettre à jour les références dans products

                # template_tenant
                connection.execute(sa.text(f"""
                    UPDATE template_tenant.products
                    SET {product_column} = :new_value
                    WHERE {product_column} = :old_value
                """), {"new_value": new_value, "old_value": old_value})

                # user schemas
                result = connection.execute(sa.text("""
                    SELECT DISTINCT table_schema
                    FROM information_schema.tables
                    WHERE table_schema LIKE 'user_%'
                    AND table_name = 'products'
                """))
                user_schemas = [row[0] for row in result]

                for schema in user_schemas:
                    connection.execute(sa.text(f"""
                        UPDATE {schema}.products
                        SET {product_column} = :new_value
                        WHERE {product_column} = :old_value
                    """), {"new_value": new_value, "old_value": old_value})

                # Maintenant on peut UPDATE la PK
                connection.execute(sa.text(f"""
                    UPDATE product_attributes.{table_name}
                    SET {pk_column} = :new_value
                    WHERE {pk_column} = :old_value
                """), {"new_value": new_value, "old_value": old_value})

                print(f"  ✓ '{old_value}' → '{new_value}'")

            total_updated += 1

        # Vérifier le résultat
        result = connection.execute(sa.text(f"""
            SELECT COUNT(*) FROM product_attributes.{table_name}
            WHERE {pk_column} != LOWER({pk_column})
        """))
        remaining = result.scalar()

        if remaining > 0:
            print(f"  ⚠️  Warning: {remaining} values still not lowercase in {table_name}")
        else:
            print(f"  ✅ {table_name}: all values now lowercase")

    print(f"\n  📊 Total: {total_updated} values standardized to lowercase")


def downgrade() -> None:
    """
    Note: Le downgrade n'est pas implémenté car il faudrait stocker
    la casse originale de chaque valeur, ce qui est complexe.
    Cette migration est considérée comme irréversible.
    """
    print("  ⚠️  This migration is irreversible (original case not stored)")
    pass
