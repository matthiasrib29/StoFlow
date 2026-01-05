"""seed: populate vinted_id for brands, colors, materials, sizes

Revision ID: 20260105_1400
Revises: 20260105_1300
Create Date: 2026-01-05

Populates the vinted_id columns in product_attributes tables.
Data extracted from dev database where these values were set.

This ensures prod database has the same mapping data as dev,
enabling the reverse mapping (Vinted -> Stoflow) to work correctly.

Tables updated:
- brands.vinted_id (161 entries)
- colors.vinted_id (32 entries)
- materials.vinted_id (35 entries)
- sizes.vinted_women_id and vinted_men_id (102 entries)
"""
from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '20260105_1400'
down_revision = '20260105_1300'
branch_labels = None
depends_on = None


# =============================================================================
# BRANDS -> Vinted ID mapping
# =============================================================================
BRANDS_VINTED_IDS = [
    ('3sixteen', '623847'),
    ('Adidas', '14'),
    ('Nike', '53'),
    ('a.p.c.', '251'),
    ('acne studios', '180798'),
    ('acronym', '712647'),
    ('adidas', '14'),
    ('affliction', '272035'),
    ('akademiks', '130046'),
    ('anchor blue', '44519'),
    ('and wander', '1512834'),
    ("arc'teryx", '319730'),
    ('auralee', '2053426'),
    ('avirex', '4565'),
    ('bape', '4691320'),
    ('battenwear', '1102097'),
    ('ben davis', '85872'),
    ('bershka', '140'),
    ('big train', '2496245'),
    ('blind', '56158'),
    ('brixton', '56682'),
    ('bugle boy', '306806'),
    ('burberrys', '364'),
    ('butter goods', '901821'),
    ('calvin klein', '255'),
    ('carhartt', '362'),
    ('celio', '2615'),
    ('chevignon', '12205'),
    ('coogi', '21359'),
    ('corteiz', '3036449'),
    ('crooks & castles', '48527'),
    ('denham', '102502'),
    ('dickies', '65'),
    ('diesel', '161'),
    ('dime', '326479'),
    ('divided', '15452320'),
    ('dynam', '24329'),
    ('ecko unltd', '30575'),
    ('ecko unltd.', '30575'),
    ('ed hardy', '1761'),
    ('edwin', '4471'),
    ('element', '2037'),
    ('energie', '15985'),
    ('engineered garments', '609050'),
    ('enyce', '76428'),
    ('evisu', '214088'),
    ('foot korner', '381270'),
    ('freenote cloth', '2125308'),
    ('fubu', '57822'),
    ('full count', '2890372'),
    ('g-star raw', '2782756'),
    ('g-unit', '42813'),
    ('gant jeans', '6075'),
    ('gap', '6'),
    ('goldwin', '330213'),
    ('gramicci', '896209'),
    ('guess', '20'),
    ('heron preston', '389625'),
    ('homecore', '209540'),
    ('houdini', '379143'),
    ('huf', '14185'),
    ('indigofera', '742615'),
    ('iron heart', '492896'),
    ('izod', '238478'),
    ('jackwolfskin', '147650'),
    ('japan blue', '451051'),
    ('jizo', '10037867'),
    ('jnco', '290909'),
    ('kangaroo poo', '779366'),
    ('kapital', '576107'),
    ('karl kani', '13989'),
    ('kiabi', '60'),
    ('kiko kostadinov', '5821136'),
    ('klättermusen', '1638071'),
    ('lacoste', '304'),
    ('lagerfeld', '103'),
    ('lee', '63'),
    ('lee cooper', '407'),
    ('lemaire', '295938'),
    ("levi's", '10'),
    ("levi's made & crafted", '5982593'),
    ("levi's vintage clothing", '5983207'),
    ('maharishi', '326054'),
    ('maison mihara yasuhiro', '2514944'),
    ('majestic', '5725'),
    ('marni', '12251'),
    ('mecca', '238862'),
    ('mlb', '77420'),
    ('momotaro', '358913'),
    ('mont bell', '15088880'),
    ('montbell', '615130'),
    ('naked & famous denim', '1148437'),
    ('nascar', '185574'),
    ('neighborhood', '330747'),
    ('nfl', '33275'),
    ('nigel cabourn', '696416'),
    ('nike', '53'),
    ('no fear', '26101'),
    ('norrøna', '356632'),
    ('nudie jeans', '95256'),
    ('obey', '2069'),
    ('oni arai', '17653347'),
    ('orslow', '373463'),
    ('our legacy', '218132'),
    ('palace', '139960'),
    ('pass port', '15497435'),
    ('passport', '27217'),
    ('pelle pelle', '6989'),
    ('phat farm', '207738'),
    ('poetic collective', '924571'),
    ('pointer', '27275'),
    ('polar skate', '375147'),
    ('polar skate co.', '7006283'),
    ('pop trading company', '906755'),
    ('puma', '535'),
    ('pure blue japan', '859861'),
    ('ralph lauren', '88'),
    ('rare humans', '5582686'),
    ('red pepper', '717159'),
    ('rica lewis', '506'),
    ("robin's jean", '129064'),
    ('rocawear', '29507'),
    ('rogue territory', '770322'),
    ('résolute', '862485'),
    ('samurai', '278324'),
    ('sean john', '56628'),
    ('service works', '3364686'),
    ('snow peak', '666350'),
    ('south pole', '12235'),
    ('southpole', '12235'),
    ('stan ray', '449441'),
    ('starter', '28365'),
    ('state property', '335771'),
    ("studio d'artisan", '458183'),
    ('stuka', '288610'),
    ('stüssy', '441'),
    ('sugar cane', '178936'),
    ('sunnei', '834075'),
    ('supreme', '14969'),
    ('tcb jeans', '1945864'),
    ('tellason', '379872'),
    ('the flat head', '2182295'),
    ('the north face', '2319'),
    ('timberland', '44'),
    ('tommy hilfiger', '94'),
    ('tribal', '126096'),
    ('true religion', '9075'),
    ('unbranded', '14803'),
    ('under armour', '52035'),
    ('universal works', '378695'),
    ('vans', '139'),
    ('veilance', '3388210'),
    ('vokal', '300441'),
    ('volcom', '66'),
    ('warehouse', '7441'),
    ('wrangler', '259'),
    ('wrung', '6937'),
    ('wtaps', '320615'),
    ('wu-wear', '334532'),
    ('yardsale', '273608'),
    ('zoo york', '10401'),
]

