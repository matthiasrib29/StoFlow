"""
Tests for Product Many-to-Many Attributes

Tests for M2M relationships: colors, materials, condition_sups.

Business Rules Tested (2026-01-07):
- Multiple colors per product (max 5, first = primary)
- Multiple materials per product (max 3, optional percentages)
- Multiple condition_sups per product (max 10)
- FK validation to product_attributes tables
- Duplicate detection
- REPLACE strategy on update
- Helper properties (primary_color, color_list, etc.)
- Dual-write to deprecated columns
- Vinted mapper (colors[] <-> color/color2)
"""

import pytest
from decimal import Decimal
from sqlalchemy.orm import Session

from models.public.brand import Brand
from models.public.category import Category
from models.public.color import Color
from models.public.condition import Condition
from models.public.condition_sup import ConditionSup
from models.public.material import Material
from models.user.product import Product, ProductStatus
from models.user.product_attributes_m2m import (
    ProductColor,
    ProductMaterial,
    ProductConditionSup,
)
from schemas.product_schemas import ProductCreate, ProductUpdate, MaterialDetail
from services.product_service import ProductService
from services.vinted.vinted_mapper import VintedMapper


# ===== FIXTURES =====


@pytest.fixture(scope="function")
def seed_m2m_attributes(db_session: Session):
    """
    Seed attributes for M2M tests.

    Includes colors, materials, condition_sups, and basic attributes.
    """
    # Brands
    brands = [
        Brand(name="Levi's", description="Iconic denim brand"),
        Brand(name="Nike", description="Athletic apparel"),
    ]
    db_session.add_all(brands)

    # Categories
    categories = [
        Category(name_en="Jeans", name_fr="Jeans"),
        Category(name_en="T-Shirts", name_fr="T-Shirts"),
    ]
    db_session.add_all(categories)

    # Conditions
    conditions = [
        Condition(note=10, name_en="New with tags", name_fr="Neuf avec étiquettes", coefficient=1.0),
        Condition(note=8, name_en="Excellent", name_fr="Excellent état", coefficient=0.9),
    ]
    db_session.add_all(conditions)

    # Colors (M2M)
    colors = [
        Color(name_en="Black", name_fr="Noir"),
        Color(name_en="Blue", name_fr="Bleu"),
        Color(name_en="White", name_fr="Blanc"),
        Color(name_en="Red", name_fr="Rouge"),
        Color(name_en="Green", name_fr="Vert"),
    ]
    db_session.add_all(colors)

    # Materials (M2M)
    materials = [
        Material(name_en="Cotton", name_fr="Coton"),
        Material(name_en="Polyester", name_fr="Polyester"),
        Material(name_en="Denim", name_fr="Denim"),
        Material(name_en="Wool", name_fr="Laine"),
    ]
    db_session.add_all(materials)

    # Condition Supplements (M2M)
    condition_sups = [
        ConditionSup(name_en="Faded", name_fr="Décoloré"),
        ConditionSup(name_en="Small hole", name_fr="Petit trou"),
        ConditionSup(name_en="Missing button", name_fr="Bouton manquant"),
        ConditionSup(name_en="Light stain", name_fr="Tache légère"),
    ]
    db_session.add_all(condition_sups)

    db_session.commit()


# ===== TESTS: CREATE WITH M2M =====


