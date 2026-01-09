"""
Unit tests for group determination logic.

Tests all 69 pricing groups, material priority logic, edge cases, and special rules.
"""

import pytest
from services.pricing.group_determination import determine_group
from services.pricing.constants import VALID_GROUPS


class TestDetermineGroupJackets:
    """Test jacket group determination (6 variants)."""

    def test_jacket_leather(self):
        assert determine_group("jacket", ["leather"]) == "jacket_leather"

    def test_jacket_leather_priority(self):
        """Leather wins over other materials."""
        assert determine_group("jacket", ["cotton", "leather", "polyester"]) == "jacket_leather"

    def test_jacket_denim(self):
        assert determine_group("jacket", ["denim"]) == "jacket_denim"

    def test_jacket_wool(self):
        assert determine_group("jacket", ["wool"]) == "jacket_wool"

    def test_jacket_wool_cashmere(self):
        assert determine_group("jacket", ["cashmere"]) == "jacket_wool"

    def test_jacket_natural_cotton(self):
        assert determine_group("jacket", ["cotton"]) == "jacket_natural"

    def test_jacket_natural_linen(self):
        assert determine_group("jacket", ["linen"]) == "jacket_natural"

    def test_jacket_technical_nylon(self):
        assert determine_group("jacket", ["nylon"]) == "jacket_technical"

    def test_jacket_technical_fleece(self):
        assert determine_group("jacket", ["fleece"]) == "jacket_technical"

    def test_jacket_synthetic_polyester(self):
        assert determine_group("jacket", ["polyester"]) == "jacket_synthetic"

    def test_jacket_synthetic_acrylic(self):
        assert determine_group("jacket", ["acrylic"]) == "jacket_synthetic"

    def test_jacket_empty_materials(self):
        """Fallback to natural."""
        assert determine_group("jacket", []) == "jacket_natural"


class TestDetermineGroupCoats:
    """Test coat group determination (5 variants)."""

    def test_coat_leather(self):
        assert determine_group("coat", ["leather"]) == "coat_leather"

    def test_coat_wool(self):
        assert determine_group("coat", ["wool"]) == "coat_wool"

    def test_coat_wool_cashmere(self):
        assert determine_group("coat", ["cashmere"]) == "coat_wool"

    def test_coat_natural_cotton(self):
        assert determine_group("coat", ["cotton"]) == "coat_natural"

    def test_coat_technical_nylon(self):
        assert determine_group("coat", ["nylon"]) == "coat_technical"

    def test_coat_synthetic_polyester(self):
        assert determine_group("coat", ["polyester"]) == "coat_synthetic"


class TestDetermineGroupBlazers:
    """Test blazer group determination (4 variants)."""

    def test_blazer_leather(self):
        assert determine_group("blazer", ["leather"]) == "blazer_leather"

    def test_blazer_wool(self):
        assert determine_group("blazer", ["wool"]) == "blazer_wool"

    def test_blazer_natural_cotton(self):
        assert determine_group("blazer", ["cotton"]) == "blazer_natural"

    def test_blazer_synthetic_polyester(self):
        assert determine_group("blazer", ["polyester"]) == "blazer_synthetic"


class TestDetermineGroupFixedOuterwear:
    """Test fixed outerwear groups (ignore materials)."""

    def test_bomber_ignores_materials(self):
        """Bomber always returns 'bomber' regardless of materials."""
        assert determine_group("bomber", ["leather"]) == "bomber"
        assert determine_group("bomber", ["nylon"]) == "bomber"
        assert determine_group("bomber", []) == "bomber"

    def test_puffer(self):
        assert determine_group("puffer", ["polyester"]) == "puffer"

    def test_parka(self):
        assert determine_group("parka", ["nylon"]) == "parka"

    def test_trench(self):
        assert determine_group("trench", ["cotton"]) == "trench"

    def test_windbreaker(self):
        assert determine_group("windbreaker", ["nylon"]) == "windbreaker"

    def test_raincoat(self):
        assert determine_group("raincoat", ["polyester"]) == "raincoat"

    def test_fashion_outerwear_cape(self):
        assert determine_group("cape", ["wool"]) == "fashion_outerwear"

    def test_fashion_outerwear_poncho(self):
        assert determine_group("poncho", ["cotton"]) == "fashion_outerwear"

    def test_fashion_outerwear_kimono(self):
        assert determine_group("kimono", ["silk"]) == "fashion_outerwear"

    def test_vest(self):
        assert determine_group("vest", ["polyester"]) == "vest"

    def test_fleece(self):
        assert determine_group("fleece jacket", ["fleece"]) == "fleece"

    def test_half_zip(self):
        assert determine_group("half-zip", ["fleece"]) == "half_zip"


