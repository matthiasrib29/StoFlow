"""
Tests unitaires pour les schemas de produit.

Couverture:
- ProductCreate validation (champs obligatoires, XSS protection)
- ProductUpdate validation
- ProductResponse structure
- ProductImageItem (JSONB structure)

Author: Claude
Date: 2025-12-10
Updated: 2026-01-03 - Migration vers JSONB pour les images
"""

import pytest
from decimal import Decimal
from datetime import datetime
from pydantic import ValidationError

from schemas.product_schemas import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductImageItem,
    ProductListResponse,
)


class TestProductImageItem:
    """Tests pour le schema ProductImageItem (JSONB)."""

    def test_valid_image_item(self):
        """Test image item valide."""
        image = ProductImageItem(
            url="https://cdn.stoflow.io/1/products/5/abc123.jpg",
            order=0,
            created_at=datetime.now()
        )

        assert image.url == "https://cdn.stoflow.io/1/products/5/abc123.jpg"
        assert image.order == 0

    def test_negative_order_rejected(self):
        """Test que order négatif est rejeté."""
        with pytest.raises(ValidationError):
            ProductImageItem(
                url="https://cdn.stoflow.io/1/products/5/abc123.jpg",
                order=-1,
                created_at=datetime.now()
            )

    def test_missing_url_rejected(self):
        """Test que url manquant est rejeté."""
        with pytest.raises(ValidationError):
            ProductImageItem(
                order=0,
                created_at=datetime.now()
            )


class TestProductCreateRequiredFields:
    """Tests pour les champs obligatoires de ProductCreate."""

    def test_valid_product_minimal(self):
        """Test produit valide avec champs minimaux obligatoires."""
        product = ProductCreate(
            title="Test Product",
            description="Test description",
            category="Jeans",
            condition=8,  # 8 = Très bon état (EXCELLENT)
            brand="Levi's",
            size_original="32",
            color="Blue"
        )

        assert product.title == "Test Product"
        assert product.category == "Jeans"
        assert product.stock_quantity == 1  # default

    def test_missing_title(self):
        """Test sans titre."""
        with pytest.raises(ValidationError) as exc_info:
            ProductCreate(
                description="Test description",
                category="Jeans",
                condition=8,
                brand="Levi's",
                size_original="32",
                color="Blue"
            )

        assert "title" in str(exc_info.value).lower()

    def test_missing_description(self):
        """Test sans description."""
        with pytest.raises(ValidationError) as exc_info:
            ProductCreate(
                title="Test Product",
                category="Jeans",
                condition=8,
                brand="Levi's",
                size_original="32",
                color="Blue"
            )

        assert "description" in str(exc_info.value).lower()

    def test_missing_category(self):
        """Test sans catégorie."""
        with pytest.raises(ValidationError) as exc_info:
            ProductCreate(
                title="Test Product",
                description="Test description",
                condition=8,
                brand="Levi's",
                size_original="32",
                color="Blue"
            )

        assert "category" in str(exc_info.value).lower()

    def test_missing_condition(self):
        """Test sans condition."""
        with pytest.raises(ValidationError) as exc_info:
            ProductCreate(
                title="Test Product",
                description="Test description",
                category="Jeans",
                brand="Levi's",
                size_original="32",
                color="Blue"
            )

        assert "condition" in str(exc_info.value).lower()

    def test_optional_brand(self):
        """Test que brand est optionnel."""
        # brand est maintenant optionnel - pas d'erreur attendue
        product = ProductCreate(
            title="Test Product",
            description="Test description",
            category="Jeans",
            condition=8,
            size_original="32",
            color="Blue"
        )
        assert product.brand is None

    def test_optional_size_original(self):
        """Test que size_original est optionnel."""
        # size_original est maintenant optionnel - pas d'erreur attendue
        product = ProductCreate(
            title="Test Product",
            description="Test description",
            category="Jeans",
            condition=8,
            brand="Levi's",
            color="Blue"
        )
        assert product.size_original is None

    def test_optional_color(self):
        """Test que color est optionnel."""
        # color est maintenant optionnel - pas d'erreur attendue
        product = ProductCreate(
            title="Test Product",
            description="Test description",
            category="Jeans",
            condition=8,
            brand="Levi's",
            size_original="32"
        )
        assert product.color is None