class TestProductCreateM2M:
    """Tests for creating products with M2M attributes."""

    def test_create_product_with_multiple_colors(self, db_session: Session, test_user, seed_m2m_attributes):
        """Create product with 3 colors, first should be primary."""
        product_data = ProductCreate(
            title="Test Product - Multiple Colors",
            description="Product with 3 colors",
            price=Decimal("50.00"),
            category="Jeans",
            condition=8,
            brand="Levi's",
            colors=["Black", "Blue", "White"],  # NEW M2M field
            stock_quantity=1,
        )

        product = ProductService.create_product(db_session, product_data, test_user.id)

        # Verify product created
        assert product.id is not None
        assert product.title == "Test Product - Multiple Colors"

        # Verify M2M colors
        assert len(product.product_colors) == 3
        color_names = [pc.color for pc in product.product_colors]
        assert set(color_names) == {"Black", "Blue", "White"}

        # Verify first color is primary
        primary_colors = [pc for pc in product.product_colors if pc.is_primary]
        assert len(primary_colors) == 1
        assert primary_colors[0].color == "Black"

        # Verify helper properties
        assert product.primary_color == "Black"
        assert product.colors == ["Black", "Blue", "White"]

        # Verify DUAL-WRITE: old column filled
        assert product.color == "Black"

    def test_create_product_with_multiple_materials(self, db_session: Session, test_user, seed_m2m_attributes):
        """Create product with 2 materials, no percentages."""
        product_data = ProductCreate(
            title="Test Product - Multiple Materials",
            description="Product with 2 materials",
            price=Decimal("60.00"),
            category="T-Shirts",
            condition=10,
            brand="Nike",
            materials=["Cotton", "Polyester"],  # NEW M2M field
            stock_quantity=1,
        )

        product = ProductService.create_product(db_session, product_data, test_user.id)

        # Verify M2M materials
        assert len(product.product_materials) == 2
        material_names = [pm.material for pm in product.product_materials]
        assert set(material_names) == {"Cotton", "Polyester"}

        # Verify no percentages
        for pm in product.product_materials:
            assert pm.percentage is None

        # Verify helper property
        assert set(product.materials) == {"Cotton", "Polyester"}

        # Verify DUAL-WRITE: old column filled
        assert product.material == "Cotton"

    def test_create_product_with_material_percentages(self, db_session: Session, test_user, seed_m2m_attributes):
        """Create product with materials and percentages."""
        product_data = ProductCreate(
            title="Test Product - Material Percentages",
            description="Product with material composition",
            price=Decimal("70.00"),
            category="Jeans",
            condition=8,
            brand="Levi's",
            material_details=[
                MaterialDetail(material="Cotton", percentage=80),
                MaterialDetail(material="Polyester", percentage=20),
            ],
            stock_quantity=1,
        )

        product = ProductService.create_product(db_session, product_data, test_user.id)

        # Verify M2M materials with percentages
        assert len(product.product_materials) == 2

        material_percentages = {pm.material: pm.percentage for pm in product.product_materials}
        assert material_percentages == {"Cotton": 80, "Polyester": 20}

    def test_create_product_with_condition_sups(self, db_session: Session, test_user, seed_m2m_attributes):
        """Create product with multiple condition supplements."""
        product_data = ProductCreate(
            title="Test Product - Condition Sups",
            description="Product with condition supplements",
            price=Decimal("40.00"),
            category="Jeans",
            condition=8,
            brand="Levi's",
            condition_sups=["Faded", "Small hole"],  # NEW M2M field
            stock_quantity=1,
        )

        product = ProductService.create_product(db_session, product_data, test_user.id)

        # Verify M2M condition_sups
        assert len(product.product_condition_sups) == 2
        condition_sup_names = [pcs.condition_sup for pcs in product.product_condition_sups]
        assert set(condition_sup_names) == {"Faded", "Small hole"}

        # Verify helper property
        assert set(product.condition_sups) == {"Faded", "Small hole"}

        # Verify DUAL-WRITE: old column filled
        assert set(product.condition_sup) == {"Faded", "Small hole"}

    def test_create_product_with_all_m2m_attributes(self, db_session: Session, test_user, seed_m2m_attributes):
        """Create product with colors, materials, and condition_sups."""
        product_data = ProductCreate(
            title="Test Product - All M2M",
            description="Product with all M2M attributes",
            price=Decimal("80.00"),
            category="Jeans",
            condition=8,
            brand="Levi's",
            colors=["Blue", "Black"],
            materials=["Denim", "Cotton"],
            condition_sups=["Faded"],
            stock_quantity=1,
        )

        product = ProductService.create_product(db_session, product_data, test_user.id)

        # Verify all M2M attributes
        assert len(product.product_colors) == 2
        assert len(product.product_materials) == 2
        assert len(product.product_condition_sups) == 1

        # Verify helper properties work
        assert product.primary_color == "Blue"
        assert len(product.colors) == 2
        assert len(product.materials) == 2
        assert len(product.condition_sups) == 1


