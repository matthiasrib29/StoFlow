"""
Pricing constants for group determination.

This module defines the 69 pricing groups based on the official group specification.
Groups are organized as:
- Variable groups: category with material variants (e.g., jacket_leather, jacket_wool)
- Fixed groups: single group regardless of materials (e.g., jeans, bomber, hoodie)

System Overview:
- 69 pricing groups total
- Material types: LEATHER, DENIM, WOOL_LUXURY, SILK_LUXURY, NATURAL, TECHNICAL, SYNTHETIC, FIXED
- Material priority: LEATHER > SILK_LUXURY > DENIM > WOOL_LUXURY > NATURAL > TECHNICAL > SYNTHETIC
"""

# ===== MATERIAL TYPE CATEGORIES =====

MATERIAL_LEATHER = "leather"
MATERIAL_SILK_LUXURY = "silk_luxury"
MATERIAL_DENIM = "denim"
MATERIAL_WOOL_LUXURY = "wool_luxury"
MATERIAL_NATURAL = "natural"
MATERIAL_TECHNICAL = "technical"
MATERIAL_SYNTHETIC = "synthetic"
MATERIAL_FIXED = "fixed"  # For groups that don't vary by material

# Material priority for conflict resolution (highest to lowest)
MATERIAL_PRIORITY = [
    MATERIAL_LEATHER,      # Highest: real leather, suede
    MATERIAL_SILK_LUXURY,  # Silk, satin (luxury fabrics)
    MATERIAL_DENIM,        # Denim fabric
    MATERIAL_WOOL_LUXURY,  # Wool, cashmere, tweed
    MATERIAL_NATURAL,      # Cotton, linen, hemp, flannel, corduroy
    MATERIAL_TECHNICAL,    # Nylon, fleece, technical fabrics
    MATERIAL_SYNTHETIC,    # Lowest: polyester, acrylic, viscose, rayon
]

# ===== MATERIAL MAPPINGS =====

MATERIAL_TYPE_MAPPING = {
    # === LEATHER ===
    "leather": MATERIAL_LEATHER,
    "suede": MATERIAL_LEATHER,
    "nubuck": MATERIAL_LEATHER,
    "patent leather": MATERIAL_LEATHER,

    # Faux leather is SYNTHETIC
    "faux leather": MATERIAL_SYNTHETIC,
    "vegan leather": MATERIAL_SYNTHETIC,
    "pu leather": MATERIAL_SYNTHETIC,

    # === SILK/LUXURY FABRICS ===
    "silk": MATERIAL_SILK_LUXURY,
    "satin": MATERIAL_SILK_LUXURY,
    "velvet": MATERIAL_SILK_LUXURY,

    # === DENIM ===
    "denim": MATERIAL_DENIM,

    # === WOOL/LUXURY ===
    "wool": MATERIAL_WOOL_LUXURY,
    "cashmere": MATERIAL_WOOL_LUXURY,
    "merino": MATERIAL_WOOL_LUXURY,
    "merino wool": MATERIAL_WOOL_LUXURY,
    "tweed": MATERIAL_WOOL_LUXURY,
    "alpaca": MATERIAL_WOOL_LUXURY,
    "mohair": MATERIAL_WOOL_LUXURY,
    "angora": MATERIAL_WOOL_LUXURY,

    # === NATURAL FIBERS ===
    "cotton": MATERIAL_NATURAL,
    "organic cotton": MATERIAL_NATURAL,
    "linen": MATERIAL_NATURAL,
    "hemp": MATERIAL_NATURAL,
    "flannel": MATERIAL_NATURAL,
    "corduroy": MATERIAL_NATURAL,
    "crochet": MATERIAL_NATURAL,
    "lace": MATERIAL_NATURAL,
    "bamboo": MATERIAL_NATURAL,

    # === TECHNICAL/PERFORMANCE ===
    "nylon": MATERIAL_TECHNICAL,
    "fleece": MATERIAL_TECHNICAL,
    "technical fabric": MATERIAL_TECHNICAL,
    "gore-tex": MATERIAL_TECHNICAL,
    "spandex": MATERIAL_TECHNICAL,
    "elastane": MATERIAL_TECHNICAL,
    "lycra": MATERIAL_TECHNICAL,
    "neoprene": MATERIAL_TECHNICAL,

    # === SYNTHETIC ===
    "polyester": MATERIAL_SYNTHETIC,
    "acrylic": MATERIAL_SYNTHETIC,
    "viscose": MATERIAL_SYNTHETIC,
    "rayon": MATERIAL_SYNTHETIC,
    "modal": MATERIAL_SYNTHETIC,
    "lyocell": MATERIAL_SYNTHETIC,
    "polyamide": MATERIAL_SYNTHETIC,
    "polypropylene": MATERIAL_SYNTHETIC,
}

# ===== CATEGORY TO GROUP MAPPING =====
# Maps category names to their group structure (variable or fixed)