# =============================================================================
# COLORS -> Vinted ID mapping
# =============================================================================
COLORS_VINTED_IDS = [
    ('beige', 4),
    ('black', 1),
    ('blue', 9),
    ('brown', 2),
    ('burgundy', 23),
    ('camel', 2),
    ('charcoal', 3),
    ('cognac', 2),
    ('coral', 22),
    ('cream', 20),
    ('fuchsia', 5),
    ('gold', 14),
    ('gray', 3),
    ('green', 10),
    ('khaki', 16),
    ('lavender', 25),
    ('light-blue', 26),
    ('mint', 30),
    ('multicolor', 15),
    ('mustard', 29),
    ('navy', 27),
    ('olive', 16),
    ('orange', 11),
    ('pink', 24),
    ('purple', 6),
    ('red', 7),
    ('silver', 13),
    ('tan', 2),
    ('teal', 17),
    ('turquoise', 17),
    ('white', 12),
    ('yellow', 8),
]

# =============================================================================
# MATERIALS -> Vinted ID mapping
# =============================================================================
MATERIALS_VINTED_IDS = [
    ('Acrylic', 149),
    ('Cashmere', 123),
    ('Cotton', 44),
    ('Denim', 303),
    ('Fleece', 120),
    ('Leather', 43),
    ('Linen', 146),
    ('Nylon', 52),
    ('Polyester', 45),
    ('Silk', 49),
    ('Spandex', 53),
    ('Suede', 298),
    ('Velvet', 466),
    ('Viscose', 48),
    ('Wool', 46),
    ('acrylic', 149),
    ('cashmere', 123),
    ('corduroy', 299),
    ('cotton', 44),
    ('denim', 303),
    ('elastane', 53),
    ('flannel', 451),
    ('fleece', 120),
    ('leather', 43),
    ('linen', 146),
    ('nylon', 52),
    ('polyester', 45),
    ('satin', 311),
    ('silk', 49),
    ('spandex', 53),
    ('suede', 298),
    ('tweed', 465),
    ('velvet', 466),
    ('viscose', 48),
    ('wool', 46),
]