# ===== TESTS: UPDATE WITH M2M =====


class TestProductUpdateM2M:
    """Tests for updating products with M2M attributes (REPLACE strategy)."""

    def test_update_product_replace_colors(self, db_session: Session, test_user, seed_m2m_attributes):
        """Update product colors - should REPLACE all existing colors."""
        # Create product with initial colors
        product_data = ProductCreate(
            title="Test Product",
            description="Initial product",
            price=Decimal("50.00"),
            category="Jeans",
            condition=8,
            brand="Levi's",
            colors=["Black", "White"],
            stock_quantity=1,
        )
        product = ProductService.create_product(db_session, product_data, test_user.id)

        # Verify initial colors
        assert len(product.product_colors) == 2

        # Update with new colors (REPLACE strategy)
        update_data = ProductUpdate(colors=["Red", "Blue", "Green"])
        updated_product = ProductService.update_product(db_session, product.id, update_data)

        # Verify colors were REPLACED (not added)
        assert len(updated_product.product_colors) == 3
        color_names = [pc.color for pc in updated_product.product_colors]
        assert set(color_names) == {"Red", "Blue", "Green"}

        # Old colors should be gone
        assert "Black" not in color_names
        assert "White" not in color_names

        # New primary color should be first
        assert updated_product.primary_color == "Red"

    def test_update_product_replace_materials(self, db_session: Session, test_user, seed_m2m_attributes):
        """Update product materials - should REPLACE all existing materials."""
        # Create product
        product_data = ProductCreate(
            title="Test Product",
            description="Initial product",
            price=Decimal("50.00"),
            category="Jeans",
            condition=8,
            brand="Levi's",
            materials=["Denim"],
            stock_quantity=1,
        )
        product = ProductService.create_product(db_session, product_data, test_user.id)

        # Update materials
        update_data = ProductUpdate(materials=["Cotton", "Polyester"])
        updated_product = ProductService.update_product(db_session, product.id, update_data)

        # Verify REPLACE
        assert len(updated_product.product_materials) == 2
        material_names = [pm.material for pm in updated_product.product_materials]
        assert set(material_names) == {"Cotton", "Polyester"}
        assert "Denim" not in material_names

    def test_update_product_clear_colors(self, db_session: Session, test_user, seed_m2m_attributes):
        """Update product with empty colors list - should clear all colors."""
        # Create product with colors
        product_data = ProductCreate(
            title="Test Product",
            description="Initial product",
            price=Decimal("50.00"),
            category="Jeans",
            condition=8,
            brand="Levi's",
            colors=["Black", "White"],
            stock_quantity=1,
        )
        product = ProductService.create_product(db_session, product_data, test_user.id)

        # Clear colors
        update_data = ProductUpdate(colors=[])
        updated_product = ProductService.update_product(db_session, product.id, update_data)

        # Verify all colors removed
        assert len(updated_product.product_colors) == 0
        assert updated_product.primary_color is None
        assert updated_product.colors == []


# ===== TESTS: VALIDATION =====