class TestDetermineGroupPants:
    """Test pants group determination (4 variants)."""

    def test_pants_leather(self):
        assert determine_group("pants", ["leather"]) == "pants_leather"

    def test_pants_wool(self):
        assert determine_group("pants", ["wool"]) == "pants_wool"

    def test_pants_natural_cotton(self):
        assert determine_group("pants", ["cotton"]) == "pants_natural"

    def test_pants_synthetic_polyester(self):
        assert determine_group("pants", ["polyester"]) == "pants_synthetic"

    def test_pants_alias_dress_pants(self):
        """dress-pants maps to pants."""
        assert determine_group("dress-pants", ["cotton"]) == "pants_natural"

    def test_pants_alias_chinos(self):
        """chinos maps to pants."""
        assert determine_group("chinos", ["cotton"]) == "pants_natural"

    def test_pants_alias_cargo_pants(self):
        """cargo-pants maps to pants."""
        assert determine_group("cargo-pants", ["cotton"]) == "pants_natural"


class TestDetermineGroupSkirts:
    """Test skirt group determination (5 variants)."""

    def test_skirt_leather(self):
        assert determine_group("skirt", ["leather"]) == "skirt_leather"

    def test_skirt_denim(self):
        assert determine_group("skirt", ["denim"]) == "skirt_denim"

    def test_skirt_wool(self):
        assert determine_group("skirt", ["wool"]) == "skirt_wool"

    def test_skirt_natural_cotton(self):
        assert determine_group("skirt", ["cotton"]) == "skirt_natural"

    def test_skirt_synthetic_polyester(self):
        assert determine_group("skirt", ["polyester"]) == "skirt_synthetic"

    def test_skirt_alias_culottes(self):
        """culottes maps to skirt."""
        assert determine_group("culottes", ["cotton"]) == "skirt_natural"


class TestDetermineGroupFixedBottoms:
    """Test fixed bottom groups (ignore materials)."""

    def test_shorts(self):
        assert determine_group("shorts", ["cotton"]) == "shorts"
        assert determine_group("shorts", ["denim"]) == "shorts"

    def test_shorts_alias_bermuda(self):
        assert determine_group("bermuda", ["cotton"]) == "shorts"

    def test_joggers(self):
        assert determine_group("joggers", ["cotton"]) == "joggers"

    def test_leggings(self):
        assert determine_group("leggings", ["spandex"]) == "leggings"

    def test_leggings_alias_sports_leggings(self):
        assert determine_group("sports-leggings", ["elastane"]) == "leggings"

    def test_jeans(self):
        """Jeans always return 'jeans' regardless of materials."""
        assert determine_group("jeans", ["denim"]) == "jeans"
        assert determine_group("jeans", ["denim", "elastane"]) == "jeans"
        assert determine_group("jeans", []) == "jeans"

    def test_overalls(self):
        assert determine_group("overalls", ["denim"]) == "overalls"


class TestDetermineGroupShirts:
    """Test shirt group determination (3 variants)."""

    def test_shirt_luxury_silk(self):
        """Silk maps to luxury for shirts."""
        assert determine_group("shirt", ["silk"]) == "shirt_luxury"

    def test_shirt_luxury_satin(self):
        assert determine_group("shirt", ["satin"]) == "shirt_luxury"

    def test_shirt_natural_cotton(self):
        assert determine_group("shirt", ["cotton"]) == "shirt_natural"

    def test_shirt_natural_linen(self):
        assert determine_group("shirt", ["linen"]) == "shirt_natural"

    def test_shirt_synthetic_polyester(self):
        assert determine_group("shirt", ["polyester"]) == "shirt_synthetic"


class TestDetermineGroupBlouses:
    """Test blouse group determination (3 variants)."""

    def test_blouse_luxury_silk(self):
        """Silk maps to luxury for blouses."""
        assert determine_group("blouse", ["silk"]) == "blouse_luxury"

    def test_blouse_natural_cotton(self):
        assert determine_group("blouse", ["cotton"]) == "blouse_natural"

    def test_blouse_synthetic_polyester(self):
        assert determine_group("blouse", ["polyester"]) == "blouse_synthetic"

    def test_blouse_alias_top(self):
        """top maps to blouse."""
        assert determine_group("top", ["silk"]) == "blouse_luxury"

    def test_blouse_alias_camisole(self):
        """camisole maps to blouse."""
        assert determine_group("camisole", ["cotton"]) == "blouse_natural"