# =============================================================================
# SIZES -> Vinted Women/Men ID mapping
# Format: (name_en, vinted_women_id, vinted_men_id)
# =============================================================================
SIZES_VINTED_IDS = [
    ('3XL', 310, 212),
    ('4XL', 311, 308),
    ('L', 5, 209),
    ('M', 4, 208),
    ('S', 3, 207),
    ('W22/L28', 1226, 1631),
    ('W22/L32', 1226, 1631),
    ('W24', 102, 1632),
    ('W24/L28', 102, 1632),
    ('W24/L30', 102, 1632),
    ('W24/L32', 102, 1632),
    ('W24/L34', 102, 1632),
    ('W26', 2, 1634),
    ('W26/L26', 2, 1634),
    ('W26/L28', 2, 1634),
    ('W26/L30', 2, 1634),
    ('W26/L32', 2, 1634),
    ('W26/L34', 2, 1634),
    ('W26/L38', 2, 1634),
    ('W28', 3, 1636),
    ('W28/L24', 3, 1636),
    ('W28/L26', 3, 1636),
    ('W28/L28', 3, 1636),
    ('W28/L30', 3, 1636),
    ('W28/L32', 3, 1636),
    ('W28/L34', 3, 1636),
    ('W28/L36', 3, 1636),
    ('W30', 4, 1638),
    ('W30/L24', 4, 1638),
    ('W30/L26', 4, 1638),
    ('W30/L28', 4, 1638),
    ('W30/L30', 4, 1638),
    ('W30/L32', 4, 1638),
    ('W30/L34', 4, 1638),
    ('W30/L36', 4, 1638),
    ('W30/L38', 4, 1638),
    ('W32', 5, 1640),
    ('W32/L26', 5, 1640),
    ('W32/L28', 5, 1640),
    ('W32/L30', 5, 1640),
    ('W32/L32', 5, 1640),
    ('W32/L34', 5, 1640),
    ('W32/L36', 5, 1640),
    ('W32/L38', 5, 1640),
    ('W34', 6, 1642),
    ('W34/L26', 6, 1642),
    ('W34/L28', 6, 1642),
    ('W34/L30', 6, 1642),
    ('W34/L32', 6, 1642),
    ('W34/L34', 6, 1642),
    ('W34/L36', 6, 1642),
    ('W34/L38', 6, 1642),
    ('W36', 310, 1643),
    ('W36/L26', 310, 1643),
    ('W36/L28', 310, 1643),
    ('W36/L30', 310, 1643),
    ('W36/L32', 310, 1643),
    ('W36/L34', 310, 1643),
    ('W36/L36', 310, 1643),
    ('W38', 311, 1644),
    ('W38/L26', 311, 1644),
    ('W38/L28', 311, 1644),
    ('W38/L30', 311, 1644),
    ('W38/L32', 311, 1644),
    ('W38/L34', 311, 1644),
    ('W38/L36', 311, 1644),
    ('W38/L38', 311, 1644),
    ('W40', 312, 1645),
    ('W40/L28', 312, 1645),
    ('W40/L30', 312, 1645),
    ('W40/L32', 312, 1645),
    ('W40/L34', 312, 1645),
    ('W40/L36', 312, 1645),
    ('W40/L38', 312, 1645),
    ('W42', 1227, 1646),
    ('W42/L26', 1227, 1646),
    ('W42/L28', 1227, 1646),
    ('W42/L30', 1227, 1646),
    ('W42/L32', 1227, 1646),
    ('W42/L34', 1227, 1646),
    ('W44', 1228, 1647),
    ('W44/L30', 1228, 1647),
    ('W44/L32', 1228, 1647),
    ('W44/L34', 1228, 1647),
    ('W46', 1229, 1648),
    ('W46/L28', 1229, 1648),
    ('W46/L30', 1229, 1648),
    ('W46/L32', 1229, 1648),
    ('W46/L34', 1229, 1648),
    ('W48/L32', 1230, 1649),
    ('W48/L34', 1230, 1649),
    ('W50/L32', 1230, 1704),
    ('W50/L34', 1230, 1704),
    ('W52', 1230, 1705),
    ('W52/L32', 1230, 1705),
    ('W52/L36', 1230, 1705),
    ('W54/L32', 1230, 1706),
    ('W56/L32', 1230, 1706),
    ('XL', 6, 210),
    ('XS', 2, 206),
    ('XXL', 7, 211),
    ('XXS', 102, 206),
]


