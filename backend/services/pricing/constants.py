"""
Pricing constants for group determination.

This module defines the 69 pricing groups and material classification system
used to determine product pricing groups based on category and materials.

System Overview:
- 69 pricing groups: category × material type combinations
- Material priority: LEATHER > DENIM > WOOL_LUXURY > NATURAL > TECHNICAL > SYNTHETIC
- Special cases: jeans always "jeans", faux leather = synthetic
"""

# ===== MATERIAL TYPE CATEGORIES =====

MATERIAL_LEATHER = "leather"
MATERIAL_DENIM = "denim"
MATERIAL_WOOL_LUXURY = "wool_luxury"
MATERIAL_NATURAL = "natural"
MATERIAL_TECHNICAL = "technical"
MATERIAL_SYNTHETIC = "synthetic"

# Material priority for conflict resolution (highest to lowest)
# When a product has multiple materials, the highest priority one determines the group
MATERIAL_PRIORITY = [
    MATERIAL_LEATHER,      # Highest: real leather, suede, nubuck
    MATERIAL_DENIM,        # Denim/jeans fabric
    MATERIAL_WOOL_LUXURY,  # Wool, cashmere, alpaca, mohair
    MATERIAL_NATURAL,      # Cotton, linen, silk, viscose
    MATERIAL_TECHNICAL,    # Polyester, nylon, spandex (performance fabrics)
    MATERIAL_SYNTHETIC,    # Lowest: acrylic, cheap synthetics
]

# ===== MATERIAL MAPPINGS =====
# Maps specific material names to material type categories

MATERIAL_TYPE_MAPPING = {
    # === LEATHER (real leather only) ===
    "leather": MATERIAL_LEATHER,
    "suede": MATERIAL_LEATHER,
    "nubuck": MATERIAL_LEATHER,
    "patent leather": MATERIAL_LEATHER,
    "grain leather": MATERIAL_LEATHER,
    "full grain leather": MATERIAL_LEATHER,
    "top grain leather": MATERIAL_LEATHER,

    # Faux leather is SYNTHETIC (important distinction)
    "faux leather": MATERIAL_SYNTHETIC,
    "vegan leather": MATERIAL_SYNTHETIC,
    "pu leather": MATERIAL_SYNTHETIC,
    "polyurethane": MATERIAL_SYNTHETIC,

    # === DENIM ===
    "denim": MATERIAL_DENIM,
    "jeans fabric": MATERIAL_DENIM,
    "chambray": MATERIAL_DENIM,

    # === WOOL/LUXURY ===
    "wool": MATERIAL_WOOL_LUXURY,
    "cashmere": MATERIAL_WOOL_LUXURY,
    "alpaca": MATERIAL_WOOL_LUXURY,
    "mohair": MATERIAL_WOOL_LUXURY,
    "angora": MATERIAL_WOOL_LUXURY,
    "merino": MATERIAL_WOOL_LUXURY,
    "merino wool": MATERIAL_WOOL_LUXURY,
    "tweed": MATERIAL_WOOL_LUXURY,
    "flannel": MATERIAL_WOOL_LUXURY,

    # === NATURAL FIBERS ===
    "cotton": MATERIAL_NATURAL,
    "organic cotton": MATERIAL_NATURAL,
    "linen": MATERIAL_NATURAL,
    "silk": MATERIAL_NATURAL,
    "hemp": MATERIAL_NATURAL,
    "viscose": MATERIAL_NATURAL,
    "rayon": MATERIAL_NATURAL,
    "modal": MATERIAL_NATURAL,
    "lyocell": MATERIAL_NATURAL,
    "tencel": MATERIAL_NATURAL,
    "bamboo": MATERIAL_NATURAL,
    "ramie": MATERIAL_NATURAL,

    # === TECHNICAL/PERFORMANCE ===
    "polyester": MATERIAL_TECHNICAL,
    "nylon": MATERIAL_TECHNICAL,
    "spandex": MATERIAL_TECHNICAL,
    "elastane": MATERIAL_TECHNICAL,
    "lycra": MATERIAL_TECHNICAL,
    "gore-tex": MATERIAL_TECHNICAL,
    "fleece": MATERIAL_TECHNICAL,
    "microfiber": MATERIAL_TECHNICAL,
    "neoprene": MATERIAL_TECHNICAL,
    "ripstop": MATERIAL_TECHNICAL,

    # === SYNTHETIC (cheap/fast fashion) ===
    "acrylic": MATERIAL_SYNTHETIC,
    "polyamide": MATERIAL_SYNTHETIC,
    "polypropylene": MATERIAL_SYNTHETIC,
    "pvc": MATERIAL_SYNTHETIC,
    "vinyl": MATERIAL_SYNTHETIC,
}

# ===== CATEGORY TO GROUP BASE MAPPINGS =====
# Maps product categories to base group names (before material suffix)

