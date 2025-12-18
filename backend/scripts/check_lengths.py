"""Script pour vérifier que la migration lengths a bien fonctionné."""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Charger les variables d'environnement
load_dotenv()

# Créer l'engine
engine = create_engine(os.getenv('DATABASE_URL'))

with engine.connect() as conn:
    # Compter les lengths
    result = conn.execute(text('SELECT COUNT(*) FROM product_attributes.lengths'))
    count = result.scalar()
    print(f'✅ Lengths table has {count} lengths')

    # Afficher quelques lengths
    result = conn.execute(text('SELECT name_en, name_fr FROM product_attributes.lengths LIMIT 5'))
    print('\n📋 Sample lengths:')
    for row in result:
        print(f'  - {row[0]} ({row[1]})')

    # Vérifier la colonne dans template_tenant
    result = conn.execute(text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'template_tenant'
        AND table_name = 'products'
        AND column_name = 'length'
    """))
    if result.scalar():
        print('\n✅ Length column exists in template_tenant.products')

    # Vérifier la colonne dans les user schemas
    result = conn.execute(text("""
        SELECT table_schema
        FROM information_schema.columns
        WHERE table_schema LIKE 'user_%'
        AND table_name = 'products'
        AND column_name = 'length'
        ORDER BY table_schema
    """))
    schemas = [row[0] for row in result]
    print(f'\n✅ Length column added to {len(schemas)} user schemas:')
    for schema in schemas:
        print(f'  - {schema}')

print('\n🎉 Migration lengths completed successfully!')
