"""
Product Utils

Utilitaires pour la manipulation de données produit.

Business Rules (2025-12-08):
- adjust_size(): Ajustement automatique taille selon dimensions
- Format: W{waist}/L{inseam} en MAJUSCULES
- Compatible avec PostEditFlet logic

Author: Claude
Date: 2025-12-08
"""


class ProductUtils:
    """Utilitaires pour manipulation de données produit."""

    @staticmethod
    def adjust_size(size_original: str | None, dim1: int | None, dim6: int | None) -> str | None:
        """
        Ajuste automatiquement la taille selon les dimensions mesurées.

        Business Rules (2025-12-08):
        - Si dim1 (waist) ET dim6 (inseam) → Format: "W{dim1}/L{dim6}" (MAJUSCULES)
        - Si seulement dim1 (waist) → Format: "W{dim1}" (pour shorts, jupes)
        - Sinon → Garder size_original (taille étiquette originale)
        - Format toujours en MAJUSCULES (ex: "W32/L34", pas "w32/l34")

        Args:
            size_original: Taille étiquette originale (ex: "32/34", "L", "M")
            dim1: Tour de taille (waist) en cm
            dim6: Entrejambe (inseam) en cm

        Returns:
            str | None: Taille ajustée ou taille originale

        Examples:
            >>> ProductUtils.adjust_size("M", 32, 34)
            "W32/L34"

            >>> ProductUtils.adjust_size("L", 30, None)
            "W30"

            >>> ProductUtils.adjust_size("XL", None, None)
            "XL"

            >>> ProductUtils.adjust_size(None, 32, 34)
            "W32/L34"
        """
        # Si waist ET inseam renseignés → Format W{waist}/L{inseam}
        if dim1 is not None and dim6 is not None:
            return f"W{dim1}/L{dim6}"

        # Si seulement waist → Format W{waist} (shorts, jupes)
        if dim1 is not None:
            return f"W{dim1}"

        # Sinon → Garder taille étiquette
        return size_original

    @staticmethod
    def normalize_model_case(model: str | None) -> str | None:
        """
        Normalise la casse du modèle (majuscule après chiffre).

        Business Rules (2025-12-08):
        - Compatible avec PostEditFlet logic
        - Ex: "501" → "501", "501original" → "501Original"
        - Majuscule après chaque chiffre

        Args:
            model: Référence modèle (ex: "501", "501original", "Air Max 90")

        Returns:
            str | None: Modèle normalisé

        Examples:
            >>> ProductUtils.normalize_model_case("501original")
            "501Original"

            >>> ProductUtils.normalize_model_case("air max 90")
            "Air Max 90"

            >>> ProductUtils.normalize_model_case(None)
            None
        """
        if not model:
            return None

        # Logique de normalisation (à implémenter si nécessaire)
        # Pour l'instant, retourne le modèle tel quel
        return model
