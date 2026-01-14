"""
Script pour identifier les produits qui ont perdu leur marque.
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


def find_lost_brands(source_engine, target_engine):
    """Trouve les produits qui ont perdu leur marque."""
    print("=" * 80)
    print("IDENTIFICATION DES MARQUES PERDUES")
    print("=" * 80)

    with source_engine.connect() as source_conn, target_engine.connect() as target_conn:
        target_conn.execute(text("SET search_path TO user_1, public"))

        # Get products with brand in source but not in target
        print("\n🔍 Recherche des produits qui ont perdu leur marque...")

        result = source_conn.execute(text("""
            SELECT sku, name, brand, category, price
            FROM product.products
            WHERE brand IS NOT NULL
            ORDER BY sku
        """))

        source_products = {row.sku: row for row in result}

        # Get all products from target
        result = target_conn.execute(text("""
            SELECT id, title, brand, category, price
            FROM products
        """))

        target_products = {row.id: row for row in result}

        # Find products with lost brand
        lost_brands = []

        for sku, source_row in source_products.items():
            if sku not in target_products:
                lost_brands.append({
                    'sku': sku,
                    'name': source_row.name,
                    'brand_lost': source_row.brand,
                    'category': source_row.category,
                    'price': source_row.price,
                    'reason': 'Product missing in target'
                })
            else:
                target_row = target_products[sku]
                if target_row.brand is None:
                    lost_brands.append({
                        'sku': sku,
                        'name': source_row.name,
                        'brand_lost': source_row.brand,
                        'category': source_row.category,
                        'price': source_row.price,
                        'reason': 'Brand is NULL in target'
                    })

        # Display results
        print(f"\n📊 Résultat: {len(lost_brands)} produits ont perdu leur marque\n")

        if not lost_brands:
            print("✅ Aucune marque perdue!")
            return

        # Group by brand
        by_brand = {}
        for item in lost_brands:
            brand = item['brand_lost']
            if brand not in by_brand:
                by_brand[brand] = []
            by_brand[brand].append(item)

        print("=" * 80)
        print("DÉTAIL PAR MARQUE")
        print("=" * 80)

        for brand in sorted(by_brand.keys()):
            products = by_brand[brand]
            print(f"\n🏷️  Marque: {brand} ({len(products)} produits)")
            print("-" * 80)

            for p in products:
                name = p['name'][:50] if p['name'] else '(sans nom)'
                print(f"  SKU {p['sku']}: {name}")
                print(f"    Catégorie: {p['category']}")
                print(f"    Prix: {p['price']}€")
                print(f"    Raison: {p['reason']}")
                print()

        # Summary
        print("=" * 80)
        print("RÉSUMÉ")
        print("=" * 80)
        print(f"\nNombre total de produits avec marque perdue: {len(lost_brands)}")
        print(f"Nombre de marques différentes concernées: {len(by_brand)}")
        print("\nRépartition par marque:")
        for brand in sorted(by_brand.keys(), key=lambda x: len(by_brand[x]), reverse=True):
            count = len(by_brand[brand])
            print(f"  - {brand}: {count} produit(s)")


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

        find_lost_brands(source_engine, target_engine)

    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
