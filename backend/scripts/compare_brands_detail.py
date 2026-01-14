"""
Script pour comparer les marques côte à côte entre pythonApiWOO et StoFlow.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

# Database URLs
SOURCE_DB_URL = "postgresql://appuser:apppass@127.0.0.1:5432/appdb"
TARGET_DB_URL = os.getenv('DATABASE_URL', 'postgresql://stoflow:stoflow_password@localhost:5432/stoflow')


def compare_brands_for_lost_products(source_engine, target_engine):
    """Compare les marques pour les 21 produits identifiés."""
    print("=" * 100)
    print("COMPARAISON DES MARQUES: pythonApiWOO vs StoFlow")
    print("=" * 100)

    # Les 21 SKUs identifiés
    lost_skus = [
        266, 330, 676, 744, 751, 840, 850, 894, 909, 915,
        1075, 1116, 1140, 1148, 1382, 1422, 1423, 1985, 2465, 2554, 2759
    ]

    with source_engine.connect() as source_conn, target_engine.connect() as target_conn:
        target_conn.execute(text("SET search_path TO user_1, public"))

        print(f"\n🔍 Comparaison pour {len(lost_skus)} produits\n")
        print("=" * 100)
        print(f"{'SKU':<6} | {'pythonApiWOO':<20} | {'StoFlow':<20} | {'Changement'}")
        print("=" * 100)

        for sku in sorted(lost_skus):
            # Get brand from source
            source_row = source_conn.execute(text("""
                SELECT brand FROM product.products WHERE sku = :sku
            """), {"sku": sku}).fetchone()

            # Get brand from target
            target_row = target_conn.execute(text("""
                SELECT brand FROM products WHERE id = :id
            """), {"id": sku}).fetchone()

            source_brand = source_row.brand if source_row else "(not found)"
            target_brand = target_row.brand if target_row and target_row.brand else "(NULL)"

            # Determine change type
            if source_brand == "(not found)":
                change = "⚠️  Produit manquant"
            elif target_brand == "(NULL)":
                change = "❌ PERDU"
            elif source_brand.lower() != target_brand.lower():
                change = f"🔄 Changé"
            else:
                change = "✅ OK (case only)"

            print(f"{sku:<6} | {source_brand:<20} | {target_brand:<20} | {change}")

        print("=" * 100)


def check_all_brand_changes(source_engine, target_engine):
    """Vérifie TOUS les changements de marques (pas seulement les perdus)."""
    print("\n" + "=" * 100)
    print("TOUS LES CHANGEMENTS DE MARQUES (échantillon de 50)")
    print("=" * 100)

    with source_engine.connect() as source_conn, target_engine.connect() as target_conn:
        target_conn.execute(text("SET search_path TO user_1, public"))

        # Get all products with different brands
        result = source_conn.execute(text("""
            SELECT sku, name, brand, category
            FROM product.products
            WHERE brand IS NOT NULL
            ORDER BY sku
            LIMIT 50
        """))

        print(f"\n{'SKU':<6} | {'pythonApiWOO':<20} | {'StoFlow':<20} | {'Status'}")
        print("=" * 100)

        for row in result:
            sku = row.sku
            source_brand = row.brand

            # Get brand from target
            target_row = target_conn.execute(text("""
                SELECT brand FROM products WHERE id = :id
            """), {"id": sku}).fetchone()

            target_brand = target_row.brand if target_row and target_row.brand else "(NULL)"

            # Determine status
            if target_brand == "(NULL)":
                status = "❌ PERDU"
            elif source_brand == target_brand:
                status = "✅ Identique"
            elif source_brand.lower() == target_brand.lower():
                status = "🔄 Capitalisé"
            else:
                status = "⚠️  Changé"

            print(f"{sku:<6} | {source_brand:<20} | {target_brand:<20} | {status}")

        print("=" * 100)


def check_brands_table(target_engine):
    """Vérifie quelles marques existent dans product_attributes.brands."""
    print("\n" + "=" * 100)
    print("MARQUES DISPONIBLES DANS product_attributes.brands")
    print("=" * 100)

    with target_engine.connect() as conn:
        # Check if nike/adidas variants exist
        brands_to_check = [
            'nike', 'Nike', 'NIKE',
            'adidas', 'Adidas', 'ADIDAS',
            'Unbranded', 'unbranded',
            'Wrangler', 'wrangler'
        ]

        print("\n🔍 Vérification de la présence des marques:\n")

        for brand in brands_to_check:
            result = conn.execute(text("""
                SELECT COUNT(*) FROM product_attributes.brands WHERE name = :brand
            """), {"brand": brand})
            count = result.scalar()

            status = "✅ Existe" if count > 0 else "❌ N'existe pas"
            print(f"  {brand:<15} : {status}")

        # Get all brands starting with 'n' or 'a'
        print("\n📋 Toutes les marques commençant par 'N':")
        result = conn.execute(text("""
            SELECT name FROM product_attributes.brands
            WHERE LOWER(name) LIKE 'n%'
            ORDER BY name
            LIMIT 20
        """))
        for row in result:
            print(f"  - {row.name}")

        print("\n📋 Toutes les marques commençant par 'A':")
        result = conn.execute(text("""
            SELECT name FROM product_attributes.brands
            WHERE LOWER(name) LIKE 'a%'
            ORDER BY name
            LIMIT 20
        """))
        for row in result:
            print(f"  - {row.name}")


def main():
    print("\nConnexion aux bases de données...")
    source_engine = create_engine(SOURCE_DB_URL)
    target_engine = create_engine(TARGET_DB_URL)

    try:
        # Test connections
        with source_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        with target_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Connexions établies\n")

        # Compare brands for lost products
        compare_brands_for_lost_products(source_engine, target_engine)

        # Check all brand changes (sample)
        check_all_brand_changes(source_engine, target_engine)

        # Check brands table
        check_brands_table(target_engine)

    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
