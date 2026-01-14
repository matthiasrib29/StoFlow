"""
Script de réparation: Restaurer les 21 marques perdues (Nike et Adidas).
"""
import sys
from pathlib import Path
import argparse

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


def verify_brands_exist(target_engine):
    """Vérifie que les marques capitalisées existent dans product_attributes.brands."""
    print("\n" + "=" * 80)
    print("1. VÉRIFICATION DES MARQUES CIBLES")
    print("=" * 80)

    with target_engine.connect() as conn:
        # Check Nike
        nike_exists = conn.execute(text("""
            SELECT COUNT(*) FROM product_attributes.brands WHERE name = 'Nike'
        """)).scalar()

        # Check Adidas
        adidas_exists = conn.execute(text("""
            SELECT COUNT(*) FROM product_attributes.brands WHERE name = 'Adidas'
        """)).scalar()

        print(f"\n✅ Nike existe dans product_attributes.brands: {nike_exists > 0}")
        print(f"✅ Adidas existe dans product_attributes.brands: {adidas_exists > 0}")

        if nike_exists == 0 or adidas_exists == 0:
            print("\n❌ ERREUR: Les marques cibles n'existent pas dans product_attributes.brands")
            return False

        return True


def get_products_to_repair(source_engine, target_engine):
    """Récupère les produits à réparer avec leurs marques source."""
    print("\n" + "=" * 80)
    print("2. IDENTIFICATION DES PRODUITS À RÉPARER")
    print("=" * 80)

    # Les 21 SKUs identifiés
    lost_skus = [
        266, 330, 676, 744, 751, 840, 850, 894, 909, 915,
        1075, 1116, 1140, 1148, 1382, 1422, 1423, 1985, 2465, 2554, 2759
    ]

    products_to_repair = []

    with source_engine.connect() as source_conn, target_engine.connect() as target_conn:
        target_conn.execute(text("SET search_path TO user_1, public"))

        for sku in lost_skus:
            # Get brand from source
            source_row = source_conn.execute(text("""
                SELECT brand, name FROM product.products WHERE sku = :sku
            """), {"sku": sku}).fetchone()

            if not source_row:
                print(f"⚠️  SKU {sku}: Non trouvé dans source")
                continue

            source_brand = source_row.brand

            # Get brand from target
            target_row = target_conn.execute(text("""
                SELECT brand, title FROM products WHERE id = :id
            """), {"id": sku}).fetchone()

            if not target_row:
                print(f"⚠️  SKU {sku}: Non trouvé dans target")
                continue

            target_brand = target_row.brand

            # Map lowercase to capitalized
            if source_brand == 'nike':
                new_brand = 'Nike'
            elif source_brand == 'adidas':
                new_brand = 'Adidas'
            else:
                print(f"⚠️  SKU {sku}: Marque inattendue '{source_brand}'")
                continue

            products_to_repair.append({
                'sku': sku,
                'name': source_row.name or target_row.title,
                'old_brand': target_brand,
                'new_brand': new_brand,
                'source_brand': source_brand
            })

    print(f"\n📊 {len(products_to_repair)} produits à réparer")
    return products_to_repair


def display_repair_plan(products):
    """Affiche le plan de réparation."""
    print("\n" + "=" * 80)
    print("3. PLAN DE RÉPARATION")
    print("=" * 80)

    nike_count = sum(1 for p in products if p['new_brand'] == 'Nike')
    adidas_count = sum(1 for p in products if p['new_brand'] == 'Adidas')

    print(f"\n📋 Résumé:")
    print(f"  - Nike: {nike_count} produits")
    print(f"  - Adidas: {adidas_count} produits")

    print(f"\n{'SKU':<6} | {'Nom (tronqué)':<40} | {'NULL → Nouvelle marque'}")
    print("=" * 80)

    for p in products:
        name = (p['name'][:37] + '...') if p['name'] and len(p['name']) > 40 else (p['name'] or '(sans nom)')
        print(f"{p['sku']:<6} | {name:<40} | NULL → {p['new_brand']}")

    print("=" * 80)


