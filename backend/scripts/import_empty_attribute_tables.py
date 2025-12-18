#!/usr/bin/env python3
"""
Import Empty Attribute Tables from pythonApiWOO

Script pour importer les données des tables d'attributs vides depuis pythonApiWOO.

Tables à importer:
- brands
- colors
- conditions
- fits
- genders
- materials
- seasons
- sizes

Usage:
    python scripts/import_empty_attribute_tables.py
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()


# ===== CONFIGURATION POSTGRESQL SOURCE (pythonApiWOO) =====
SOURCE_PG_URL = "postgresql://appuser:apppass@127.0.0.1:5432/appdb"

# ===== CONFIGURATION POSTGRESQL DESTINATION (Stoflow) =====
DEST_PG_URL = os.getenv("DATABASE_URL")


def get_source_session():
    """Créer une session PostgreSQL pour pythonApiWOO (source)."""
    engine = create_engine(SOURCE_PG_URL)
    Session = sessionmaker(bind=engine)
    return Session()


def get_dest_session():
    """Créer une session PostgreSQL pour Stoflow (destination)."""
    engine = create_engine(DEST_PG_URL)
    Session = sessionmaker(bind=engine)
    return Session()


def import_table(source_session, dest_session, source_table: str, dest_table: str = None):
    """
    Importer les données d'une table depuis pythonApiWOO vers Stoflow.

    Args:
        source_session: Session PostgreSQL source (pythonApiWOO)
        dest_session: Session PostgreSQL destination (Stoflow)
        source_table: Nom de la table source dans schema "attribut"
        dest_table: Nom de la table destination (si différent de source_table)
    """
    if dest_table is None:
        dest_table = source_table

    print(f"\n📦 Importing: {source_table} → {dest_table}")

    # Extraire les données de la source (pythonApiWOO)
    query = text(f"SELECT * FROM attribut.{source_table}")
    result = source_session.execute(query)
    rows = [dict(row._mapping) for row in result]

    if not rows:
        print(f"  ⚠️  No data found in attribut.{source_table}")
        return 0

    # Déterminer les colonnes disponibles
    columns = list(rows[0].keys())

    # Définir quelles colonnes importer selon la table
    if source_table == 'brand':
        # Pour brands: importer toutes les colonnes pertinentes
        columns_to_import = [col for col in columns if col in ['name', 'vinted_id', 'description', 'monitoring', 'sector_jeans', 'sector_jacket']]
    elif 'name_en' in columns:
        # Pour les tables multilingues: garder uniquement les traductions
        translation_columns = ['name_en', 'name_fr', 'name_de', 'name_it', 'name_es', 'name_nl', 'name_pl']
        columns_to_import = [col for col in translation_columns if col in columns]
    else:
        # Pour les autres tables: garder toutes les colonnes
        columns_to_import = columns

    print(f"  📋 Columns to import: {', '.join(columns_to_import)}")

    # Préparer la requête d'insertion PostgreSQL
    columns_str = ', '.join(columns_to_import)
    placeholders = ", ".join([f":{col}" for col in columns_to_import])

    # Déterminer la clé primaire selon la table
    if source_table == 'brand':
        pk_column = 'name'
    elif 'name_en' in columns_to_import:
        pk_column = 'name_en'
    else:
        pk_column = columns_to_import[0]

    update_cols = [col for col in columns_to_import if col != pk_column]

    insert_query = f"""
        INSERT INTO product_attributes.{dest_table} ({columns_str})
        VALUES ({placeholders})
        ON CONFLICT ({pk_column}) DO UPDATE SET
            {', '.join([f'{col} = EXCLUDED.{col}' for col in update_cols]) if update_cols else 'name_en = EXCLUDED.name_en'}
    """

    # Insérer les données dans PostgreSQL
    inserted = 0
    for row in rows:
        try:
            # Filtrer les données pour ne garder que les colonnes à importer
            filtered_row = {k: v for k, v in row.items() if k in columns_to_import}
            dest_session.execute(text(insert_query), filtered_row)
            inserted += 1
        except Exception as e:
            print(f"  ❌ Error inserting row: {row.get(pk_column, 'unknown')}")
            print(f"     Error: {e}")

    dest_session.commit()
    print(f"  ✅ Imported {inserted}/{len(rows)} rows")
    return inserted


def main():
    """Fonction principale."""
    print("=" * 60)
    print("🚀 STARTING EMPTY ATTRIBUTE TABLES IMPORT")
    print("=" * 60)

    # Tables à importer (toutes ont le même nom source et destination)
    tables = [
        "brand",      # → brands (au pluriel en destination)
        "color",      # → colors
        "condition",  # → conditions
        "fit",        # → fits
        "gender",     # → genders
        "material",   # → materials
        "season",     # → seasons
        "size",       # → sizes
    ]

    # Mapping source → destination (ajouter 's' au pluriel)
    table_mappings = [(table, table + "s") for table in tables]

    # Connexions
    source_session = None
    dest_session = None
    total_imported = 0

    try:
        # Créer les connexions
        print("\n🔌 Connecting to databases...")
        source_session = get_source_session()
        dest_session = get_dest_session()
        print("  ✅ Connected to PostgreSQL source (pythonApiWOO)")
        print("  ✅ Connected to PostgreSQL destination (Stoflow)")

        # Importer chaque table
        for source_table, dest_table in table_mappings:
            imported = import_table(source_session, dest_session, source_table, dest_table)
            total_imported += imported

        print("\n" + "=" * 60)
        print(f"✅ IMPORT COMPLETED: {total_imported} total rows imported")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        if dest_session:
            dest_session.rollback()
        sys.exit(1)

    finally:
        # Fermer les connexions
        if source_session:
            source_session.close()
        if dest_session:
            dest_session.close()


if __name__ == "__main__":
    main()
