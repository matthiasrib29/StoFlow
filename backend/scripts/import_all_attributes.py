#!/usr/bin/env python3
"""
Import All Attribute Data from pythonApiWOO

Script pour extraire toutes les données des tables d'attributs de pythonApiWOO
et les importer dans notre base de données Stoflow.

Tables à importer:
- condition_sups
- closures
- decades
- origins
- rises
- sleeve_lengths
- trends
- unique_features

Usage:
    python scripts/import_all_attributes.py
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


def import_table(source_session, dest_session, source_table: str, dest_table: str):
    """
    Importer les données d'une table depuis pythonApiWOO vers Stoflow.

    Args:
        source_session: Session PostgreSQL source (pythonApiWOO)
        dest_session: Session PostgreSQL destination (Stoflow)
        source_table: Nom de la table source dans schema "attribut"
        dest_table: Nom de la table destination dans schema "public"
    """
    print(f"\n📦 Importing: {source_table} → {dest_table}")

    # Extraire les données de la source (pythonApiWOO)
    # Les tables sont dans le schema "attribut" de pythonApiWOO
    # Sélectionner uniquement les colonnes de traduction standard
    translation_columns = ['name_en', 'name_fr', 'name_de', 'name_it', 'name_es', 'name_nl', 'name_pl']
    columns_str = ', '.join(translation_columns)
    query = text(f"SELECT {columns_str} FROM attribut.{source_table}")
    result = source_session.execute(query)
    rows = [dict(row._mapping) for row in result]

    if not rows:
        print(f"  ⚠️  No data found in attribut.{source_table}")
        return 0

    # Préparer la requête d'insertion PostgreSQL
    placeholders = ", ".join([f":{col}" for col in translation_columns])
    insert_query = f"""
        INSERT INTO public.{dest_table} ({columns_str})
        VALUES ({placeholders})
        ON CONFLICT (name_en) DO UPDATE SET
            {', '.join([f'{col} = EXCLUDED.{col}' for col in translation_columns if col != 'name_en'])}
    """

    # Insérer les données dans PostgreSQL
    inserted = 0
    for row in rows:
        try:
            dest_session.execute(text(insert_query), row)
            inserted += 1
        except Exception as e:
            print(f"  ❌ Error inserting row: {row.get('name_en', 'unknown')}")
            print(f"     Error: {e}")

    dest_session.commit()
    print(f"  ✅ Imported {inserted}/{len(rows)} rows")
    return inserted


def main():
    """Fonction principale."""
    print("=" * 60)
    print("🚀 STARTING ATTRIBUTE DATA IMPORT")
    print("=" * 60)

    # Tables à importer: (source_name, dest_name)
    # source_name = nom dans schema "attribut" de pythonApiWOO
    # dest_name = nom dans schema "public" de Stoflow
    table_mappings = [
        ("condition_sup", "condition_sups"),
        ("closure", "closures"),
        ("decade", "decades"),
        ("origin", "origins"),
        ("rise", "rises"),
        ("sleeve_length", "sleeve_lengths"),
        ("trend", "trends"),
        ("unique_feature", "unique_features"),
    ]

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