def repair_brands(target_engine, products, dry_run=False):
    """Répare les marques."""
    print("\n" + "=" * 80)
    print("4. RÉPARATION EN COURS")
    print("=" * 80)

    if dry_run:
        print("\n⚠️  MODE DRY-RUN: Aucune modification ne sera effectuée")
        return True

    # Use begin() to get a transaction-ready connection
    with target_engine.begin() as conn:
        conn.execute(text("SET search_path TO user_1, public"))

        success_count = 0
        failed_count = 0

        for p in products:
            try:
                # Update brand
                result = conn.execute(text("""
                    UPDATE products
                    SET brand = :brand,
                        updated_at = NOW()
                    WHERE id = :id
                """), {
                    "brand": p['new_brand'],
                    "id": p['sku']
                })

                if result.rowcount > 0:
                    success_count += 1
                    print(f"✅ SKU {p['sku']}: brand mis à jour → {p['new_brand']}")
                else:
                    failed_count += 1
                    print(f"❌ SKU {p['sku']}: Aucune ligne mise à jour")

            except Exception as e:
                failed_count += 1
                print(f"❌ SKU {p['sku']}: Erreur - {str(e)[:50]}")
                # Rollback and re-raise to abort transaction
                raise

        # Transaction will auto-commit when exiting the with block

        print("\n" + "=" * 80)
        print(f"✅ Réparation terminée: {success_count} succès, {failed_count} échecs")
        print("=" * 80)

        return failed_count == 0


def verify_repair(target_engine, products):
    """Vérifie que la réparation a fonctionné."""
    print("\n" + "=" * 80)
    print("5. VÉRIFICATION POST-RÉPARATION")
    print("=" * 80)

    with target_engine.connect() as conn:
        conn.execute(text("SET search_path TO user_1, public"))

        success_count = 0
        failed_count = 0

        for p in products:
            # Get current brand
            result = conn.execute(text("""
                SELECT brand FROM products WHERE id = :id
            """), {"id": p['sku']})

            row = result.fetchone()

            if row and row.brand == p['new_brand']:
                success_count += 1
            else:
                failed_count += 1
                current_brand = row.brand if row else "(not found)"
                print(f"❌ SKU {p['sku']}: brand = {current_brand} (attendu: {p['new_brand']})")

        print(f"\n✅ Vérification: {success_count}/{len(products)} produits OK")

        if failed_count > 0:
            print(f"⚠️  {failed_count} produits n'ont pas été réparés correctement")
            return False

        return True


def main():
    parser = argparse.ArgumentParser(description="Réparer les marques perdues (Nike et Adidas)")
    parser.add_argument("--dry-run", action="store_true", help="Afficher le plan sans modifier")
    args = parser.parse_args()

    print("=" * 80)
    print("RÉPARATION DES MARQUES PERDUES")
    print("=" * 80)

    if args.dry_run:
        print("\n⚠️  MODE DRY-RUN ACTIVÉ")

    # Connect to databases
    print("\nConnexion aux bases de données...")
    source_engine = create_engine(SOURCE_DB_URL)
    target_engine = create_engine(TARGET_DB_URL)

    try:
        # Test connections
        with source_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        with target_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Connexions établies")

        # Step 1: Verify target brands exist
        if not verify_brands_exist(target_engine):
            print("\n❌ Impossible de continuer: marques cibles manquantes")
            return

        # Step 2: Get products to repair
        products = get_products_to_repair(source_engine, target_engine)

        if not products:
            print("\n⚠️  Aucun produit à réparer")
            return

        # Step 3: Display repair plan
        display_repair_plan(products)

        # Step 4: Repair (or dry-run)
        if args.dry_run:
            print("\n" + "=" * 80)
            print("MODE DRY-RUN: Afficher le plan ci-dessus")
            print("Pour exécuter la réparation, lancez sans --dry-run")
            print("=" * 80)
        else:
            # Ask for confirmation
            print("\n" + "=" * 80)
            print("⚠️  ATTENTION: Vous allez modifier les données de production")
            print("=" * 80)
            confirmation = input("\nTaper 'OUI' pour confirmer la réparation: ")

            if confirmation != "OUI":
                print("\n❌ Réparation annulée")
                return

            success = repair_brands(target_engine, products, dry_run=False)

            if success:
                # Step 5: Verify
                verify_repair(target_engine, products)
                print("\n" + "=" * 80)
                print("✅ RÉPARATION TERMINÉE AVEC SUCCÈS")
                print("=" * 80)
            else:
                print("\n" + "=" * 80)
                print("❌ LA RÉPARATION A ÉCHOUÉ")
                print("=" * 80)

    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
