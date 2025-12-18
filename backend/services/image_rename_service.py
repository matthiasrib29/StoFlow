"""
Image Rename Service

Service pour renommer les images produit selon un pattern standardisé.

Business Rules (2025-12-08):
- Pattern: image_{sku}_{n}.jpeg (ex: image_1000_1.jpeg, image_1000_2.jpeg)
- display_order séquentiel (0, 1, 2, 3...)
- Renommage local (pas d'upload marketplace)
- Compatible avec PostEditFlet logic

Author: Claude
Date: 2025-12-08
"""

import os
import shutil
from pathlib import Path
from typing import List


class ImageRenameService:
    """Service pour renommer et organiser les images produit."""

    @staticmethod
    def rename_images(
        image_paths: List[str],
        sku: str,
        destination_dir: str,
    ) -> List[tuple[str, int]]:
        """
        Renomme les images selon le pattern image_{sku}_{n}.jpeg.

        Business Rules (2025-12-08):
        - Pattern: image_{sku}_{n}.jpeg (n commence à 1)
        - display_order séquentiel (0, 1, 2, 3...)
        - Conserve l'ordre original des images
        - Déplace les images vers destination_dir
        - Crée le dossier destination si nécessaire

        Args:
            image_paths: Liste des chemins absolus des images source
            sku: SKU du produit (ex: "1000")
            destination_dir: Dossier de destination (ex: "uploads/user_1/products/123")

        Returns:
            List[tuple[str, int]]: Liste de (nouveau_chemin, display_order)

        Raises:
            FileNotFoundError: Si une image source n'existe pas
            IOError: Si erreur lors du déplacement

        Examples:
            >>> images = ["/tmp/img1.jpg", "/tmp/img2.jpg", "/tmp/img3.jpg"]
            >>> result = ImageRenameService.rename_images(
            ...     images, "1000", "uploads/user_1/products/123"
            ... )
            >>> print(result)
            [
                ("uploads/user_1/products/123/image_1000_1.jpeg", 0),
                ("uploads/user_1/products/123/image_1000_2.jpeg", 1),
                ("uploads/user_1/products/123/image_1000_3.jpeg", 2)
            ]
        """
        # Créer le dossier destination si nécessaire
        dest_path = Path(destination_dir)
        dest_path.mkdir(parents=True, exist_ok=True)

        renamed_images = []

        for index, source_path in enumerate(image_paths, start=1):
            # Vérifier que le fichier source existe
            if not os.path.exists(source_path):
                raise FileNotFoundError(f"Image source not found: {source_path}")

            # Générer le nouveau nom : image_{sku}_{n}.jpeg
            new_filename = f"image_{sku}_{index}.jpeg"
            new_path = dest_path / new_filename

            # Déplacer et renommer le fichier
            try:
                shutil.move(source_path, str(new_path))
            except Exception as e:
                raise IOError(f"Failed to move image {source_path} to {new_path}: {e}")

            # display_order commence à 0 (mais le nom commence à 1)
            display_order = index - 1

            renamed_images.append((str(new_path), display_order))

        return renamed_images

    @staticmethod
    def delete_images(image_paths: List[str]) -> None:
        """
        Supprime les images source après traitement.

        Business Rules:
        - Suppression physique des fichiers
        - Ignore les fichiers déjà supprimés (pas d'erreur)

        Args:
            image_paths: Liste des chemins absolus des images à supprimer

        Examples:
            >>> ImageRenameService.delete_images(["/tmp/img1.jpg", "/tmp/img2.jpg"])
        """
        for path in image_paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception:
                # Ignorer les erreurs de suppression (fichier déjà supprimé, permissions, etc.)
                pass

    @staticmethod
    def validate_image_format(file_path: str) -> bool:
        """
        Valide que le fichier est une image supportée.

        Business Rules:
        - Formats acceptés: .jpg, .jpeg, .png
        - Validation basée sur l'extension

        Args:
            file_path: Chemin du fichier à valider

        Returns:
            bool: True si format valide, False sinon

        Examples:
            >>> ImageRenameService.validate_image_format("photo.jpg")
            True

            >>> ImageRenameService.validate_image_format("document.pdf")
            False
        """
        valid_extensions = {".jpg", ".jpeg", ".png"}
        file_ext = Path(file_path).suffix.lower()
        return file_ext in valid_extensions

    @staticmethod
    def get_product_images_dir(base_upload_dir: str, user_id: int, product_id: int) -> str:
        """
        Génère le chemin du dossier images pour un produit.

        Business Rules:
        - Format: {base_upload_dir}/{user_id}/products/{product_id}
        - Compatible avec isolation multi-tenant

        Args:
            base_upload_dir: Dossier racine uploads (ex: "uploads")
            user_id: ID de l'utilisateur
            product_id: ID du produit

        Returns:
            str: Chemin complet du dossier

        Examples:
            >>> ImageRenameService.get_product_images_dir("uploads", 1, 123)
            "uploads/1/products/123"
        """
        return f"{base_upload_dir}/{user_id}/products/{product_id}"