class TestDetermineGroupFixedTops:
    """Test fixed top groups (ignore materials)."""

    def test_tshirt(self):
        assert determine_group("t-shirt", ["cotton"]) == "tshirt"
        assert determine_group("t-shirt", ["polyester"]) == "tshirt"

    def test_tshirt_alias_crop_top(self):
        assert determine_group("crop-top", ["cotton"]) == "tshirt"

    def test_tank_top(self):
        assert determine_group("tank-top", ["cotton"]) == "tank_top"

    def test_polo(self):
        assert determine_group("polo", ["cotton"]) == "polo"

    def test_corset(self):
        assert determine_group("corset", ["satin"]) == "corset"

    def test_bustier(self):
        assert determine_group("bustier", ["silk"]) == "bustier"

    def test_bodysuit(self):
        assert determine_group("body suit", ["cotton"]) == "bodysuit"

    def test_overshirt(self):
        assert determine_group("overshirt", ["cotton"]) == "overshirt"


class TestDetermineGroupFixedKnitwear:
    """Test fixed knitwear groups (ignore materials)."""

    def test_sweater(self):
        assert determine_group("sweater", ["wool"]) == "sweater"
        assert determine_group("sweater", ["cotton"]) == "sweater"
        assert determine_group("sweater", ["cashmere"]) == "sweater"

    def test_cardigan(self):
        assert determine_group("cardigan", ["wool"]) == "cardigan"

    def test_hoodie(self):
        assert determine_group("hoodie", ["cotton"]) == "hoodie"

    def test_sweatshirt(self):
        assert determine_group("sweatshirt", ["cotton"]) == "sweatshirt"


class TestDetermineGroupDresses:
    """Test dress group determination (3 variants)."""

    def test_dress_luxury_silk(self):
        """Silk maps to luxury for dresses."""
        assert determine_group("dress", ["silk"]) == "dress_luxury"

    def test_dress_natural_cotton(self):
        assert determine_group("dress", ["cotton"]) == "dress_natural"

    def test_dress_synthetic_polyester(self):
        assert determine_group("dress", ["polyester"]) == "dress_synthetic"


class TestDetermineGroupFixedOnePieces:
    """Test fixed one-piece groups (ignore materials)."""

    def test_jumpsuit(self):
        assert determine_group("jump suit", ["cotton"]) == "jumpsuit"

    def test_romper(self):
        assert determine_group("romper", ["cotton"]) == "romper"


class TestDetermineGroupFixedFormal:
    """Test fixed formal groups (ignore materials)."""

    def test_suit(self):
        assert determine_group("suit", ["wool"]) == "suit"

    def test_tuxedo(self):
        assert determine_group("tuxedo", ["wool"]) == "tuxedo"

    def test_waistcoat(self):
        assert determine_group("waistcoat", ["wool"]) == "waistcoat"


class TestDetermineGroupFixedSportswear:
    """Test fixed sportswear groups (ignore materials)."""

    def test_sportswear_top_sports_bra(self):
        assert determine_group("sports-bra", ["polyester"]) == "sportswear_top"

    def test_sportswear_top_sports_top(self):
        assert determine_group("sports-top", ["polyester"]) == "sportswear_top"

    def test_sportswear_bottom(self):
        assert determine_group("sports-shorts", ["polyester"]) == "sportswear_bottom"

    def test_sports_jersey(self):
        assert determine_group("sports-jersey", ["polyester"]) == "sports_jersey"

    def test_tracksuit(self):
        assert determine_group("track suit", ["polyester"]) == "tracksuit"

    def test_swimwear_bikini(self):
        assert determine_group("bikini", ["polyester"]) == "swimwear"

    def test_swimwear_swim_suit(self):
        assert determine_group("swim suit", ["nylon"]) == "swimwear"


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_unknown_category_raises_error(self):
        with pytest.raises(ValueError, match="Unknown category"):
            determine_group("spaceship", ["titanium"])

    def test_category_normalization_uppercase(self):
        """Categories are case-insensitive."""
        assert determine_group("JACKET", ["LEATHER"]) == "jacket_leather"

    def test_category_normalization_whitespace(self):
        assert determine_group(" Jacket ", ["leather"]) == "jacket_leather"

    def test_material_normalization_uppercase(self):
        """Materials are case-insensitive."""
        assert determine_group("jacket", ["LEATHER"]) == "jacket_leather"

    def test_material_normalization_whitespace(self):
        assert determine_group("jacket", [" Leather "]) == "jacket_leather"

    def test_unknown_material_fallback(self):
        """Unknown materials use category default (natural)."""
        assert determine_group("jacket", ["unknown_material"]) == "jacket_natural"
        assert determine_group("pants", ["unknown_material"]) == "pants_natural"

    def test_empty_material_strings(self):
        """Empty strings in materials list are ignored."""
        assert determine_group("jacket", ["", "cotton", ""]) == "jacket_natural"