class TestProductM2MValidation:
    """Tests for M2M validation (FK, duplicates)."""

    def test_create_with_invalid_color_raises_error(self, db_session: Session, test_user, seed_m2m_attributes):
        """Creating product with invalid color should raise ValueError."""
        product_data = ProductCreate(
            title="Test Product",
            description="Product with invalid color",
            price=Decimal("50.00"),
            category="Jeans",
            condition=8,
            brand="Levi's",
            colors=["InvalidColor"],  # Does not exist
            stock_quantity=1,
        )

        with pytest.raises(ValueError, match="Color 'InvalidColor' does not exist"):
            ProductService.create_product(db_session, product_data, test_user.id)

    def test_create_with_duplicate_colors_raises_error(self, db_session: Session, test_user, seed_m2m_attributes):
        """Creating product with duplicate colors should raise ValueError."""
        product_data = ProductCreate(
            title="Test Product",
            description="Product with duplicate colors",
            price=Decimal("50.00"),
            category="Jeans",
            condition=8,
            brand="Levi's",
            colors=["Black", "Black"],  # Duplicate
            stock_quantity=1,
        )

        with pytest.raises(ValueError, match="Duplicate colors are not allowed"):
            ProductService.create_product(db_session, product_data, test_user.id)

    def test_create_with_invalid_material_raises_error(self, db_session: Session, test_user, seed_m2m_attributes):
        """Creating product with invalid material should raise ValueError."""
        product_data = ProductCreate(
            title="Test Product",
            description="Product with invalid material",
            price=Decimal("50.00"),
            category="Jeans",
            condition=8,
            brand="Levi's",
            materials=["InvalidMaterial"],
            stock_quantity=1,
        )

        with pytest.raises(ValueError, match="Material 'InvalidMaterial' does not exist"):
            ProductService.create_product(db_session, product_data, test_user.id)

    def test_create_with_invalid_condition_sup_raises_error(self, db_session: Session, test_user, seed_m2m_attributes):
        """Creating product with invalid condition_sup should raise ValueError."""
        product_data = ProductCreate(
            title="Test Product",
            description="Product with invalid condition_sup",
            price=Decimal("50.00"),
            category="Jeans",
            condition=8,
            brand="Levi's",
            condition_sups=["InvalidConditionSup"],
            stock_quantity=1,
        )

        with pytest.raises(ValueError, match="Condition supplement 'InvalidConditionSup' does not exist"):
            ProductService.create_product(db_session, product_data, test_user.id)


# ===== TESTS: HELPER PROPERTIES =====


class TestProductM2MHelperProperties:
    """Tests for helper properties (primary_color, color_list, etc.)."""

    def test_primary_color_returns_first_color(self, db_session: Session, test_user, seed_m2m_attributes):
        """primary_color should return the is_primary=TRUE color."""
        product_data = ProductCreate(
            title="Test Product",
            description="Test",
            price=Decimal("50.00"),
            category="Jeans",
            condition=8,
            brand="Levi's",
            colors=["Red", "Blue", "Green"],
            stock_quantity=1,
        )
        product = ProductService.create_product(db_session, product_data, test_user.id)

        assert product.primary_color == "Red"  # First color

    def test_primary_color_returns_none_when_no_colors(self, db_session: Session, test_user, seed_m2m_attributes):
        """primary_color should return None when no colors."""
        product_data = ProductCreate(
            title="Test Product",
            description="Test",
            price=Decimal("50.00"),
            category="Jeans",
            condition=8,
            brand="Levi's",
            colors=[],
            stock_quantity=1,
        )
        product = ProductService.create_product(db_session, product_data, test_user.id)

        assert product.primary_color is None

    def test_color_list_returns_all_colors(self, db_session: Session, test_user, seed_m2m_attributes):
        """color_list should return all colors as a list."""
        product_data = ProductCreate(
            title="Test Product",
            description="Test",
            price=Decimal("50.00"),
            category="Jeans",
            condition=8,
            brand="Levi's",
            colors=["Black", "White", "Red"],
            stock_quantity=1,
        )
        product = ProductService.create_product(db_session, product_data, test_user.id)

        assert len(product.colors) == 3
        assert set(product.colors) == {"Black", "White", "Red"}

    def test_material_list_returns_all_materials(self, db_session: Session, test_user, seed_m2m_attributes):
        """material_list should return all materials as a list."""
        product_data = ProductCreate(
            title="Test Product",
            description="Test",
            price=Decimal("50.00"),
            category="Jeans",
            condition=8,
            brand="Levi's",
            materials=["Cotton", "Polyester"],
            stock_quantity=1,
        )
        product = ProductService.create_product(db_session, product_data, test_user.id)

        assert len(product.materials) == 2
        assert set(product.materials) == {"Cotton", "Polyester"}


# ===== TESTS: VINTED MAPPER =====


