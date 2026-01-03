"""
Product Service

Service pour la logique métier des produits.

Business Rules (Updated 2025-12-09):
- ID auto-incrémenté comme identifiant unique (PostgreSQL SERIAL)
- Prix calculé automatiquement si absent
- Taille ajustée automatiquement selon dimensions
- Auto-création size si manquante
- Validation automatique des FK (brand, category, condition doivent exister)
- Status MVP: DRAFT, PUBLISHED, SOLD, ARCHIVED uniquement
- Soft delete (deleted_at au lieu de suppression physique)
"""

from decimal import Decimal
from typing import Optional

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from models.public.brand import Brand
from models.public.category import Category
from models.public.color import Color
from models.public.condition import Condition
from models.public.fit import Fit
from models.public.gender import Gender
from shared.datetime_utils import utc_now
from models.public.material import Material
from models.public.season import Season
from models.public.size import Size
from models.user.product import Product, ProductStatus
from services.validators import AttributeValidator
from schemas.product_schemas import ProductCreate, ProductUpdate
from services.product_utils import ProductUtils
from services.pricing_service import PricingService
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class ProductService:
    """Service pour gérer les produits."""

    # Statuts autorisés pour MVP
    MVP_STATUSES = [
        ProductStatus.DRAFT,
        ProductStatus.PUBLISHED,
        ProductStatus.SOLD,
        ProductStatus.ARCHIVED,
    ]

    @staticmethod
    def create_product(db: Session, product_data: ProductCreate, user_id: int) -> Product:
        """
        Crée un nouveau produit avec toutes les fonctionnalités PostEditFlet.

        Business Rules (Updated 2025-12-09):
        - ID auto-incrémenté comme identifiant unique (PostgreSQL SERIAL)
        - Prix calculé automatiquement si absent (PricingService)
        - Taille ajustée automatiquement si dim1/dim6 fournis (W{dim1}/L{dim6})
        - Auto-création size si manquante (pièce unique vintage)
        - Validation stricte brand (pas d'auto-création)
        - Status par défaut: DRAFT
        - stock_quantity par défaut: 1 (pièce unique)

        Args:
            db: Session SQLAlchemy
            product_data: Données du produit à créer
            user_id: ID de l'utilisateur (pour schema user_X)

        Returns:
            Product: Le produit créé

        Raises:
            ValueError: Si un attribut FK est invalide (brand, category, condition, etc.)
        """
        import time
        start_time = time.time()

        logger.info(
            f"[ProductService] Starting create_product: user_id={user_id}, "
            f"title={product_data.title[:50] if product_data.title else 'N/A'}, "
            f"category={product_data.category}, brand={product_data.brand}"
        )

        schema_name = f"user_{user_id}"

        # ===== 1. AJUSTER TAILLE SI DIMENSIONS FOURNIES (Business Rule 2025-12-09) =====
        size_original = ProductUtils.adjust_size(
            product_data.size_original,
            product_data.dim1,
            product_data.dim6
        )

        # ===== 2. AUTO-CRÉER SIZE SI MANQUANTE (Business Rule 2025-12-09) =====
        if size_original:
            size_exists = db.query(Size).filter(Size.name == size_original).first()
            if not size_exists:
                new_size = Size(name=size_original, name_fr=None)
                db.add(new_size)
                db.commit()

        # ===== 3. CALCULER PRIX SI ABSENT (Business Rule 2025-12-09) =====
        price = product_data.price
        if not price:
            # Calculer automatiquement
            price = PricingService.calculate_price(
                db=db,
                brand=product_data.brand,
                category=product_data.category,
                condition=product_data.condition,
                rarity=None,  # TODO: Ajouter si besoin
                quality=None,  # TODO: Ajouter si besoin
            )

        # ===== 4. VALIDATION DES ATTRIBUTS (Refactored 2025-12-09) =====
        # Valider tous les attributs FK
        validation_data = product_data.model_dump()
        validation_data['size_original'] = size_original  # Utiliser taille ajustée
        AttributeValidator.validate_product_attributes(db, validation_data)

        # ===== 5. CRÉER LE PRODUIT =====
        product = Product(
            title=product_data.title,
            description=product_data.description,
            price=price,
            category=product_data.category,
            brand=product_data.brand,
            condition=product_data.condition,
            size_original=size_original,  # Taille originale (ajustée si dimensions fournies)
            color=product_data.color,
            material=product_data.material,
            fit=product_data.fit,
            gender=product_data.gender,
            season=product_data.season,
            condition_sup=product_data.condition_sup,
            rise=product_data.rise,
            closure=product_data.closure,
            sleeve_length=product_data.sleeve_length,
            origin=product_data.origin,
            decade=product_data.decade,
            trend=product_data.trend,
            name_sup=product_data.name_sup,
            location=product_data.location,
            model=product_data.model,
            dim1=product_data.dim1,
            dim2=product_data.dim2,
            dim3=product_data.dim3,
            dim4=product_data.dim4,
            dim5=product_data.dim5,
            dim6=product_data.dim6,
            stock_quantity=product_data.stock_quantity,  # Default: 1
            status=ProductStatus.DRAFT,
        )

        db.add(product)
        db.commit()
        db.refresh(product)

        elapsed = time.time() - start_time
        logger.info(
            f"[ProductService] create_product completed: product_id={product.id}, "
            f"title={product.title[:50] if product.title else 'N/A'}, "
            f"price={product.price}, duration={elapsed:.2f}s"
        )

        return product

    @staticmethod
    def get_product_by_id(db: Session, product_id: int) -> Optional[Product]:
        """
        Récupère un produit par ID.

        Business Rules:
        - Ignore les produits soft-deleted (deleted_at NOT NULL)

        Args:
            db: Session SQLAlchemy
            product_id: ID du produit

        Returns:
            Product ou None si non trouvé/supprimé
        """
        return (
            db.query(Product)
            .filter(Product.id == product_id, Product.deleted_at == None)
            .first()
        )

    @staticmethod
    def list_products(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[ProductStatus] = None,
        category: Optional[str] = None,
        brand: Optional[str] = None,
    ) -> tuple[list[Product], int]:
        """
        Liste les produits avec filtres et pagination.

        Business Rules:
        - Ignore les produits soft-deleted
        - Tri par défaut: created_at DESC (plus récents en premier)
        - Limit max: 100 (défini par l'API)

        Args:
            db: Session SQLAlchemy
            skip: Nombre de résultats à sauter (pagination)
            limit: Nombre max de résultats
            status: Filtre par status (optionnel)
            category: Filtre par catégorie (optionnel)
            brand: Filtre par marque (optionnel)

        Returns:
            Tuple (liste de produits, total count)
        """
        # Base query: seulement produits non supprimés
        query = db.query(Product).filter(Product.deleted_at == None)

        # Filtres optionnels
        if status:
            query = query.filter(Product.status == status)
        if category:
            query = query.filter(Product.category == category)
        if brand:
            query = query.filter(Product.brand == brand)

        # Total count (avant pagination)
        total = query.count()

        # Appliquer tri et pagination
        products = query.order_by(Product.created_at.desc()).offset(skip).limit(limit).all()

        return products, total

    @staticmethod
    def update_product(
        db: Session, product_id: int, product_data: ProductUpdate
    ) -> Optional[Product]:
        """
        Met à jour un produit.

        Business Rules:
        - Validation des FK si modifiés (brand, category, condition, etc.)
        - updated_at automatiquement mis à jour par SQLAlchemy
        - Ne peut pas modifier un produit supprimé

        Args:
            db: Session SQLAlchemy
            product_id: ID du produit à modifier
            product_data: Nouvelles données (champs optionnels)

        Returns:
            Product mis à jour ou None si non trouvé

        Raises:
            ValueError: Si un attribut FK est invalide
        """
        import time
        start_time = time.time()

        logger.info(f"[ProductService] Starting update_product: product_id={product_id}")

        product = ProductService.get_product_by_id(db, product_id)
        if not product:
            logger.warning(f"[ProductService] update_product: product_id={product_id} not found")
            return None

        # ===== BUSINESS RULE (2025-12-05): SOLD products are immutable =====
        if product.status == ProductStatus.SOLD:
            raise ValueError(
                "Cannot modify SOLD product. Product is locked after sale. "
                "Contact support if price/data correction needed."
            )

        # ===== VALIDATION DES ATTRIBUTS (Refactored 2025-12-05) =====
        # Validation partielle : seulement les attributs modifiés (was 30 lines!)
        update_dict = product_data.model_dump(exclude_unset=True)
        AttributeValidator.validate_product_attributes(db, update_dict, partial=True)

        # Appliquer les modifications
        for key, value in update_dict.items():
            setattr(product, key, value)

        db.commit()
        db.refresh(product)

        elapsed = time.time() - start_time
        logger.info(
            f"[ProductService] update_product completed: product_id={product_id}, "
            f"fields_updated={len(update_dict)}, duration={elapsed:.2f}s"
        )

        return product

    @staticmethod
    def delete_product(db: Session, product_id: int) -> bool:
        """
        Supprime un produit (soft delete).

        Business Rules (2025-12-04):
        - Soft delete: marque deleted_at au lieu de supprimer physiquement
        - Les images ne sont PAS supprimées (restent pour historique)
        - Le produit reste visible dans les rapports mais invisible dans les listes

        Args:
            db: Session SQLAlchemy
            product_id: ID du produit à supprimer

        Returns:
            bool: True si supprimé, False si non trouvé
        """
        logger.info(f"[ProductService] Starting delete_product: product_id={product_id}")

        product = ProductService.get_product_by_id(db, product_id)
        if not product:
            logger.warning(f"[ProductService] delete_product: product_id={product_id} not found")
            return False

        product.deleted_at = utc_now()
        db.commit()

        logger.info(f"[ProductService] delete_product completed: product_id={product_id} (soft deleted)")

        return True

    @staticmethod
    def add_image(
        db: Session, product_id: int, image_url: str, display_order: int | None = None
    ) -> dict:
        """
        Ajoute une image à un produit (JSONB).

        Business Rules (Updated 2026-01-03):
        - Maximum 20 images par produit (limite Vinted)
        - Vérifier que le produit existe et n'est pas supprimé
        - display_order auto-calculé si non fourni (append à la fin)
        - Images stockées en JSONB: [{url, order, created_at}, ...]

        Args:
            db: Session SQLAlchemy
            product_id: ID du produit
            image_url: URL de l'image (CDN)
            display_order: Ordre d'affichage (auto si None)

        Returns:
            dict: L'image créée {url, order, created_at}

        Raises:
            ValueError: Si produit non trouvé ou limite atteinte
        """
        product = ProductService.get_product_by_id(db, product_id)
        if not product:
            raise ValueError(f"Product with id {product_id} not found")

        # ===== BUSINESS RULE: Cannot add images to SOLD products =====
        if product.status == ProductStatus.SOLD:
            raise ValueError(
                "Cannot add images to SOLD product. Product is locked after sale."
            )

        # Get current images (ensure list)
        images = product.images or []

        # Vérifier la limite de 20 images
        if len(images) >= 20:
            raise ValueError(f"Product already has {len(images)} images (max 20)")

        # Auto-calculate display_order if not provided
        if display_order is None:
            display_order = len(images)

        # Create new image entry
        new_image = {
            "url": image_url,
            "order": display_order,
            "created_at": utc_now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

        # Append and save
        images.append(new_image)
        product.images = images
        db.flush()

        return new_image

    @staticmethod
    def delete_image(db: Session, product_id: int, image_url: str) -> bool:
        """
        Supprime une image par URL.

        Business Rules (Updated 2026-01-03):
        - Suppression de l'entrée JSONB
        - Le fichier CDN doit être supprimé par FileService (R2)
        - Réordonne automatiquement les images restantes

        Args:
            db: Session SQLAlchemy
            product_id: ID du produit
            image_url: URL de l'image à supprimer

        Returns:
            bool: True si supprimée, False si non trouvée
        """
        product = ProductService.get_product_by_id(db, product_id)
        if not product:
            return False

        images = product.images or []

        # Filter out the image to delete
        new_images = [img for img in images if img.get("url") != image_url]

        if len(new_images) == len(images):
            return False  # Image not found

        # Reorder remaining images (0, 1, 2, ...)
        for i, img in enumerate(new_images):
            img["order"] = i

        product.images = new_images
        db.commit()

        return True

    @staticmethod
    def reorder_images(
        db: Session, product_id: int, ordered_urls: list[str]
    ) -> list[dict]:
        """
        Réordonne les images d'un produit.

        Business Rules (Updated 2026-01-03):
        - ordered_urls: liste d'URLs dans le nouvel ordre
        - L'ordre dans la liste détermine le display_order (0, 1, 2, ...)
        - Vérifie que toutes les URLs appartiennent au produit

        Args:
            db: Session SQLAlchemy
            product_id: ID du produit
            ordered_urls: Liste d'URLs dans l'ordre souhaité

        Returns:
            list[dict]: Images réordonnées

        Raises:
            ValueError: Si une URL n'appartient pas au produit
        """
        product = ProductService.get_product_by_id(db, product_id)
        if not product:
            raise ValueError(f"Product with id {product_id} not found")

        images = product.images or []
        current_urls = {img.get("url") for img in images}

        # Vérifier que toutes les URLs existent
        for url in ordered_urls:
            if url not in current_urls:
                raise ValueError(
                    f"Image URL not found in product {product_id}: {url}"
                )

        # Build URL -> image mapping
        url_to_image = {img.get("url"): img for img in images}

        # Reorder based on ordered_urls
        reordered = []
        for i, url in enumerate(ordered_urls):
            img = url_to_image[url].copy()
            img["order"] = i
            reordered.append(img)

        product.images = reordered
        db.commit()
        db.refresh(product)

        return product.images

    @staticmethod
    def update_product_status(
        db: Session, product_id: int, new_status: ProductStatus
    ) -> Optional[Product]:
        """
        Met à jour le status d'un produit.

        Business Rules (MVP - 2025-12-04):
        - Transitions MVP autorisées:
          - DRAFT → PUBLISHED
          - PUBLISHED → SOLD
          - PUBLISHED → ARCHIVED
          - SOLD → ARCHIVED
        - Autres statuts non autorisés pour MVP

        Args:
            db: Session SQLAlchemy
            product_id: ID du produit
            new_status: Nouveau status

        Returns:
            Product mis à jour ou None si non trouvé

        Raises:
            ValueError: Si status non autorisé pour MVP ou transition invalide
        """
        if new_status not in ProductService.MVP_STATUSES:
            raise ValueError(
                f"Status {new_status} not allowed in MVP. "
                f"Allowed: {', '.join([s.value for s in ProductService.MVP_STATUSES])}"
            )

        product = ProductService.get_product_by_id(db, product_id)
        if not product:
            return None

        # Valider les transitions (Business Rules 2025-12-05)
        current_status = product.status
        valid_transitions = {
            ProductStatus.DRAFT: [ProductStatus.PUBLISHED, ProductStatus.ARCHIVED],  # Can archive draft
            ProductStatus.PUBLISHED: [ProductStatus.SOLD, ProductStatus.ARCHIVED],
            ProductStatus.SOLD: [ProductStatus.ARCHIVED],
            ProductStatus.ARCHIVED: [],  # Aucune transition depuis ARCHIVED
        }

        if new_status not in valid_transitions.get(current_status, []):
            raise ValueError(
                f"Invalid transition: {current_status.value} → {new_status.value}"
            )

        # ===== BUSINESS RULES (2025-12-05): Publication validation =====
        if new_status == ProductStatus.PUBLISHED:
            # Cannot publish with zero stock
            if product.stock_quantity <= 0:
                raise ValueError(
                    f"Cannot publish product with zero or negative stock. "
                    f"Current stock: {product.stock_quantity}. Please add inventory first."
                )
            # Cannot publish without images (min 1 required)
            image_count = len(product.images or [])
            if image_count == 0:
                raise ValueError(
                    "Cannot publish product without images. "
                    "Please add at least 1 product image before publishing."
                )

        # Mettre à jour le status
        product.status = new_status

        # Mettre à jour sold_at si vendu + reset stock (Business Rule 2025-12-05)
        if new_status == ProductStatus.SOLD:
            if not product.sold_at:
                product.sold_at = utc_now()
            # Produit vendu → stock à zéro (produit unique)
            product.stock_quantity = 0

        db.commit()
        db.refresh(product)

        return product
