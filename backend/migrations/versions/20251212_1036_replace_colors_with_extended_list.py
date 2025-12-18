"""replace_colors_with_extended_list

Revision ID: 5o6p7q8r9s0t
Revises: 4n5o6p7q8r9s
Create Date: 2025-12-12 10:36:00.000000+01:00

Cette migration remplace la liste des couleurs par une liste étendue et améliorée.

Business Rule (Validé 2025-12-12):
- Remplacer les 15 couleurs de base par 32 couleurs plus complètes
- Ajouter des nuances (navy, light-blue, charcoal, etc.)
- Ajouter des tons neutres (camel, cognac, tan, etc.)
- Ajouter multicolor
- Convertir en lowercase pour cohérence

Actions:
1. Supprimer toutes les anciennes couleurs
2. Insérer les 32 nouvelles couleurs

Note: Les références existantes dans products.color seront préservées,
mais pointeront vers des couleurs qui n'existent plus. À nettoyer manuellement si nécessaire.

Author: Claude
Date: 2025-12-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5o6p7q8r9s0t'
down_revision: Union[str, None] = '4n5o6p7q8r9s'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Nouvelle liste de couleurs (32 couleurs)
NEW_COLORS = [
    ('black', 'Noir'),
    ('white', 'Blanc'),
    ('cream', 'Crème'),
    ('beige', 'Beige'),
    ('camel', 'Camel'),
    ('brown', 'Marron'),
    ('cognac', 'Cognac'),
    ('tan', 'Hâle'),
    ('gold', 'Doré'),
    ('silver', 'Argenté'),
    ('yellow', 'Jaune'),
    ('mustard', 'Moutarde'),
    ('orange', 'Orange'),
    ('coral', 'Corail'),
    ('red', 'Rouge'),
    ('burgundy', 'Bordeaux'),
    ('pink', 'Rose'),
    ('fuchsia', 'Fuchsia'),
    ('purple', 'Violet'),
    ('lavender', 'Lavande'),
    ('navy', 'Bleu marine'),
    ('blue', 'Bleu'),
    ('light-blue', 'Bleu clair'),
    ('teal', 'Bleu canard'),
    ('turquoise', 'Turquoise'),
    ('green', 'Vert'),
    ('olive', 'Olive'),
    ('khaki', 'Kaki'),
    ('mint', 'Menthe'),
    ('gray', 'Gris'),
    ('charcoal', 'Gris anthracite'),
    ('multicolor', 'Multicolore'),
]


def upgrade() -> None:
    """
    Remplace les couleurs par la nouvelle liste étendue.
    """
    connection = op.get_bind()

    # 1. Sauvegarder les anciennes couleurs pour le downgrade
    result = connection.execute(sa.text("""
        SELECT name_en, name_fr FROM product_attributes.colors
        ORDER BY name_en
    """))
    old_colors = list(result)
    print(f"  ℹ️  Backing up {len(old_colors)} old colors")

    # 2. Supprimer toutes les anciennes couleurs
    connection.execute(sa.text("""
        DELETE FROM product_attributes.colors
    """))
    print(f"  ✓ Deleted {len(old_colors)} old colors")

    # 3. Insérer les nouvelles couleurs
    for name_en, name_fr in NEW_COLORS:
        connection.execute(sa.text("""
            INSERT INTO product_attributes.colors (name_en, name_fr)
            VALUES (:name_en, :name_fr)
        """), {"name_en": name_en, "name_fr": name_fr})

    print(f"  ✓ Inserted {len(NEW_COLORS)} new colors")

    # 4. Vérifier le résultat
    result = connection.execute(sa.text("SELECT COUNT(*) FROM product_attributes.colors"))
    count = result.scalar()
    print(f"  ✅ Colors updated: {len(old_colors)} → {count}")


def downgrade() -> None:
    """
    Restaure les anciennes couleurs.
    """
    connection = op.get_bind()

    # Anciennes couleurs à restaurer (15 couleurs)
    OLD_COLORS = [
        ('beige', 'beige'),
        ('black', 'noir'),
        ('blue', 'bleu'),
        ('brown', 'marron'),
        ('burgundy', 'bordeaux'),
        ('cream', 'crème'),
        ('gray', 'gris'),
        ('green', 'vert'),
        ('khaki', 'kaki'),
        ('orange', 'orange'),
        ('pink', 'rose'),
        ('purple', 'violet'),
        ('red', 'rouge'),
        ('white', 'blanc'),
        ('yellow', 'jaune'),
    ]

    # Supprimer les nouvelles couleurs
    connection.execute(sa.text("DELETE FROM product_attributes.colors"))
    print(f"  ✓ Deleted new colors")

    # Restaurer les anciennes couleurs
    for name_en, name_fr in OLD_COLORS:
        connection.execute(sa.text("""
            INSERT INTO product_attributes.colors (name_en, name_fr)
            VALUES (:name_en, :name_fr)
        """), {"name_en": name_en, "name_fr": name_fr})

    print(f"  ✓ Restored {len(OLD_COLORS)} old colors")
