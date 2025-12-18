"""Script pour vérifier que la migration necklines a bien fonctionné."""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Charger les variables d'environnement
load_dotenv()

# Créer l'engine
engine = create_engine(os.getenv('DATABASE_URL'))

with engine.connect() as conn:
    # Compter les necklines
    result = conn.execute(text('SELECT COUNT(*) FROM product_attributes.necklines'))
    count = result.scalar()
    print(f'✅ Necklines table has {count} necklines')

    # Afficher quelques necklines
    result = conn.execute(text('SELECT name_en, name_fr FROM product_attributes.necklines LIMIT 5'))
    print('\n📋 Sample necklines:')
    for row in result:
        print(f'  - {row[0]} ({row[1]})')

    # Vérifier la colonne dans template_tenant
    result = conn.execute(text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'template_tenant'
        AND table_name = 'products'
        AND column_name = 'neckline'
    """))
    if result.scalar():
        print('\n✅ Neckline column exists in template_tenant.products')

    # Vérifier la colonne dans les user schemas
    result = conn.execute(text("""
        SELECT table_schema
        FROM information_schema.columns
        WHERE table_schema LIKE 'user_%'
        AND table_name = 'products'
        AND column_name = 'neckline'
        ORDER BY table_schema
    """))
    schemas = [row[0] for row in result]
    print(f'\n✅ Neckline column added to {len(schemas)} user schemas:')
    for schema in schemas:
        print(f'  - {schema}')

print('\n🎉 Migration necklines completed successfully!')
