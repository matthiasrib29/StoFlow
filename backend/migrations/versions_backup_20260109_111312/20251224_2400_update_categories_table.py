"""Update categories table with complete hierarchy

Revision ID: 20251224_2400
Revises: 20251224_2300
Create Date: 2025-12-24

Replaces all categories with the correct hierarchy and genders.
"""

from alembic import op

revision = "20251224_2400"
down_revision = "20251224_2300"
branch_labels = None
depends_on = None


CATEGORIES = [
    # (name_en, parent_category, name_fr, genders)
    ("clothing", None, "Vêtements", ["men", "women", "boys", "girls"]),
    ("tops", "clothing", "Hauts", ["men", "women", "boys", "girls"]),
    ("t-shirt", "tops", "T-shirt", ["men", "women", "boys", "girls"]),
    ("tank-top", "tops", "Débardeur", ["men", "women", "boys", "girls"]),
    ("shirt", "tops", "Chemise", ["men", "women", "boys", "girls"]),
    ("blouse", "tops", "Blouse", ["women", "girls"]),
    ("top", "tops", "Top", ["women", "girls"]),
    ("bodysuit", "tops", "Body", ["women"]),
    ("corset", "tops", "Corset", ["women"]),
    ("bustier", "tops", "Bustier", ["women"]),
    ("camisole", "tops", "Caraco", ["women"]),
    ("crop-top", "tops", "Crop top", ["women", "girls"]),
    ("polo", "tops", "Polo", ["men", "women", "boys", "girls"]),
    ("sweater", "tops", "Pull", ["men", "women", "boys", "girls"]),
    ("cardigan", "tops", "Cardigan", ["men", "women", "boys", "girls"]),
    ("sweatshirt", "tops", "Sweat", ["men", "women", "boys", "girls"]),
    ("hoodie", "tops", "Hoodie", ["men", "women", "boys", "girls"]),
    ("fleece", "tops", "Polaire", ["men", "women", "boys", "girls"]),
    ("overshirt", "tops", "Surchemise", ["men", "women"]),
    ("bottoms", "clothing", "Bas", ["men", "women", "boys", "girls"]),
    ("pants", "bottoms", "Pantalon", ["men", "women", "boys", "girls"]),
    ("jeans", "bottoms", "Jean", ["men", "women", "boys", "girls"]),
    ("chinos", "bottoms", "Chino", ["men", "women", "boys", "girls"]),
    ("joggers", "bottoms", "Jogging", ["men", "women", "boys", "girls"]),
    ("cargo-pants", "bottoms", "Pantalon cargo", ["men", "women", "boys", "girls"]),
    ("dress-pants", "bottoms", "Pantalon habillé", ["men", "women", "boys", "girls"]),
    ("shorts", "bottoms", "Short", ["men", "women", "boys", "girls"]),
    ("bermuda", "bottoms", "Bermuda", ["men", "women", "boys", "girls"]),
    ("skirt", "bottoms", "Jupe", ["women", "girls"]),
    ("leggings", "bottoms", "Legging", ["women", "girls", "boys"]),
    ("culottes", "bottoms", "Jupe-culotte", ["women", "girls"]),
    ("outerwear", "clothing", "Vêtements d'extérieur", ["men", "women", "boys", "girls"]),
    ("jacket", "outerwear", "Veste", ["men", "women", "boys", "girls"]),
    ("bomber", "outerwear", "Blouson", ["men", "women", "boys", "girls"]),
    ("puffer", "outerwear", "Doudoune", ["men", "women", "boys", "girls"]),
    ("coat", "outerwear", "Manteau", ["men", "women", "boys", "girls"]),
    ("trench", "outerwear", "Trench", ["men", "women", "boys", "girls"]),
    ("parka", "outerwear", "Parka", ["men", "women", "boys", "girls"]),
    ("raincoat", "outerwear", "Imperméable", ["men", "women", "boys", "girls"]),
    ("windbreaker", "outerwear", "Coupe-vent", ["men", "women", "boys", "girls"]),
    ("blazer", "outerwear", "Blazer", ["men", "women", "boys", "girls"]),
    ("vest", "outerwear", "Gilet", ["men", "women", "boys", "girls"]),
    ("half-zip", "outerwear", "Demi-zip", ["men", "women", "boys", "girls"]),
    ("cape", "outerwear", "Cape", ["women", "girls"]),
    ("poncho", "outerwear", "Poncho", ["men", "women", "boys", "girls"]),
    ("kimono", "outerwear", "Kimono", ["women"]),
    ("dresses-jumpsuits", "clothing", "Robes et combinaisons", ["women", "girls"]),
    ("dress", "dresses-jumpsuits", "Robe", ["women", "girls"]),
    ("jumpsuit", "dresses-jumpsuits", "Combinaison", ["men", "women", "boys", "girls"]),
    ("romper", "dresses-jumpsuits", "Combishort", ["women", "girls"]),
    ("overalls", "dresses-jumpsuits", "Salopette", ["men", "women", "boys", "girls"]),
    ("formalwear", "clothing", "Costumes et tenues habillées", ["men", "women", "boys", "girls"]),
    ("suit", "formalwear", "Costume", ["men", "women"]),
    ("tuxedo", "formalwear", "Smoking", ["men"]),
    ("womens-suit", "formalwear", "Tailleur", ["women"]),
    ("suit-vest", "formalwear", "Gilet de costume", ["men", "boys", "girls"]),
    ("sportswear", "clothing", "Vêtements de sport", ["men", "women", "boys", "girls"]),
    ("sports-bra", "sportswear", "Brassière de sport", ["women", "girls"]),
    ("sports-top", "sportswear", "T-shirt de sport", ["men", "women", "boys", "girls"]),
    ("sports-jersey", "sportswear", "Maillot de sport", ["men", "women", "boys", "girls"]),
    ("sports-shorts", "sportswear", "Short de sport", ["men", "women", "boys", "girls"]),
    ("sports-leggings", "sportswear", "Legging de sport", ["women", "girls"]),
    ("tracksuit", "sportswear", "Survêtement", ["men", "women", "boys", "girls"]),
    ("swimsuit", "sportswear", "Maillot de bain", ["men", "women", "boys", "girls"]),
    ("bikini", "sportswear", "Bikini", ["women", "girls"]),
]


def upgrade() -> None:
    # Clear existing categories
    op.execute("DELETE FROM product_attributes.categories")
    print("  ✓ Cleared existing categories")

    # Insert new categories
    for name_en, parent, name_fr, genders in CATEGORIES:
        genders_array = "ARRAY[" + ", ".join(f"'{g}'" for g in genders) + "]::VARCHAR[]"
        parent_value = f"'{parent}'" if parent else "NULL"
        # Escape single quotes in French names
        name_fr_escaped = name_fr.replace("'", "''")

        sql = f"""
            INSERT INTO product_attributes.categories (name_en, parent_category, name_fr, genders)
            VALUES ('{name_en}', {parent_value}, '{name_fr_escaped}', {genders_array})
        """
        op.execute(sql)
    
    print(f"  ✓ Inserted {len(CATEGORIES)} categories")


def downgrade() -> None:
    # Not reverting - data migration
    pass
