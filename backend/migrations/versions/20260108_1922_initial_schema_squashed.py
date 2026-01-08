"""initial_schema_squashed

Squashed migration combining 81 previous migrations into a single base.

Revision ID: 9e1b5d86d3ec
Revises: None
Create Date: 2026-01-08 19:22:57.930609+01:00

Business Context:
- Squashed 81 migrations (from project inception to 2026-01-08)
- Includes all product_attributes tables with multilingual support (EN, FR, DE, IT, ES, NL, PL)
- Multi-tenant architecture with user schemas
- Marketplace integrations (Vinted, eBay, Etsy)

For new installations:
- Run the SQL schema file: backend/migrations/squashed_schema.sql
- Then mark this migration as applied

For existing installations:
- This migration is automatically marked as applied during squash
- Schema already exists, no changes needed

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9e1b5d86d3ec'
down_revision: Union[str, None] = None  # This is now the base migration
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    For new installations, apply the squashed schema manually:
    psql -U stoflow_user -d stoflow_db -f migrations/squashed_schema.sql

    Then mark this migration as applied:
    alembic stamp head
    """
    # Empty - schema must be applied via squashed_schema.sql for new installations
    # For existing installations, this is a no-op (already has the schema)
    pass


def downgrade() -> None:
    """Cannot downgrade from initial squashed migration."""
    raise NotImplementedError("Cannot downgrade from squashed base migration")