class TestVintedMapperM2M:
    """Tests for Vinted mapper with M2M colors."""

    def test_stoflow_to_vinted_maps_two_colors(self, db_session: Session):
        """StoFlow colors[] should map to Vinted color + color2."""
        stoflow_product = {
            "title": "Test Product",
            "description": "Test",
            "price": 50.00,
            "category": "Jeans",
            "brand": "Levi's",
            "colors": ["Black", "White", "Red"],  # 3 colors
            "condition": 8,
            "gender": "men",
        }

        mapper = VintedMapper.with_db(db_session)
        vinted_product = mapper.stoflow_to_vinted_with_db(stoflow_product, include_dimensions=False)

        # Vinted supports max 2 colors: color + color2
        assert vinted_product["color"] == "Black"  # First color
        assert vinted_product["color2"] == "White"  # Second color
        # Third color "Red" is ignored (Vinted limitation)

    def test_stoflow_to_vinted_single_color(self, db_session: Session):
        """Single color should map to color only, color2=None."""
        stoflow_product = {
            "title": "Test Product",
            "description": "Test",
            "price": 50.00,
            "category": "Jeans",
            "brand": "Levi's",
            "colors": ["Black"],  # Only 1 color
            "condition": 8,
            "gender": "men",
        }

        mapper = VintedMapper.with_db(db_session)
        vinted_product = mapper.stoflow_to_vinted_with_db(stoflow_product, include_dimensions=False)

        assert vinted_product["color"] == "Black"
        assert vinted_product["color2"] is None

    def test_vinted_to_stoflow_extracts_two_colors(self):
        """Vinted color + color2 should map to StoFlow colors[]."""
        vinted_item = {
            "id": 123,
            "title": "Test Product",
            "description": "Test",
            "price": "50.00",
            "brand_title": "Levi's",
            "catalog_id": 1193,
            "status_id": 2,
            "color": "Black",
            "color2": "White",
            "photos": [],
        }

        stoflow_product = VintedMapper.platform_to_stoflow(vinted_item)

        # Should extract both colors into colors[]
        assert "colors" in stoflow_product
        assert stoflow_product["colors"] == ["Black", "White"]
        # DEPRECATED: old color field also filled
        assert stoflow_product["color"] == "Black"

    def test_vinted_to_stoflow_single_color(self):
        """Vinted with only color (no color2) should map correctly."""
        vinted_item = {
            "id": 123,
            "title": "Test Product",
            "description": "Test",
            "price": "50.00",
            "brand_title": "Levi's",
            "catalog_id": 1193,
            "status_id": 2,
            "color": "Black",
            # No color2
            "photos": [],
        }

        stoflow_product = VintedMapper.platform_to_stoflow(vinted_item)

        assert stoflow_product["colors"] == ["Black"]
        assert stoflow_product["color"] == "Black"


# ===== TESTS: BACKWARD COMPATIBILITY =====


class TestProductM2MBackwardCompatibility:
    """Tests for backward compatibility with deprecated fields."""

    def test_create_with_deprecated_color_field(self, db_session: Session, test_user, seed_m2m_attributes):
        """Creating product with old 'color' field should still work."""
        product_data = ProductCreate(
            title="Test Product",
            description="Test",
            price=Decimal("50.00"),
            category="Jeans",
            condition=8,
            brand="Levi's",
            color="Black",  # OLD deprecated field
            stock_quantity=1,
        )

        product = ProductService.create_product(db_session, product_data, test_user.id)

        # Should create M2M entry
        assert len(product.product_colors) == 1
        assert product.product_colors[0].color == "Black"
        assert product.product_colors[0].is_primary is True

    def test_create_prefers_new_colors_over_deprecated_color(self, db_session: Session, test_user, seed_m2m_attributes):
        """When both 'colors' and 'color' provided, should prefer 'colors'."""
        product_data = ProductCreate(
            title="Test Product",
            description="Test",
            price=Decimal("50.00"),
            category="Jeans",
            condition=8,
            brand="Levi's",
            color="Red",  # OLD deprecated field
            colors=["Black", "White"],  # NEW M2M field - should take precedence
            stock_quantity=1,
        )

        product = ProductService.create_product(db_session, product_data, test_user.id)

        # Should use 'colors' (not 'color')
        assert len(product.product_colors) == 2
        color_names = [pc.color for pc in product.product_colors]
        assert set(color_names) == {"Black", "White"}
        assert "Red" not in color_names
