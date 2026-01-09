"""
Unit Tests for ProductService

Tests product CRUD operations, M2M attribute management, and business rules.

Business Rules Tested:
- Auto-incremented ID as unique identifier
- Price calculated automatically if absent (PricingService)
- Size adjusted automatically based on dimensions
- Auto-create size if missing
- Strict FK validation (brand, category, condition must exist)
- Default status: DRAFT
- Soft delete (deleted_at instead of physical deletion)
- SOLD products are immutable
- Optimistic locking (version_number)
- M2M attributes: colors, materials, condition_sups

Created: 2026-01-08
Phase 1.1: Unit testing
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock, patch, call

from models.user.product import Product, ProductStatus
from models.user.product_attributes_m2m import (
    ProductColor,
    ProductMaterial,
    ProductConditionSup,
)
from services.product_service import ProductService
from schemas.product_schemas import ProductCreate, ProductUpdate
from shared.exceptions import ConcurrentModificationError


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_db():
    """Mock database session."""
    session = MagicMock()
    session.query = Mock()
    session.add = Mock()
    session.flush = Mock()
    session.commit = Mock()
    session.refresh = Mock()
    session.execute = Mock()
    session.rollback = Mock()
    return session


@pytest.fixture
def mock_product():
    """Mock Product instance."""
    product = Product(
        id=1,
        title="Vintage Levi's 501 Jeans",
        description="Classic denim jeans from the 90s",
        price=49.99,
        category="Jeans",
        brand="Levi's",
        condition=8,  # Integer 0-10
        size_original="W32/L34",
        gender="male",
        stock_quantity=1,
        status=ProductStatus.DRAFT,
        version_number=1,
        created_at=datetime.now(timezone.utc),
    )
    return product


@pytest.fixture
def mock_product_create():
    """Mock ProductCreate schema."""
    return ProductCreate(
        title="Vintage Levi's 501 Jeans",
        description="Classic denim jeans from the 90s",
        price=49.99,
        category="Jeans",
        brand="Levi's",
        condition=8,  # Integer 0-10
        size_original="W32/L34",
        gender="male",
        colors=["Blue"],
        materials=["Denim"],
        condition_sups=["Vintage wear"],
        stock_quantity=1,
    )


@pytest.fixture
def mock_product_update():
    """Mock ProductUpdate schema."""
    return ProductUpdate(
        title="Updated Title",
        price=59.99,
    )


# =============================================================================
# CREATE PRODUCT TESTS
# =============================================================================


class TestCreateProduct:
    """Tests for ProductService.create_product."""

    @patch('services.product_service.ProductRepository')
    @patch('services.product_service.ProductUtils')
    @patch('services.product_service.AttributeValidator')
    @patch('services.product_service.PricingService')
    def test_create_product_success(
        self, mock_pricing, mock_validator, mock_utils, mock_repo, mock_db, mock_product_create
    ):
        """Should create a product with all attributes."""
        # Setup mocks
        mock_utils.adjust_size.return_value = "W32/L34"
        mock_validator.validate_colors.return_value = ["Blue"]
        mock_validator.validate_materials.return_value = (["Denim"], {"Denim": None})
        mock_validator.validate_condition_sups.return_value = ["Vintage wear"]
        mock_validator.validate_product_attributes.return_value = None

        # Mock flush to set product ID
        def mock_flush():
            pass
        mock_db.flush = mock_flush

        # Mock refresh to return product with ID
        created_product = Product(
            id=1,
            title=mock_product_create.title,
            status=ProductStatus.DRAFT,
        )

        def mock_refresh(product):
            product.id = 1

        mock_db.refresh = mock_refresh

        with patch.object(ProductService, '_create_product_colors'):
            with patch.object(ProductService, '_create_product_materials'):
                with patch.object(ProductService, '_create_product_condition_sups'):
                    result = ProductService.create_product(
                        mock_db, mock_product_create, user_id=1
                    )

        # Verify repository called
        mock_repo.create.assert_called_once()

    @patch('services.product_service.ProductRepository')
    @patch('services.product_service.ProductUtils')
    @patch('services.product_service.AttributeValidator')
    @patch('services.product_service.PricingService')
    def test_create_product_auto_calculates_price(
        self, mock_pricing, mock_validator, mock_utils, mock_repo, mock_db
    ):
        """Should auto-calculate price when not provided."""
        # Create product without price
        product_data = ProductCreate(
            title="Test Product",
            description="Test description",
            category="T-shirt",
            brand="Nike",
            condition=7,  # Integer 0-10
            colors=["White"],
            stock_quantity=1,
        )

        mock_utils.adjust_size.return_value = None
        mock_pricing.calculate_price.return_value = 25.00
        mock_validator.validate_colors.return_value = ["White"]
        mock_validator.validate_materials.return_value = ([], {})
        mock_validator.validate_condition_sups.return_value = []
        mock_validator.validate_product_attributes.return_value = None

        def mock_refresh(product):
            product.id = 1

        mock_db.refresh = mock_refresh

        with patch.object(ProductService, '_create_product_colors'):
            with patch.object(ProductService, '_create_product_materials'):
                with patch.object(ProductService, '_create_product_condition_sups'):
                    ProductService.create_product(mock_db, product_data, user_id=1)

        # Verify pricing service was called
        mock_pricing.calculate_price.assert_called_once()

    @patch('services.product_service.ProductRepository')
    @patch('services.product_service.ProductUtils')
    @patch('services.product_service.AttributeValidator')
    def test_create_product_adjusts_size_with_dimensions(
        self, mock_validator, mock_utils, mock_repo, mock_db
    ):
        """Should adjust size based on dim1/dim6."""
        product_data = ProductCreate(
            title="Test Product",
            description="Test",
            category="Jeans",
            brand="Levi's",
            condition=7,  # Integer 0-10
            price=50.00,
            dim1=32,  # waist
            dim6=34,  # length
            stock_quantity=1,
        )

        mock_utils.adjust_size.return_value = "W32/L34"
        mock_validator.validate_colors.return_value = []
        mock_validator.validate_materials.return_value = ([], {})
        mock_validator.validate_condition_sups.return_value = []
        mock_validator.validate_product_attributes.return_value = None

        def mock_refresh(product):
            product.id = 1

        mock_db.refresh = mock_refresh

        with patch.object(ProductService, '_create_product_colors'):
            with patch.object(ProductService, '_create_product_materials'):
                with patch.object(ProductService, '_create_product_condition_sups'):
                    with patch('repositories.size_original_repository.SizeOriginalRepository'):
                        ProductService.create_product(mock_db, product_data, user_id=1)

        mock_utils.adjust_size.assert_called_once_with(None, 32, 34)

    @patch('services.product_service.ProductRepository')
    @patch('services.product_service.ProductUtils')
    @patch('services.product_service.AttributeValidator')
    def test_create_product_validates_brand_fk(
        self, mock_validator, mock_utils, mock_repo, mock_db
    ):
        """Should validate brand FK exists."""
        product_data = ProductCreate(
            title="Test Product",
            description="Test",
            category="T-shirt",
            brand="InvalidBrand",
            condition=7,  # Integer 0-10
            price=50.00,
            stock_quantity=1,
        )

        mock_utils.adjust_size.return_value = None
        mock_validator.validate_colors.return_value = []
        mock_validator.validate_materials.return_value = ([], {})
        mock_validator.validate_condition_sups.return_value = []
        mock_validator.validate_product_attributes.side_effect = ValueError(
            "Invalid brand: InvalidBrand"
        )

        with pytest.raises(ValueError, match="Invalid brand"):
            ProductService.create_product(mock_db, product_data, user_id=1)

    @patch('services.product_service.ProductRepository')
    @patch('services.product_service.ProductUtils')
    @patch('services.product_service.AttributeValidator')
    def test_create_product_validates_category_fk(
        self, mock_validator, mock_utils, mock_repo, mock_db
    ):
        """Should validate category FK exists."""
        product_data = ProductCreate(
            title="Test Product",
            description="Test",
            category="InvalidCategory",
            brand="Nike",
            condition=7,  # Integer 0-10
            price=50.00,
            stock_quantity=1,
        )

        mock_utils.adjust_size.return_value = None
        mock_validator.validate_colors.return_value = []
        mock_validator.validate_materials.return_value = ([], {})
        mock_validator.validate_condition_sups.return_value = []
        mock_validator.validate_product_attributes.side_effect = ValueError(
            "Invalid category: InvalidCategory"
        )

        with pytest.raises(ValueError, match="Invalid category"):
            ProductService.create_product(mock_db, product_data, user_id=1)

    @patch('services.product_service.ProductRepository')
    @patch('services.product_service.ProductUtils')
    @patch('services.product_service.AttributeValidator')
    def test_create_product_validates_condition_fk(
        self, mock_validator, mock_utils, mock_repo, mock_db
    ):
        """Should validate condition FK exists."""
        product_data = ProductCreate(
            title="Test Product",
            description="Test",
            category="T-shirt",
            brand="Nike",
            condition=9,  # Valid integer, but FK doesn't exist in DB
            price=50.00,
            stock_quantity=1,
        )

        mock_utils.adjust_size.return_value = None
        mock_validator.validate_colors.return_value = []
        mock_validator.validate_materials.return_value = ([], {})
        mock_validator.validate_condition_sups.return_value = []
        mock_validator.validate_product_attributes.side_effect = ValueError(
            "Invalid condition: 9"
        )

        with pytest.raises(ValueError, match="Invalid condition"):
            ProductService.create_product(mock_db, product_data, user_id=1)

    @patch('services.product_service.ProductRepository')
    @patch('services.product_service.ProductUtils')
    @patch('services.product_service.AttributeValidator')
    def test_create_product_default_status_draft(
        self, mock_validator, mock_utils, mock_repo, mock_db
    ):
        """Should set default status to DRAFT."""
        product_data = ProductCreate(
            title="Test Product",
            description="Test",
            category="T-shirt",
            brand="Nike",
            condition=7,  # Integer 0-10
            price=50.00,
            stock_quantity=1,
        )

        mock_utils.adjust_size.return_value = None
        mock_validator.validate_colors.return_value = []
        mock_validator.validate_materials.return_value = ([], {})
        mock_validator.validate_condition_sups.return_value = []
        mock_validator.validate_product_attributes.return_value = None

        def mock_refresh(product):
            product.id = 1

        mock_db.refresh = mock_refresh

        # Capture the product passed to repository
        created_product = None

        def capture_create(db, product):
            nonlocal created_product
            created_product = product

        mock_repo.create.side_effect = capture_create

        with patch.object(ProductService, '_create_product_colors'):
            with patch.object(ProductService, '_create_product_materials'):
                with patch.object(ProductService, '_create_product_condition_sups'):
                    ProductService.create_product(mock_db, product_data, user_id=1)

        assert created_product.status == ProductStatus.DRAFT


# =============================================================================
# CREATE DRAFT FOR UPLOAD TESTS
# =============================================================================


class TestCreateDraftForUpload:
    """Tests for ProductService.create_draft_for_upload."""

    @patch('services.product_service.ProductRepository')
    def test_create_draft_for_upload_success(self, mock_repo, mock_db):
        """Should create minimal draft product."""
        def mock_refresh(product):
            product.id = 1

        mock_db.refresh = mock_refresh

        result = ProductService.create_draft_for_upload(mock_db, user_id=1)

        mock_repo.create.assert_called_once()
        mock_db.commit.assert_called_once()

    @patch('services.product_service.ProductRepository')
    def test_create_draft_for_upload_empty_title(self, mock_repo, mock_db):
        """Draft should have empty title to identify auto-created drafts."""
        created_product = None

        def capture_create(db, product):
            nonlocal created_product
            created_product = product

        mock_repo.create.side_effect = capture_create

        def mock_refresh(product):
            product.id = 1

        mock_db.refresh = mock_refresh

        ProductService.create_draft_for_upload(mock_db, user_id=1)

        assert created_product.title == ""

    @patch('services.product_service.ProductRepository')
    def test_create_draft_for_upload_default_stock(self, mock_repo, mock_db):
        """Draft should have default stock of 1."""
        created_product = None

        def capture_create(db, product):
            nonlocal created_product
            created_product = product

        mock_repo.create.side_effect = capture_create

        def mock_refresh(product):
            product.id = 1

        mock_db.refresh = mock_refresh

        ProductService.create_draft_for_upload(mock_db, user_id=1)

        assert created_product.stock_quantity == 1


# =============================================================================
# GET PRODUCT TESTS
# =============================================================================


class TestGetProductById:
    """Tests for ProductService.get_product_by_id."""

    @patch('services.product_service.ProductRepository')
    def test_get_product_by_id_success(self, mock_repo, mock_db, mock_product):
        """Should return product when found."""
        mock_repo.get_by_id.return_value = mock_product

        result = ProductService.get_product_by_id(mock_db, product_id=1)

        assert result is not None
        assert result.id == 1
        assert result.title == "Vintage Levi's 501 Jeans"
        mock_repo.get_by_id.assert_called_once_with(mock_db, 1)

    @patch('services.product_service.ProductRepository')
    def test_get_product_by_id_not_found(self, mock_repo, mock_db):
        """Should return None when product not found."""
        mock_repo.get_by_id.return_value = None

        result = ProductService.get_product_by_id(mock_db, product_id=999)

        assert result is None

    @patch('services.product_service.ProductRepository')
    def test_get_product_excludes_soft_deleted(self, mock_repo, mock_db):
        """Should not return soft-deleted products (handled by repository)."""
        # Repository excludes soft-deleted by default
        mock_repo.get_by_id.return_value = None

        result = ProductService.get_product_by_id(mock_db, product_id=1)

        assert result is None


# =============================================================================
# LIST PRODUCTS TESTS
# =============================================================================


class TestListProducts:
    """Tests for ProductService.list_products."""

    @patch('services.product_service.ProductRepository')
    def test_list_products_success(self, mock_repo, mock_db, mock_product):
        """Should return list of products with count."""
        mock_repo.list.return_value = ([mock_product], 1)

        products, total = ProductService.list_products(mock_db)

        assert len(products) == 1
        assert total == 1
        mock_repo.list.assert_called_once()

    @patch('services.product_service.ProductRepository')
    def test_list_products_pagination(self, mock_repo, mock_db):
        """Should respect skip and limit parameters."""
        mock_repo.list.return_value = ([], 0)

        ProductService.list_products(mock_db, skip=10, limit=20)

        mock_repo.list.assert_called_once_with(
            mock_db,
            skip=10,
            limit=20,
            status=None,
            category=None,
            brand=None,
        )

    @patch('services.product_service.ProductRepository')
    def test_list_products_filter_by_status(self, mock_repo, mock_db, mock_product):
        """Should filter by status."""
        mock_product.status = ProductStatus.PUBLISHED
        mock_repo.list.return_value = ([mock_product], 1)

        products, total = ProductService.list_products(
            mock_db, status=ProductStatus.PUBLISHED
        )

        mock_repo.list.assert_called_once_with(
            mock_db,
            skip=0,
            limit=100,
            status=ProductStatus.PUBLISHED,
            category=None,
            brand=None,
        )

    @patch('services.product_service.ProductRepository')
    def test_list_products_filter_by_brand(self, mock_repo, mock_db, mock_product):
        """Should filter by brand."""
        mock_repo.list.return_value = ([mock_product], 1)

        products, total = ProductService.list_products(mock_db, brand="Levi's")

        mock_repo.list.assert_called_once_with(
            mock_db,
            skip=0,
            limit=100,
            status=None,
            category=None,
            brand="Levi's",
        )

    @patch('services.product_service.ProductRepository')
    def test_list_products_filter_by_category(self, mock_repo, mock_db, mock_product):
        """Should filter by category."""
        mock_repo.list.return_value = ([mock_product], 1)

        products, total = ProductService.list_products(mock_db, category="Jeans")

        mock_repo.list.assert_called_once_with(
            mock_db,
            skip=0,
            limit=100,
            status=None,
            category="Jeans",
            brand=None,
        )

    @patch('services.product_service.ProductRepository')
    def test_list_products_empty_result(self, mock_repo, mock_db):
        """Should return empty list when no products found."""
        mock_repo.list.return_value = ([], 0)

        products, total = ProductService.list_products(mock_db)

        assert products == []
        assert total == 0


# =============================================================================
# UPDATE PRODUCT TESTS
# =============================================================================


class TestUpdateProduct:
    """Tests for ProductService.update_product."""

    @patch('services.product_service.ProductRepository')
    @patch('services.product_service.ProductStatusManager')
    @patch('services.product_service.AttributeValidator')
    def test_update_product_success(
        self, mock_validator, mock_status_mgr, mock_repo, mock_db, mock_product
    ):
        """Should update product fields."""
        mock_repo.get_by_id.return_value = mock_product
        mock_status_mgr.is_immutable.return_value = False
        mock_validator.validate_product_attributes.return_value = None

        # Mock execute result
        mock_result = Mock()
        mock_result.rowcount = 1
        mock_db.execute.return_value = mock_result

        update_data = ProductUpdate(title="Updated Title", price=59.99)

        result = ProductService.update_product(mock_db, product_id=1, product_data=update_data)

        assert result is not None
        mock_db.execute.assert_called_once()

    @patch('services.product_service.ProductRepository')
    def test_update_product_not_found(self, mock_repo, mock_db):
        """Should return None when product not found."""
        mock_repo.get_by_id.return_value = None

        update_data = ProductUpdate(title="Updated Title")

        result = ProductService.update_product(mock_db, product_id=999, product_data=update_data)

        assert result is None

    @patch('services.product_service.ProductRepository')
    @patch('services.product_service.ProductStatusManager')
    def test_update_sold_product_raises_error(
        self, mock_status_mgr, mock_repo, mock_db, mock_product
    ):
        """Should raise error when trying to update SOLD product."""
        mock_product.status = ProductStatus.SOLD
        mock_repo.get_by_id.return_value = mock_product
        mock_status_mgr.is_immutable.return_value = True

        update_data = ProductUpdate(title="Updated Title")

        with pytest.raises(ValueError, match="Cannot modify SOLD product"):
            ProductService.update_product(mock_db, product_id=1, product_data=update_data)

    @patch('services.product_service.ProductRepository')
    @patch('services.product_service.ProductStatusManager')
    @patch('services.product_service.AttributeValidator')
    def test_update_product_validates_fk(
        self, mock_validator, mock_status_mgr, mock_repo, mock_db, mock_product
    ):
        """Should validate FK attributes on update."""
        mock_repo.get_by_id.return_value = mock_product
        mock_status_mgr.is_immutable.return_value = False
        mock_validator.validate_product_attributes.side_effect = ValueError(
            "Invalid brand: BadBrand"
        )

        update_data = ProductUpdate(brand="BadBrand")

        with pytest.raises(ValueError, match="Invalid brand"):
            ProductService.update_product(mock_db, product_id=1, product_data=update_data)

    @patch('services.product_service.ProductRepository')
    @patch('services.product_service.ProductStatusManager')
    @patch('services.product_service.AttributeValidator')
    def test_update_product_concurrent_modification(
        self, mock_validator, mock_status_mgr, mock_repo, mock_db, mock_product
    ):
        """Should raise ConcurrentModificationError on version mismatch."""
        mock_repo.get_by_id.return_value = mock_product
        mock_status_mgr.is_immutable.return_value = False
        mock_validator.validate_product_attributes.return_value = None

        # Mock execute result with 0 rows affected (version mismatch)
        mock_result = Mock()
        mock_result.rowcount = 0
        mock_db.execute.return_value = mock_result

        update_data = ProductUpdate(title="Updated Title")

        with pytest.raises(ConcurrentModificationError):
            ProductService.update_product(mock_db, product_id=1, product_data=update_data)

    @patch('services.product_service.ProductRepository')
    @patch('services.product_service.ProductStatusManager')
    @patch('services.product_service.AttributeValidator')
    def test_update_product_m2m_colors(
        self, mock_validator, mock_status_mgr, mock_repo, mock_db, mock_product
    ):
        """Should update M2M color entries."""
        mock_repo.get_by_id.return_value = mock_product
        mock_status_mgr.is_immutable.return_value = False
        mock_validator.validate_colors.return_value = ["Red", "Blue"]
        mock_validator.validate_product_attributes.return_value = None

        # Mock execute result
        mock_result = Mock()
        mock_result.rowcount = 1
        mock_db.execute.return_value = mock_result

        update_data = ProductUpdate(colors=["Red", "Blue"])

        with patch.object(ProductService, '_replace_product_colors') as mock_replace:
            ProductService.update_product(mock_db, product_id=1, product_data=update_data)
            mock_replace.assert_called_once_with(mock_db, 1, ["Red", "Blue"])


# =============================================================================
# DELETE PRODUCT TESTS
# =============================================================================


class TestDeleteProduct:
    """Tests for ProductService.delete_product."""

    @patch('services.product_service.ProductRepository')
    def test_delete_product_success(self, mock_repo, mock_db, mock_product):
        """Should soft delete product."""
        mock_repo.get_by_id.return_value = mock_product

        result = ProductService.delete_product(mock_db, product_id=1)

        assert result is True
        mock_repo.soft_delete.assert_called_once_with(mock_db, mock_product)
        mock_db.commit.assert_called_once()

    @patch('services.product_service.ProductRepository')
    def test_delete_product_not_found(self, mock_repo, mock_db):
        """Should return False when product not found."""
        mock_repo.get_by_id.return_value = None

        result = ProductService.delete_product(mock_db, product_id=999)

        assert result is False
        mock_repo.soft_delete.assert_not_called()

    @patch('services.product_service.ProductRepository')
    def test_delete_product_keeps_images(self, mock_repo, mock_db, mock_product):
        """Soft delete should NOT delete images (kept for history)."""
        mock_repo.get_by_id.return_value = mock_product

        ProductService.delete_product(mock_db, product_id=1)

        # Only soft_delete called, no image deletion
        mock_repo.soft_delete.assert_called_once()


# =============================================================================
# M2M HELPER METHODS TESTS
# =============================================================================


class TestCreateProductColors:
    """Tests for ProductService._create_product_colors."""

    def test_create_product_colors_success(self, mock_db):
        """Should create ProductColor entries."""
        ProductService._create_product_colors(mock_db, product_id=1, colors=["Blue", "Red"])

        # Should add 2 color entries
        assert mock_db.add.call_count == 2

    def test_create_product_colors_first_is_primary(self, mock_db):
        """First color should be marked as primary."""
        captured_colors = []

        def capture_add(obj):
            if isinstance(obj, ProductColor):
                captured_colors.append(obj)

        mock_db.add.side_effect = capture_add

        ProductService._create_product_colors(mock_db, product_id=1, colors=["Blue", "Red"])

        assert captured_colors[0].is_primary is True
        assert captured_colors[1].is_primary is False

    def test_create_product_colors_empty_list(self, mock_db):
        """Should not add anything for empty list."""
        ProductService._create_product_colors(mock_db, product_id=1, colors=[])

        mock_db.add.assert_not_called()


class TestCreateProductMaterials:
    """Tests for ProductService._create_product_materials."""

    def test_create_product_materials_success(self, mock_db):
        """Should create ProductMaterial entries."""
        ProductService._create_product_materials(
            mock_db,
            product_id=1,
            materials=["Cotton", "Polyester"],
            percentages={"Cotton": 60, "Polyester": 40}
        )

        assert mock_db.add.call_count == 2

    def test_create_product_materials_with_percentages(self, mock_db):
        """Should assign percentages to materials."""
        captured_materials = []

        def capture_add(obj):
            if isinstance(obj, ProductMaterial):
                captured_materials.append(obj)

        mock_db.add.side_effect = capture_add

        ProductService._create_product_materials(
            mock_db,
            product_id=1,
            materials=["Cotton", "Polyester"],
            percentages={"Cotton": 60, "Polyester": 40}
        )

        cotton = next(m for m in captured_materials if m.material == "Cotton")
        polyester = next(m for m in captured_materials if m.material == "Polyester")

        assert cotton.percentage == 60
        assert polyester.percentage == 40

    def test_create_product_materials_empty_list(self, mock_db):
        """Should not add anything for empty list."""
        ProductService._create_product_materials(mock_db, product_id=1, materials=[], percentages={})

        mock_db.add.assert_not_called()


class TestCreateProductConditionSups:
    """Tests for ProductService._create_product_condition_sups."""

    def test_create_product_condition_sups_success(self, mock_db):
        """Should create ProductConditionSup entries."""
        ProductService._create_product_condition_sups(
            mock_db,
            product_id=1,
            condition_sups=["Vintage wear", "Light discoloration"]
        )

        assert mock_db.add.call_count == 2

    def test_create_product_condition_sups_empty_list(self, mock_db):
        """Should not add anything for empty list."""
        ProductService._create_product_condition_sups(mock_db, product_id=1, condition_sups=[])

        mock_db.add.assert_not_called()


class TestReplaceProductColors:
    """Tests for ProductService._replace_product_colors."""

    def test_replace_product_colors_deletes_existing(self, mock_db):
        """Should delete existing colors before creating new ones."""
        # Mock query chain
        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query

        with patch.object(ProductService, '_create_product_colors') as mock_create:
            ProductService._replace_product_colors(mock_db, product_id=1, new_colors=["Red"])

            mock_filter.delete.assert_called_once()
            mock_create.assert_called_once_with(mock_db, 1, ["Red"])


class TestReplaceProductMaterials:
    """Tests for ProductService._replace_product_materials."""

    def test_replace_product_materials_deletes_existing(self, mock_db):
        """Should delete existing materials before creating new ones."""
        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query

        with patch.object(ProductService, '_create_product_materials') as mock_create:
            ProductService._replace_product_materials(
                mock_db,
                product_id=1,
                new_materials=["Cotton"],
                percentages={"Cotton": 100}
            )

            mock_filter.delete.assert_called_once()
            mock_create.assert_called_once()


class TestReplaceProductConditionSups:
    """Tests for ProductService._replace_product_condition_sups."""

    def test_replace_product_condition_sups_deletes_existing(self, mock_db):
        """Should delete existing condition_sups before creating new ones."""
        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query

        with patch.object(ProductService, '_create_product_condition_sups') as mock_create:
            ProductService._replace_product_condition_sups(
                mock_db,
                product_id=1,
                new_condition_sups=["Vintage wear"]
            )

            mock_filter.delete.assert_called_once()
            mock_create.assert_called_once_with(mock_db, 1, ["Vintage wear"])


# =============================================================================
# DELEGATED METHODS TESTS
# =============================================================================


class TestDelegatedMethods:
    """Tests for delegated methods (to specialized services)."""

    @patch('services.product_service.ProductImageService')
    def test_add_image_delegates(self, mock_image_service, mock_db):
        """Should delegate to ProductImageService."""
        mock_image_service.add_image.return_value = {"url": "http://example.com/img.jpg"}

        result = ProductService.add_image(mock_db, product_id=1, image_url="http://example.com/img.jpg")

        mock_image_service.add_image.assert_called_once_with(mock_db, 1, "http://example.com/img.jpg", None)

    @patch('services.product_service.ProductImageService')
    def test_delete_image_delegates(self, mock_image_service, mock_db):
        """Should delegate to ProductImageService."""
        mock_image_service.delete_image.return_value = True

        result = ProductService.delete_image(mock_db, product_id=1, image_url="http://example.com/img.jpg")

        mock_image_service.delete_image.assert_called_once_with(mock_db, 1, "http://example.com/img.jpg")

    @patch('services.product_service.ProductImageService')
    def test_reorder_images_delegates(self, mock_image_service, mock_db):
        """Should delegate to ProductImageService."""
        mock_image_service.reorder_images.return_value = []

        urls = ["http://example.com/1.jpg", "http://example.com/2.jpg"]
        result = ProductService.reorder_images(mock_db, product_id=1, ordered_urls=urls)

        mock_image_service.reorder_images.assert_called_once_with(mock_db, 1, urls)

    @patch('services.product_service.ProductStatusManager')
    def test_update_product_status_delegates(self, mock_status_mgr, mock_db, mock_product):
        """Should delegate to ProductStatusManager."""
        mock_status_mgr.update_status.return_value = mock_product

        result = ProductService.update_product_status(mock_db, product_id=1, new_status=ProductStatus.PUBLISHED)

        mock_status_mgr.update_status.assert_called_once_with(mock_db, 1, ProductStatus.PUBLISHED)


# =============================================================================
# EDGE CASES AND BUSINESS RULES
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    @patch('services.product_service.ProductRepository')
    @patch('services.product_service.ProductUtils')
    @patch('services.product_service.AttributeValidator')
    def test_create_product_with_deprecated_color_field(
        self, mock_validator, mock_utils, mock_repo, mock_db
    ):
        """Should handle deprecated single color field (convert to list)."""
        # ProductCreate with single color instead of colors list
        product_data = ProductCreate(
            title="Test Product",
            description="Test",
            category="T-shirt",
            brand="Nike",
            condition=7,  # Integer 0-10
            price=50.00,
            color="Blue",  # deprecated single color
            stock_quantity=1,
        )

        mock_utils.adjust_size.return_value = None
        mock_validator.validate_colors.return_value = ["Blue"]
        mock_validator.validate_materials.return_value = ([], {})
        mock_validator.validate_condition_sups.return_value = []
        mock_validator.validate_product_attributes.return_value = None

        def mock_refresh(product):
            product.id = 1

        mock_db.refresh = mock_refresh

        with patch.object(ProductService, '_create_product_colors') as mock_create_colors:
            with patch.object(ProductService, '_create_product_materials'):
                with patch.object(ProductService, '_create_product_condition_sups'):
                    ProductService.create_product(mock_db, product_data, user_id=1)

        # Should have validated ["Blue"] (converted from single value)
        mock_validator.validate_colors.assert_called()

    @patch('services.product_service.ProductRepository')
    @patch('services.product_service.ProductUtils')
    @patch('services.product_service.AttributeValidator')
    def test_create_product_normalizes_empty_m2m_fields(
        self, mock_validator, mock_utils, mock_repo, mock_db
    ):
        """Should normalize None and [] as equivalent for M2M fields."""
        product_data = ProductCreate(
            title="Test Product",
            description="Test",
            category="T-shirt",
            brand="Nike",
            condition=7,  # Integer 0-10
            price=50.00,
            colors=None,  # None should be treated as []
            materials=None,
            condition_sups=None,
            stock_quantity=1,
        )

        mock_utils.adjust_size.return_value = None
        mock_validator.validate_colors.return_value = []
        mock_validator.validate_materials.return_value = ([], {})
        mock_validator.validate_condition_sups.return_value = []
        mock_validator.validate_product_attributes.return_value = None

        def mock_refresh(product):
            product.id = 1

        mock_db.refresh = mock_refresh

        with patch.object(ProductService, '_create_product_colors') as mock_colors:
            with patch.object(ProductService, '_create_product_materials') as mock_materials:
                with patch.object(ProductService, '_create_product_condition_sups') as mock_cond:
                    ProductService.create_product(mock_db, product_data, user_id=1)

        # validate_colors should be called with empty list (normalized from None)
        mock_validator.validate_colors.assert_called_once()
