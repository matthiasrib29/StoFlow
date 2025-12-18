"""
Vinted Task Handler (LEGACY)

DEPRECATED (2025-12-12): Ancienne version - Voir vinted_task_handlers.py

Ce fichier sera supprimé une fois migration terminée vers architecture step-by-step.

Author: Claude
Date: 2024-12-10
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from models.user.plugin_task import PluginTask
from models.user.vinted_error_log import VintedErrorLog
from repositories.vinted_product_repository import VintedProductRepository
from repositories.vinted_error_log_repository import VintedErrorLogRepository

logger = logging.getLogger(__name__)


class VintedTaskHandler:
    """
    Handler pour traiter les résultats des tâches Vinted.

    Appelé lorsque le plugin retourne un résultat via POST /api/plugin/tasks/{id}/result
    """

    @staticmethod
    def handle_task_result(db: Session, task: PluginTask) -> None:
        """
        Traite le résultat d'une tâche Vinted selon son type.

        Args:
            db: Session SQLAlchemy
            task: PluginTask avec result/error

        Business Rules:
        - SUCCESS: Met à jour VintedProduct avec les données Vinted
        - FAILED: Crée un VintedErrorLog et marque VintedProduct en erreur
        """
        if task.task_type == "vinted_publish":
            VintedTaskHandler._handle_publish_result(db, task)
        elif task.task_type == "vinted_update":
            VintedTaskHandler._handle_update_result(db, task)
        elif task.task_type == "vinted_delete":
            VintedTaskHandler._handle_delete_result(db, task)
        else:
            logger.warning(f"Type de tâche non géré: {task.task_type}")

    @staticmethod
    def _handle_publish_result(db: Session, task: PluginTask) -> None:
        """
        Traite le résultat d'une publication Vinted.

        Args:
            db: Session SQLAlchemy
            task: PluginTask VINTED_PUBLISH

        Success result format:
        {
            "vinted_id": 987654321,
            "url": "https://vinted.fr/items/987654321",
            "image_ids": "123,456,789"
        }

        Error result format:
        {
            "error_type": "mapping_error",
            "error_details": "Brand not mapped"
        }
        """
        try:
            vinted_product_id = task.payload.get("vinted_product_id")
            product_id = task.product_id

            if not vinted_product_id:
                logger.error(f"Task #{task.id}: vinted_product_id manquant dans payload")
                return

            vinted_product = VintedProductRepository.get_by_id(db, vinted_product_id)
            if not vinted_product:
                logger.error(f"Task #{task.id}: VintedProduct #{vinted_product_id} non trouvé")
                return

            # SUCCESS: Mettre à jour VintedProduct avec données Vinted
            if task.status.value == 'success' and task.result:
                vinted_id = task.result.get("vinted_id")
                url = task.result.get("url")
                image_ids = task.result.get("image_ids")

                if vinted_id:
                    vinted_product.vinted_id = vinted_id
                if url:
                    vinted_product.url = url
                if image_ids:
                    vinted_product.image_ids = image_ids

                vinted_product.status = 'published'
                from datetime import date
                vinted_product.date = date.today()

                db.commit()
                logger.info(
                    f"✅ Publication réussie - Product #{product_id} → Vinted ID {vinted_id}"
                )

            # FAILED: Créer un log d'erreur
            elif task.status.value == 'failed':
                error_type = "api_error"
                error_message = task.error_message or "Échec publication"
                error_details = None

                # Extraire error_type et details du result si disponibles
                if task.result:
                    error_type = task.result.get("error_type", error_type)
                    error_details = task.result.get("error_details")

                # Créer VintedErrorLog
                error_log = VintedErrorLog(
                    product_id=product_id,
                    operation='publish',
                    error_type=error_type,
                    error_message=error_message,
                    error_details=str(error_details) if error_details else None
                )
                VintedErrorLogRepository.create(db, error_log)

                # Marquer VintedProduct en erreur
                vinted_product.status = 'error'
                db.commit()

                logger.error(
                    f"❌ Échec publication - Product #{product_id}: {error_message}"
                )

        except Exception as e:
            logger.error(f"Erreur traitement résultat publication: {e}", exc_info=True)

    @staticmethod
    def _handle_update_result(db: Session, task: PluginTask) -> None:
        """
        Traite le résultat d'une mise à jour Vinted.

        Args:
            db: Session SQLAlchemy
            task: PluginTask VINTED_UPDATE
        """
        try:
            product_id = task.product_id
            if not product_id:
                return

            vinted_product = VintedProductRepository.get_by_product_id(db, product_id)
            if not vinted_product:
                logger.error(f"Task #{task.id}: VintedProduct pour product #{product_id} non trouvé")
                return

            if task.status.value == 'success':
                # Mise à jour réussie
                if task.result:
                    # Mettre à jour les champs modifiés
                    if "title" in task.result:
                        vinted_product.title = task.result["title"]
                    if "price" in task.result:
                        vinted_product.price = task.result["price"]

                db.commit()
                logger.info(f"✅ Mise à jour réussie - Product #{product_id}")

            elif task.status.value == 'failed':
                # Créer log d'erreur
                error_log = VintedErrorLog(
                    product_id=product_id,
                    operation='update',
                    error_type='api_error',
                    error_message=task.error_message or "Échec mise à jour",
                    error_details=str(task.result) if task.result else None
                )
                VintedErrorLogRepository.create(db, error_log)

                logger.error(f"❌ Échec mise à jour - Product #{product_id}")

        except Exception as e:
            logger.error(f"Erreur traitement résultat update: {e}", exc_info=True)

    @staticmethod
    def _handle_delete_result(db: Session, task: PluginTask) -> None:
        """
        Traite le résultat d'une suppression Vinted.

        Args:
            db: Session SQLAlchemy
            task: PluginTask VINTED_DELETE
        """
        try:
            product_id = task.product_id
            if not product_id:
                return

            vinted_product = VintedProductRepository.get_by_product_id(db, product_id)
            if not vinted_product:
                logger.error(f"Task #{task.id}: VintedProduct pour product #{product_id} non trouvé")
                return

            if task.status.value == 'success':
                # Suppression réussie
                vinted_product.status = 'deleted'
                db.commit()
                logger.info(f"✅ Suppression réussie - Product #{product_id}")

            elif task.status.value == 'failed':
                # Créer log d'erreur
                error_log = VintedErrorLog(
                    product_id=product_id,
                    operation='delete',
                    error_type='api_error',
                    error_message=task.error_message or "Échec suppression",
                    error_details=str(task.result) if task.result else None
                )
                VintedErrorLogRepository.create(db, error_log)

                logger.error(f"❌ Échec suppression - Product #{product_id}")

        except Exception as e:
            logger.error(f"Erreur traitement résultat delete: {e}", exc_info=True)