class TestProductCreateXSSProtection:
    """Tests pour la protection XSS dans ProductCreate."""

    def test_title_with_html_rejected(self):
        """Test titre avec HTML rejeté."""
        with pytest.raises(ValidationError) as exc_info:
            ProductCreate(
                title="<script>alert('xss')</script>",
                description="Normal description",
                category="Jeans",
                condition=8,
                brand="Levi's",
                size_original="32",
                color="Blue"
            )

        assert "HTML" in str(exc_info.value)

    def test_description_with_html_rejected(self):
        """Test description avec HTML rejetée."""
        with pytest.raises(ValidationError) as exc_info:
            ProductCreate(
                title="Normal title",
                description="<iframe src='evil.com'></iframe>",
                category="Jeans",
                condition=8,
                brand="Levi's",
                size_original="32",
                color="Blue"
            )

        assert "HTML" in str(exc_info.value)

    def test_title_with_angle_brackets_rejected(self):
        """Test titre avec < et > rejeté."""
        with pytest.raises(ValidationError) as exc_info:
            ProductCreate(
                title="Test <Product>",
                description="Normal description",
                category="Jeans",
                condition=8,
                brand="Levi's",
                size_original="32",
                color="Blue"
            )

        assert "HTML" in str(exc_info.value) or "forbidden" in str(exc_info.value).lower()

    def test_condition_sup_with_html_rejected(self):
        """Test condition_sup avec HTML rejeté."""
        with pytest.raises(ValidationError) as exc_info:
            ProductCreate(
                title="Normal title",
                description="Normal description",
                category="Jeans",
                condition=8,
                brand="Levi's",
                size_original="32",
                color="Blue",
                condition_sup=["<b>Bad</b>"]
            )

        assert "HTML" in str(exc_info.value)

    def test_normal_text_allowed(self):
        """Test texte normal accepté."""
        product = ProductCreate(
            title="Levi's 501 Vintage Jeans - Great Condition!",
            description="These are amazing jeans (1990s) - 100% cotton. Size: W32 L34.",
            category="Jeans",
            condition=8,
            brand="Levi's",
            size_original="32",
            color="Blue"
        )

        assert "amazing" in product.description


class TestProductCreateOptionalFields:
    """Tests pour les champs optionnels de ProductCreate."""

    def test_all_optional_fields(self):
        """Test avec tous les champs optionnels."""
        product = ProductCreate(
            title="Complete Product",
            description="Full description with all fields",
            price=Decimal("49.99"),
            category="Jeans",
            condition=8,
            brand="Levi's",
            size_original="32",
            color="Blue",
            material="Denim",
            fit="Regular",
            gender="Men",
            season="All Season",
            condition_sup=["Minor wear"],
            rise="Mid Rise",
            closure="Button",
            sleeve_length=None,
            origin="USA",
            decade="90s",
            trend="Vintage",
            location="A3",
            model="501",
            dim1=32,
            dim2=80,
            dim3=None,
            dim4=32,
            dim5=40,
            dim6=34,
            stock_quantity=5
        )

        assert product.price == Decimal("49.99")
        assert product.material == "Denim"
        assert product.stock_quantity == 5

    def test_price_can_be_none(self):
        """Test que le prix peut être None (calculé auto)."""
        product = ProductCreate(
            title="Test",
            description="Test",
            price=None,
            category="Jeans",
            condition=8,
            brand="Levi's",
            size_original="32",
            color="Blue"
        )

        assert product.price is None

    def test_price_must_be_positive(self):
        """Test que le prix doit être positif."""
        with pytest.raises(ValidationError):
            ProductCreate(
                title="Test",
                description="Test",
                price=Decimal("0"),
                category="Jeans",
                condition=8,
                brand="Levi's",
                size_original="32",
                color="Blue"
            )

    def test_stock_default_is_one(self):
        """Test que le stock par défaut est 1."""
        product = ProductCreate(
            title="Test",
            description="Test",
            category="Jeans",
            condition=8,
            brand="Levi's",
            size_original="32",
            color="Blue"
        )

        assert product.stock_quantity == 1

    def test_stock_cannot_be_negative(self):
        """Test que le stock ne peut pas être négatif."""
        with pytest.raises(ValidationError):
            ProductCreate(
                title="Test",
                description="Test",
                category="Jeans",
                condition=8,
                brand="Levi's",
                size_original="32",
                color="Blue",
                stock_quantity=-1
            )

    def test_dimensions_must_be_positive(self):
        """Test que les dimensions doivent être positives."""
        with pytest.raises(ValidationError):
            ProductCreate(
                title="Test",
                description="Test",
                category="Jeans",
                condition=8,
                brand="Levi's",
                size_original="32",
                color="Blue",
                dim1=-5
            )