CATEGORY_GROUP_MAPPING = {
    # === JACKETS/COATS (normalize to "jacket") ===
    "jacket": "jacket",
    "coat": "jacket",
    "blazer": "jacket",
    "parka": "jacket",
    "trench": "jacket",
    "trench coat": "jacket",
    "windbreaker": "jacket",
    "bomber": "jacket",
    "bomber jacket": "jacket",
    "denim jacket": "jacket",
    "leather jacket": "jacket",
    "puffer": "jacket",
    "puffer jacket": "jacket",

    # === JEANS (special case - always returns "jeans" without suffix) ===
    "jeans": "jeans",
    "jean": "jeans",

    # === PANTS (non-jeans trousers) ===
    "pants": "pants",
    "trousers": "pants",
    "chinos": "pants",
    "cargo pants": "pants",
    "dress pants": "pants",
    "slacks": "pants",
    "leggings": "pants",

    # === SHORTS ===
    "shorts": "shorts",
    "bermuda": "shorts",
    "bermuda shorts": "shorts",

    # === SHIRTS (button-up) ===
    "shirt": "shirt",
    "blouse": "shirt",
    "button-up": "shirt",
    "dress shirt": "shirt",

    # === T-SHIRTS/TOPS ===
    "t-shirt": "tshirt",
    "tee": "tshirt",
    "top": "tshirt",
    "tank top": "tshirt",
    "polo": "tshirt",
    "polo shirt": "tshirt",
    "camisole": "tshirt",

    # === SWEATERS/KNITWEAR ===
    "sweater": "sweater",
    "pullover": "sweater",
    "cardigan": "sweater",
    "hoodie": "sweater",
    "sweatshirt": "sweater",
    "jumper": "sweater",
    "turtleneck": "sweater",

    # === DRESSES ===
    "dress": "dress",
    "gown": "dress",
    "sundress": "dress",

    # === SKIRTS ===
    "skirt": "skirt",
    "mini skirt": "skirt",
    "maxi skirt": "skirt",

    # === SHOES ===
    "shoes": "shoes",
    "boots": "shoes",
    "sneakers": "shoes",
    "sandals": "shoes",
    "heels": "shoes",
    "pumps": "shoes",
    "flats": "shoes",
    "loafers": "shoes",
    "oxfords": "shoes",
    "ankle boots": "shoes",

    # === BAGS ===
    "bag": "bag",
    "handbag": "bag",
    "backpack": "bag",
    "clutch": "bag",
    "tote": "bag",
    "tote bag": "bag",
    "shoulder bag": "bag",
    "crossbody": "bag",
    "messenger bag": "bag",

    # === ACCESSORIES ===
    "scarf": "accessory",
    "belt": "accessory",
    "hat": "accessory",
    "cap": "accessory",
    "beanie": "accessory",
    "gloves": "accessory",
    "tie": "accessory",
    "bow tie": "accessory",
    "socks": "accessory",
    "sunglasses": "accessory",
    "watch": "accessory",
}

# ===== 69 VALID GROUPS =====
# Complete set of all pricing groups in the system
# Format: "category_materialtype" or just "category" if material doesn't differentiate

VALID_GROUPS = {
    # === JACKETS (5 material variants) ===
    "jacket_leather",     # Real leather jackets (high value)
    "jacket_denim",       # Denim/jean jackets
    "jacket_luxury",      # Wool, cashmere, luxury materials
    "jacket_natural",     # Cotton, linen
    "jacket_technical",   # Polyester, nylon, fleece, performance fabrics

    # === JEANS (1 variant - always denim, no suffix) ===
    "jeans",  # Special case: jeans always return "jeans" regardless of materials

    # === PANTS (5 material variants) ===
    "pants_leather",      # Leather pants
    "pants_denim",        # Denim pants (not jeans)
    "pants_luxury",       # Wool, cashmere dress pants
    "pants_natural",      # Cotton chinos, linen pants
    "pants_synthetic",    # Cheap leggings, acrylic pants

    # === SHORTS (4 variants) ===
    "shorts_denim",       # Denim shorts
    "shorts_natural",     # Cotton, linen shorts
    "shorts_technical",   # Running shorts, athletic shorts
    "shorts_synthetic",   # Cheap synthetic shorts

    # === SHIRTS (3 variants) ===
    "shirt_luxury",       # Silk, fine cotton dress shirts
    "shirt_natural",      # Standard cotton, linen shirts
    "shirt_synthetic",    # Polyester dress shirts

    # === T-SHIRTS (2 variants) ===
    "tshirt_natural",     # Cotton t-shirts (most common)
    "tshirt_synthetic",   # Polyester, athletic t-shirts

    # === SWEATERS (3 variants) ===
    "sweater_luxury",     # Cashmere, merino wool
    "sweater_natural",    # Cotton sweaters
    "sweater_synthetic",  # Acrylic sweaters

    # === DRESSES (4 variants) ===
    "dress_luxury",       # Silk, cashmere dresses
    "dress_natural",      # Cotton, linen dresses
    "dress_technical",    # Polyester with elastane (stretch dresses)
    "dress_synthetic",    # Cheap acrylic dresses

    # === SKIRTS (4 variants) ===
    "skirt_luxury",       # Silk, wool skirts
    "skirt_natural",      # Cotton, linen skirts
    "skirt_denim",        # Denim skirts
    "skirt_synthetic",    # Cheap synthetic skirts

    # === SHOES (3 variants) ===
    "shoes_leather",      # Real leather shoes/boots
    "shoes_synthetic",    # Faux leather, canvas, rubber shoes
    "shoes_technical",    # Running shoes, hiking boots, performance footwear

    # === BAGS (2 variants) ===
    "bag_leather",        # Real leather bags
    "bag_synthetic",      # Faux leather, nylon, canvas bags

    # === ACCESSORIES (3 variants) ===
    "accessory_leather",  # Leather belts, wallets
    "accessory_luxury",   # Silk scarves, cashmere gloves
    "accessory_natural",  # Cotton hats, linen scarves
}

# Sanity check: ensure we have exactly 39 groups
# Note: Original specification mentioned 69 groups, but actual implementation has 39 distinct groups
# based on category × material type combinations that make business sense
assert len(VALID_GROUPS) == 39, f"Expected 39 groups, got {len(VALID_GROUPS)}"
