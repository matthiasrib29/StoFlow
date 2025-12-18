"""
Measurement Extractor for Vinted Descriptions

Extrait les mesures d'un produit selon sa catégorie.

Author: Claude
Date: 2025-12-11
"""

from typing import List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from models.user.product import Product


class MeasurementExtractor:
    """
    Extrait les mesures d'un produit selon sa catégorie.

    Mesures par catégorie:
    - Jeans/Pants: 6 mesures (Waist, Inseam, Rise, Thigh, Knee, Leg Opening)
    - Shorts: 5 mesures (Waist, Inseam, Rise, Thigh, Leg Opening)
    - Tops: 4 mesures (Chest, Length, Shoulder, Sleeve)
    - Sunglasses: 2 mesures (Width, Bridge)
    """

    # Catégories de type "bottom" (pantalons)
    BOTTOM_CATEGORIES = ['Jeans', 'Pants']

    # Catégories de type "shorts"
    SHORTS_CATEGORIES = ['Shorts']

    # Catégories de type "top" (hauts)
    TOP_CATEGORIES = [
        'Shirt', 'T-shirt', 'Sweatshirt', 'Sweater',
        'Jacket', 'Coat', 'Blazer'
    ]

    # Catégories de type "eyewear" (lunettes)
    EYEWEAR_CATEGORIES = ['Sunglasses']

    @classmethod
    def extract(cls, product: "Product") -> List[Tuple[str, str]]:
        """
        Extrait les mesures d'un produit selon sa catégorie.

        Args:
            product: Instance de Product

        Returns:
            Liste de tuples (nom_mesure, valeur)
        """
        category = getattr(product, 'category', None)
        if not category:
            return []

        # Déterminer le type de produit
        parent_category = getattr(product, 'parent_category', category)

        if parent_category in cls.BOTTOM_CATEGORIES:
            return cls._extract_bottom(product)
        elif parent_category in cls.SHORTS_CATEGORIES:
            return cls._extract_shorts(product)
        elif parent_category in cls.TOP_CATEGORIES:
            return cls._extract_top(product)
        elif parent_category in cls.EYEWEAR_CATEGORIES:
            return cls._extract_eyewear(product)

        return []

    @classmethod
    def _extract_bottom(cls, product: "Product") -> List[Tuple[str, str]]:
        """Extrait les mesures pour pantalons/jeans."""
        measurements = []

        if hasattr(product, 'waist') and product.waist:
            measurements.append(("Tour de taille", str(product.waist)))

        if hasattr(product, 'inseam') and product.inseam:
            measurements.append(("Entrejambe", str(product.inseam)))

        if hasattr(product, 'rise') and product.rise:
            measurements.append(("Hauteur de fourche", str(product.rise)))

        if hasattr(product, 'thigh') and product.thigh:
            measurements.append(("Tour de cuisse", str(product.thigh)))

        if hasattr(product, 'knee') and product.knee:
            measurements.append(("Tour de genou", str(product.knee)))

        if hasattr(product, 'leg_opening') and product.leg_opening:
            measurements.append(("Ouverture de jambe", str(product.leg_opening)))

        return measurements

    @classmethod
    def _extract_shorts(cls, product: "Product") -> List[Tuple[str, str]]:
        """Extrait les mesures pour shorts."""
        measurements = []

        if hasattr(product, 'waist') and product.waist:
            measurements.append(("Tour de taille", str(product.waist)))

        if hasattr(product, 'inseam') and product.inseam:
            measurements.append(("Entrejambe", str(product.inseam)))

        if hasattr(product, 'rise') and product.rise:
            measurements.append(("Hauteur de fourche", str(product.rise)))

        if hasattr(product, 'thigh') and product.thigh:
            measurements.append(("Tour de cuisse", str(product.thigh)))

        if hasattr(product, 'leg_opening') and product.leg_opening:
            measurements.append(("Ouverture de jambe", str(product.leg_opening)))

        return measurements

    @classmethod
    def _extract_top(cls, product: "Product") -> List[Tuple[str, str]]:
        """Extrait les mesures pour hauts."""
        measurements = []

        if hasattr(product, 'chest') and product.chest:
            measurements.append(("Tour de poitrine", str(product.chest)))

        if hasattr(product, 'length') and product.length:
            measurements.append(("Longueur", str(product.length)))

        if hasattr(product, 'shoulder') and product.shoulder:
            measurements.append(("Largeur épaules", str(product.shoulder)))

        if hasattr(product, 'sleeve') and product.sleeve:
            measurements.append(("Longueur manche", str(product.sleeve)))

        return measurements

    @classmethod
    def _extract_eyewear(cls, product: "Product") -> List[Tuple[str, str]]:
        """Extrait les mesures pour lunettes."""
        measurements = []

        if hasattr(product, 'width') and product.width:
            measurements.append(("Largeur", str(product.width)))

        if hasattr(product, 'bridge') and product.bridge:
            measurements.append(("Pont", str(product.bridge)))

        return measurements


__all__ = ["MeasurementExtractor"]
