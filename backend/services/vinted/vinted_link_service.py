"""
Vinted Link Service

Service pour lier/délier les produits Vinted aux produits Stoflow.

Business Rules:
- Un VintedProduct peut être lié à max 1 Product (relation 1:1)
- Un Product peut être lié à max 1 VintedProduct (relation 1:1)
- La liaison est passive (pas de sync automatique)
- Création depuis Vinted: mappe les attributs via BDD (condition, category, etc.)

Author: Claude
Date: 2025-01-03
"""

from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from models.user.product import Product
from models.user.vinted_product import VintedProduct
from repositories.vinted_mapping_repository import VintedMappingRepository
from services.vinted.vinted_mapping_service import VintedMappingService
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class VintedLinkService:
    """
    Service pour gérer la liaison entre VintedProduct et Product.
    """

    def __init__(self, db: Session):
        """
        Initialize service with database session.

        Args:
            db: SQLAlchemy session (user schema)
        """
        self.db = db
        self._mapping_repo = VintedMappingRepository(db)

    def link_to_existing_product(
        self,
        vinted_id: int,
        product_id: int
    ) -> VintedProduct:
        """
        Lie un VintedProduct à un Product existant.

        Args:
            vinted_id: ID Vinted du produit
            product_id: ID du Product Stoflow à lier

        Returns:
            VintedProduct mis à jour

        Raises:
            ValueError: Si VintedProduct ou Product non trouvé
            ValueError: Si VintedProduct déjà lié à un autre Product
            ValueError: Si Product déjà lié à un autre VintedProduct
        """
        # Get VintedProduct
        vinted_product = self.db.query(VintedProduct).filter(
            VintedProduct.vinted_id == vinted_id
        ).first()

        if not vinted_product:
            raise ValueError(f"VintedProduct #{vinted_id} not found")

        # Check if already linked to a different product
        if vinted_product.product_id and vinted_product.product_id != product_id:
            raise ValueError(
                f"VintedProduct #{vinted_id} is already linked to Product #{vinted_product.product_id}"
            )

        # Get Product
        product = self.db.query(Product).filter(
            Product.id == product_id,
            Product.deleted_at.is_(None)
        ).first()

        if not product:
            raise ValueError(f"Product #{product_id} not found")

        # Check if Product is already linked to a different VintedProduct
        existing_vinted = self.db.query(VintedProduct).filter(
            VintedProduct.product_id == product_id,
            VintedProduct.id != vinted_product.id
        ).first()

        if existing_vinted:
            raise ValueError(
                f"Product #{product_id} is already linked to VintedProduct #{existing_vinted.vinted_id}"
            )

        # Link
        vinted_product.product_id = product_id
        self.db.flush()

        logger.info(f"Linked VintedProduct #{vinted_id} to Product #{product_id}")

        return vinted_product

    def unlink(self, vinted_id: int) -> VintedProduct:
        """
        Délie un VintedProduct de son Product.

        Args:
            vinted_id: ID Vinted du produit

        Returns:
            VintedProduct mis à jour

        Raises:
            ValueError: Si VintedProduct non trouvé
            ValueError: Si VintedProduct n'est pas lié
        """
        vinted_product = self.db.query(VintedProduct).filter(
            VintedProduct.vinted_id == vinted_id
        ).first()

        if not vinted_product:
            raise ValueError(f"VintedProduct #{vinted_id} not found")

        if not vinted_product.product_id:
            raise ValueError(f"VintedProduct #{vinted_id} is not linked to any Product")

        old_product_id = vinted_product.product_id
        vinted_product.product_id = None
        self.db.flush()

        logger.info(f"Unlinked VintedProduct #{vinted_id} from Product #{old_product_id}")

        return vinted_product

    def create_product_from_vinted(
        self,
        vinted_id: int,
        override_data: Optional[dict] = None
    ) -> tuple[Product, VintedProduct]:
        """
        Crée un Product Stoflow à partir des données VintedProduct et les lie.

        Args:
            vinted_id: ID Vinted du produit source
            override_data: Données à remplacer (optionnel)

        Returns:
            Tuple (Product créé, VintedProduct mis à jour)

        Raises:
            ValueError: Si VintedProduct non trouvé
            ValueError: Si VintedProduct déjà lié
        """
        # Get VintedProduct
        vinted_product = self.db.query(VintedProduct).filter(
            VintedProduct.vinted_id == vinted_id
        ).first()

        if not vinted_product:
            raise ValueError(f"VintedProduct #{vinted_id} not found")

        if vinted_product.product_id:
            raise ValueError(
                f"VintedProduct #{vinted_id} is already linked to Product #{vinted_product.product_id}"
            )

        # Map Vinted data to Stoflow format
        product_data = self._map_vinted_to_stoflow(vinted_product)

        # Apply overrides
        if override_data:
            product_data.update(override_data)

        # Create Product
        product = Product(**product_data)
        self.db.add(product)
        self.db.flush()

        # Link
        vinted_product.product_id = product.id
        self.db.flush()

        logger.info(
            f"Created Product #{product.id} from VintedProduct #{vinted_id} and linked"
        )

        return product, vinted_product

    def _map_vinted_to_stoflow(self, vinted_product: VintedProduct) -> dict:
        """
        Mappe les données VintedProduct vers le format Product Stoflow.

        Utilise les tables de mapping en BDD pour TOUS les attributs FK.
        Garantit que seules les valeurs existantes en BDD sont utilisées.

        Args:
            vinted_product: VintedProduct source

        Returns:
            dict: Données pour créer un Product
        """
        # Reverse lookup category via BDD (using catalog_id)
        category, gender = self._mapping_repo.reverse_map_category(
            vinted_product.catalog_id
        ) if vinted_product.catalog_id else (None, None)

        # Reverse lookup condition via BDD (using condition_id)
        condition = VintedMappingService.reverse_map_condition(
            self.db,
            vinted_product.condition_id
        )

        # Reverse lookup brand via BDD (using brand_id)
        brand = VintedMappingService.reverse_map_brand(
            self.db,
            vinted_product.brand_id
        )

        # Reverse lookup color via BDD (using color1_id)
        color = VintedMappingService.reverse_map_color(
            self.db,
            vinted_product.color1_id
        )

        # Validate material exists in BDD (no vinted_id, so validate by name)
        material = VintedMappingService.reverse_map_material(
            self.db,
            vinted_product.material
        )

        # Reverse lookup size via BDD (using size_id)
        size_normalized = VintedMappingService.reverse_map_size(
            self.db,
            vinted_product.size_id
        )

        # Build product data
        product_data = {
            "title": vinted_product.title or "Untitled",
            "description": vinted_product.description or "",
            "price": Decimal(str(vinted_product.price)) if vinted_product.price else Decimal("0"),

            # All attributes mapped via BDD (FK-safe)
            "category": category or "other",
            "gender": gender,
            "condition": condition,
            "brand": brand,
            "color": color,
            "material": material,
            "size_normalized": size_normalized,

            # Direct copy (no FK constraint) - keep original text
            "size_original": vinted_product.size,

            # Dimensions
            "dim1": vinted_product.measurement_width,
            "dim2": vinted_product.measurement_length,

            # Stock (Vinted = always 1 unique item)
            "stock_quantity": 1,
        }

        # Remove None values to use defaults
        product_data = {k: v for k, v in product_data.items() if v is not None}

        return product_data

    def get_linkable_products(
        self,
        search: Optional[str] = None,
        limit: int = 20
    ) -> list[Product]:
        """
        Récupère les produits Stoflow pouvant être liés.

        Exclut les produits déjà liés à un VintedProduct.

        Args:
            search: Recherche textuelle (titre, marque)
            limit: Nombre max de résultats

        Returns:
            Liste de Products non liés
        """
        # Subquery: product_ids already linked
        linked_ids = self.db.query(VintedProduct.product_id).filter(
            VintedProduct.product_id.isnot(None)
        ).subquery()

        # Query products not linked
        query = self.db.query(Product).filter(
            Product.deleted_at.is_(None),
            Product.id.notin_(linked_ids)
        )

        # Search filter
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Product.title.ilike(search_term)) |
                (Product.brand.ilike(search_term))
            )

        # Order by most recent
        query = query.order_by(Product.created_at.desc())

        return query.limit(limit).all()


__all__ = ["VintedLinkService"]