class TestMaterialPriority:
    """Test material priority logic."""

    def test_leather_over_all(self):
        """Leather has highest priority."""
        assert determine_group("jacket", ["polyester", "leather"]) == "jacket_leather"
        assert determine_group("jacket", ["cotton", "leather", "denim"]) == "jacket_leather"

    def test_silk_luxury_over_denim(self):
        """Silk luxury is second highest priority."""
        assert determine_group("shirt", ["cotton", "silk"]) == "shirt_luxury"
        assert determine_group("dress", ["polyester", "silk"]) == "dress_luxury"

    def test_denim_over_wool(self):
        """Denim beats wool, natural, technical, synthetic."""
        assert determine_group("jacket", ["cotton", "denim"]) == "jacket_denim"
        assert determine_group("skirt", ["polyester", "denim"]) == "skirt_denim"

    def test_wool_over_natural(self):
        """Wool beats natural materials."""
        assert determine_group("jacket", ["cotton", "wool"]) == "jacket_wool"
        assert determine_group("coat", ["linen", "cashmere"]) == "coat_wool"

    def test_natural_over_technical(self):
        """Natural beats technical."""
        assert determine_group("jacket", ["nylon", "cotton"]) == "jacket_natural"

    def test_technical_over_synthetic(self):
        """Technical beats synthetic."""
        assert determine_group("jacket", ["acrylic", "nylon"]) == "jacket_technical"


class TestFauxLeather:
    """Test faux leather special cases."""

    def test_faux_leather_is_synthetic(self):
        """Faux leather must be treated as synthetic, never as real leather."""
        result = determine_group("jacket", ["faux leather"])
        assert result != "jacket_leather", "Faux leather should never return leather group"
        assert result == "jacket_synthetic"

    def test_vegan_leather_is_synthetic(self):
        assert determine_group("pants", ["vegan leather"]) == "pants_synthetic"

    def test_pu_leather_is_synthetic(self):
        assert determine_group("blazer", ["pu leather"]) == "blazer_synthetic"


class TestSilkVsWoolMapping:
    """Test that silk and wool map to different suffixes."""

    def test_silk_maps_to_luxury_for_shirts(self):
        """Silk materials map to 'luxury' suffix for shirts/blouses/dresses."""
        assert determine_group("shirt", ["silk"]) == "shirt_luxury"
        assert determine_group("blouse", ["satin"]) == "blouse_luxury"
        assert determine_group("dress", ["velvet"]) == "dress_luxury"

    def test_wool_maps_to_wool_for_jackets(self):
        """Wool materials map to 'wool' suffix for jackets/coats/etc."""
        assert determine_group("jacket", ["wool"]) == "jacket_wool"
        assert determine_group("coat", ["cashmere"]) == "coat_wool"
        assert determine_group("blazer", ["tweed"]) == "blazer_wool"
        assert determine_group("pants", ["merino"]) == "pants_wool"


class TestGroupValidation:
    """Test that all returned groups are valid."""

    def test_all_groups_in_valid_set(self):
        """Ensure all returned groups are in VALID_GROUPS."""
        test_cases = [
            ("jacket", ["leather"]),
            ("jacket", ["denim"]),
            ("jacket", ["wool"]),
            ("jacket", ["cotton"]),
            ("jacket", ["nylon"]),
            ("jacket", ["polyester"]),
            ("coat", ["leather"]),
            ("blazer", ["wool"]),
            ("pants", ["cotton"]),
            ("skirt", ["denim"]),
            ("shirt", ["silk"]),
            ("blouse", ["cotton"]),
            ("dress", ["silk"]),
            ("jeans", ["denim"]),
            ("bomber", ["nylon"]),
            ("t-shirt", ["cotton"]),
            ("sweater", ["wool"]),
            ("jump suit", ["cotton"]),  # Note: "jump suit" with space, not "jumpsuit"
        ]
        for category, materials in test_cases:
            group = determine_group(category, materials)
            assert group in VALID_GROUPS, f"Group '{group}' not in VALID_GROUPS"

    def test_valid_groups_count(self):
        """Ensure we have exactly 69 valid groups."""
        assert len(VALID_GROUPS) == 69, f"Expected 69 groups, got {len(VALID_GROUPS)}"
