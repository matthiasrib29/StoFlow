"""
eBay Description Tags.

SEO tags generation for eBay HTML descriptions (max 40 tags).
Three-tier priority system: HIGH (product attributes), MEDIUM (mapped tags), LOW (generic filler).

Ported from pythonApiWOO/services/ebay/ebay_description_multilang_service.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.user.product import Product


MAX_TAGS_EBAY = 40

# Fixed tags always included (per language)
FIXED_TAGS: dict[str, list[str]] = {
    "en": ["#vintage", "#secondhand", "#sustainable", "#authentic", "#quality", "#vintagefashion"],
    "fr": ["#vintage", "#secondemain", "#durable", "#authentique", "#qualite", "#modevintage"],
    "de": ["#vintage", "#secondhand", "#nachhaltig", "#authentisch", "#qualitat", "#vintagemode"],
    "it": ["#vintage", "#secondhand", "#sostenibile", "#autentico", "#qualita", "#modavintage"],
    "es": ["#vintage", "#segundamano", "#sostenible", "#autentico", "#calidad", "#modavintage"],
    "nl": ["#vintage", "#tweedehands", "#duurzaam", "#authentiek", "#kwaliteit", "#vintagemode"],
    "pl": ["#vintage", "#secondhand", "#zrownowazony", "#autentyczny", "#jakosc", "#modawintage"],
}

# Category-specific tags (EN - universal)
CATEGORY_TAGS: dict[str, list[str]] = {
    "jeans": ["#jeans", "#denim", "#vintagejeans", "#denimstyle", "#vintagedenim"],
    "jean": ["#jeans", "#denim", "#vintagejeans"],
    "pants": ["#pants", "#trousers", "#vintagepants", "#bottoms"],
    "short": ["#shorts", "#vintageshorts", "#summerstyle"],
    "jacket": ["#jacket", "#vintagejacket", "#outerwear", "#coat"],
    "shirt": ["#shirt", "#vintageshirt", "#buttonup"],
    "t-shirt": ["#tshirt", "#tee", "#vintagetee"],
    "sweat": ["#sweatshirt", "#hoodie", "#crewneck"],
    "sweater": ["#sweater", "#knitwear", "#vintagesweater"],
}

# Fit type tags (EN - universal)
FIT_TAGS: dict[str, list[str]] = {
    "baggy": ["#baggy", "#baggyjeans", "#oversized", "#loose"],
    "loose": ["#loose", "#loosefit", "#relaxedfit"],
    "regular": ["#regular", "#regularfit", "#classic"],
    "slim": ["#slim", "#slimfit", "#fitted"],
    "skinny": ["#skinny", "#skinnyjeans", "#tightfit"],
    "bootcut": ["#bootcut", "#bootcutjeans", "#flared"],
    "flare": ["#flare", "#flarejeans", "#bellbottoms"],
    "straight": ["#straight", "#straightleg", "#straightfit"],
    "wide": ["#wide", "#wideleg", "#widejeans"],
}

# Decade tags (EN - universal)
DECADE_TAGS: dict[str, list[str]] = {
    "90s": ["#90s", "#1990s", "#90sfashion", "#nineties"],
    "1990": ["#90s", "#1990s", "#90sfashion"],
    "80s": ["#80s", "#1980s", "#80sfashion", "#eighties"],
    "1980": ["#80s", "#1980s", "#80sfashion"],
    "2000": ["#y2k", "#2000s", "#2000sfashion", "#millenial"],
    "2000s": ["#y2k", "#2000s", "#y2kfashion"],
    "y2k": ["#y2k", "#y2kfashion", "#2000s"],
    "70s": ["#70s", "#1970s", "#70sstyle", "#seventies"],
    "1970": ["#70s", "#1970s", "#70sfashion"],
    "60s": ["#60s", "#1960s", "#60sstyle", "#sixties"],
}

# Material tags (EN - universal)
MATERIAL_TAGS: dict[str, list[str]] = {
    "denim": ["#denim", "#jeanfabric", "#cottonblend"],
    "cotton": ["#cotton", "#100cotton", "#naturalfiber"],
    "leather": ["#leather", "#genuineleather", "#leatherjacket"],
    "wool": ["#wool", "#woolblend", "#knitwear"],
    "corduroy": ["#corduroy", "#corduroypants", "#textured"],
    "linen": ["#linen", "#linenblend", "#summerfabric"],
}

# Brand-specific tags (EN - universal)
BRAND_TAGS: dict[str, list[str]] = {
    "levis": ["#levis", "#levisjeans", "#levis501", "#levisvintage"],
    "levi's": ["#levis", "#levisjeans", "#levis501"],
    "wrangler": ["#wrangler", "#wranglerjeans", "#wranglerwestern"],
    "lee": ["#lee", "#leejeans", "#leevintage"],
    "carhartt": ["#carhartt", "#carharttworkwear", "#carharttvintage"],
    "dickies": ["#dickies", "#dickiesworkwear", "#dickiespants"],
    "nike": ["#nike", "#nikevintage", "#nikesportswear"],
    "adidas": ["#adidas", "#adidasvintage", "#adidasoriginals"],
    "champion": ["#champion", "#championvintage", "#championsweatshirt"],
    "ralph lauren": ["#ralphlauren", "#polo", "#poloralphlauren"],
    "tommy hilfiger": ["#tommyhilfiger", "#tommy", "#tommyjeans"],
    "calvin klein": ["#calvinklein", "#ck", "#ckvintage"],
}

# Style tags (EN - universal)
STYLE_TAGS: dict[str, list[str]] = {
    "casual": ["#casual", "#casualwear", "#casualstyle", "#everyday"],
    "streetwear": ["#streetwear", "#streetstyle", "#urban", "#hiphop"],
    "workwear": ["#workwear", "#utilitarian", "#worker", "#industrial"],
    "preppy": ["#preppy", "#preppystyle", "#classic", "#collegiate"],
    "western": ["#western", "#cowboy", "#westernwear", "#ranch"],
    "sporty": ["#sporty", "#athletic", "#sportswear", "#activewear"],
}

# Trending filler tags (EN - universal)
TRENDING_VINTAGE: list[str] = [
    "#vintageclothing", "#retro", "#retrostyle", "#throwback", "#oldschool",
    "#classic", "#timeless", "#authentic", "#vintageshop", "#vintagestyle",
]
TRENDING_ECO: list[str] = [
    "#sustainable", "#ecofriendly", "#secondhand", "#thrifted", "#preloved",
    "#slowfashion", "#ethicalfashion", "#zerowaste", "#recycled", "#upcycled",
]
GENERIC_POPULAR: list[str] = [
    "#fashion", "#style", "#outfit", "#mensfashion", "#womensfashion",
    "#unisex", "#fashionstyle", "#stylish", "#trendy", "#unique",
]


def _safe_str(value: str | None) -> str:
    """Return cleaned string or empty string if None/invalid."""
    if value is None or str(value).lower() in ("null", "none", "n/a", ""):
        return ""
    return str(value).strip()


def _to_tag(value: str) -> str:
    """Convert a value to a hashtag (lowercase, no spaces/dashes)."""
    return "#" + value.lower().replace(" ", "").replace("-", "").replace("_", "")


def build_ebay_tags(product: Product, lang: str) -> str:
    """
    Build SEO tags for eBay description (max 40 tags).

    Priority tiers:
    - HIGH: Product attributes as English tags
    - MEDIUM: Mapped tags (brand, category, fit, decade, material, style)
    - LOW: Generic filler (vintage, eco, popular)

    Args:
        product: StoFlow Product model.
        lang: Language code (fr, en, de, it, es, nl, pl).

    Returns:
        Space-separated tag string for HTML inclusion.
    """
    tags: set[str] = set(FIXED_TAGS.get(lang, FIXED_TAGS["en"]))

    # --- HIGH PRIORITY: Product attributes as English tags ---
    simple_attrs = [
        "brand", "category", "fit", "decade", "trend",
        "season", "rise", "closure", "origin",
        "gender", "pattern", "sleeve_length",
    ]
    for attr_name in simple_attrs:
        value = _safe_str(getattr(product, attr_name, None))
        if not value or value.lower() == "unbranded":
            continue
        tags.add(_to_tag(value))

    # Model (free text)
    model = _safe_str(product.model)
    if model:
        tags.add(_to_tag(model))

    # Color (M2M - first color)
    if product.colors:
        color_val = _safe_str(product.colors[0])
        if color_val:
            tags.add(_to_tag(color_val))

    # Material (M2M - first material)
    if product.materials:
        material_val = _safe_str(product.materials[0])
        if material_val:
            tags.add(_to_tag(material_val))

    # Unique features (JSONB list)
    if product.unique_feature:
        for feature in product.unique_feature:
            feat = _safe_str(feature)
            if feat:
                tags.add(_to_tag(feat))

    # --- MEDIUM PRIORITY: Mapped tags ---

    # Brand
    brand = _safe_str(product.brand).lower()
    if brand and brand != "unbranded":
        brand_tags = BRAND_TAGS.get(brand, [_to_tag(brand)])
        tags.update(brand_tags[:3])

    # Category
    category = _safe_str(product.category).lower()
    for key, tag_list in CATEGORY_TAGS.items():
        if key in category:
            tags.update(tag_list[:3])
            break

    # Fit
    fit = _safe_str(product.fit).lower()
    if fit in FIT_TAGS:
        tags.update(FIT_TAGS[fit][:3])

    # Decade
    decade = _safe_str(product.decade).lower()
    for key, tag_list in DECADE_TAGS.items():
        if key in decade:
            tags.update(tag_list[:3])
            break

    # Material (mapped)
    material = _safe_str(product.materials[0]).lower() if product.materials else ""
    for key, tag_list in MATERIAL_TAGS.items():
        if key in material:
            tags.update(tag_list[:2])
            break

    # Style/Trend
    trend = _safe_str(product.trend).lower()
    if trend:
        tags.add(_to_tag(trend))
        for style_key, style_tag_list in STYLE_TAGS.items():
            if style_key in trend:
                tags.update(style_tag_list[:2])
                break

    # --- LOW PRIORITY: Generic filler up to MAX_TAGS_EBAY ---
    for filler_list in (TRENDING_VINTAGE, TRENDING_ECO, GENERIC_POPULAR):
        for tag in filler_list:
            if len(tags) >= MAX_TAGS_EBAY:
                break
            tags.add(tag)
        if len(tags) >= MAX_TAGS_EBAY:
            break

    return " ".join(list(tags)[:MAX_TAGS_EBAY])
