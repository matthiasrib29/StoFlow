"""
File Service

Service pour la gestion des uploads de fichiers (images produits).

Business Rules (2025-12-04, Updated 2025-12-10):
- Stockage local: uploads/{user_id}/products/{product_id}/
- Formats autorisés: jpg, jpeg, png
- Taille max: 5MB par image
- Maximum 20 images par produit (limite Vinted)
- Nom de fichier unique (UUID)
- Pas de thumbnails (original uniquement)
"""

import imghdr
import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import UploadFile
from sqlalchemy.orm import Session

from models.user.product_image import ProductImage
from shared.config import settings
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class FileService:
    """Service pour gérer les uploads de fichiers."""

    # Configuration (Updated: 2025-12-05 - Security review)
    UPLOAD_BASE_DIR = "uploads"
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB (Security: 2025-12-05)
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
    MAX_IMAGES_PER_PRODUCT = 20

    @staticmethod
    def ensure_upload_directory() -> None:
        """
        Crée le répertoire uploads/ s'il n'existe pas.

        À appeler au démarrage de l'application (startup event).
        """
        upload_dir = Path(FileService.UPLOAD_BASE_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    async def save_product_image(
        user_id: int, product_id: int, file: UploadFile
    ) -> str:
        """
        Sauvegarde une image produit sur le filesystem.

        Business Rules (Updated: 2025-12-05):
        - Vérifier extension (jpg, jpeg, png uniquement)
        - Vérifier taille (max 10MB - Security review 2025-12-05)
        - Vérifier format réel du fichier avec magic bytes (anti-spoofing)
        - Créer répertoire si nécessaire
        - Générer nom unique (UUID)

        Args:
            user_id: ID de l'utilisateur (pour isolation)
            product_id: ID du produit
            file: Fichier uploadé (FastAPI UploadFile)

        Returns:
            str: Chemin relatif de l'image (ex: uploads/1/products/5/abc123.jpg)

        Raises:
            ValueError: Si extension, format ou taille invalide
        """
        logger.info(
            f"[FileService] Starting save_product_image: user_id={user_id}, "
            f"product_id={product_id}, filename={file.filename}"
        )

        # ===== VALIDATION EXTENSION =====
        if not file.filename:
            raise ValueError("Filename is missing")

        extension = file.filename.split(".")[-1].lower()
        if extension not in FileService.ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Invalid file extension: {extension}. "
                f"Allowed: {', '.join(FileService.ALLOWED_EXTENSIONS)}"
            )

        # ===== VALIDATION FORMAT RÉEL (anti-spoofing) =====
        # Lire les premiers bytes pour vérifier le format réel
        content = await file.read(512)
        await file.seek(0)  # Reset pour lecture complète après

        image_type = imghdr.what(None, content)
        if image_type not in ["jpeg", "png"]:
            raise ValueError(
                f"Invalid image format: {image_type}. File may be corrupted or not a valid image."
            )

        # Vérifier cohérence extension vs format réel
        if (extension in ["jpg", "jpeg"] and image_type != "jpeg") or (
            extension == "png" and image_type != "png"
        ):
            raise ValueError(
                f"File extension '{extension}' does not match actual format '{image_type}'"
            )

        # ===== VALIDATION TAILLE =====
        # Lire le fichier complet pour vérifier la taille
        content_full = await file.read()
        file_size = len(content_full)

        if file_size > FileService.MAX_FILE_SIZE:
            size_mb = file_size / (1024 * 1024)
            max_mb = FileService.MAX_FILE_SIZE / (1024 * 1024)
            raise ValueError(f"File too large: {size_mb:.2f}MB (max {max_mb}MB)")

        if file_size == 0:
            raise ValueError("File is empty")

        # ===== CRÉER RÉPERTOIRE =====
        upload_path = Path(FileService.UPLOAD_BASE_DIR) / str(user_id) / "products" / str(product_id)
        upload_path.mkdir(parents=True, exist_ok=True)

        # ===== GÉNÉRER NOM UNIQUE =====
        unique_filename = f"{uuid.uuid4().hex}.{extension}"
        file_path = upload_path / unique_filename

        # ===== SAUVEGARDER FICHIER =====
        with open(file_path, "wb") as f:
            f.write(content_full)

        # Retourner chemin relatif (pour stockage en BDD)
        relative_path = str(file_path)

        logger.info(
            f"[FileService] save_product_image completed: user_id={user_id}, "
            f"product_id={product_id}, path={relative_path}, size={file_size/1024:.1f}KB"
        )

        return relative_path

    @staticmethod
    def delete_product_image(image_path: str) -> bool:
        """
        Supprime une image du filesystem.

        Business Rules (Updated: 2025-12-05):
        - Suppression physique du fichier
        - Ne pas lever d'erreur si le fichier n'existe pas (déjà supprimé)
        - SECURITY: Protection path traversal (bloquer ../, vérifier resolve)

        Args:
            image_path: Chemin relatif de l'image (ex: uploads/1/products/5/abc123.jpg)

        Returns:
            bool: True si fichier supprimé, False si n'existait pas

        Raises:
            ValueError: Si path traversal détecté (Security: 2025-12-05)
        """
        # ===== SECURITY FIX (2025-12-05): Path Traversal Protection =====
        # Défense #1: Bloquer ../ explicitement
        if ".." in image_path:
            raise ValueError(
                "Path traversal attempt detected: '..' not allowed in file path"
            )

        file_path = Path(image_path)

        # Défense #2: Vérifier que le chemin résolu est bien dans uploads/
        try:
            resolved_path = file_path.resolve()
            upload_base = Path(FileService.UPLOAD_BASE_DIR).resolve()

            # Check que le fichier est bien dans uploads/
            if not str(resolved_path).startswith(str(upload_base)):
                raise ValueError(
                    f"Path traversal attempt detected: file must be inside {upload_base}"
                )
        except Exception as e:
            # Si erreur de résolution, c'est suspect
            raise ValueError(f"Invalid file path: {str(e)}")

        if not file_path.exists():
            return False

        try:
            file_path.unlink()  # Supprime le fichier
            logger.info(f"[FileService] Image deleted: path={image_path}")
            return True
        except Exception as e:
            # Si erreur de permission ou autre, retourner False
            logger.warning(f"[FileService] Failed to delete image: path={image_path}, error={e}")
            return False

    @staticmethod
    def validate_image_count(db: Session, product_id: int) -> None:
        """
        Vérifie que le produit n'a pas atteint la limite de 20 images.

        Business Rules:
        - Maximum 20 images par produit (limite Vinted)

        Args:
            db: Session SQLAlchemy
            product_id: ID du produit

        Raises:
            ValueError: Si limite atteinte (>= 20 images)
        """
        image_count = (
            db.query(ProductImage).filter(ProductImage.product_id == product_id).count()
        )

        if image_count >= FileService.MAX_IMAGES_PER_PRODUCT:
            raise ValueError(
                f"Product already has {image_count} images "
                f"(max {FileService.MAX_IMAGES_PER_PRODUCT})"
            )

    @staticmethod
    def get_image_full_path(image_path: str) -> Path:
        """
        Retourne le chemin complet d'une image.

        Args:
            image_path: Chemin relatif de l'image

        Returns:
            Path: Chemin complet absolu
        """
        return Path(image_path).resolve()

    @staticmethod
    def image_exists(image_path: str) -> bool:
        """
        Vérifie si une image existe sur le filesystem.

        Args:
            image_path: Chemin relatif de l'image

        Returns:
            bool: True si le fichier existe
        """
        return Path(image_path).exists()
