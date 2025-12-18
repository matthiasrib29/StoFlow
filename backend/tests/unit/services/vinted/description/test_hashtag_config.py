"""
Tests for HashtagConfig

Tests the hashtag configuration for Vinted descriptions.
"""
import pytest
from services.vinted.description.hashtag_config import HashtagConfig


class TestHashtagConfigConstants:
    """Tests for HashtagConfig constants."""

    def test_max_hashtags(self):
        """Test MAX_HASHTAGS constant."""
        assert HashtagConfig.MAX_HASHTAGS == 40

    def test_fixed_hashtags_count(self):
        """Test that there are exactly 5 fixed hashtags."""
        assert len(HashtagConfig.FIXED) == 5

    def test_fixed_hashtags_format(self):
        """Test that all fixed hashtags start with #."""
        for tag in HashtagConfig.FIXED:
            assert tag.startswith("#"), f"'{tag}' should start with #"

    def test_fixed_hashtags_content(self):
        """Test expected fixed hashtags are present."""
        expected = ["#vintagestyle", "#secondemain", "#friperie", "#modeethique", "#vintagestore"]
        for tag in expected:
            assert tag in HashtagConfig.FIXED


class TestHashtagCategories:
    """Tests for hashtag category mappings."""

    def test_by_category_has_jeans(self):
        """Test that Jeans category has hashtags."""
        assert "Jeans" in HashtagConfig.BY_CATEGORY
        assert "#jeans" in HashtagConfig.BY_CATEGORY["Jeans"]
        assert "#denim" in HashtagConfig.BY_CATEGORY["Jeans"]

    def test_by_fit_has_slim(self):
        """Test that Slim fit has hashtags."""
        assert "Slim" in HashtagConfig.BY_FIT
        assert "#slim" in HashtagConfig.BY_FIT["Slim"]
        assert "#slimfit" in HashtagConfig.BY_FIT["Slim"]

    def test_by_decade_has_90s(self):
        """Test that 90s decade has hashtags."""
        assert "90s" in HashtagConfig.BY_DECADE
        assert "#90s" in HashtagConfig.BY_DECADE["90s"]
        assert "#vintage90s" in HashtagConfig.BY_DECADE["90s"]

    def test_by_material_has_denim(self):
        """Test that Denim material has hashtags."""
        assert "Denim" in HashtagConfig.BY_MATERIAL
        assert "#denim" in HashtagConfig.BY_MATERIAL["Denim"]

    def test_by_brand_has_levis(self):
        """Test that Levi's brand has hashtags."""
        assert "Levi's" in HashtagConfig.BY_BRAND
        assert "#levis" in HashtagConfig.BY_BRAND["Levi's"]
        assert "#501" in HashtagConfig.BY_BRAND["Levi's"]

    def test_by_season_has_summer(self):
        """Test that Summer season has hashtags."""
        assert "Summer" in HashtagConfig.BY_SEASON
        assert "#summer" in HashtagConfig.BY_SEASON["Summer"]

    def test_by_occasion_has_casual(self):
        """Test that Casual occasion has hashtags."""
        assert "Casual" in HashtagConfig.BY_OCCASION
        assert "#casual" in HashtagConfig.BY_OCCASION["Casual"]


class TestTrendingHashtags:
    """Tests for trending hashtags."""

    def test_trending_hashtags_not_empty(self):
        """Test that trending hashtags exist."""
        assert len(HashtagConfig.TRENDING) > 0

    def test_trending_hashtags_format(self):
        """Test that all trending hashtags start with #."""
        for tag in HashtagConfig.TRENDING:
            assert tag.startswith("#"), f"'{tag}' should start with #"

    def test_common_trending_hashtags(self):
        """Test common trending hashtags are present."""
        expected = ["#fashion", "#style", "#vintage", "#ootd"]
        for tag in expected:
            assert tag in HashtagConfig.TRENDING
