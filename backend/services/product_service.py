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
from models.user.product_image import ProductImage
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
        label_size = ProductUtils.adjust_size(
            product_data.label_size,
            product_data.dim1,
            product_data.dim6
        )

        # ===== 2. AUTO-CRÉER SIZE SI MANQUANTE (Business Rule 2025-12-09) =====
        if label_size:
            size_exists = db.query(Size).filter(Size.name == label_size).first()
            if not size_exists:
                new_size = Size(name=label_size, name_fr=None)
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
        validation_data['label_size'] = label_size  # Utiliser taille ajustée
        AttributeValidator.validate_product_attributes(db, validation_data)

        # ===== 5. CRÉER LE PRODUIT =====
        product = Product(
            title=product_data.title,
            description=product_data.description,
            price=price,
            category=product_data.category,
            brand=product_data.brand,
            condition=product_data.condition,
            label_size=label_size,  # Taille ajustée
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
        db: Session, product_id: int, image_path: str, display_order: int = 0
    ) -> ProductImage:
        """
        Ajoute une image à un produit.

        Business Rules (2025-12-04):
        - Maximum 20 images par produit (limite Vinted)
        - Vérifier que le produit existe et n'est pas supprimé
        - display_order détermine l'ordre d'affichage

        Args:
            db: Session SQLAlchemy
            product_id: ID du produit
            image_path: Chemin relatif de l'image
            display_order: Ordre d'affichage (0 = première image)

        Returns:
            ProductImage: L'image créée

        Raises:
            ValueError: Si produit non trouvé ou limite atteinte
        """
        # Vérifier que le produit existe
        product = ProductService.get_product_by_id(db, product_id)
        if not product:
            raise ValueError(f"Product with id {product_id} not found")

        # ===== BUSINESS RULE (2025-12-05): Cannot add images to SOLD products =====
        if product.status == ProductStatus.SOLD:
            raise ValueError(
                "Cannot add images to SOLD product. Product is locked after sale."
            )

        # Vérifier la limite de 20 images avec row lock (prevent race condition)
        # Use SELECT FOR UPDATE to lock the product row
        from sqlalchemy import select
        db.execute(select(Product).where(Product.id == product_id).with_for_update())

        image_count = db.query(ProductImage).filter(ProductImage.product_id == product_id).count()
        if image_count >= 20:
            raise ValueError(f"Product already has {image_count} images (max 20)")

        # Créer l'image
        product_image = ProductImage(
            product_id=product_id, image_path=image_path, display_order=display_order
        )

        db.add(product_image)
        db.commit()
        db.refresh(product_image)

        return product_image

    @staticmethod
    def delete_image(db: Session, image_id: int) -> bool:
        """
        Supprime une image.

        Business Rules:
        - Suppression physique (pas soft delete pour les images)
        - Le fichier filesystem doit être supprimé par FileService

        Args:
            db: Session SQLAlchemy
            image_id: ID de l'image

        Returns:
            bool: True si supprimée, False si non trouvée
        """
        image = db.query(ProductImage).filter(ProductImage.id == image_id).first()
        if not image:
            return False

        db.delete(image)
        db.commit()

        return True

    @staticmethod
    def reorder_images(
        db: Session, product_id: int, image_orders: dict[int, int]
    ) -> list[ProductImage]:
        """
        Réordonne les images d'un produit.

        Business Rules:
        - image_orders: {image_id: new_display_order}
        - Vérifie que toutes les images appartiennent au produit

        Args:
            db: Session SQLAlchemy
            product_id: ID du produit
            image_orders: Dictionnaire {image_id: new_display_order}

        Returns:
            list[ProductImage]: Images réordonnées

        Raises:
            ValueError: Si une image n'appartient pas au produit
        """
        # Récupérer toutes les images du produit
        images = (
            db.query(ProductImage)
            .filter(ProductImage.product_id == product_id)
            .all()
        )

        image_ids = {img.id for img in images}

        # Vérifier que toutes les images existent et appartiennent au produit
        for image_id in image_orders.keys():
            if image_id not in image_ids:
                raise ValueError(
                    f"Image {image_id} does not belong to product {product_id}"
                )

        # Appliquer le réordonnancement
        for image_id, new_order in image_orders.items():
            image = next(img for img in images if img.id == image_id)
            image.display_order = new_order

        db.commit()

        # Retourner les images réordonnées
        return (
            db.query(ProductImage)
            .filter(ProductImage.product_id == product_id)
            .order_by(ProductImage.display_order)
            .all()
        )

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
            image_count = db.query(ProductImage).filter(ProductImage.product_id == product_id).count()
            if image_count == 0:
                raise ValueError(
                    "Cannot publish product without images. "
                    "Please add at least 1 product image before publishing."
                )

        # Mettre à jour le status
        product.status = new_status

        # Mettre à jour published_at si publication
        if new_status == ProductStatus.PUBLISHED and not product.published_at:
            product.published_at = utc_now()

        # Mettre à jour sold_at si vendu + reset stock (Business Rule 2025-12-05)
        if new_status == ProductStatus.SOLD:
            if not product.sold_at:
                product.sold_at = utc_now()
            # Produit vendu → stock à zéro (produit unique)
            product.stock_quantity = 0

        db.commit()
        db.refresh(product)

        return product
