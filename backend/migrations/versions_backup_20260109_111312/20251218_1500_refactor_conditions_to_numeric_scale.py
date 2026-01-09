"""Refactor conditions table to use numeric scale 0-10

Changes:
- Replace string-based conditions (name) with numeric scale (note 0-10)
- Add multilingual name columns (name_en, name_fr, etc.)
- Update user_1.products.condition from varchar to integer
- Map old values: a->9, b->7, c->5, d->1

Revision ID: 20251218_1500
Revises: 20251218_1400
Create Date: 2025-12-18
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '20251218_1500'
down_revision = '20251218_1400'
branch_labels = None
depends_on = None


# Condition data (note 0-10)
CONDITIONS_DATA = [
    {
        'note': 10,
        'name_en': 'New',
        'name_fr': 'Neuf',
        'name_de': 'Neu',
        'name_it': 'Nuovo',
        'name_es': 'Nuevo',
        'name_nl': 'Nieuw',
        'name_pl': 'Nowy',
        'vinted_id': 6,
        'ebay_condition': 'NEW',
        'coefficient': 1.0
    },
    {
        'note': 9,
        'name_en': 'Like new',
        'name_fr': 'Comme neuf',
        'name_de': 'Wie neu',
        'name_it': 'Come nuovo',
        'name_es': 'Como nuevo',
        'name_nl': 'Als nieuw',
        'name_pl': 'Jak nowy',
        'vinted_id': 1,
        'ebay_condition': 'PRE_OWNED_EXCELLENT',
        'coefficient': 0.95
    },
    {
        'note': 8,
        'name_en': 'Excellent',
        'name_fr': 'Excellent état',
        'name_de': 'Ausgezeichnet',
        'name_it': 'Eccellente',
        'name_es': 'Excelente',
        'name_nl': 'Uitstekend',
        'name_pl': 'Doskonały',
        'vinted_id': 2,
        'ebay_condition': 'PRE_OWNED_EXCELLENT',
        'coefficient': 0.90
    },
    {
        'note': 7,
        'name_en': 'Very good',
        'name_fr': 'Très bon état',
        'name_de': 'Sehr gut',
        'name_it': 'Molto buono',
        'name_es': 'Muy bueno',
        'name_nl': 'Zeer goed',
        'name_pl': 'Bardzo dobry',
        'vinted_id': 2,
        'ebay_condition': 'PRE_OWNED_GOOD',
        'coefficient': 0.85
    },
    {
        'note': 6,
        'name_en': 'Good',
        'name_fr': 'Bon état',
        'name_de': 'Gut',
        'name_it': 'Buono',
        'name_es': 'Bueno',
        'name_nl': 'Goed',
        'name_pl': 'Dobry',
        'vinted_id': 3,
        'ebay_condition': 'PRE_OWNED_GOOD',
        'coefficient': 0.80
    },
    {
        'note': 5,
        'name_en': 'Shows wear',
        'name_fr': 'Traces d\'usure visibles',
        'name_de': 'Gebrauchsspuren',
        'name_it': 'Segni di usura',
        'name_es': 'Señales de uso',
        'name_nl': 'Gebruikssporen',
        'name_pl': 'Ślady użytkowania',
        'vinted_id': 3,
        'ebay_condition': 'PRE_OWNED_FAIR',
        'coefficient': 0.70
    },
    {
        'note': 4,
        'name_en': 'Acceptable',
        'name_fr': 'État acceptable',
        'name_de': 'Akzeptabel',
        'name_it': 'Accettabile',
        'name_es': 'Aceptable',
        'name_nl': 'Acceptabel',
        'name_pl': 'Akceptowalny',
        'vinted_id': 4,
        'ebay_condition': 'PRE_OWNED_FAIR',
        'coefficient': 0.60
    },
    {
        'note': 3,
        'name_en': 'Poor',
        'name_fr': 'Mauvais état',
        'name_de': 'Schlecht',
        'name_it': 'Scarso',
        'name_es': 'Malo',
        'name_nl': 'Slecht',
        'name_pl': 'Zły',
        'vinted_id': 4,
        'ebay_condition': 'PRE_OWNED_POOR',
        'coefficient': 0.50
    },
    {
        'note': 2,
        'name_en': 'Very poor',
        'name_fr': 'Très mauvais état',
        'name_de': 'Sehr schlecht',
        'name_it': 'Molto scarso',
        'name_es': 'Muy malo',
        'name_nl': 'Zeer slecht',
        'name_pl': 'Bardzo zły',
        'vinted_id': 4,
        'ebay_condition': 'PRE_OWNED_POOR',
        'coefficient': 0.40
    },
    {
        'note': 1,
        'name_en': 'For parts only',
        'name_fr': 'Pour pièces uniquement',
        'name_de': 'Nur für Teile',
        'name_it': 'Solo per parti',
        'name_es': 'Solo para piezas',
        'name_nl': 'Alleen voor onderdelen',
        'name_pl': 'Tylko na części',
        'vinted_id': 4,
        'ebay_condition': 'FOR_PARTS_OR_NOT_WORKING',
        'coefficient': 0.30
    },
    {
        'note': 0,
        'name_en': 'Major defects',
        'name_fr': 'Défauts majeurs',
        'name_de': 'Große Mängel',
        'name_it': 'Difetti maggiori',
        'name_es': 'Defectos mayores',
        'name_nl': 'Grote gebreken',
        'name_pl': 'Poważne wady',
        'vinted_id': 4,
        'ebay_condition': 'FOR_PARTS_OR_NOT_WORKING',
        'coefficient': 0.20
    },
]

# Mapping old values to new notes
OLD_TO_NEW_MAPPING = {
    'a': 9,
    'b': 7,
    'c': 5,
    'd': 1,
    'excellent': 8,
    'good': 6,
    'fair': 5,
    'poor': 3,
}


def upgrade():
    conn = op.get_bind()

    # Check if migration was already applied (conditions table has 'note' column)
    already_migrated = conn.execute(sa.text('''
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'product_attributes'
            AND table_name = 'conditions'
            AND column_name = 'note'
        )
    ''')).scalar()

    if already_migrated:
        print("  ⏭️  Conditions table already migrated to numeric scale, skipping")
        return

    # Step 1: Create new conditions table with note as PK
    op.execute('''
        CREATE TABLE product_attributes.conditions_new (
            note INTEGER PRIMARY KEY CHECK (note >= 0 AND note <= 10),
            name_en VARCHAR(100) NOT NULL,
            name_fr VARCHAR(100) NOT NULL,
            name_de VARCHAR(100),
            name_it VARCHAR(100),
            name_es VARCHAR(100),
            name_nl VARCHAR(100),
            name_pl VARCHAR(100),
            vinted_id BIGINT,
            ebay_condition TEXT,
            coefficient NUMERIC(4,3) DEFAULT 1.000
        )
    ''')

    # Step 2: Insert new condition data
    for cond in CONDITIONS_DATA:
        conn.execute(
            sa.text('''
                INSERT INTO product_attributes.conditions_new
                (note, name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl, vinted_id, ebay_condition, coefficient)
                VALUES (:note, :name_en, :name_fr, :name_de, :name_it, :name_es, :name_nl, :name_pl, :vinted_id, :ebay_condition, :coefficient)
            '''),
            cond
        )

    # Step 3: Get all user schemas
    result = conn.execute(sa.text('''
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%' AND schema_name != 'user_invalid'
    '''))
    user_schemas = [row[0] for row in result]

    # Step 4: Update products.condition in each user schema
    for schema in user_schemas:
        # Check if products table exists in this schema
        table_exists = conn.execute(sa.text(f'''
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = '{schema}' AND table_name = 'products'
            )
        ''')).scalar()

        if not table_exists:
            continue

        # Add temporary column for new condition
        conn.execute(sa.text(f'ALTER TABLE {schema}.products ADD COLUMN condition_new INTEGER'))

        # Map old string values to new integer values
        for old_val, new_val in OLD_TO_NEW_MAPPING.items():
            conn.execute(sa.text(f'''
                UPDATE {schema}.products
                SET condition_new = {new_val}
                WHERE LOWER(condition) = '{old_val}'
            '''))

        # Set default for unmapped values (default to 5 - shows wear)
        conn.execute(sa.text(f'''
            UPDATE {schema}.products
            SET condition_new = 5
            WHERE condition IS NOT NULL AND condition_new IS NULL
        '''))

        # Drop old column and rename new one
        conn.execute(sa.text(f'ALTER TABLE {schema}.products DROP COLUMN condition'))
        conn.execute(sa.text(f'ALTER TABLE {schema}.products RENAME COLUMN condition_new TO condition'))

    # Step 5: Drop old conditions table and rename new one
    op.execute('DROP TABLE product_attributes.conditions')
    op.execute('ALTER TABLE product_attributes.conditions_new RENAME TO conditions')

    # Step 6: Update template_tenant if exists
    template_exists = conn.execute(sa.text('''
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'template_tenant' AND table_name = 'products'
        )
    ''')).scalar()

    if template_exists:
        # Check if condition column exists and its type
        col_info = conn.execute(sa.text('''
            SELECT data_type FROM information_schema.columns
            WHERE table_schema = 'template_tenant' AND table_name = 'products' AND column_name = 'condition'
        ''')).fetchone()

        if col_info and 'character' in col_info[0]:
            conn.execute(sa.text('ALTER TABLE template_tenant.products ADD COLUMN condition_new INTEGER'))
            for old_val, new_val in OLD_TO_NEW_MAPPING.items():
                conn.execute(sa.text(f'''
                    UPDATE template_tenant.products
                    SET condition_new = {new_val}
                    WHERE LOWER(condition) = '{old_val}'
                '''))
            conn.execute(sa.text('ALTER TABLE template_tenant.products DROP COLUMN condition'))
            conn.execute(sa.text('ALTER TABLE template_tenant.products RENAME COLUMN condition_new TO condition'))


def downgrade():
    conn = op.get_bind()

    # Step 1: Recreate old conditions table
    op.execute('''
        CREATE TABLE product_attributes.conditions_old (
            name VARCHAR(100) PRIMARY KEY,
            description_fr VARCHAR(255),
            description_en VARCHAR(255),
            vinted_id BIGINT,
            ebay_condition TEXT,
            coefficient NUMERIC(4,3),
            description_de VARCHAR(255),
            description_it VARCHAR(255),
            description_es VARCHAR(255),
            description_nl VARCHAR(255),
            description_pl VARCHAR(255)
        )
    ''')

    # Step 2: Insert old data
    conn.execute(sa.text('''
        INSERT INTO product_attributes.conditions_old VALUES
        ('excellent', 'Très bon état', 'Excellent', 2, 'PRE_OWNED_EXCELLENT', 1.000, 'Ausgezeichnet', 'Eccellente', 'Excelente', 'Uitstekend', 'Doskonały'),
        ('good', 'Bon état', 'Good', 3, 'PRE_OWNED_GOOD', 0.850, 'Gut', 'Buono', 'Bueno', 'Goed', 'Dobry'),
        ('fair', 'État usé', 'Fair', 4, 'PRE_OWNED_FAIR', 0.600, 'Akzeptabel', 'Discreto', 'Aceptable', 'Redelijk', 'Zadowalający'),
        ('poor', 'État très usé', 'Poor', 4, 'PRE_OWNED_POOR', 0.500, 'Schlecht', 'Scarso', 'Malo', 'Slecht', 'Zły')
    '''))

    # Step 3: Reverse mapping for user schemas
    new_to_old = {9: 'a', 7: 'b', 5: 'c', 1: 'd'}

    result = conn.execute(sa.text('''
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%' AND schema_name != 'user_invalid'
    '''))
    user_schemas = [row[0] for row in result]

    for schema in user_schemas:
        table_exists = conn.execute(sa.text(f'''
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = '{schema}' AND table_name = 'products'
            )
        ''')).scalar()

        if not table_exists:
            continue

        conn.execute(sa.text(f'ALTER TABLE {schema}.products ADD COLUMN condition_old VARCHAR(100)'))

        for new_val, old_val in new_to_old.items():
            conn.execute(sa.text(f'''
                UPDATE {schema}.products
                SET condition_old = '{old_val}'
                WHERE condition = {new_val}
            '''))

        conn.execute(sa.text(f'ALTER TABLE {schema}.products DROP COLUMN condition'))
        conn.execute(sa.text(f'ALTER TABLE {schema}.products RENAME COLUMN condition_old TO condition'))

    # Step 4: Drop new and rename old
    op.execute('DROP TABLE product_attributes.conditions')
    op.execute('ALTER TABLE product_attributes.conditions_old RENAME TO conditions')