class TestProductUpdate:
    """Tests pour le schema ProductUpdate."""

    def test_all_fields_optional(self):
        """Test que tous les champs sont optionnels."""
        update = ProductUpdate()

        # Tous les champs doivent être None par défaut
        assert update.title is None
        assert update.description is None
        assert update.price is None
        assert update.category is None

    def test_partial_update(self):
        """Test mise à jour partielle."""
        update = ProductUpdate(title="New Title", price=Decimal("59.99"))

        assert update.title == "New Title"
        assert update.price == Decimal("59.99")
        assert update.description is None

    def test_xss_protection_on_update(self):
        """Test protection XSS sur update."""
        with pytest.raises(ValidationError):
            ProductUpdate(title="<script>evil()</script>")

    def test_price_validation_on_update(self):
        """Test validation prix sur update."""
        with pytest.raises(ValidationError):
            ProductUpdate(price=Decimal("0"))


class TestProductResponse:
    """Tests pour le schema ProductResponse."""

    def test_from_attributes(self):
        """Test que from_attributes est activé."""
        # Créer un mock qui simule un objet ORM
        class MockProduct:
            id = 1
            title = "Test Product"
            description = "Test description"
            price = Decimal("29.99")
            category = "Jeans"
            brand = "Levi's"
            condition = 8  # 8 = Très bon état
            size_normalized = None
            size_original = "32"
            color = "Blue"
            material = None
            fit = None
            gender = None
            season = None
            condition_sup = None
            rise = None
            closure = None
            sleeve_length = None
            origin = None
            decade = None
            trend = None
            location = None
            model = None
            pattern = None
            neckline = None
            length = None
            sport = None
            unique_feature = None
            dim1 = None
            dim2 = None
            dim3 = None
            dim4 = None
            dim5 = None
            dim6 = None
            stock_quantity = 1
            status = "draft"
            sold_at = None
            deleted_at = None
            created_at = datetime.now()
            updated_at = datetime.now()
            images = []  # JSONB: [{url, order, created_at}, ...]

        response = ProductResponse.model_validate(MockProduct())

        assert response.id == 1
        assert response.title == "Test Product"
        assert response.price == Decimal("29.99")
        assert response.images == []


class TestProductListResponse:
    """Tests pour le schema ProductListResponse."""

    def test_list_response_structure(self):
        """Test structure de la réponse liste."""
        response = ProductListResponse(
            products=[],
            total=42,
            page=1,
            page_size=20,
            total_pages=3
        )

        assert response.total == 42
        assert response.page == 1
        assert response.page_size == 20
        assert response.total_pages == 3
        assert len(response.products) == 0


class TestProductCreateFieldLengths:
    """Tests pour les limites de longueur des champs."""

    def test_title_max_length(self):
        """Test longueur maximale du titre."""
        with pytest.raises(ValidationError):
            ProductCreate(
                title="A" * 501,  # > 500
                description="Test",
                category="Jeans",
                condition=8,
                brand="Levi's",
                size_original="32",
                color="Blue"
            )

    def test_title_min_length(self):
        """Test longueur minimale du titre."""
        with pytest.raises(ValidationError):
            ProductCreate(
                title="",  # empty
                description="Test",
                category="Jeans",
                condition=8,
                brand="Levi's",
                size_original="32",
                color="Blue"
            )

    def test_category_max_length(self):
        """Test longueur maximale de la catégorie."""
        with pytest.raises(ValidationError):
            ProductCreate(
                title="Test",
                description="Test",
                category="A" * 256,  # > 255
                condition=8,
                brand="Levi's",
                size_original="32",
                color="Blue"
            )

    def test_brand_max_length(self):
        """Test longueur maximale de la marque."""
        with pytest.raises(ValidationError):
            ProductCreate(
                title="Test",
                description="Test",
                category="Jeans",
                condition=8,
                brand="A" * 101,  # > 100
                size_original="32",
                color="Blue"
            )
