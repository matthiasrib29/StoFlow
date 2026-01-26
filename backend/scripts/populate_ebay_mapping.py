"""
Populate eBay category mapping.

Inserts the mapping between StoFlow categories (category + gender) and
eBay category IDs into the ebay.mapping table.

Usage:
    python scripts/populate_ebay_mapping.py

Author: Claude
Date: 2026-01-23
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from shared.database import engine


# Mapping data: (my_category, my_gender, ebay_category_path)
MAPPING_DATA = [
    ("bermuda", "men", "Men > Men's Clothing > Shorts"),
    ("bermuda", "women", "Women > Women's Clothing > Shorts"),
    ("bermuda", "boys", "Kids > Boys > Boys' Clothing (2-16 Years) > Shorts"),
    ("bermuda", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Shorts"),
    ("bikini", "women", "Women > Women's Clothing > Swimwear"),
    ("bikini", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Swimwear"),
    ("blazer", "men", "Men > Men's Clothing > Suits & Tailoring"),
    ("blazer", "women", "Women > Women's Clothing > Suits & Suit Separates"),
    ("blazer", "boys", "Kids > Boys > Boys' Clothing (2-16 Years) > Suits"),
    ("blazer", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Outerwear"),
    ("blouse", "women", "Women > Women's Clothing > Tops & Shirts"),
    ("blouse", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > T-Shirts, Tops & Shirts"),
    ("body suit", "women", "Women > Women's Clothing > Lingerie & Nightwear > Bodysuits"),
    ("bomber", "men", "Men > Men's Clothing > Coats, Jackets & Waistcoats"),
    ("bomber", "women", "Women > Women's Clothing > Coats, Jackets & Waistcoats"),
    ("bomber", "boys", "Kids > Boys > Boys' Clothing (2-16 Years) > Outerwear"),
    ("bomber", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Outerwear"),
    ("bottoms", "men", "Men > Men's Clothing > Trousers"),
    ("bottoms", "women", "Women > Women's Clothing > Trousers"),
    ("bottoms", "boys", "Kids > Boys > Boys' Clothing (2-16 Years) > Trousers"),
    ("bottoms", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Trousers"),
    ("bustier", "women", "Women > Women's Clothing > Lingerie & Nightwear > Basques & Corsets"),
    ("camisole", "women", "Women > Women's Clothing > Lingerie & Nightwear > Camisoles & Vests"),
    ("cape", "women", "Women > Women's Clothing > Coats, Jackets & Waistcoats"),
    ("cape", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Outerwear"),
    ("cardigan", "men", "Men > Men's Clothing > Jumpers & Cardigans"),
    ("cardigan", "women", "Women > Women's Clothing > Jumpers & Cardigans"),
    ("cardigan", "boys", "Kids > Boys > Boys' Clothing (2-16 Years) > Jumpers & Cardigans"),
    ("cardigan", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Jumpers & Cardigans"),
    ("cargo-pants", "men", "Men > Men's Clothing > Trousers"),
    ("cargo-pants", "women", "Women > Women's Clothing > Trousers"),
    ("cargo-pants", "boys", "Kids > Boys > Boys' Clothing (2-16 Years) > Trousers"),
    ("cargo-pants", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Trousers"),
    ("chinos", "men", "Men > Men's Clothing > Trousers"),
    ("chinos", "women", "Women > Women's Clothing > Trousers"),
    ("chinos", "boys", "Kids > Boys > Boys' Clothing (2-16 Years) > Trousers"),
    ("chinos", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Trousers"),
    ("clothing", "men", "Men > Men's Clothing"),
    ("clothing", "women", "Women > Women's Clothing"),
    ("clothing", "boys", "Kids > Boys > Boys' Clothing (2-16 Years)"),
    ("clothing", "girls", "Kids > Girls > Girls' Clothing (2-16 Years)"),
    ("coat", "men", "Men > Men's Clothing > Coats, Jackets & Waistcoats"),
    ("coat", "women", "Women > Women's Clothing > Coats, Jackets & Waistcoats"),
    ("coat", "boys", "Kids > Boys > Boys' Clothing (2-16 Years) > Outerwear"),
    ("coat", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Outerwear"),
    ("corset", "women", "Women > Women's Clothing > Lingerie & Nightwear > Basques & Corsets"),
    ("crop-top", "women", "Women > Women's Clothing > Tops & Shirts"),
    ("crop-top", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > T-Shirts, Tops & Shirts"),
    ("culottes", "women", "Women > Women's Clothing > Trousers"),
    ("culottes", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Trousers"),
    ("dress", "women", "Women > Women's Clothing > Dresses"),
    ("dress", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Dresses"),
    ("dress-pants", "men", "Men > Men's Clothing > Suits & Tailoring"),
    ("dress-pants", "women", "Women > Women's Clothing > Suits & Suit Separates"),
    ("dress-pants", "boys", "Kids > Boys > Boys' Clothing (2-16 Years) > Suits"),
    ("dress-pants", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Trousers"),
    ("fleece jacket", "men", "Men > Men's Clothing > Coats, Jackets & Waistcoats"),
    ("fleece jacket", "women", "Women > Women's Clothing > Coats, Jackets & Waistcoats"),
    ("fleece jacket", "boys", "Kids > Boys > Boys' Clothing (2-16 Years) > Outerwear"),
    ("fleece jacket", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Outerwear"),
    ("formalwear", "men", "Men > Men's Clothing > Suits & Tailoring"),
    ("formalwear", "women", "Women > Women's Clothing > Suits & Suit Separates"),
    ("formalwear", "boys", "Kids > Boys > Boys' Clothing (2-16 Years) > Suits"),
    ("formalwear", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Dresses"),
    ("half-zip", "men", "Men > Men's Clothing > Jumpers & Cardigans"),
    ("half-zip", "women", "Women > Women's Clothing > Jumpers & Cardigans"),
    ("half-zip", "boys", "Kids > Boys > Boys' Clothing (2-16 Years) > Jumpers & Cardigans"),
    ("half-zip", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Jumpers & Cardigans"),
    ("hoodie", "men", "Men > Men's Clothing > Activewear > Hoodies & Sweatshirts"),
    ("hoodie", "women", "Women > Women's Clothing > Activewear > Hoodies & Sweatshirts"),
    ("hoodie", "boys", "Kids > Boys > Boys' Clothing (2-16 Years) > Hoodies"),
    ("hoodie", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Hoodies"),
    ("jacket", "men", "Men > Men's Clothing > Coats, Jackets & Waistcoats"),
    ("jacket", "women", "Women > Women's Clothing > Coats, Jackets & Waistcoats"),
    ("jacket", "boys", "Kids > Boys > Boys' Clothing (2-16 Years) > Outerwear"),
    ("jacket", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Outerwear"),
    ("jeans", "men", "Men > Men's Clothing > Jeans"),
    ("jeans", "women", "Women > Women's Clothing > Jeans"),
    ("jeans", "boys", "Kids > Boys > Boys' Clothing (2-16 Years) > Jeans"),
    ("jeans", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Jeans"),
    ("joggers", "men", "Men > Men's Clothing > Activewear > Activewear Trousers"),
    ("joggers", "women", "Women > Women's Clothing > Activewear > Activewear Trousers"),
    ("joggers", "boys", "Kids > Boys > Boys' Clothing (2-16 Years) > Activewear > Activewear Trousers"),
    ("joggers", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Activewear > Activewear Trousers"),
    ("jump suit", "men", "Men > Men's Clothing > Trousers"),
    ("jump suit", "women", "Women > Women's Clothing > Jumpsuits & Playsuits"),
    ("jump suit", "boys", "Kids > Boys > Boys' Clothing (2-16 Years) > Outfits & Sets"),
    ("jump suit", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Jumpsuits & Playsuits"),
    ("kimono", "women", "Women > Women's Clothing > Tops & Shirts"),
    ("leggings", "women", "Women > Women's Clothing > Leggings"),
    ("leggings", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Leggings"),
    ("leggings", "boys", "Kids > Boys > Boys' Clothing (2-16 Years) > Activewear > Activewear Trousers"),
    ("outerwear", "men", "Men > Men's Clothing > Coats, Jackets & Waistcoats"),
    ("outerwear", "women", "Women > Women's Clothing > Coats, Jackets & Waistcoats"),
    ("outerwear", "boys", "Kids > Boys > Boys' Clothing (2-16 Years) > Outerwear"),
    ("outerwear", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Outerwear"),
    ("overalls", "men", "Men > Men's Clothing > Trousers"),
    ("overalls", "women", "Women > Women's Clothing > Jumpsuits & Playsuits"),
    ("overalls", "boys", "Kids > Boys > Boys' Clothing (2-16 Years) > Trousers"),
    ("overalls", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Jumpsuits & Playsuits"),
    ("overshirt", "men", "Men > Men's Clothing > Shirts & Tops > Casual Shirts & Tops"),
    ("overshirt", "women", "Women > Women's Clothing > Tops & Shirts"),
    ("pants", "men", "Men > Men's Clothing > Trousers"),
    ("pants", "women", "Women > Women's Clothing > Trousers"),
    ("pants", "boys", "Kids > Boys > Boys' Clothing (2-16 Years) > Trousers"),
    ("pants", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Trousers"),
    ("parka", "men", "Men > Men's Clothing > Coats, Jackets & Waistcoats"),
    ("parka", "women", "Women > Women's Clothing > Coats, Jackets & Waistcoats"),
    ("parka", "boys", "Kids > Boys > Boys' Clothing (2-16 Years) > Outerwear"),
    ("parka", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Outerwear"),
    ("polo", "men", "Men > Men's Clothing > Shirts & Tops > Polos"),
    ("polo", "women", "Women > Women's Clothing > Tops & Shirts"),
    ("polo", "boys", "Kids > Boys > Boys' Clothing (2-16 Years) > T-Shirts, Tops & Shirts"),
    ("polo", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > T-Shirts, Tops & Shirts"),
    ("poncho", "men", "Men > Men's Clothing > Coats, Jackets & Waistcoats"),
    ("poncho", "women", "Women > Women's Clothing > Coats, Jackets & Waistcoats"),
    ("poncho", "boys", "Kids > Boys > Boys' Clothing (2-16 Years) > Outerwear"),
    ("poncho", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Outerwear"),
    ("puffer", "men", "Men > Men's Clothing > Coats, Jackets & Waistcoats"),
    ("puffer", "women", "Women > Women's Clothing > Coats, Jackets & Waistcoats"),
    ("puffer", "boys", "Kids > Boys > Boys' Clothing (2-16 Years) > Outerwear"),
    ("puffer", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Outerwear"),
    ("raincoat", "men", "Men > Men's Clothing > Coats, Jackets & Waistcoats"),
    ("raincoat", "women", "Women > Women's Clothing > Coats, Jackets & Waistcoats"),
    ("raincoat", "boys", "Kids > Boys > Boys' Clothing (2-16 Years) > Outerwear"),
    ("raincoat", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Outerwear"),
    ("romper", "women", "Women > Women's Clothing > Jumpsuits & Playsuits"),
    ("romper", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Jumpsuits & Playsuits"),
    ("shirt", "men", "Men > Men's Clothing > Shirts & Tops > Casual Shirts & Tops"),
    ("shirt", "women", "Women > Women's Clothing > Tops & Shirts"),
    ("shirt", "boys", "Kids > Boys > Boys' Clothing (2-16 Years) > T-Shirts, Tops & Shirts"),
    ("shirt", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > T-Shirts, Tops & Shirts"),
    ("shorts", "men", "Men > Men's Clothing > Shorts"),
    ("shorts", "women", "Women > Women's Clothing > Shorts"),
    ("shorts", "boys", "Kids > Boys > Boys' Clothing (2-16 Years) > Shorts"),
    ("shorts", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Shorts"),
    ("skirt", "women", "Women > Women's Clothing > Skirts"),
    ("skirt", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Skirts & Skorts"),
    ("sports-bra", "women", "Women > Women's Clothing > Activewear > Sports Bras"),
    ("sports-bra", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Activewear > Activewear Tops"),
    ("sports-jersey", "men", "Men > Men's Clothing > Activewear > Activewear Tops"),
    ("sports-jersey", "women", "Women > Women's Clothing > Activewear > Activewear Tops"),
    ("sports-jersey", "boys", "Kids > Boys > Boys' Clothing (2-16 Years) > Activewear > Activewear Tops"),
    ("sports-jersey", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Activewear > Activewear Tops"),
    ("sports-leggings", "women", "Women > Women's Clothing > Activewear > Activewear Trousers"),
    ("sports-leggings", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Activewear > Activewear Trousers"),
    ("sports-shorts", "men", "Men > Men's Clothing > Activewear > Activewear Shorts"),
    ("sports-shorts", "women", "Women > Women's Clothing > Activewear > Activewear Shorts"),
    ("sports-shorts", "boys", "Kids > Boys > Boys' Clothing (2-16 Years) > Activewear > Activewear Shorts"),
    ("sports-shorts", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Activewear > Activewear Shorts"),
    ("sports-top", "men", "Men > Men's Clothing > Activewear > Activewear Tops"),
    ("sports-top", "women", "Women > Women's Clothing > Activewear > Activewear Tops"),
    ("sports-top", "boys", "Kids > Boys > Boys' Clothing (2-16 Years) > Activewear > Activewear Tops"),
    ("sports-top", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Activewear > Activewear Tops"),
    ("sportswear", "men", "Men > Men's Clothing > Activewear"),
    ("sportswear", "women", "Women > Women's Clothing > Activewear"),
    ("sportswear", "boys", "Kids > Boys > Boys' Clothing (2-16 Years) > Activewear"),
    ("sportswear", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Activewear"),
    ("suit", "men", "Men > Men's Clothing > Suits & Tailoring"),
    ("suit", "women", "Women > Women's Clothing > Suits & Suit Separates"),
    ("sweater", "men", "Men > Men's Clothing > Jumpers & Cardigans"),
    ("sweater", "women", "Women > Women's Clothing > Jumpers & Cardigans"),
    ("sweater", "boys", "Kids > Boys > Boys' Clothing (2-16 Years) > Jumpers & Cardigans"),
    ("sweater", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Jumpers & Cardigans"),
    ("sweatshirt", "men", "Men > Men's Clothing > Activewear > Hoodies & Sweatshirts"),
    ("sweatshirt", "women", "Women > Women's Clothing > Activewear > Hoodies & Sweatshirts"),
    ("sweatshirt", "boys", "Kids > Boys > Boys' Clothing (2-16 Years) > Jumpers & Cardigans"),
    ("sweatshirt", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Activewear > Hoodies & Sweatshirts"),
    ("swim suit", "men", "Men > Men's Clothing > Swimwear"),
    ("swim suit", "women", "Women > Women's Clothing > Swimwear"),
    ("swim suit", "boys", "Kids > Boys > Boys' Clothing (2-16 Years) > Swimwear"),
    ("swim suit", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Swimwear"),
    ("t-shirt", "men", "Men > Men's Clothing > Shirts & Tops > T-Shirts"),
    ("t-shirt", "women", "Women > Women's Clothing > Tops & Shirts"),
    ("t-shirt", "boys", "Kids > Boys > Boys' Clothing (2-16 Years) > T-Shirts, Tops & Shirts"),
    ("t-shirt", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > T-Shirts, Tops & Shirts"),
    ("tank-top", "men", "Men > Men's Clothing > Shirts & Tops > Casual Shirts & Tops"),
    ("tank-top", "women", "Women > Women's Clothing > Tops & Shirts"),
    ("tank-top", "boys", "Kids > Boys > Boys' Clothing (2-16 Years) > T-Shirts, Tops & Shirts"),
    ("tank-top", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > T-Shirts, Tops & Shirts"),
    ("top", "women", "Women > Women's Clothing > Tops & Shirts"),
    ("top", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > T-Shirts, Tops & Shirts"),
    ("tops", "men", "Men > Men's Clothing > Shirts & Tops"),
    ("tops", "women", "Women > Women's Clothing > Tops & Shirts"),
    ("tops", "boys", "Kids > Boys > Boys' Clothing (2-16 Years) > T-Shirts, Tops & Shirts"),
    ("tops", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > T-Shirts, Tops & Shirts"),
    ("track suit", "men", "Men > Men's Clothing > Activewear > Tracksuits & Sets"),
    ("track suit", "women", "Women > Women's Clothing > Activewear > Tracksuits & Sets"),
    ("track suit", "boys", "Kids > Boys > Boys' Clothing (2-16 Years) > Activewear > Tracksuits & Sets"),
    ("track suit", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Activewear > Tracksuits & Sets"),
    ("trench", "men", "Men > Men's Clothing > Coats, Jackets & Waistcoats"),
    ("trench", "women", "Women > Women's Clothing > Coats, Jackets & Waistcoats"),
    ("trench", "boys", "Kids > Boys > Boys' Clothing (2-16 Years) > Outerwear"),
    ("trench", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Outerwear"),
    ("tuxedo", "men", "Men > Men's Clothing > Suits & Tailoring"),
    ("vest", "men", "Men > Men's Clothing > Underwear"),
    ("vest", "women", "Women > Women's Clothing > Lingerie & Nightwear > Camisoles & Vests"),
    ("vest", "boys", "Kids > Boys > Boys' Clothing (2-16 Years) > Underwear"),
    ("vest", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Underwear"),
    ("waistcoat", "men", "Men > Men's Clothing > Coats, Jackets & Waistcoats"),
    ("waistcoat", "boys", "Kids > Boys > Boys' Clothing (2-16 Years) > Suits"),
    ("waistcoat", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Outerwear"),
    ("windbreaker", "men", "Men > Men's Clothing > Coats, Jackets & Waistcoats"),
    ("windbreaker", "women", "Women > Women's Clothing > Coats, Jackets & Waistcoats"),
    ("windbreaker", "boys", "Kids > Boys > Boys' Clothing (2-16 Years) > Outerwear"),
    ("windbreaker", "girls", "Kids > Girls > Girls' Clothing (2-16 Years) > Outerwear"),
]

# Default categories for reverse mapping (eBay → StoFlow).
# For each (ebay_category_id, gender) group with multiple mappings,
# the most generic StoFlow category is chosen as default.
# Categories that are alone in their group are auto-detected as default.
REVERSE_DEFAULTS = {
    # Men
    ("jacket", "men"),       # Coats, Jackets & Waistcoats
    ("pants", "men"),        # Trousers
    ("shorts", "men"),       # Shorts
    ("sweater", "men"),      # Jumpers & Cardigans
    ("hoodie", "men"),       # Hoodies & Sweatshirts
    ("shirt", "men"),        # Casual Shirts & Tops
    ("suit", "men"),         # Suits & Tailoring
    ("sports-top", "men"),   # Activewear Tops
    # Women
    ("jacket", "women"),     # Coats, Jackets & Waistcoats
    ("pants", "women"),      # Trousers
    ("shorts", "women"),     # Shorts
    ("sweater", "women"),    # Jumpers & Cardigans
    ("hoodie", "women"),     # Hoodies & Sweatshirts
    ("top", "women"),        # Tops & Shirts
    ("suit", "women"),       # Suits & Suit Separates
    ("jump suit", "women"),  # Jumpsuits & Playsuits
    ("corset", "women"),     # Basques & Corsets
    ("camisole", "women"),   # Camisoles & Vests
    ("swim suit", "women"),  # Swimwear
    ("sports-top", "women"), # Activewear Tops
    ("joggers", "women"),    # Activewear Trousers
    # Boys
    ("jacket", "boys"),      # Outerwear
    ("pants", "boys"),       # Trousers
    ("shorts", "boys"),      # Shorts
    ("sweater", "boys"),     # Jumpers & Cardigans
    ("t-shirt", "boys"),     # T-Shirts, Tops & Shirts
    ("formalwear", "boys"),  # Suits
    ("sports-top", "boys"),  # Activewear Tops
    ("joggers", "boys"),     # Activewear Trousers
    # Girls
    ("jacket", "girls"),     # Outerwear
    ("pants", "girls"),      # Trousers
    ("shorts", "girls"),     # Shorts
    ("sweater", "girls"),    # Jumpers & Cardigans
    ("t-shirt", "girls"),    # T-Shirts, Tops & Shirts
    ("dress", "girls"),      # Dresses
    ("jump suit", "girls"),  # Jumpsuits & Playsuits
    ("swim suit", "girls"),  # Swimwear
    ("sports-top", "girls"), # Activewear Tops
    ("joggers", "girls"),    # Activewear Trousers
}


def main():
    print("=" * 60)
    print("POPULATE EBAY MAPPING")
    print("=" * 60)

    # Load path -> category_id lookup from DB
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT path, category_id FROM ebay.categories")).fetchall()
        path_to_id = {r[0]: r[1] for r in rows}

    print(f"\nLoaded {len(path_to_id)} category paths from DB")

    # Resolve paths to category IDs
    resolved = []
    errors = []
    for my_category, my_gender, ebay_path in MAPPING_DATA:
        cat_id = path_to_id.get(ebay_path)
        if cat_id:
            resolved.append((my_category, my_gender, cat_id))
        else:
            errors.append((my_category, my_gender, ebay_path))

    if errors:
        print(f"\nERROR: {len(errors)} paths not found in DB:")
        for cat, gender, path in errors:
            print(f"  {cat} / {gender} -> {path}")
        sys.exit(1)

    print(f"Resolved {len(resolved)} mappings")

    # Compute is_default for each mapping:
    # 1. Explicitly listed in REVERSE_DEFAULTS
    # 2. Auto-detected: only mapping for that (ebay_category_id, gender) group
    from collections import Counter
    group_counts = Counter((cat_id, gender) for _, gender, cat_id in resolved)
    singles = {k for k, v in group_counts.items() if v == 1}

    resolved_with_default = []
    for my_category, my_gender, ebay_category_id in resolved:
        is_default = (
            (my_category, my_gender) in REVERSE_DEFAULTS
            or (ebay_category_id, my_gender) in singles
        )
        resolved_with_default.append((my_category, my_gender, ebay_category_id, is_default))

    default_count = sum(1 for _, _, _, d in resolved_with_default if d)
    print(f"Defaults: {default_count} (explicit + auto-detected singles)")

    # Upsert into ebay.mapping
    print("\nUpserting to ebay.mapping...")
    count = 0
    with engine.connect() as conn:
        # Clear existing data
        conn.execute(text("TRUNCATE TABLE ebay.mapping RESTART IDENTITY"))
        conn.commit()

        for my_category, my_gender, ebay_category_id, is_default in resolved_with_default:
            conn.execute(
                text("""
                    INSERT INTO ebay.mapping (my_category, my_gender, ebay_category_id, is_default)
                    VALUES (:my_category, :my_gender, :ebay_category_id, :is_default)
                    ON CONFLICT (my_category, my_gender) DO UPDATE SET
                        ebay_category_id = EXCLUDED.ebay_category_id,
                        is_default = EXCLUDED.is_default
                """),
                {
                    "my_category": my_category,
                    "my_gender": my_gender,
                    "ebay_category_id": ebay_category_id,
                    "is_default": is_default,
                },
            )
            count += 1
        conn.commit()

    print(f"  Inserted {count} mappings")

    # Verify
    with engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM ebay.mapping")).scalar()
        print(f"\nVerification: {total} mappings in database")

        defaults = conn.execute(text("SELECT COUNT(*) FROM ebay.mapping WHERE is_default = true")).scalar()
        print(f"  Defaults: {defaults}, Non-defaults: {total - defaults}")

        # Stats by gender
        rows = conn.execute(text("""
            SELECT my_gender, COUNT(*) as cnt,
                   SUM(CASE WHEN is_default THEN 1 ELSE 0 END) as defaults
            FROM ebay.mapping
            GROUP BY my_gender
            ORDER BY my_gender
        """)).fetchall()
        print("\nBy gender:")
        for r in rows:
            print(f"  {r[0]}: {r[1]} mappings ({r[2]} defaults)")

    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)


if __name__ == "__main__":
    main()
