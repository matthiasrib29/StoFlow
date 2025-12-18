"""
Vinted Task Handlers - Post-processing après exécution plugin

DEPRECATED (2025-12-12): Architecture legacy - Utilisé uniquement pour rétrocompatibilité

Nouvelle architecture (step-by-step):
- Le backend orchestre avec await wait_for_task_completion()
- Le post-processing est géré par VintedPublishService.execute_next_step()
- Pas besoin de routing par task_type car le backend garde le contexte

Ce fichier est conservé pour:
- Rétrocompatibilité avec anciennes tâches ayant task_type défini
- Migration progressive vers nouvelle architecture
- Sera supprimé une fois migration terminée

Author: Claude
Date: 2025-12-12
"""

import logging
from datetime import date, datetime
from typing import Any

from sqlalchemy.orm import Session

from models.user.plugin_task import PluginTask
from models.user.product import Product, ProductStatus
from models.user.vinted_product import VintedProduct

logger = logging.getLogger(__name__)


class VintedTaskHandler:
    """
    Handlers pour les tâches Vinted après exécution plugin.

    Chaque méthode handle_{task_type} traite un type de tâche spécifique
    et retourne les données à envoyer au frontend.
    """

    @staticmethod
    def handle_vinted_publish(
        db: Session,
        task: PluginTask,
        result: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Handler pour VINTED_PUBLISH.

        Après publication réussie sur Vinted:
        1. Crée ou met à jour VintedProduct avec vinted_id
        2. Met à jour Product.status = PUBLISHED
        3. Stocke les métadonnées (URL, image_ids, etc.)

        Args:
            db: Session SQLAlchemy (user schema)
            task: PluginTask avec product_id dans payload
            result: Résultat retourné par le plugin (status + data)

        Returns:
            dict: Données pour notification frontend
                {
                    'product_id': int,
                    'vinted_id': int,
                    'url': str,
                    'status': 'published'
                }

        Raises:
            ValueError: Si product_id manquant ou produit introuvable
        """
        logger.info(f"[VintedTaskHandler] VINTED_PUBLISH - Task #{task.id}")

        # Extraire product_id depuis payload
        product_id = task.payload.get('product_id')
        if not product_id:
            raise ValueError("product_id manquant dans task.payload")

        # Récupérer le Product
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ValueError(f"Product #{product_id} introuvable")

        # Extraire données Vinted depuis le résultat
        vinted_data = result.get('data', {})
        vinted_id = vinted_data.get('id')
        vinted_url = vinted_data.get('url')
        image_ids = vinted_data.get('photos', [])

        if not vinted_id:
            raise ValueError("vinted_id manquant dans le résultat de publication")

        logger.info(f"[VintedTaskHandler] Publication réussie - vinted_id={vinted_id}")

        # Vérifier si VintedProduct existe déjà
        vinted_product = db.query(VintedProduct).filter(
            VintedProduct.product_id == product_id
        ).first()

        if vinted_product:
            # Mettre à jour VintedProduct existant
            vinted_product.vinted_id = vinted_id
            vinted_product.status = 'published'
            vinted_product.url = vinted_url
            vinted_product.date = date.today()
            if image_ids:
                vinted_product.set_image_ids([img['id'] for img in image_ids if 'id' in img])
        else:
            # Créer nouveau VintedProduct
            vinted_product = VintedProduct(
                product_id=product_id,
                vinted_id=vinted_id,
                status='published',
                title=product.title,
                price=vinted_data.get('price_numeric'),
                url=vinted_url,
                date=date.today()
            )
            if image_ids:
                vinted_product.set_image_ids([img['id'] for img in image_ids if 'id' in img])
            db.add(vinted_product)

        # Mettre à jour Product status
        product.status = ProductStatus.PUBLISHED

        db.commit()

        logger.info(f"[VintedTaskHandler] DB updated - Product #{product_id} = PUBLISHED")

        return {
            'product_id': product_id,
            'vinted_id': vinted_id,
            'url': vinted_url,
            'status': 'published',
            'message': f'Produit publié avec succès sur Vinted (ID: {vinted_id})'
        }

    @staticmethod
    def handle_vinted_update_price(
        db: Session,
        task: PluginTask,
        result: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Handler pour VINTED_UPDATE_PRICE.

        Après mise à jour prix sur Vinted:
        1. Met à jour VintedProduct.price
        2. Peut mettre à jour Product.price si nécessaire

        Args:
            db: Session SQLAlchemy
            task: PluginTask avec product_id et new_price
            result: Résultat plugin

        Returns:
            dict: Données pour frontend
        """
        logger.info(f"[VintedTaskHandler] VINTED_UPDATE_PRICE - Task #{task.id}")

        product_id = task.payload.get('product_id')
        new_price = task.payload.get('new_price')

        if not product_id or new_price is None:
            raise ValueError("product_id ou new_price manquant dans payload")

        # Récupérer VintedProduct
        vinted_product = db.query(VintedProduct).filter(
            VintedProduct.product_id == product_id
        ).first()

        if not vinted_product:
            raise ValueError(f"VintedProduct introuvable pour product_id={product_id}")

        # Mettre à jour le prix
        old_price = vinted_product.price
        vinted_product.price = new_price

        db.commit()

        logger.info(
            f"[VintedTaskHandler] Prix mis à jour - Product #{product_id}: "
            f"{old_price}€ → {new_price}€"
        )

        return {
            'product_id': product_id,
            'vinted_id': vinted_product.vinted_id,
            'old_price': float(old_price) if old_price else None,
            'new_price': float(new_price),
            'message': f'Prix mis à jour: {old_price}€ → {new_price}€'
        }

    @staticmethod
    def handle_vinted_update_stock(
        db: Session,
        task: PluginTask,
        result: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Handler pour VINTED_UPDATE_STOCK.

        Met à jour la disponibilité du produit (visible/caché).

        Args:
            db: Session SQLAlchemy
            task: PluginTask avec product_id et available
            result: Résultat plugin

        Returns:
            dict: Données pour frontend
        """
        logger.info(f"[VintedTaskHandler] VINTED_UPDATE_STOCK - Task #{task.id}")

        product_id = task.payload.get('product_id')
        available = task.payload.get('available')

        if not product_id or available is None:
            raise ValueError("product_id ou available manquant dans payload")

        vinted_product = db.query(VintedProduct).filter(
            VintedProduct.product_id == product_id
        ).first()

        if not vinted_product:
            raise ValueError(f"VintedProduct introuvable pour product_id={product_id}")

        # Mettre à jour le statut selon disponibilité
        # Note: Vinted n'a pas vraiment de "stock", mais plutôt visible/caché
        # On peut utiliser status pour tracker ça
        if available:
            vinted_product.status = 'published'
        else:
            vinted_product.status = 'archived'  # Caché

        db.commit()

        logger.info(
            f"[VintedTaskHandler] Stock mis à jour - Product #{product_id}: "
            f"available={available}"
        )

        return {
            'product_id': product_id,
            'vinted_id': vinted_product.vinted_id,
            'available': available,
            'message': f'Disponibilité mise à jour: {"Visible" if available else "Caché"}'
        }

    @staticmethod
    def handle_vinted_delete(
        db: Session,
        task: PluginTask,
        result: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Handler pour VINTED_DELETE.

        Après suppression sur Vinted:
        1. Met à jour VintedProduct.status = 'deleted'
        2. Met à jour Product.status = ARCHIVED (ou soft delete)

        Args:
            db: Session SQLAlchemy
            task: PluginTask avec product_id
            result: Résultat plugin

        Returns:
            dict: Données pour frontend
        """
        logger.info(f"[VintedTaskHandler] VINTED_DELETE - Task #{task.id}")

        product_id = task.payload.get('product_id')
        if not product_id:
            raise ValueError("product_id manquant dans payload")

        # Récupérer VintedProduct et Product
        vinted_product = db.query(VintedProduct).filter(
            VintedProduct.product_id == product_id
        ).first()
        product = db.query(Product).filter(Product.id == product_id).first()

        if not vinted_product:
            raise ValueError(f"VintedProduct introuvable pour product_id={product_id}")

        vinted_id = vinted_product.vinted_id

        # Mettre à jour statuts
        vinted_product.status = 'deleted'
        if product:
            product.status = ProductStatus.ARCHIVED

        db.commit()

        logger.info(f"[VintedTaskHandler] Produit supprimé - vinted_id={vinted_id}")

        return {
            'product_id': product_id,
            'vinted_id': vinted_id,
            'status': 'deleted',
            'message': f'Produit supprimé de Vinted (ID: {vinted_id})'
        }

    @staticmethod
    def handle_vinted_update_details(
        db: Session,
        task: PluginTask,
        result: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Handler pour VINTED_UPDATE_DETAILS.

        Met à jour titre, description, photos, etc.

        Args:
            db: Session SQLAlchemy
            task: PluginTask avec product_id et update_data
            result: Résultat plugin

        Returns:
            dict: Données pour frontend
        """
        logger.info(f"[VintedTaskHandler] VINTED_UPDATE_DETAILS - Task #{task.id}")

        product_id = task.payload.get('product_id')
        update_data = task.payload.get('update_data', {})

        if not product_id:
            raise ValueError("product_id manquant dans payload")

        vinted_product = db.query(VintedProduct).filter(
            VintedProduct.product_id == product_id
        ).first()

        if not vinted_product:
            raise ValueError(f"VintedProduct introuvable pour product_id={product_id}")

        # Mettre à jour les champs modifiés
        updated_fields = []

        if 'title' in update_data:
            vinted_product.title = update_data['title']
            updated_fields.append('title')

        if 'photos' in result.get('data', {}):
            image_ids = result['data']['photos']
            vinted_product.set_image_ids([img['id'] for img in image_ids if 'id' in img])
            updated_fields.append('photos')

        db.commit()

        logger.info(
            f"[VintedTaskHandler] Détails mis à jour - Product #{product_id}: "
            f"{', '.join(updated_fields)}"
        )

        return {
            'product_id': product_id,
            'vinted_id': vinted_product.vinted_id,
            'updated_fields': updated_fields,
            'message': f'Détails mis à jour: {", ".join(updated_fields)}'
        }

    @staticmethod
    def route_task_handler(
        db: Session,
        task: PluginTask,
        result: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Router principal qui dispatche vers le bon handler selon task_type.

        DEPRECATED (2025-12-12): Utilisé uniquement pour rétrocompatibilité.
        Nouvelle architecture = backend orchestre step-by-step sans task_type.

        Args:
            db: Session SQLAlchemy
            task: PluginTask exécutée
            result: Résultat retourné par le plugin

        Returns:
            dict: Données pour notification frontend

        Raises:
            ValueError: Si task_type inconnu ou handler non implémenté
        """
        task_type = task.task_type

        logger.info(f"[VintedTaskHandler] LEGACY routing task #{task.id} - type={task_type}")

        # Mapping task_type (string) → handler
        handlers = {
            "vinted_publish": VintedTaskHandler.handle_vinted_publish,
            "vinted_update_price": VintedTaskHandler.handle_vinted_update_price,
            "vinted_update_stock": VintedTaskHandler.handle_vinted_update_stock,
            "vinted_update_details": VintedTaskHandler.handle_vinted_update_details,
            "vinted_delete": VintedTaskHandler.handle_vinted_delete,
        }

        # Trouver le handler approprié
        handler = handlers.get(task_type)

        if not handler:
            # Pas de handler = tâche technique sans post-processing
            logger.debug(f"[VintedTaskHandler] Pas de handler pour {task_type} (OK)")
            return {
                'task_id': task.id,
                'task_type': task_type,
                'message': 'Tâche exécutée avec succès (pas de post-processing)'
            }

        # Exécuter le handler
        try:
            handler_result = handler(db, task, result)
            logger.info(f"[VintedTaskHandler] Handler success - task #{task.id}")
            return handler_result
        except Exception as e:
            logger.error(f"[VintedTaskHandler] Handler error - task #{task.id}: {e}")
            db.rollback()
            raise
