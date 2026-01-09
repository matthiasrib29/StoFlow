"""Complete partial attribute tables with missing data

Revision ID: 20251224_2100
Revises: 20251224_2000
Create Date: 2024-12-24 21:00:00

This migration completes partial tables with data from ALL_PRODUCT_ATTRIBUTES.txt:
1. brands: 189 values (was 8)
2. categories: 65 values (was 5)
3. sizes: 117 values (was 23)
4. fits: 11 values (was 6)
5. materials: 24 values (was 15)

Author: Claude
Date: 2025-12-24
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = "20251224_2100"
down_revision = "20251224_2000"
branch_labels = None
depends_on = None


# ===== DATA =====

BRANDS_DATA = [
    "2pac", "3sixteen", "a.p.c.", "acne studios", "acronym", "adidas", "aem'kei nyc",
    "affliction", "akademiks", "anchor blue", "and wander", "arc'teryx", "arm jeans",
    "auralee", "avirex", "bape", "bastard", "battenwear", "baz 40", "ben davis",
    "bershka", "big train", "blind", "blueskin", "brixton", "bugle boy", "burberrys",
    "butter goods", "calvin klein", "carhartt", "celio", "champion", "chaps",
    "chevignon", "citizens of humanity", "coogi", "corteiz", "crooks & castles",
    "denham", "denime", "dickies", "diesel", "dime", "divided", "dynam", "ecko unltd",
    "ecko unltd.", "ed hardy", "edwin", "element", "energie", "engineered garments",
    "enyce", "evisu", "foot korner", "frame", "freeman", "freenote cloth", "fubu",
    "full count", "g-star raw", "g-unit", "gant jeans", "gap", "goldwin", "gramicci",
    "guess", "hawk", "heron preston", "homecore", "houdini", "huf", "hugo boss",
    "indigofera", "iron heart", "izac", "izod", "jackwolfskin", "japan blue", "jizo",
    "jnco", "kangaroo poo", "kapital", "karl kani", "keegan", "kiabi", "kiko kostadinov",
    "klättermusen", "kolapso", "lacoste", "lagerfeld", "lee", "lee cooper",
    "left field nyc", "lemaire", "levi's", "levi's made & crafted",
    "levi's vintage clothing", "maharishi", "maison mihara yasuhiro", "majestic",
    "marni", "mecca", "mlb", "momotaro", "mont bell", "montbell",
    "naked & famous denim", "napapijri", "nascar", "neighborhood", "nfl",
    "nigel cabourn", "nike", "no fear", "norrøna", "nudie jeans", "nylaus", "obey",
    "oni arai", "orslow", "our legacy", "outback", "palace", "pass port", "passport",
    "pelle pelle", "pepe jeans", "phat farm", "poetic collective", "pointer",
    "polar skate", "polar skate co.", "pop trading company", "puma", "pure blue japan",
    "rag & bone", "ralph lauren", "rare humans", "red pepper", "reebok", "reell",
    "rica lewis", "robin's jean", "rocawear", "rogue territory", "roy jeans",
    "résolute", "samurai", "sean john", "service works", "snow peak", "sohk",
    "south pole", "southpole", "stan ray", "starter", "state property",
    "studio d'artisan", "stuka", "stüssy", "sugar cane", "sunnei", "supreme",
    "tcb jeans", "tela genova", "tellason", "the flat head", "the north face",
    "timberland", "tommy hilfiger", "tribal", "true religion", "unbranded",
    "under armour", "universal works", "vans", "veilance", "victorinox", "vokal",
    "volcom", "warehouse", "wrangler", "wrung", "wtaps", "wu-wear", "yardsale",
    "zoo york"
]

# Categories with parent relationship
CATEGORIES_DATA = [
    # Parent categories
    ("clothing", None, "Vêtements"),
    ("tops", "clothing", "Hauts"),
    ("bottoms", "clothing", "Bas"),
    ("outerwear", "clothing", "Vêtements d'extérieur"),
    ("dresses-jumpsuits", "clothing", "Robes et combinaisons"),
    ("sportswear", "clothing", "Vêtements de sport"),
    ("formalwear", "clothing", "Tenues de cérémonie"),
    # Tops
    ("t-shirt", "tops", "T-shirt"),
    ("shirt", "tops", "Chemise"),
    ("blouse", "tops", "Blouse"),
    ("polo", "tops", "Polo"),
    ("sweater", "tops", "Pull"),
    ("sweatshirt", "tops", "Sweatshirt"),
    ("hoodie", "tops", "Sweat à capuche"),
    ("cardigan", "tops", "Cardigan"),
    ("tank-top", "tops", "Débardeur"),
    ("crop-top", "tops", "Crop top"),
    ("camisole", "tops", "Caraco"),
    ("top", "tops", "Haut"),
    ("half-zip", "tops", "Demi-zip"),
    ("overshirt", "tops", "Surchemise"),
    # Bottoms
    ("jeans", "bottoms", "Jeans"),
    ("pants", "bottoms", "Pantalon"),
    ("shorts", "bottoms", "Short"),
    ("skirt", "bottoms", "Jupe"),
    ("chinos", "bottoms", "Chinos"),
    ("cargo-pants", "bottoms", "Cargo"),
    ("joggers", "bottoms", "Jogging"),
    ("leggings", "bottoms", "Leggings"),
    ("culottes", "bottoms", "Jupe-culotte"),
    ("bermuda", "bottoms", "Bermuda"),
    ("dress-pants", "bottoms", "Pantalon habillé"),
    ("overalls", "bottoms", "Salopette"),
    # Outerwear
    ("jacket", "outerwear", "Veste"),
    ("coat", "outerwear", "Manteau"),
    ("blazer", "outerwear", "Blazer"),
    ("bomber", "outerwear", "Bomber"),
    ("parka", "outerwear", "Parka"),
    ("puffer", "outerwear", "Doudoune"),
    ("trench", "outerwear", "Trench"),
    ("windbreaker", "outerwear", "Coupe-vent"),
    ("raincoat", "outerwear", "Imperméable"),
    ("fleece", "outerwear", "Polaire"),
    ("vest", "outerwear", "Gilet"),
    ("cape", "outerwear", "Cape"),
    ("poncho", "outerwear", "Poncho"),
    ("kimono", "outerwear", "Kimono"),
    # Dresses & Jumpsuits
    ("dress", "dresses-jumpsuits", "Robe"),
    ("jumpsuit", "dresses-jumpsuits", "Combinaison"),
    ("romper", "dresses-jumpsuits", "Combishort"),
    ("bodysuit", "dresses-jumpsuits", "Body"),
    ("bustier", "dresses-jumpsuits", "Bustier"),
    ("corset", "dresses-jumpsuits", "Corset"),
    # Sportswear
    ("tracksuit", "sportswear", "Survêtement"),
    ("sports-jersey", "sportswear", "Maillot de sport"),
    ("sports-shorts", "sportswear", "Short de sport"),
    ("sports-leggings", "sportswear", "Legging de sport"),
    ("sports-bra", "sportswear", "Brassière de sport"),
    ("sports-top", "sportswear", "Haut de sport"),
    ("swimsuit", "sportswear", "Maillot de bain"),
    ("bikini", "sportswear", "Bikini"),
    # Formalwear
    ("suit", "formalwear", "Costume"),
    ("tuxedo", "formalwear", "Smoking"),
    ("suit-vest", "formalwear", "Gilet de costume"),
    ("womens-suit", "formalwear", "Tailleur"),
]

SIZES_DATA = [
    "XXS", "XS", "S", "M", "L", "XL", "XXL", "3XL", "4XL", "one-size",
    # Waist sizes
    "W24", "W26", "W28", "W30", "W32", "W34", "W36", "W38", "W40", "W42", "W44", "W46", "W52",
    # Waist x Length combinations
    "W22/L28", "W22/L32",
    "W24/L26", "W24/L28", "W24/L30", "W24/L32", "W24/L34", "W24/L36",
    "W26/L26", "W26/L28", "W26/L30", "W26/L32", "W26/L34", "W26/L36", "W26/L38",
    "W28/L14", "W28/L24", "W28/L26", "W28/L28", "W28/L30", "W28/L32", "W28/L34", "W28/L36", "W28/L38",
    "W30/L22", "W30/L24", "W30/L26", "W30/L28", "W30/L30", "W30/L32", "W30/L34", "W30/L36", "W30/L38",
    "W32/L22", "W32/L26", "W32/L28", "W32/L30", "W32/L32", "W32/L34", "W32/L36", "W32/L38",
    "W34/L26", "W34/L28", "W34/L30", "W34/L32", "W34/L34", "W34/L36", "W34/L38", "W34/L40",
    "W36/L26", "W36/L28", "W36/L30", "W36/L32", "W36/L34", "W36/L36",
    "W38/L26", "W38/L28", "W38/L30", "W38/L32", "W38/L34", "W38/L36", "W38/L38",
    "W40/L28", "W40/L30", "W40/L32", "W40/L34", "W40/L36", "W40/L38",
    "W42/L26", "W42/L28", "W42/L30", "W42/L32", "W42/L34", "W42/L36",
    "W44/L26", "W44/L30", "W44/L32", "W44/L34",
    "W46/L28", "W46/L30", "W46/L32", "W46/L34",
    "W48/L30", "W48/L32", "W48/L34",
    "W50/L32", "W50/L34",
    "W52/L32", "W52/L36",
    "W54/L32", "W56/L32",
    # Special sizes
    "W11/L1", "W11/L11", "W111/L11",
]

FITS_DATA = [
    ("athletic", "Athlétique"),
    ("baggy", "Baggy"),
    ("bootcut", "Bootcut"),
    ("flare", "Évasé"),
    ("loose", "Ample"),
    ("oversized", "Oversize"),
    ("regular", "Regular"),
    ("relaxed", "Décontracté"),
    ("skinny", "Skinny"),
    ("slim", "Slim"),
    ("straight", "Droit"),
]

MATERIALS_DATA = [
    ("acrylic", "Acrylique"),
    ("cashmere", "Cachemire"),
    ("corduroy", "Velours côtelé"),
    ("cotton", "Coton"),
    ("denim", "Denim"),
    ("elastane", "Élasthanne"),
    ("flannel", "Flanelle"),
    ("fleece", "Polaire"),
    ("hemp", "Chanvre"),
    ("leather", "Cuir"),
    ("linen", "Lin"),
    ("lyocell", "Lyocell"),
    ("modal", "Modal"),
    ("nylon", "Nylon"),
    ("polyester", "Polyester"),
    ("rayon", "Rayonne"),
    ("satin", "Satin"),
    ("silk", "Soie"),
    ("spandex", "Spandex"),
    ("suede", "Daim"),
    ("tweed", "Tweed"),
    ("velvet", "Velours"),
    ("viscose", "Viscose"),
    ("wool", "Laine"),
]

GENDERS_DATA = [
    ("men", "Homme"),
    ("women", "Femme"),
    ("unisex", "Unisexe"),
    ("boys", "Garçon"),
    ("girls", "Fille"),
]


def upgrade() -> None:
    """Complete partial attribute tables with missing data."""
    connection = op.get_bind()

    # ===== 1. BRANDS =====
    print("  📦 Completing brands...")
    inserted = 0
    for name in BRANDS_DATA:
        result = connection.execute(
            sa.text("""
                INSERT INTO product_attributes.brands (name, monitoring)
                VALUES (:name, false)
                ON CONFLICT (name) DO NOTHING
                RETURNING name
            """),
            {"name": name}
        )
        if result.rowcount > 0:
            inserted += 1
    print(f"  ✅ Added {inserted} new brands (total: {len(BRANDS_DATA)})")

    # ===== 2. CATEGORIES =====
    print("  📦 Completing categories...")
    inserted = 0
    for name_en, parent, name_fr in CATEGORIES_DATA:
        result = connection.execute(
            sa.text("""
                INSERT INTO product_attributes.categories (name_en, parent_category, name_fr)
                VALUES (:name_en, :parent, :name_fr)
                ON CONFLICT (name_en) DO UPDATE SET
                    parent_category = COALESCE(EXCLUDED.parent_category, product_attributes.categories.parent_category),
                    name_fr = COALESCE(EXCLUDED.name_fr, product_attributes.categories.name_fr)
                RETURNING name_en
            """),
            {"name_en": name_en, "parent": parent, "name_fr": name_fr}
        )
        if result.rowcount > 0:
            inserted += 1
    print(f"  ✅ Added/updated {inserted} categories (total: {len(CATEGORIES_DATA)})")

    # ===== 3. SIZES =====
    print("  📦 Completing sizes...")
    inserted = 0
    for name in SIZES_DATA:
        result = connection.execute(
            sa.text("""
                INSERT INTO product_attributes.sizes (name_en, name_fr)
                VALUES (:name, :name)
                ON CONFLICT (name_en) DO NOTHING
                RETURNING name_en
            """),
            {"name": name}
        )
        if result.rowcount > 0:
            inserted += 1
    print(f"  ✅ Added {inserted} new sizes (total: {len(SIZES_DATA)})")

    # ===== 4. FITS =====
    print("  📦 Completing fits...")
    inserted = 0
    for name_en, name_fr in FITS_DATA:
        result = connection.execute(
            sa.text("""
                INSERT INTO product_attributes.fits (name_en, name_fr)
                VALUES (:name_en, :name_fr)
                ON CONFLICT (name_en) DO UPDATE SET
                    name_fr = COALESCE(EXCLUDED.name_fr, product_attributes.fits.name_fr)
                RETURNING name_en
            """),
            {"name_en": name_en, "name_fr": name_fr}
        )
        if result.rowcount > 0:
            inserted += 1
    print(f"  ✅ Added/updated {inserted} fits (total: {len(FITS_DATA)})")

    # ===== 5. MATERIALS =====
    print("  📦 Completing materials...")
    inserted = 0
    for name_en, name_fr in MATERIALS_DATA:
        result = connection.execute(
            sa.text("""
                INSERT INTO product_attributes.materials (name_en, name_fr)
                VALUES (:name_en, :name_fr)
                ON CONFLICT (name_en) DO UPDATE SET
                    name_fr = COALESCE(EXCLUDED.name_fr, product_attributes.materials.name_fr)
                RETURNING name_en
            """),
            {"name_en": name_en, "name_fr": name_fr}
        )
        if result.rowcount > 0:
            inserted += 1
    print(f"  ✅ Added/updated {inserted} materials (total: {len(MATERIALS_DATA)})")

    # ===== 6. GENDERS (cleanup duplicates and complete) =====
    print("  📦 Completing genders...")
    # First, delete potential duplicates (case-insensitive)
    connection.execute(sa.text("""
        DELETE FROM product_attributes.genders
        WHERE name_en IN ('Men', 'Women', 'Unisex', 'Kids')
    """))
    inserted = 0
    for name_en, name_fr in GENDERS_DATA:
        result = connection.execute(
            sa.text("""
                INSERT INTO product_attributes.genders (name_en, name_fr)
                VALUES (:name_en, :name_fr)
                ON CONFLICT (name_en) DO UPDATE SET
                    name_fr = COALESCE(EXCLUDED.name_fr, product_attributes.genders.name_fr)
                RETURNING name_en
            """),
            {"name_en": name_en, "name_fr": name_fr}
        )
        if result.rowcount > 0:
            inserted += 1
    print(f"  ✅ Added/updated {inserted} genders (total: {len(GENDERS_DATA)})")

    # Summary
    print(f"\n  🎉 Completed 6 attribute tables")


def downgrade() -> None:
    """
    Note: This migration adds data, downgrade would need to track
    which specific records were added. For safety, we don't delete
    existing data on downgrade.
    """
    print("  ⚠️  Downgrade: No data deleted (safety measure)")
    pass
