"""remove_button_fly_from_unique_features

Revision ID: 5533a6a37c28
Revises: 16637868e60c
Create Date: 2026-01-13 13:13:12.216636+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5533a6a37c28'
down_revision: Union[str, None] = '16637868e60c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DELETE FROM product_attributes.unique_features
        WHERE name_en = 'Button fly'
    """)


def downgrade() -> None:
    op.execute("""
        INSERT INTO product_attributes.unique_features (name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl)
        VALUES ('Button fly', 'Braguette à boutons', 'Knopfleiste', 'Abbottonatura', 'Bragueta de botones', 'Knoopsluiting', 'Rozporek na guziki')
        ON CONFLICT (name_en) DO NOTHING
    """)
