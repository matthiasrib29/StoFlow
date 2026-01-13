"""
Migration Script: pythonApiWOO → Stoflow_BackEnd

Migrates ~3000 products from the old pythonApiWOO database to Stoflow_BackEnd.

Source: PostgreSQL appdb (port 5432) - schema product.products
Target: PostgreSQL stoflow_db (port 5433) - schema user_1.products

Rules:
- SKU from source becomes id in target
- Status waiting_ai/waiting_revue → draft
- Images reference old paths (no file copy)
- Only products and images (no VintedProduct)

Usage:
    python scripts/migrate_from_pythonapiwoo.py [--dry-run]
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime
from decimal import Decimal

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


# Database configurations
SOURCE_DB_URL = "postgresql://appuser:apppass@127.0.0.1:5432/appdb"
TARGET_DB_URL = "postgresql://stoflow_user:stoflow_dev_password_2024@localhost:5433/stoflow_db"

# Status mapping (target uses UPPERCASE enum values)
STATUS_MAPPING = {
    "draft": "DRAFT",
    "waiting_ai": "DRAFT",
    "waiting_revue": "DRAFT",
    "published": "PUBLISHED",
}


def get_source_products(source_session):
    """
    Fetch all products from source database.

    Returns:
        List of product dictionaries
    """
    query = text("""
        SELECT
            sku,
            name,
            price,
            pricing_edit,
            status,
            stock_quantity,
            created_at,
            updated_at,
            brand,
            category,
            color,
            condition,
            condition_sup,
            size,
            label_size,
            material,
            fit,
            rise,
            gender,
            season,
            origin,
            decade,
            trend,
            pricing_rarity,
            pricing_quality,
            pricing_details,
            pricing_style,
            closure,
            unique_feature,
            model,
            sleeve_length,
            marking,
            dim1,
            dim2,
            dim3,
            dim4,
            dim5,
            dim6,
            name_sup,
            location
        FROM product.products
        ORDER BY sku
    """)

    result = source_session.execute(query)
    products = []

    for row in result:
        products.append({
            "sku": row.sku,
            "name": row.name,
            "price": row.price,
            "pricing_edit": row.pricing_edit,
            "status": row.status,
            "stock_quantity": row.stock_quantity,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
            "brand": row.brand,
            "category": row.category,
            "color": row.color,
            "condition": row.condition,
            "condition_sup": row.condition_sup,
            "size_normalized": row.size,
            "size_original": row.label_size,
            "material": row.material,
            "fit": row.fit,
            "rise": row.rise,
            "gender": row.gender,
            "season": row.season,
            "origin": row.origin,
            "decade": row.decade,
            "trend": row.trend,
            "pricing_rarity": row.pricing_rarity,
            "pricing_quality": row.pricing_quality,
            "pricing_details": row.pricing_details,
            "pricing_style": row.pricing_style,
            "closure": row.closure,
            "unique_feature": row.unique_feature,
            "model": row.model,
            "sleeve_length": row.sleeve_length,
            "marking": row.marking,
            "dim1": row.dim1,
            "dim2": row.dim2,
            "dim3": row.dim3,
            "dim4": row.dim4,
            "dim5": row.dim5,
            "dim6": row.dim6,
            "name_sup": row.name_sup,
            "location": row.location,
        })

    return products


def get_source_images(source_session):
    """
    Fetch all product images from source database.

    Returns:
        Dict mapping SKU to list of images
    """
    query = text("""
        SELECT
            sku,
            image_path,
            display_order,
            link,
            link_optimized,
            created_at
        FROM product.product_images
        ORDER BY sku, display_order
    """)

    result = source_session.execute(query)
    images_by_sku = {}

    for row in result:
        sku = row.sku
        if sku not in images_by_sku:
            images_by_sku[sku] = []

        images_by_sku[sku].append({
            "image_path": row.image_path,
            "display_order": row.display_order,
            "link": row.link,
            "link_optimized": row.link_optimized,
            "created_at": row.created_at,
        })

    return images_by_sku


def clear_target_tables(target_session):
    """
    Clear user_1.products and user_1.product_images tables.
    """
    # Delete images first (foreign key constraint)
    target_session.execute(text("DELETE FROM user_1.product_images"))
    target_session.execute(text("DELETE FROM user_1.products"))
    target_session.commit()
    print("  Tables user_1.products et user_1.product_images vidées")


def ensure_sequences(target_session):
    """
    Ensure sequences exist for products and product_images tables.
    """
    # Create sequence for products if not exists
    target_session.execute(text("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_sequences WHERE schemaname = 'user_1' AND sequencename = 'products_id_seq') THEN
                CREATE SEQUENCE user_1.products_id_seq;
                ALTER TABLE user_1.products ALTER COLUMN id SET DEFAULT nextval('user_1.products_id_seq');
            END IF;
        END $$;
    """))

    # Create sequence for product_images if not exists
    target_session.execute(text("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_sequences WHERE schemaname = 'user_1' AND sequencename = 'product_images_id_seq') THEN
                CREATE SEQUENCE user_1.product_images_id_seq;
                ALTER TABLE user_1.product_images ALTER COLUMN id SET DEFAULT nextval('user_1.product_images_id_seq');
            END IF;
        END $$;
    """))

    target_session.commit()
    print("  Séquences créées/vérifiées")


def map_status(source_status):
    """Map source status to target status (uppercase for PostgreSQL enum)."""
    if source_status is None:
        return "DRAFT"
    status_str = str(source_status).replace("ProductStatus.", "")
    return STATUS_MAPPING.get(status_str, "DRAFT")


def insert_products(target_session, products, images_by_sku, dry_run=False):
    """
    Insert products into target database.

    Args:
        target_session: SQLAlchemy session for target DB
        products: List of product dictionaries
        images_by_sku: Dict mapping SKU to list of images
        dry_run: If True, don't commit changes
    """
    inserted_count = 0
    image_count = 0
    errors = []
    skipped = []

    for product in products:
        sku = product["sku"]

        # Map fields
        title = product["name"] or f"Product {sku}"
        description = title  # Use title as description if none

        # Handle NULL price: set to 0 and force DRAFT status
        if product["price"] is None or product["price"] == 0:
            price = Decimal("0")
            status = "DRAFT"
        else:
            price = Decimal(str(product["price"]))
            status = map_status(product["status"])

        stock_quantity = product["stock_quantity"] or 1

        # Category and condition can be NULL for DRAFT products
        category = product["category"]
        condition = product["condition"]

        # Products without category or condition become DRAFT
        if not category:
            status = "DRAFT"
            category = None

        if not condition:
            status = "DRAFT"
            condition = None

        # Use savepoint for each product
        try:
            target_session.execute(text("SAVEPOINT product_savepoint"))

            # Insert product with SKU as id (cast status to enum using CAST)
            insert_product = text("""
                INSERT INTO user_1.products (
                    id, title, description, price, status, stock_quantity,
                    category, condition, brand, label_size, color, material,
                    fit, gender, season, origin, decade, trend,
                    pricing_edit, pricing_rarity, pricing_quality, pricing_details, pricing_style,
                    closure, unique_feature, model, sleeve_length, marking,
                    dim1, dim2, dim3, dim4, dim5, dim6,
                    name_sup, location, condition_sup, rise,
                    created_at, updated_at
                ) VALUES (
                    :id, :title, :description, :price, CAST(:status AS product_status), :stock_quantity,
                    :category, :condition, :brand, :label_size, :color, :material,
                    :fit, :gender, :season, :origin, :decade, :trend,
                    :pricing_edit, :pricing_rarity, :pricing_quality, :pricing_details, :pricing_style,
                    :closure, :unique_feature, :model, :sleeve_length, :marking,
                    :dim1, :dim2, :dim3, :dim4, :dim5, :dim6,
                    :name_sup, :location, :condition_sup, :rise,
                    :created_at, :updated_at
                )
            """)

            target_session.execute(insert_product, {
                "id": sku,
                "title": title,
                "description": description,
                "price": price,
                "status": status,
                "stock_quantity": stock_quantity,
                "category": category,
                "condition": condition,
                "brand": product["brand"],
                "label_size": product["label_size"],
                "color": product["color"],
                "material": product["material"],
                "fit": product["fit"],
                "gender": product["gender"],
                "season": product["season"],
                "origin": product["origin"],
                "decade": product["decade"],
                "trend": product["trend"],
                "pricing_edit": product["pricing_edit"],
                "pricing_rarity": product["pricing_rarity"],
                "pricing_quality": product["pricing_quality"],
                "pricing_details": product["pricing_details"],
                "pricing_style": product["pricing_style"],
                "closure": product["closure"],
                "unique_feature": product["unique_feature"],
                "model": product["model"],
                "sleeve_length": product["sleeve_length"],
                "marking": product["marking"],
                "dim1": product["dim1"],
                "dim2": product["dim2"],
                "dim3": product["dim3"],
                "dim4": product["dim4"],
                "dim5": product["dim5"],
                "dim6": product["dim6"],
                "name_sup": product["name_sup"],
                "location": product["location"],
                "condition_sup": product["condition_sup"],
                "rise": product["rise"],
                "created_at": product["created_at"] or datetime.now(),
                "updated_at": product["updated_at"] or datetime.now(),
            })

            inserted_count += 1

            # Insert images for this product
            if sku in images_by_sku:
                for img in images_by_sku[sku]:
                    insert_image = text("""
                        INSERT INTO user_1.product_images (
                            product_id, image_path, display_order, created_at
                        ) VALUES (
                            :product_id, :image_path, :display_order, :created_at
                        )
                    """)

                    target_session.execute(insert_image, {
                        "product_id": sku,
                        "image_path": img["image_path"],
                        "display_order": img["display_order"] or 0,
                        "created_at": img["created_at"] or datetime.now(),
                    })
                    image_count += 1

            # Release savepoint on success
            target_session.execute(text("RELEASE SAVEPOINT product_savepoint"))

            # Progress indicator
            if inserted_count % 500 == 0:
                print(f"    Progression: {inserted_count} produits insérés...")

        except Exception as e:
            # Rollback to savepoint on error
            target_session.execute(text("ROLLBACK TO SAVEPOINT product_savepoint"))
            errors.append(f"SKU {sku}: {str(e)[:100]}")

    if not dry_run:
        target_session.commit()

    return inserted_count, image_count, errors + skipped


def reset_sequence(target_session, max_id):
    """
    Reset the products id sequence to start after max_id.
    """
    target_session.execute(text(f"""
        SELECT setval('user_1.products_id_seq', {max_id + 1}, false)
    """))
    target_session.commit()
    print(f"  Séquence réinitialisée à {max_id + 1}")


def main():
    parser = argparse.ArgumentParser(description="Migrate products from pythonApiWOO to Stoflow")
    parser.add_argument("--dry-run", action="store_true", help="Don't commit changes")
    args = parser.parse_args()

    print("=" * 60)
    print("MIGRATION: pythonApiWOO → Stoflow_BackEnd")
    print("=" * 60)

    if args.dry_run:
        print("\n*** MODE DRY-RUN: Aucune modification ne sera commitée ***\n")

    # Connect to databases
    print("\n1. Connexion aux bases de données...")
    source_engine = create_engine(SOURCE_DB_URL)
    target_engine = create_engine(TARGET_DB_URL)

    SourceSession = sessionmaker(bind=source_engine)
    TargetSession = sessionmaker(bind=target_engine)

    source_session = SourceSession()
    target_session = TargetSession()

    try:
        # Test connections
        source_session.execute(text("SELECT 1"))
        target_session.execute(text("SELECT 1"))
        print("  Connexions établies")

        # Use schema_translate_map for ORM queries (survives commit/rollback)
        target_session = target_session.execution_options(
            schema_translate_map={"tenant": "user_1"}
        )
        # Also set search_path for text() queries
        target_session.execute(text("SET search_path TO user_1, public"))

        # Fetch source data
        print("\n2. Lecture des données source...")
        products = get_source_products(source_session)
        print(f"  {len(products)} produits trouvés")

        images_by_sku = get_source_images(source_session)
        total_images = sum(len(imgs) for imgs in images_by_sku.values())
        print(f"  {total_images} images trouvées")

        # Ensure sequences exist
        print("\n3. Création/vérification des séquences...")
        if not args.dry_run:
            ensure_sequences(target_session)
        else:
            print("  [DRY-RUN] Séquences non créées")

        # Clear target tables
        print("\n4. Nettoyage des tables cibles...")
        if not args.dry_run:
            clear_target_tables(target_session)
        else:
            print("  [DRY-RUN] Tables non vidées")

        # Insert data
        print("\n5. Insertion des données...")
        inserted, images_inserted, errors = insert_products(
            target_session, products, images_by_sku, dry_run=args.dry_run
        )

        # Reset sequence
        if not args.dry_run and products:
            print("\n6. Réinitialisation de la séquence...")
            max_sku = max(p["sku"] for p in products)
            reset_sequence(target_session, max_sku)

        # Summary
        print("\n" + "=" * 60)
        print("RÉSUMÉ DE LA MIGRATION")
        print("=" * 60)
        print(f"  Produits migrés:    {inserted}/{len(products)}")
        print(f"  Images migrées:     {images_inserted}/{total_images}")
        print(f"  Erreurs:            {len(errors)}")

        if errors:
            print("\n  Erreurs détaillées (10 premières):")
            for error in errors[:10]:
                print(f"    - {error}")
            if len(errors) > 10:
                print(f"    ... et {len(errors) - 10} autres erreurs")

        if args.dry_run:
            print("\n*** DRY-RUN: Aucune modification n'a été commitée ***")
        else:
            print("\n Migration terminée avec succès!")

    except Exception as e:
        print(f"\n ERREUR: {e}")
        target_session.rollback()
        raise

    finally:
        source_session.close()
        target_session.close()


if __name__ == "__main__":
    main()
