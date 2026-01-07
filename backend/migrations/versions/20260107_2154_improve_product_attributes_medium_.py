"""improve_product_attributes_medium_priority

Medium Priority Improvements:
1. Harmonize CATEGORIES format (add spaces: swimsuit → swim suit)
2. Rename suit-vest → waistcoat, fleece → fleece jacket
3. Delete womens-suit category
4. Remove Modern/Vintage from DECADES (keep in TRENDS)
5. Clarify DECADES: 00s → 2000s, 10s → 2010s, 20s → 2020s
6. Add 2025 trends: Old Money, Quiet Luxury, Coquette, etc.
7. Add missing CONDITION_SUP: Color bleeding, Sun fading, Moth holes, etc.
8. Add missing CLOSURES: Hook and eye, Snap buttons, Toggle, Velcro, Drawstring
9. Create LININGS table: Unlined, Fully lined, Partially lined, Fleece lined

Revision ID: a9b8c7d6e5f4
Revises: f262703133fd
Create Date: 2026-01-07 21:54:XX

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'a9b8c7d6e5f4'
down_revision: Union[str, None] = 'f262703133fd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_user_schemas(conn):
    """Get all user schemas including template_tenant."""
    result = conn.execute(text("""
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%' OR schema_name = 'template_tenant'
        ORDER BY schema_name
    """))
    return [row[0] for row in result]


def table_exists(conn, schema, table):
    """Check if table exists in schema."""
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = :schema AND table_name = :table
        )
    """), {"schema": schema, "table": table})
    return result.scalar()


