"""
Size Original Repository

Repository pour la gestion des tailles originales (auto-créables).

Business Rules:
- Auto-création via get_or_create() si la taille n'existe pas
- Normalisation des noms (uppercase pour patterns W/L)
- Lookup case-insensitive pour éviter duplicates
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.public.size_original import SizeOriginal


class SizeOriginalRepository:
    """Repository pour gérer les tailles originales."""

    @staticmethod
    def normalize_name(name: str) -> str:
        """
        Normalise le nom de la taille pour éviter duplicates.

        Rules:
        - Strip whitespace
        - Uppercase patterns W/L: "w32/l34" → "W32/L34"
        - Preserve case pour autres: "M", "42 EU"

        Args:
            name: Nom de la taille à normaliser.

        Returns:
            Nom normalisé.

        Examples:
            >>> SizeOriginalRepository.normalize_name("  w32/l34  ")
            'W32/L34'
            >>> SizeOriginalRepository.normalize_name("M")
            'M'
            >>> SizeOriginalRepository.normalize_name("42 EU")
            '42 EU'
        """
        name = name.strip()

        # Uppercase pour patterns W/L (jeans/pantalons)
        if 'w' in name.lower() and 'l' in name.lower():
            return name.upper()

        return name

    @staticmethod
    def get_or_create(db: Session, name: str) -> SizeOriginal:
        """
        Récupère ou crée une taille originale.

        Lookup case-insensitive pour éviter duplicates.

        Args:
            db: Session SQLAlchemy.
            name: Nom de la taille (sera normalisé).

        Returns:
            Instance SizeOriginal (existante ou nouvellement créée).

        Examples:
            >>> size = SizeOriginalRepository.get_or_create(db, "w32/l34")
            >>> size.name
            'W32/L34'
        """
        # Normaliser le nom
        normalized = SizeOriginalRepository.normalize_name(name)

        # Lookup case-insensitive
        stmt = select(SizeOriginal).where(
            func.upper(SizeOriginal.name) == normalized.upper()
        )
        size = db.execute(stmt).scalar_one_or_none()

        if not size:
            # Créer nouvelle taille
            size = SizeOriginal(name=normalized)
            db.add(size)
            db.flush()  # Flush pour obtenir l'objet avant commit

        return size

    @staticmethod
    def get_by_name(db: Session, name: str) -> SizeOriginal | None:
        """
        Récupère une taille par nom exact.

        Args:
            db: Session SQLAlchemy.
            name: Nom exact de la taille.

        Returns:
            Instance SizeOriginal ou None si non trouvée.
        """
        stmt = select(SizeOriginal).where(SizeOriginal.name == name)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_name_case_insensitive(db: Session, name: str) -> SizeOriginal | None:
        """
        Récupère une taille par nom (case-insensitive).

        Args:
            db: Session SQLAlchemy.
            name: Nom de la taille (insensible à la casse).

        Returns:
            Instance SizeOriginal ou None si non trouvée.
        """
        stmt = select(SizeOriginal).where(
            func.upper(SizeOriginal.name) == name.upper()
        )
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def list_all(db: Session, limit: int = 500) -> list[SizeOriginal]:
        """
        Liste toutes les tailles originales.

        Args:
            db: Session SQLAlchemy.
            limit: Nombre maximum de résultats (défaut: 500).

        Returns:
            Liste des tailles originales (ordre: plus récentes d'abord).
        """
        stmt = select(SizeOriginal).order_by(
            SizeOriginal.created_at.desc()
        ).limit(limit)
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def count(db: Session) -> int:
        """
        Compte le nombre total de tailles originales.

        Args:
            db: Session SQLAlchemy.

        Returns:
            Nombre total de tailles.
        """
        stmt = select(func.count(SizeOriginal.name))
        return db.execute(stmt).scalar_one() or 0

    @staticmethod
    def delete_by_name(db: Session, name: str) -> bool:
        """
        Supprime une taille par nom.

        Args:
            db: Session SQLAlchemy.
            name: Nom de la taille à supprimer.

        Returns:
            True si supprimée, False si non trouvée.
        """
        size = SizeOriginalRepository.get_by_name(db, name)

        if size:
            db.delete(size)
            db.flush()
            return True

        return False