# Variable groups: have material variants (_leather, _wool, etc.)
VARIABLE_GROUPS = {
    "jacket": ["leather", "denim", "wool", "natural", "technical", "synthetic"],
    "coat": ["leather", "wool", "natural", "technical", "synthetic"],
    "blazer": ["leather", "wool", "natural", "synthetic"],
    "pants": ["leather", "wool", "natural", "synthetic"],
    "dress-pants": ["leather", "wool", "natural", "synthetic"],  # Maps to pants_*
    "chinos": ["leather", "wool", "natural", "synthetic"],  # Maps to pants_*
    "cargo-pants": ["leather", "wool", "natural", "synthetic"],  # Maps to pants_*
    "skirt": ["leather", "denim", "wool", "natural", "synthetic"],
    "culottes": ["leather", "denim", "wool", "natural", "synthetic"],  # Maps to skirt_*
    "shirt": ["luxury", "natural", "synthetic"],  # Note: luxury = silk for shirts
    "blouse": ["luxury", "natural", "synthetic"],  # Note: luxury = silk for blouses
    "top": ["luxury", "natural", "synthetic"],  # Maps to blouse_*
    "camisole": ["luxury", "natural", "synthetic"],  # Maps to blouse_*
    "dress": ["luxury", "natural", "synthetic"],  # Note: luxury = silk for dresses
}

# Fixed groups: single group name regardless of materials
FIXED_GROUPS = {
    # Outerwear
    "bomber": "bomber",
    "puffer": "puffer",
    "parka": "parka",
    "trench": "trench",
    "windbreaker": "windbreaker",
    "raincoat": "raincoat",
    "cape": "fashion_outerwear",
    "poncho": "fashion_outerwear",
    "kimono": "fashion_outerwear",
    "vest": "vest",
    "fleece jacket": "fleece",
    "half-zip": "half_zip",

    # Pants
    "shorts": "shorts",
    "bermuda": "shorts",
    "joggers": "joggers",
    "leggings": "leggings",
    "sports-leggings": "leggings",
    "jeans": "jeans",

    # Tops
    "t-shirt": "tshirt",
    "crop-top": "tshirt",
    "tank-top": "tank_top",
    "polo": "polo",
    "corset": "corset",
    "bustier": "bustier",
    "body suit": "bodysuit",
    "overshirt": "overshirt",

    # Knitwear
    "sweater": "sweater",
    "cardigan": "cardigan",
    "hoodie": "hoodie",
    "sweatshirt": "sweatshirt",

    # One-pieces
    "jump suit": "jumpsuit",
    "romper": "romper",
    "overalls": "overalls",

    # Formal
    "suit": "suit",
    "tuxedo": "tuxedo",
    "waistcoat": "waistcoat",

    # Sportswear
    "sports-bra": "sportswear_top",
    "sports-top": "sportswear_top",
    "sports-shorts": "sportswear_bottom",
    "sports-jersey": "sports_jersey",
    "track suit": "tracksuit",
    "bikini": "swimwear",
    "swim suit": "swimwear",
}

# Normalize variable category names (aliases map to base name)
VARIABLE_CATEGORY_ALIASES = {
    "dress-pants": "pants",
    "chinos": "pants",
    "cargo-pants": "pants",
    "culottes": "skirt",
    "top": "blouse",
    "camisole": "blouse",
}

# ===== 69 VALID GROUPS =====

VALID_GROUPS = {
    # Jackets (6 variants)
    "jacket_leather", "jacket_denim", "jacket_wool", "jacket_natural", "jacket_technical", "jacket_synthetic",

    # Coats (5 variants)
    "coat_leather", "coat_wool", "coat_natural", "coat_technical", "coat_synthetic",

    # Blazers (4 variants)
    "blazer_leather", "blazer_wool", "blazer_natural", "blazer_synthetic",

    # Fixed outerwear (11 groups)
    "bomber", "puffer", "parka", "trench", "windbreaker", "raincoat", "fashion_outerwear", "vest", "fleece", "half_zip",

    # Pants (4 variants)
    "pants_leather", "pants_wool", "pants_natural", "pants_synthetic",

    # Skirts (5 variants)
    "skirt_leather", "skirt_denim", "skirt_wool", "skirt_natural", "skirt_synthetic",

    # Fixed bottoms (5 groups)
    "shorts", "joggers", "leggings", "jeans", "overalls",

    # Shirts (3 variants)
    "shirt_luxury", "shirt_natural", "shirt_synthetic",

    # Blouses (3 variants)
    "blouse_luxury", "blouse_natural", "blouse_synthetic",

    # Fixed tops (9 groups)
    "tshirt", "tank_top", "polo", "corset", "bustier", "bodysuit", "overshirt",

    # Fixed knitwear (4 groups)
    "sweater", "cardigan", "hoodie", "sweatshirt",

    # Dresses (3 variants)
    "dress_luxury", "dress_natural", "dress_synthetic",

    # Fixed one-pieces (3 groups)
    "jumpsuit", "romper",

    # Fixed formal (3 groups)
    "suit", "tuxedo", "waistcoat",

    # Fixed sportswear (5 groups)
    "sportswear_top", "sportswear_bottom", "sports_jersey", "tracksuit", "swimwear",
}

# Sanity check: ensure we have exactly 69 groups
assert len(VALID_GROUPS) == 69, f"Expected 69 groups, got {len(VALID_GROUPS)}"
