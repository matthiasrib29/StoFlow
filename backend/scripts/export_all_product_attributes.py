"""Script pour exporter toutes les valeurs de toutes les tables product_attributes."""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Charger les variables d'environnement
load_dotenv()

# Créer l'engine
engine = create_engine(os.getenv('DATABASE_URL'))

# Liste de toutes les tables dans product_attributes avec leur colonne principale
TABLES = {
    'brands': 'name',
    'categories': 'name_en',
    'closures': 'name_en',
    'colors': 'name_en',
    'conditions': 'name',
    'condition_sups': 'name_en',
    'decades': 'name_en',
    'fits': 'name_en',
    'genders': 'name_en',
    'lengths': 'name_en',
    'materials': 'name_en',
    'necklines': 'name_en',
    'origins': 'name_en',
    'patterns': 'name_en',
    'rises': 'name_en',
    'seasons': 'name_en',
    'sizes': 'name',
    'sleeve_lengths': 'name_en',
    'sports': 'name_en',
    'trends': 'name_en',
    'unique_features': 'name_en',
}

output = []
output.append("=" * 80)
output.append("TOUTES LES TABLES PRODUCT_ATTRIBUTES - STOFLOW")
output.append("=" * 80)
output.append(f"Date: 2025-12-11")
output.append("=" * 80)
output.append("")

total_count = 0

for table, column_name in TABLES.items():
    try:
        with engine.connect() as conn:
            # Compter les lignes
            result = conn.execute(text(f'SELECT COUNT(*) FROM product_attributes.{table}'))
            count = result.scalar()

            # Récupérer toutes les valeurs
            result = conn.execute(text(f'SELECT {column_name} FROM product_attributes.{table} ORDER BY {column_name}'))
            values = [row[0] for row in result]

            output.append(f"{table.upper()} ({count} values)")
            output.append("-" * 80)
            for value in values:
                output.append(value)
            output.append("")

            total_count += count

            print(f"✅ {table}: {count} values")

    except Exception as e:
        output.append(f"{table.upper()} - ERROR: {str(e)}")
        output.append("")
        print(f"❌ {table}: Error - {str(e)}")

output.append("=" * 80)
output.append(f"TOTAL: {total_count} values across {len(TABLES)} tables")
output.append("=" * 80)

# Écrire dans le fichier
with open('/home/maribeiro/Stoflow/Stoflow_BackEnd/ALL_PRODUCT_ATTRIBUTES.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print(f'\n🎉 Export completed! Total: {total_count} values')
print(f'📄 File: /home/maribeiro/Stoflow/Stoflow_BackEnd/ALL_PRODUCT_ATTRIBUTES.txt')