def upgrade() -> None:
    conn = op.get_bind()

    # ========================================================================
    # STEP 0: Fix FK constraints to use ON UPDATE CASCADE
    # ========================================================================
    print("Step 0: Updating FK constraints to ON UPDATE CASCADE...")

    # Fix vinted.mapping FK
    conn.execute(text("""
        ALTER TABLE vinted.mapping
        DROP CONSTRAINT IF EXISTS mapping_my_category_fkey;
    """))
    conn.execute(text("""
        ALTER TABLE vinted.mapping
        ADD CONSTRAINT mapping_my_category_fkey
        FOREIGN KEY (my_category)
        REFERENCES product_attributes.categories(name_en)
        ON UPDATE CASCADE
        ON DELETE SET NULL;
    """))

    # Fix template_tenant.products FK
    conn.execute(text("""
        ALTER TABLE template_tenant.products
        DROP CONSTRAINT IF EXISTS fk_template_tenant_products_category;
    """))
    conn.execute(text("""
        ALTER TABLE template_tenant.products
        ADD CONSTRAINT fk_template_tenant_products_category
        FOREIGN KEY (category)
        REFERENCES product_attributes.categories(name_en)
        ON UPDATE CASCADE
        ON DELETE SET NULL;
    """))

    print("✅ FK constraints updated with ON UPDATE CASCADE")

    # ========================================================================
    # STEP 1: Harmonize CATEGORIES format (add spaces)
    # ========================================================================
    print("Step 1: Harmonizing category names with spaces...")

    category_renames = [
        ("swimsuit", "swim suit"),
        ("bodysuit", "body suit"),
        ("tracksuit", "track suit"),
        ("jumpsuit", "jump suit"),
    ]

    for old_name, new_name in category_renames:
        # Update category name FIRST - CASCADE will auto-update products and vinted.mapping
        conn.execute(text("""
            UPDATE product_attributes.categories
            SET name_en = :new_name
            WHERE name_en = :old_name;
        """), {"old_name": old_name, "new_name": new_name})

    print(f"✅ Renamed {len(category_renames)} categories to space format")

    # ========================================================================
    # STEP 2: Rename specific categories
    # ========================================================================
    print("Step 2: Renaming specific categories...")

    specific_renames = [
        ("suit-vest", "waistcoat"),
        ("fleece", "fleece jacket"),
    ]

    for old_name, new_name in specific_renames:
        # Update category name FIRST - CASCADE will auto-update products and vinted.mapping
        conn.execute(text("""
            UPDATE product_attributes.categories
            SET name_en = :new_name
            WHERE name_en = :old_name;
        """), {"old_name": old_name, "new_name": new_name})

    print(f"✅ Renamed {len(specific_renames)} specific categories")

    # ========================================================================
    # STEP 3: Delete womens-suit category
    # ========================================================================
    print("Step 3: Deleting womens-suit category...")

    # Delete vinted.mapping entries for womens-suit (suit already exists)
    conn.execute(text("""
        DELETE FROM vinted.mapping
        WHERE my_category = 'womens-suit';
    """))

    # Migrate products from womens-suit to suit
    schemas = get_user_schemas(conn)
    migrated_count = 0
    for schema in schemas:
        if table_exists(conn, schema, 'products'):
            result = conn.execute(text(f"""
                UPDATE {schema}.products
                SET category = 'suit'
                WHERE category = 'womens-suit';
            """))
            migrated_count += result.rowcount

    # Delete category
    conn.execute(text("""
        DELETE FROM product_attributes.categories
        WHERE name_en = 'womens-suit';
    """))

    print(f"✅ Migrated {migrated_count} products and deleted womens-suit")

    # ========================================================================
    # STEP 4: Remove Modern/Vintage from DECADES
    # ========================================================================
    print("Step 4: Removing Modern/Vintage from DECADES...")

    # These values exist in TRENDS, so remove from DECADES
    to_remove_decades = ['Modern', 'Vintage']

    for decade in to_remove_decades:
        conn.execute(text("""
            DELETE FROM product_attributes.decades
            WHERE name_en = :decade;
        """), {"decade": decade})

    print(f"✅ Removed {len(to_remove_decades)} duplicates from DECADES")

    # ========================================================================
    # STEP 5: Clarify DECADES (00s → 2000s, etc.)
    # ========================================================================
    print("Step 5: Clarifying decade names...")

    decade_clarifications = [
        ("00s", "2000s"),
        ("10s", "2010s"),
        ("20s", "2020s"),
    ]

    for old_name, new_name in decade_clarifications:
        conn.execute(text("""
            UPDATE product_attributes.decades
            SET name_en = :new_name
            WHERE name_en = :old_name;
        """), {"old_name": old_name, "new_name": new_name})

    print(f"✅ Clarified {len(decade_clarifications)} decade names")

    # ========================================================================
    # STEP 6: Add 2025 trends
    # ========================================================================
    print("Step 6: Adding 2025 trends...")

    new_trends = [
        ("Old money", "Vieille richesse", "Altes Geld", "Vecchio denaro", "Viejo dinero", "Oud geld", "Stare pieniądze"),
        ("Quiet luxury", "Luxe discret", "Leiser Luxus", "Lusso silenzioso", "Lujo silencioso", "Stille luxe", "Cichy luksus"),
        ("Coquette", "Coquette", "Kokett", "Civetta", "Coqueta", "Kokette", "Kokietka"),
        ("Clean girl", "Clean girl", "Clean girl", "Clean girl", "Clean girl", "Clean girl", "Clean girl"),
        ("Light academia", "Light academia", "Light academia", "Light academia", "Light academia", "Light academia", "Light academia"),
        ("Balletcore", "Balletcore", "Balletcore", "Balletcore", "Balletcore", "Balletcore", "Balletcore"),
        ("Gorpcore", "Gorpcore", "Gorpcore", "Gorpcore", "Gorpcore", "Gorpcore", "Gorpcore"),
    ]

    for name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl in new_trends:
        conn.execute(text("""
            INSERT INTO product_attributes.trends (name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl)
            VALUES (:name_en, :name_fr, :name_de, :name_it, :name_es, :name_nl, :name_pl)
            ON CONFLICT (name_en) DO NOTHING;
        """), {
            "name_en": name_en, "name_fr": name_fr, "name_de": name_de,
            "name_it": name_it, "name_es": name_es, "name_nl": name_nl, "name_pl": name_pl
        })

    print(f"✅ Added {len(new_trends)} new trends for 2025")

    # ========================================================================
    # STEP 7: Add missing CONDITION_SUP
    # ========================================================================
    print("Step 7: Adding missing condition supplements...")

    new_condition_sups = [
        ("Color bleeding", "Dégorgement de couleur"),
        ("Sun fading", "Décoloration solaire"),
        ("Moth holes", "Trous de mites"),
        ("Odor", "Odeur"),
        ("Elastic worn", "Élastique usé"),
        ("Lining damaged", "Doublure abîmée"),
    ]

    for name_en, name_fr in new_condition_sups:
        conn.execute(text("""
            INSERT INTO product_attributes.condition_sups (name_en, name_fr)
            VALUES (:name_en, :name_fr)
            ON CONFLICT (name_en) DO NOTHING;
        """), {"name_en": name_en, "name_fr": name_fr})

    print(f"✅ Added {len(new_condition_sups)} new condition supplements")

    # ========================================================================
    # STEP 8: Add missing CLOSURES
    # ========================================================================
    print("Step 8: Adding missing closures...")

    new_closures = [
        ("Hook and eye", "Agrafes", "Haken und Öse", "Gancio e occhiello", "Corchete", "Haak en oog", "Haczyk i oczko"),
        ("Snap buttons", "Boutons-pression", "Druckknöpfe", "Bottoni a pressione", "Botones de presión", "Drukknopen", "Zatrzaski"),
        ("Toggle", "Bouton-bûchette", "Knebelverschluss", "Chiusura a leva", "Cierre de palanca", "Knevelsluiting", "Zatrzask"),
        ("Velcro", "Velcro", "Klettverschluss", "Velcro", "Velcro", "Klittenband", "Rzep"),
        ("Drawstring", "Cordon coulissant", "Kordelzug", "Laccio", "Cordón", "Trekkoord", "Sznurek"),
    ]

    for name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl in new_closures:
        conn.execute(text("""
            INSERT INTO product_attributes.closures (name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl)
            VALUES (:name_en, :name_fr, :name_de, :name_it, :name_es, :name_nl, :name_pl)
            ON CONFLICT (name_en) DO NOTHING;
        """), {
            "name_en": name_en, "name_fr": name_fr, "name_de": name_de,
            "name_it": name_it, "name_es": name_es, "name_nl": name_nl, "name_pl": name_pl
        })

    print(f"✅ Added {len(new_closures)} new closures")

    # ========================================================================
    # STEP 9: Create LININGS table
    # ========================================================================
    print("Step 9: Creating linings table...")

    conn.execute(text("""
        CREATE TABLE product_attributes.linings (
            name_en VARCHAR(100) PRIMARY KEY,
            name_fr VARCHAR(100),
            name_de VARCHAR(100),
            name_it VARCHAR(100),
            name_es VARCHAR(100),
            name_nl VARCHAR(100),
            name_pl VARCHAR(100)
        );
        CREATE INDEX idx_linings_name_en ON product_attributes.linings(name_en);
    """))

    # Insert initial lining types
    linings = [
        ("Unlined", "Sans doublure", "Ungefüttert", "Senza fodera", "Sin forro", "Ongevoerd", "Bez podszewki"),
        ("Fully lined", "Entièrement doublé", "Voll gefüttert", "Foderato completamente", "Completamente forrado", "Volledig gevoerd", "Całkowicie podszyte"),
        ("Partially lined", "Partiellement doublé", "Teilweise gefüttert", "Parzialmente foderato", "Parcialmente forrado", "Gedeeltelijk gevoerd", "Częściowo podszyte"),
        ("Fleece lined", "Doublure polaire", "Fleecegefüttert", "Foderato in pile", "Forro polar", "Fleece gevoerd", "Podszewka polarowa"),
    ]

    for name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl in linings:
        conn.execute(text("""
            INSERT INTO product_attributes.linings (name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl)
            VALUES (:name_en, :name_fr, :name_de, :name_it, :name_es, :name_nl, :name_pl);
        """), {
            "name_en": name_en, "name_fr": name_fr, "name_de": name_de,
            "name_it": name_it, "name_es": name_es, "name_nl": name_nl, "name_pl": name_pl
        })

    print(f"✅ Created linings table with {len(linings)} options")
    print("🎉 Medium priority improvements completed!")


