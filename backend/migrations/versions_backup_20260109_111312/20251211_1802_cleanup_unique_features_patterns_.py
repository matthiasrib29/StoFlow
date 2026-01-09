"""cleanup_unique_features_patterns_duplicates

Revision ID: 4n5o6p7q8r9s
Revises: 3m4n5o6p7q8r
Create Date: 2025-12-11 18:02:00.000000+01:00

Cette migration nettoie les doublons et valeurs inutiles dans unique_features.

Business Rule (Validé 2025-12-11):
- "color block", "ombre", "tie-dye" sont des patterns, pas des unique features
- "none" est une valeur inutile (si pas de feature, on ne met rien)

Actions:
- Supprimer "color block" de unique_features (existe dans patterns)
- Supprimer "ombre" de unique_features (existe dans patterns)
- Supprimer "tie-dye" de unique_features (existe dans patterns)
- Supprimer "none" de unique_features (valeur inutile)

Author: Claude
Date: 2025-12-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4n5o6p7q8r9s'
down_revision: Union[str, None] = '3m4n5o6p7q8r'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Supprime les doublons de patterns et la valeur "none" de unique_features.
    """
    connection = op.get_bind()

    # Valeurs à supprimer avec leur raison
    values_to_delete = [
        ('color block', 'doublon de patterns'),
        ('ombre', 'doublon de patterns'),
        ('tie-dye', 'doublon de patterns'),
        ('none', 'valeur inutile'),
    ]

    deleted_count = 0

    for value, reason in values_to_delete:
        # Vérifier si la valeur existe
        result = connection.execute(sa.text("""
            SELECT EXISTS (
                SELECT FROM product_attributes.unique_features
                WHERE name_en = :value
            )
        """), {"value": value})

        exists = result.scalar()

        if exists:
            # Supprimer la valeur
            connection.execute(sa.text("""
                DELETE FROM product_attributes.unique_features
                WHERE name_en = :value
            """), {"value": value})
            print(f"  ✓ Deleted '{value}' from unique_features ({reason})")
            deleted_count += 1
        else:
            print(f"  ⏭️  '{value}' not found in unique_features, skipping")

    # Afficher le résumé
    result = connection.execute(sa.text("SELECT COUNT(*) FROM product_attributes.unique_features"))
    count = result.scalar()
    print(f"  ℹ️  Remaining unique_features: {count} (deleted {deleted_count} duplicates/useless)")


def downgrade() -> None:
    """
    Restaure les valeurs supprimées (pour rollback).
    """
    connection = op.get_bind()

    # Ré-insérer les valeurs supprimées
    values_to_restore = [
        ('color block', 'bloc de couleur'),
        ('ombre', 'ombré'),
        ('tie-dye', 'tie-dye'),
        ('none', 'aucune'),
    ]

    for name_en, name_fr in values_to_restore:
        # Vérifier si la valeur existe déjà
        result = connection.execute(sa.text("""
            SELECT EXISTS (
                SELECT FROM product_attributes.unique_features
                WHERE name_en = :value
            )
        """), {"value": name_en})

        exists = result.scalar()

        if not exists:
            # Ré-insérer la valeur
            connection.execute(sa.text("""
                INSERT INTO product_attributes.unique_features (name_en, name_fr)
                VALUES (:name_en, :name_fr)
            """), {"name_en": name_en, "name_fr": name_fr})
            print(f"  ✓ Restored '{name_en}' to unique_features")
        else:
            print(f"  ⏭️  '{name_en}' already exists in unique_features, skipping")
