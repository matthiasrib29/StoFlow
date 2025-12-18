"""add_plugin_queue_system

Revision ID: f1g2h3i4j5k6
Revises: 062469969708
Create Date: 2025-12-10 14:00:00.000000+01:00

Ajoute le système de queue pour les plugins avec génération step-by-step:
- Table plugin_queue (nouvelle)
- Nouvelles colonnes dans plugin_tasks (queue_id, platform, http_method, path)

Business Logic:
- plugin_queue = blueprint de l'opération complète (publish_product, etc.)
- plugin_tasks = task courante générée dynamiquement step by step
- accumulated_data stocke les résultats intermédiaires (photo_ids, etc.)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f1g2h3i4j5k6'
down_revision: Union[str, None] = '062469969708'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ===== CRÉER TABLE plugin_queue dans template_tenant =====
    # Utiliser CREATE TABLE IF NOT EXISTS (plus simple que DO block)
    op.execute("""
        CREATE TABLE IF NOT EXISTS template_tenant.plugin_queue (
            id SERIAL PRIMARY KEY,
            platform VARCHAR(50) NOT NULL,
            operation VARCHAR(100) NOT NULL,
            product_id INTEGER,
            status VARCHAR(20) NOT NULL DEFAULT 'queued',
            current_step VARCHAR(100),
            accumulated_data JSONB DEFAULT '{}',
            context_data JSONB DEFAULT '{}',
            error_message TEXT,
            retry_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)

    # Indexes (CREATE IF NOT EXISTS)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_template_tenant_plugin_queue_platform
        ON template_tenant.plugin_queue(platform)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_template_tenant_plugin_queue_status
        ON template_tenant.plugin_queue(status)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_template_tenant_plugin_queue_product_id
        ON template_tenant.plugin_queue(product_id)
    """)

    # Foreign key (avec DO block car pas de IF NOT EXISTS pour constraints)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE table_schema = 'template_tenant'
                AND table_name = 'plugin_queue'
                AND constraint_name = 'fk_plugin_queue_product'
            ) THEN
                ALTER TABLE template_tenant.plugin_queue
                ADD CONSTRAINT fk_plugin_queue_product
                FOREIGN KEY (product_id) REFERENCES template_tenant.products(id) ON DELETE CASCADE;
            END IF;
        END $$;
    """)

    # ===== AJOUTER COLONNES DANS plugin_tasks =====

    # Colonne queue_id
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'template_tenant'
                AND table_name = 'plugin_tasks'
                AND column_name = 'queue_id'
            ) THEN
                ALTER TABLE template_tenant.plugin_tasks
                ADD COLUMN queue_id INTEGER;

                -- Index
                CREATE INDEX ix_template_tenant_plugin_tasks_queue_id
                ON template_tenant.plugin_tasks(queue_id);

                -- Foreign key
                ALTER TABLE template_tenant.plugin_tasks
                ADD CONSTRAINT fk_plugin_tasks_queue
                FOREIGN KEY (queue_id) REFERENCES template_tenant.plugin_queue(id) ON DELETE CASCADE;
            END IF;
        END $$;
    """)

    # Colonne platform
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'template_tenant'
                AND table_name = 'plugin_tasks'
                AND column_name = 'platform'
            ) THEN
                ALTER TABLE template_tenant.plugin_tasks
                ADD COLUMN platform VARCHAR(50);

                -- Index
                CREATE INDEX ix_template_tenant_plugin_tasks_platform
                ON template_tenant.plugin_tasks(platform);
            END IF;
        END $$;
    """)

    # Colonne http_method
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'template_tenant'
                AND table_name = 'plugin_tasks'
                AND column_name = 'http_method'
            ) THEN
                ALTER TABLE template_tenant.plugin_tasks
                ADD COLUMN http_method VARCHAR(10);
            END IF;
        END $$;
    """)

    # Colonne path
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'template_tenant'
                AND table_name = 'plugin_tasks'
                AND column_name = 'path'
            ) THEN
                ALTER TABLE template_tenant.plugin_tasks
                ADD COLUMN path VARCHAR(500);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    # Supprimer les colonnes ajoutées dans plugin_tasks
    op.execute("""
        DO $$
        BEGIN
            -- Supprimer FK queue_id
            IF EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE table_schema = 'template_tenant'
                AND table_name = 'plugin_tasks'
                AND constraint_name = 'fk_plugin_tasks_queue'
            ) THEN
                ALTER TABLE template_tenant.plugin_tasks
                DROP CONSTRAINT fk_plugin_tasks_queue;
            END IF;

            -- Supprimer colonnes
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'template_tenant'
                AND table_name = 'plugin_tasks'
                AND column_name = 'path'
            ) THEN
                ALTER TABLE template_tenant.plugin_tasks DROP COLUMN path;
            END IF;

            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'template_tenant'
                AND table_name = 'plugin_tasks'
                AND column_name = 'http_method'
            ) THEN
                ALTER TABLE template_tenant.plugin_tasks DROP COLUMN http_method;
            END IF;

            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'template_tenant'
                AND table_name = 'plugin_tasks'
                AND column_name = 'platform'
            ) THEN
                ALTER TABLE template_tenant.plugin_tasks DROP COLUMN platform;
            END IF;

            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'template_tenant'
                AND table_name = 'plugin_tasks'
                AND column_name = 'queue_id'
            ) THEN
                ALTER TABLE template_tenant.plugin_tasks DROP COLUMN queue_id;
            END IF;
        END $$;
    """)

    # Supprimer la table plugin_queue
    op.execute("DROP TABLE IF EXISTS template_tenant.plugin_queue CASCADE")
