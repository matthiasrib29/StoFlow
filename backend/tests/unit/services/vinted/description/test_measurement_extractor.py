"""
Tests for MeasurementExtractor

Tests the measurement extraction functionality for different product categories.
"""
import pytest
from unittest.mock import MagicMock
from services.vinted.description.measurement_extractor import MeasurementExtractor


class MockProduct:
    """Mock product for testing."""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class TestMeasurementExtractorBottom:
    """Tests for bottom (pants/jeans) measurements."""

    def test_extract_all_bottom_measurements(self):
        """Test extraction of all bottom measurements."""
        product = MockProduct(
            category="Jeans",
            parent_category="Jeans",
            waist=32,
            inseam=34,
            rise=10,
            thigh=24,
            knee=18,
            leg_opening=16,
        )

        measurements = MeasurementExtractor.extract(product)

        assert len(measurements) == 6
        assert ("Tour de taille", "32") in measurements
        assert ("Entrejambe", "34") in measurements
        assert ("Hauteur de fourche", "10") in measurements
        assert ("Tour de cuisse", "24") in measurements
        assert ("Tour de genou", "18") in measurements
        assert ("Ouverture de jambe", "16") in measurements

    def test_extract_partial_bottom_measurements(self):
        """Test extraction with only some measurements present."""
        product = MockProduct(
            category="Pants",
            parent_category="Pants",
            waist=32,
            inseam=34,
        )

        measurements = MeasurementExtractor.extract(product)

        assert len(measurements) == 2
        assert ("Tour de taille", "32") in measurements
        assert ("Entrejambe", "34") in measurements


class TestMeasurementExtractorShorts:
    """Tests for shorts measurements."""

    def test_extract_shorts_measurements(self):
        """Test extraction of shorts measurements."""
        product = MockProduct(
            category="Shorts",
            parent_category="Shorts",
            waist=30,
            inseam=7,
            rise=10,
            thigh=24,
            leg_opening=20,
        )

        measurements = MeasurementExtractor.extract(product)

        assert len(measurements) == 5
        assert ("Tour de taille", "30") in measurements
        assert ("Entrejambe", "7") in measurements
        # Note: Shorts don't include knee measurement


class TestMeasurementExtractorTop:
    """Tests for top (shirts, jackets, etc.) measurements."""

    def test_extract_top_measurements(self):
        """Test extraction of top measurements."""
        product = MockProduct(
            category="Shirt",
            parent_category="Shirt",
            chest=42,
            length=28,
            shoulder=18,
            sleeve=24,
        )

        measurements = MeasurementExtractor.extract(product)

        assert len(measurements) == 4
        assert ("Tour de poitrine", "42") in measurements
        assert ("Longueur", "28") in measurements
        assert ("Largeur épaules", "18") in measurements
        assert ("Longueur manche", "24") in measurements

    def test_extract_jacket_measurements(self):
        """Test extraction works for jackets too."""
        product = MockProduct(
            category="Jacket",
            parent_category="Jacket",
            chest=44,
            length=30,
        )

        measurements = MeasurementExtractor.extract(product)

        assert len(measurements) == 2
        assert ("Tour de poitrine", "44") in measurements


class TestMeasurementExtractorEyewear:
    """Tests for eyewear (sunglasses) measurements."""

    def test_extract_sunglasses_measurements(self):
        """Test extraction of sunglasses measurements."""
        product = MockProduct(
            category="Sunglasses",
            parent_category="Sunglasses",
            width=140,
            bridge=18,
        )

        measurements = MeasurementExtractor.extract(product)

        assert len(measurements) == 2
        assert ("Largeur", "140") in measurements
        assert ("Pont", "18") in measurements


class TestMeasurementExtractorEdgeCases:
    """Tests for edge cases."""

    def test_extract_no_category(self):
        """Test extraction with no category returns empty list."""
        product = MockProduct()

        measurements = MeasurementExtractor.extract(product)

        assert measurements == []

    def test_extract_unknown_category(self):
        """Test extraction with unknown category returns empty list."""
        product = MockProduct(
            category="UnknownCategory",
            parent_category="UnknownCategory",
            waist=32,
        )

        measurements = MeasurementExtractor.extract(product)

        assert measurements == []

    def test_extract_no_measurements_present(self):
        """Test extraction when no measurement attributes exist."""
        product = MockProduct(
            category="Jeans",
            parent_category="Jeans",
        )

        measurements = MeasurementExtractor.extract(product)

        assert measurements == []

    def test_extract_with_zero_values(self):
        """Test that zero values are not included."""
        product = MockProduct(
            category="Jeans",
            parent_category="Jeans",
            waist=0,
            inseam=34,
        )

        measurements = MeasurementExtractor.extract(product)

        # Only inseam should be included (waist=0 is falsy)
        assert len(measurements) == 1
        assert ("Entrejambe", "34") in measurements
