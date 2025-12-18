"""
Vinted Publish Service - Orchestration step-by-step de la publication

Inspiré de pythonApiWOO/services/vinted/vinted_sync_service.py
Architecture synchrone où le backend garde le contrôle du flux.

Business Rules (2025-12-12):
- Workflow synchrone step-by-step (comme pythonApiWOO)
- Upload photos → Créer produit → Post-processing
- Pas de TaskType, juste orchestration avec await
- Le backend SAIT à chaque étape ce qu'il fait (garde le contexte)

Flow de publication :
    1. Valider produit (stock, images, attributs)
    2. Mapper attributs Vinted (taille, couleur, marque, etc.)
    3. Calculer prix Vinted
    4. Upload photos (une par une, avec wait)
    5. Créer produit Vinted (avec wait)
    6. Post-processing (créer VintedProduct, mettre à jour Product.status)

Author: Claude
Date: 2025-12-12
"""

import asyncio
from datetime import date, datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from models.user.product import Product, ProductStatus
from models.user.vinted_product import VintedProduct
from services.plugin_task_helper import PluginTaskHelper, create_and_wait
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class VintedPublishService:
    """
    Service pour publier des produits sur Vinted avec orchestration step-by-step.

    Équivalent de pythonApiWOO/services/vinted/vinted_sync_service.py
    mais avec communication via plugin au lieu de vinted_client direct.
    """

    def __init__(self):
        self.helper = PluginTaskHelper()
        # TODO: Ajouter validators, mappers, pricing quand prêts
        # self.validator = VintedProductValidator()
        # self.mapper = VintedMappingService()
        # self.pricing = VintedPricingService()

    async def publish_product(
        self,
        db: Session,
        product_id: int
    ) -> dict[str, Any]:
        """
        Publie un produit sur Vinted avec workflow step-by-step.

        Équivalent de pythonApiWOO :
            vinted_sync_service._execute_product_workflow(sku, 'create')

        Args:
            db: Session SQLAlchemy (user schema)
            product_id: ID du produit à publier

        Returns:
            dict: {
                "success": bool,
                "vinted_id": int,
                "url": str,
                "product_id": int
            }

        Raises:
            ValueError: Si produit invalide ou déjà publié
            Exception: Si erreur durant publication

        Example:
            service = VintedPublishService()
            result = await service.publish_product(db, product_id=123)
        """
        logger.info(f"[PUBLISH] Starting publication for product_id={product_id}")

        try:
            # ===== ÉTAPE 1: Récupérer produit =====
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                raise ValueError(f"Produit #{product_id} introuvable")

            logger.info(f"  ├─ Produit: {product.title[:50]}...")

            # Vérifier si déjà publié sur Vinted
            existing = db.query(VintedProduct).filter(
                VintedProduct.product_id == product_id
            ).first()
            if existing:
                raise ValueError(
                    f"Produit #{product_id} déjà publié sur Vinted "
                    f"(vinted_id: {existing.vinted_id})"
                )

            # ===== ÉTAPE 2: Valider produit =====
            logger.info(f"  ├─ Validation...")
            # TODO: Implémenter validation complète
            # is_valid, error = self.validator.validate_for_creation(product)
            # if not is_valid:
            #     raise ValueError(f"Validation échouée: {error}")

            # Validation basique pour démo
            if not product.title:
                raise ValueError("Titre manquant")
            if product.price is None or product.price <= 0:
                raise ValueError("Prix invalide")

            logger.info(f"  ├─ ✅ Validation OK")

            # ===== ÉTAPE 3: Mapper attributs =====
            logger.info(f"  ├─ Mapping attributs Vinted...")
            # TODO: Implémenter mapping complet
            # mapped_attrs = self.mapper.map_all_attributes(product)

            # Mapping basique pour démo
            mapped_attrs = {
                "catalog_id": 1952,  # Vêtements femmes (TODO: mapper dynamiquement)
                "color_ids": [12],   # TODO: mapper depuis product.color
                "brand_id": 53,      # TODO: mapper depuis product.brand
                "size_id": 206,      # TODO: mapper depuis product.size
                "status_id": 6,      # Très bon état (TODO: mapper depuis product.condition)
            }

            logger.info(f"  ├─ ✅ Attributs mappés")

            # ===== ÉTAPE 4: Calculer prix =====
            logger.info(f"  ├─ Calcul prix Vinted...")
            # TODO: Implémenter pricing service
            # prix_vinted = self.pricing.calculate_vinted_price(product)

            # Prix basique pour démo (prix - 10%)
            prix_vinted = float(product.price) * 0.9

            logger.info(f"  ├─ ✅ Prix calculé: {prix_vinted}€")

            # ===== ÉTAPE 5: Upload photos (step-by-step) =====
            logger.info(f"  ├─ Upload photos...")

            photo_ids = []

            # TODO: Récupérer vraies photos depuis product.images
            # Pour démo, on simule 3 photos
            demo_photos = [
                {"url": "https://example.com/photo1.jpg"},
                {"url": "https://example.com/photo2.jpg"},
                {"url": "https://example.com/photo3.jpg"},
            ]

            for idx, photo_data in enumerate(demo_photos, 1):
                logger.info(f"  │  ├─ Upload photo {idx}/{len(demo_photos)}...")

                # Créer tâche + attendre résultat (comme requests.post)
                result = await create_and_wait(
                    db,
                    http_method="POST",
                    path="https://www.vinted.fr/api/v2/photos",
                    payload={"body": photo_data},
                    platform="vinted",
                    product_id=product_id,
                    timeout=30,
                    description=f"Upload photo {idx}"
                )

                # Extraire photo_id du résultat
                photo_id = result.get('id')
                if not photo_id:
                    raise Exception(f"Photo {idx}: ID manquant dans résultat")

                photo_ids.append(photo_id)
                logger.info(f"  │  ├─ ✅ Photo {idx} uploadée (id: {photo_id})")

            logger.info(f"  ├─ ✅ {len(photo_ids)} photos uploadées")

            # ===== ÉTAPE 6: Créer produit Vinted =====
            logger.info(f"  ├─ Création produit Vinted...")

            # Construire payload (comme pythonApiWOO converter)
            create_payload = {
                "title": product.title,
                "description": product.description or "Produit en excellent état",
                "price": str(prix_vinted),
                "currency": "EUR",
                "photo_ids": photo_ids,
                **mapped_attrs
            }

            # Créer produit (avec wait)
            result = await create_and_wait(
                db,
                http_method="POST",
                path="https://www.vinted.fr/api/v2/items",
                payload={"body": create_payload},
                platform="vinted",
                product_id=product_id,
                timeout=60,
                description="Création produit"
            )

            # Extraire vinted_id et URL
            vinted_id = result.get('id')
            vinted_url = result.get('url')

            if not vinted_id:
                raise Exception("vinted_id manquant dans résultat")

            logger.info(f"  ├─ ✅ Produit créé (vinted_id: {vinted_id})")

            # ===== ÉTAPE 7: Post-processing =====
            logger.info(f"  ├─ Post-processing...")

            # Créer VintedProduct
            vinted_product = VintedProduct(
                product_id=product_id,
                vinted_id=vinted_id,
                status='published',
                title=product.title,
                price=prix_vinted,
                url=vinted_url,
                date=date.today()
            )

            # Stocker photo_ids
            if photo_ids:
                vinted_product.set_image_ids(photo_ids)

            db.add(vinted_product)

            # Mettre à jour Product.status
            product.status = ProductStatus.PUBLISHED

            db.commit()

            logger.info(f"  ├─ ✅ Post-processing terminé")

            logger.info(f"═══════════════════════════════════════════════════════")
            logger.info(f"✅ Publication réussie - vinted_id: {vinted_id}")
            logger.info(f"═══════════════════════════════════════════════════════")

            return {
                "success": True,
                "vinted_id": vinted_id,
                "url": vinted_url,
                "product_id": product_id,
                "price": prix_vinted,
                "photos_count": len(photo_ids)
            }

        except Exception as e:
            logger.error(f"❌ Erreur publication produit #{product_id}: {e}")
            db.rollback()
            raise