def downgrade() -> None:
    conn = op.get_bind()

    # Drop linings table
    conn.execute(text("DROP TABLE IF EXISTS product_attributes.linings CASCADE;"))

    # Reverse closures
    new_closures = ["Hook and eye", "Snap buttons", "Toggle", "Velcro", "Drawstring"]
    for closure in new_closures:
        conn.execute(text("DELETE FROM product_attributes.closures WHERE name_en = :c;"), {"c": closure})

    # Reverse condition_sups
    new_cond_sups = ["Color bleeding", "Sun fading", "Moth holes", "Odor", "Elastic worn", "Lining damaged"]
    for cond in new_cond_sups:
        conn.execute(text("DELETE FROM product_attributes.condition_sups WHERE name_en = :c;"), {"c": cond})

    # Reverse trends
    new_trends = ["Old money", "Quiet luxury", "Coquette", "Clean girl", "Light academia", "Balletcore", "Gorpcore"]
    for trend in new_trends:
        conn.execute(text("DELETE FROM product_attributes.trends WHERE name_en = :t;"), {"t": trend})

    # Reverse decade clarifications
    conn.execute(text("UPDATE product_attributes.decades SET name_en = '00s' WHERE name_en = '2000s';"))
    conn.execute(text("UPDATE product_attributes.decades SET name_en = '10s' WHERE name_en = '2010s';"))
    conn.execute(text("UPDATE product_attributes.decades SET name_en = '20s' WHERE name_en = '2020s';"))

    # Re-add Modern/Vintage to decades
    conn.execute(text("INSERT INTO product_attributes.decades (name_en) VALUES ('Modern'), ('Vintage') ON CONFLICT DO NOTHING;"))

    # Restore womens-suit
    conn.execute(text("INSERT INTO product_attributes.categories (name_en) VALUES ('womens-suit') ON CONFLICT DO NOTHING;"))

    # Reverse category renames (partial - product references not restored)
    conn.execute(text("UPDATE product_attributes.categories SET name_en = 'waistcoat' WHERE name_en = 'suit-vest';"))
    conn.execute(text("UPDATE product_attributes.categories SET name_en = 'fleece jacket' WHERE name_en = 'fleece';"))

    print("⚠️  Downgrade completed - some data migrations are irreversible")
