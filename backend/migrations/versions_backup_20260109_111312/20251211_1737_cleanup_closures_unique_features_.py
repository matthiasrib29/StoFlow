"""cleanup_closures_unique_features_duplicates

Revision ID: 9i0j1k2l3m4n
Revises: 8h9i0j1k2l3m
Create Date: 2025-12-11 17:37:00.000000+01:00

Cette migration nettoie les doublons entre les tables closures et unique_features.

Business Rule (Validé 2025-12-11):
- "button fly" et "zip fly" sont des fermetures (closures), pas des caractéristiques uniques
- Ces valeurs doivent être retirées de unique_features

Actions:
- Supprime "button fly" de unique_features (existe déjà dans closures)
- Supprime "zip fly" de unique_features (existe déjà dans closures)

Author: Claude
Date: 2025-12-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9i0j1k2l3m4n'
down_revision: Union[str, None] = '8h9i0j1k2l3m'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Supprime les doublons de unique_features qui sont en fait des closures.
    """
    connection = op.get_bind()

    # Liste des valeurs à supprimer
    duplicates = ['button fly', 'zip fly']

    for duplicate in duplicates:
        # Vérifier si la valeur existe dans unique_features
        result = connection.execute(sa.text(f"""
            SELECT EXISTS (
                SELECT FROM product_attributes.unique_features
                WHERE name_en = :value
            )
        """), {"value": duplicate})

        exists = result.scalar()

        if exists:
            # Supprimer la valeur
            connection.execute(sa.text("""
                DELETE FROM product_attributes.unique_features
                WHERE name_en = :value
            """), {"value": duplicate})
            print(f"  ✓ Deleted '{duplicate}' from unique_features (already in closures)")
        else:
            print(f"  ⏭️  '{duplicate}' not found in unique_features, skipping")

    # Afficher le résumé
    result = connection.execute(sa.text("SELECT COUNT(*) FROM product_attributes.unique_features"))
    count = result.scalar()
    print(f"  ℹ️  Remaining unique_features: {count}")


def downgrade() -> None:
    """
    Restaure les valeurs supprimées (pour rollback).
    """
    connection = op.get_bind()

    # Ré-insérer les valeurs supprimées
    values_to_restore = [
        ('button fly', 'braguette à boutons'),
        ('zip fly', 'braguette à fermeture éclair'),
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