def upgrade() -> None:
    """Populate vinted_id for brands, colors, materials, and sizes."""
    connection = op.get_bind()

    # =========================================================================
    # UPDATE BRANDS
    # =========================================================================
    brands_updated = 0
    for brand_name, vinted_id in BRANDS_VINTED_IDS:
        result = connection.execute(
            text("""
                UPDATE product_attributes.brands
                SET vinted_id = :vinted_id
                WHERE LOWER(name) = LOWER(:brand_name)
                AND (vinted_id IS NULL OR vinted_id = '')
            """),
            {"brand_name": brand_name, "vinted_id": vinted_id}
        )
        if result.rowcount > 0:
            brands_updated += result.rowcount
    print(f"  - Updated {brands_updated} brands with vinted_id")

    # =========================================================================
    # UPDATE COLORS
    # =========================================================================
    colors_updated = 0
    for color_name, vinted_id in COLORS_VINTED_IDS:
        result = connection.execute(
            text("""
                UPDATE product_attributes.colors
                SET vinted_id = :vinted_id
                WHERE LOWER(name_en) = LOWER(:color_name)
                AND (vinted_id IS NULL OR vinted_id = 0)
            """),
            {"color_name": color_name, "vinted_id": vinted_id}
        )
        if result.rowcount > 0:
            colors_updated += result.rowcount
    print(f"  - Updated {colors_updated} colors with vinted_id")

    # =========================================================================
    # UPDATE MATERIALS
    # =========================================================================
    materials_updated = 0
    for material_name, vinted_id in MATERIALS_VINTED_IDS:
        result = connection.execute(
            text("""
                UPDATE product_attributes.materials
                SET vinted_id = :vinted_id
                WHERE LOWER(name_en) = LOWER(:material_name)
                AND (vinted_id IS NULL OR vinted_id = 0)
            """),
            {"material_name": material_name, "vinted_id": vinted_id}
        )
        if result.rowcount > 0:
            materials_updated += result.rowcount
    print(f"  - Updated {materials_updated} materials with vinted_id")

    # =========================================================================
    # UPDATE SIZES
    # =========================================================================
    sizes_updated = 0
    for size_name, women_id, men_id in SIZES_VINTED_IDS:
        result = connection.execute(
            text("""
                UPDATE product_attributes.sizes
                SET vinted_women_id = :women_id, vinted_men_id = :men_id
                WHERE LOWER(name_en) = LOWER(:size_name)
                AND (vinted_women_id IS NULL OR vinted_men_id IS NULL)
            """),
            {"size_name": size_name, "women_id": women_id, "men_id": men_id}
        )
        if result.rowcount > 0:
            sizes_updated += result.rowcount
    print(f"  - Updated {sizes_updated} sizes with vinted_women_id/vinted_men_id")


def downgrade() -> None:
    """Remove vinted_id from all tables (set to NULL)."""
    connection = op.get_bind()

    # Clear brands vinted_id
    connection.execute(text("""
        UPDATE product_attributes.brands
        SET vinted_id = NULL
        WHERE vinted_id IS NOT NULL
    """))

    # Clear colors vinted_id
    connection.execute(text("""
        UPDATE product_attributes.colors
        SET vinted_id = NULL
        WHERE vinted_id IS NOT NULL
    """))

    # Clear materials vinted_id
    connection.execute(text("""
        UPDATE product_attributes.materials
        SET vinted_id = NULL
        WHERE vinted_id IS NOT NULL
    """))

    # Clear sizes vinted_women_id and vinted_men_id
    connection.execute(text("""
        UPDATE product_attributes.sizes
        SET vinted_women_id = NULL, vinted_men_id = NULL
        WHERE vinted_women_id IS NOT NULL OR vinted_men_id IS NOT NULL
    """))

    print("  - Cleared vinted_id from brands, colors, materials, and sizes")
