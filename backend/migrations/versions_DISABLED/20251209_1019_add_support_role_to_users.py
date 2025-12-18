"""add_support_role_to_users

Revision ID: 08484e0176eb
Revises: c3d4e5f6g7h8
Create Date: 2025-12-09 10:19:13.690711+01:00

Business Rules (2025-12-09):
- Ajoute le rôle 'support' à l'enum user_role
- Les utilisateurs existants conservent leur rôle actuel (admin ou user)
- Le rôle support permet:
  * Voir tous les utilisateurs (lecture seule)
  * Voir toutes les intégrations (lecture seule)
  * Réinitialiser les mots de passe
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '08484e0176eb'
down_revision: Union[str, None] = 'c3d4e5f6g7h8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Ajoute la valeur 'support' à l'enum user_role.
    """
    # Ajouter 'support' à l'enum user_role
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'support'")


def downgrade() -> None:
    """
    Note: La suppression d'une valeur d'enum n'est pas supportée par PostgreSQL.
    Il faudrait recréer l'enum et migrer les données, ce qui est complexe.

    Pour rollback:
    1. S'assurer qu'aucun utilisateur n'a le rôle 'support'
    2. Recréer l'enum sans 'support'
    3. Restaurer les données
    """
    # Pour éviter les erreurs, on vérifie d'abord qu'aucun user n'a le rôle support
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM public.users WHERE role = 'support') THEN
                RAISE EXCEPTION 'Cannot downgrade: users with role support exist';
            END IF;
        END $$;
    """)

    # Note: Suppression effective d'une valeur enum nécessiterait de recréer l'enum
    # Ce qui est complexe et risqué. On laisse la valeur 'support' dans l'enum.
