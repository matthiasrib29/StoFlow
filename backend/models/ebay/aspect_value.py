"""
eBay Aspect Value Models

Models for multilingual aspect value translations.
Each table translates aspect values from English (GB) to other eBay marketplaces.

Structure:
- ebay_gb (PK): English/GB value (reference)
- ebay_fr, ebay_de, ebay_es, ebay_it, ebay_nl, ebay_be, ebay_pl: translations

Author: Claude
Date: 2025-12-22
"""

from typing import Optional

from sqlalchemy import Column, String, text
from sqlalchemy.orm import Session

from shared.database import Base


class AspectValueBase:
    """Base mixin for aspect value tables."""

    ebay_gb = Column(String(100), primary_key=True,
                     comment='English/GB value (reference key)')
    ebay_fr = Column(String(100), nullable=True, comment='French translation')
    ebay_de = Column(String(100), nullable=True, comment='German translation')
    ebay_es = Column(String(100), nullable=True, comment='Spanish translation')
    ebay_it = Column(String(100), nullable=True, comment='Italian translation')
    ebay_nl = Column(String(100), nullable=True, comment='Dutch translation')
    ebay_be = Column(String(100), nullable=True, comment='Belgian French translation')
    ebay_pl = Column(String(100), nullable=True, comment='Polish translation')

    def get_translation(self, marketplace_id: str) -> str:
        """
        Get translated value for a marketplace.

        Args:
            marketplace_id: Marketplace (e.g., 'EBAY_FR', 'EBAY_DE')

        Returns:
            Translated value or GB value as fallback
        """
        marketplace_code = marketplace_id.split('_')[1].lower()
        column_name = f'ebay_{marketplace_code}'
        value = getattr(self, column_name, None)
        return value or self.ebay_gb


class AspectColour(AspectValueBase, Base):
    """Colour translations (e.g., Blue → Bleu, Blau, Azul)."""
    __tablename__ = 'aspect_colour'
    __table_args__ = {'schema': 'ebay'}


class AspectSize(AspectValueBase, Base):
    """Size translations (e.g., One Size → Taille unique)."""
    __tablename__ = 'aspect_size'
    __table_args__ = {'schema': 'ebay'}


class AspectMaterial(AspectValueBase, Base):
    """Material translations (e.g., Cotton → Coton, Baumwolle)."""
    __tablename__ = 'aspect_material'
    __table_args__ = {'schema': 'ebay'}


class AspectFit(AspectValueBase, Base):
    """Fit translations (e.g., Slim → Slim, Ajustado)."""
    __tablename__ = 'aspect_fit'
    __table_args__ = {'schema': 'ebay'}


class AspectClosure(AspectValueBase, Base):
    """Closure translations (e.g., Zip → Fermeture éclair)."""
    __tablename__ = 'aspect_closure'
    __table_args__ = {'schema': 'ebay'}


class AspectRise(AspectValueBase, Base):
    """Rise translations (e.g., High → Taille haute, Hoch)."""
    __tablename__ = 'aspect_rise'
    __table_args__ = {'schema': 'ebay'}


class AspectWaistSize(AspectValueBase, Base):
    """Waist size translations."""
    __tablename__ = 'aspect_waist_size'
    __table_args__ = {'schema': 'ebay'}


class AspectInsideLeg(AspectValueBase, Base):
    """Inside leg translations."""
    __tablename__ = 'aspect_inside_leg'
    __table_args__ = {'schema': 'ebay'}


class AspectDepartment(AspectValueBase, Base):
    """Department translations (e.g., Men → Homme, Herren)."""
    __tablename__ = 'aspect_department'
    __table_args__ = {'schema': 'ebay'}


class AspectType(AspectValueBase, Base):
    """Type translations (e.g., Jeans → Jean, Vaqueros)."""
    __tablename__ = 'aspect_type'
    __table_args__ = {'schema': 'ebay'}


class AspectStyle(AspectValueBase, Base):
    """Style translations (e.g., Casual → Décontracté)."""
    __tablename__ = 'aspect_style'
    __table_args__ = {'schema': 'ebay'}


class AspectPattern(AspectValueBase, Base):
    """Pattern translations (e.g., Striped → Rayé, Gestreift)."""
    __tablename__ = 'aspect_pattern'
    __table_args__ = {'schema': 'ebay'}


class AspectNeckline(AspectValueBase, Base):
    """Neckline translations (e.g., V-Neck → Col en V)."""
    __tablename__ = 'aspect_neckline'
    __table_args__ = {'schema': 'ebay'}


class AspectSleeveLength(AspectValueBase, Base):
    """Sleeve length translations (e.g., Short Sleeve → Manches courtes)."""
    __tablename__ = 'aspect_sleeve_length'
    __table_args__ = {'schema': 'ebay'}


class AspectOccasion(AspectValueBase, Base):
    """Occasion translations (e.g., Casual → Décontracté)."""
    __tablename__ = 'aspect_occasion'
    __table_args__ = {'schema': 'ebay'}


class AspectFeatures(AspectValueBase, Base):
    """Features translations (e.g., Pockets → Poches)."""
    __tablename__ = 'aspect_features'
    __table_args__ = {'schema': 'ebay'}


# Mapping of aspect keys to their model classes
ASPECT_VALUE_MODELS = {
    'colour': AspectColour,
    'color': AspectColour,  # Alias
    'size': AspectSize,
    'material': AspectMaterial,
    'fit': AspectFit,
    'closure': AspectClosure,
    'rise': AspectRise,
    'waist_size': AspectWaistSize,
    'inside_leg': AspectInsideLeg,
    'department': AspectDepartment,
    'type': AspectType,
    'style': AspectStyle,
    'pattern': AspectPattern,
    'neckline': AspectNeckline,
    'sleeve_length': AspectSleeveLength,
    'occasion': AspectOccasion,
    'features': AspectFeatures,
}


def get_aspect_translation(
    session: Session,
    aspect_key: str,
    gb_value: str,
    marketplace_id: str
) -> Optional[str]:
    """
    Get translated aspect value for a marketplace.

    Args:
        session: SQLAlchemy session
        aspect_key: Aspect key (e.g., 'colour', 'size', 'material')
        gb_value: English/GB value to translate
        marketplace_id: Target marketplace (e.g., 'EBAY_FR', 'EBAY_DE')

    Returns:
        Translated value or None if not found

    Examples:
        >>> get_aspect_translation(session, 'colour', 'Blue', 'EBAY_FR')
        'Bleu'
        >>> get_aspect_translation(session, 'colour', 'Blue', 'EBAY_DE')
        'Blau'
    """
    model_class = ASPECT_VALUE_MODELS.get(aspect_key.lower())
    if not model_class:
        return None

    aspect = session.query(model_class).filter(
        model_class.ebay_gb == gb_value
    ).first()

    if aspect:
        return aspect.get_translation(marketplace_id)

    return None
