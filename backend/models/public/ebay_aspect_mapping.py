"""
Modèle pour les mappings d'aspects eBay multilingues.

Table de référence centrale pour mapper les aspects eBay universels
vers leurs traductions localisées par marketplace.

Permet de traduire automatiquement les aspects (Brand, Color, Size, etc.)
dans la langue de chaque marketplace eBay.

Author: Claude
Date: 2025-12-10
"""

from sqlalchemy import Column, String
from sqlalchemy.orm import Session
from shared.database import Base


class AspectMapping(Base):
    """Mapping des noms d'aspects eBay par marketplace"""

    __tablename__ = 'aspect_name_mapping'
    __table_args__ = {'schema': 'ebay'}

    # Primary key - aspect identifier (ex: 'brand', 'color', 'size')
    aspect_key = Column(String(100), primary_key=True)

    # Nom aspect pour chaque marketplace
    ebay_gb = Column(String(100), nullable=True, index=True, comment="UK/GB (ex: Colour)")
    ebay_fr = Column(String(100), nullable=True, comment="France (ex: Couleur)")
    ebay_de = Column(String(100), nullable=True, comment="Germany (ex: Farbe)")
    ebay_es = Column(String(100), nullable=True, comment="Spain (ex: Color)")
    ebay_it = Column(String(100), nullable=True, comment="Italy (ex: Colore)")
    ebay_nl = Column(String(100), nullable=True, comment="Netherlands (ex: Kleur)")
    ebay_be = Column(String(100), nullable=True, comment="Belgium (ex: Couleur)")
    ebay_pl = Column(String(100), nullable=True, comment="Poland (ex: Kolor)")

    def get_aspect_name(self, marketplace_id: str) -> str:
        """
        Récupère le nom d'aspect localisé pour une marketplace.

        Args:
            marketplace_id: ID de la marketplace ('EBAY_FR', 'EBAY_DE', etc.)

        Returns:
            str: Nom localisé de l'aspect

        Examples:
            >>> mapping = session.query(AspectMapping).get('color')
            >>> mapping.get_aspect_name('EBAY_DE')
            'Farbe'
            >>> mapping.get_aspect_name('EBAY_FR')
            'Couleur'
        """
        marketplace_columns = {
            'EBAY_FR': self.ebay_fr,
            'EBAY_GB': self.ebay_gb,
            'EBAY_DE': self.ebay_de,
            'EBAY_ES': self.ebay_es,
            'EBAY_IT': self.ebay_it,
            'EBAY_NL': self.ebay_nl,
            'EBAY_BE': self.ebay_be,
            'EBAY_PL': self.ebay_pl,
        }

        # Retourner la colonne pour la marketplace, ou fallback sur FR
        return marketplace_columns.get(marketplace_id) or self.ebay_fr

    @classmethod
    def get_all_for_marketplace(cls, session: Session, marketplace_id: str) -> dict:
        """
        Récupère tous les mappings pour une marketplace.

        Args:
            session: Session SQLAlchemy
            marketplace_id: ID de la marketplace ('EBAY_FR', 'EBAY_DE', etc.)

        Returns:
            dict: Mapping {ebay_gb: aspect_name_localized}

        Examples:
            >>> mappings = AspectMapping.get_all_for_marketplace(session, 'EBAY_DE')
            >>> mappings
            {'Brand': 'Marke', 'Colour': 'Farbe', 'Size': 'Größe', ...}
        """
        mappings = session.query(cls).all()

        return {
            m.ebay_gb: m.get_aspect_name(marketplace_id)
            for m in mappings
            if m.ebay_gb  # Skip if no GB reference name
        }

    @classmethod
    def get_reverse_mapping(cls, session: Session) -> dict:
        """
        Crée un mapping inverse: nom localisé → aspect_key.

        Utile pour extraire les aspects depuis n'importe quel marketplace.

        Args:
            session: Session SQLAlchemy

        Returns:
            dict: Mapping {localized_name: aspect_key} pour toutes les langues

        Examples:
            >>> reverse = AspectMapping.get_reverse_mapping(session)
            >>> reverse.get('Marque')  # FR
            'brand'
            >>> reverse.get('Marke')   # DE
            'brand'
            >>> reverse.get('Brand')   # GB
            'brand'
        """
        mappings = session.query(cls).all()
        reverse = {}

        for m in mappings:
            # Add all language variants pointing to the same key
            for value in [m.ebay_gb, m.ebay_fr, m.ebay_de, m.ebay_es,
                          m.ebay_it, m.ebay_nl, m.ebay_be, m.ebay_pl]:
                if value:
                    reverse[value] = m.aspect_key

        return reverse

    def __repr__(self):
        return f"<AspectMapping(key='{self.aspect_key}', gb='{self.ebay_gb}', fr='{self.ebay_fr}')>"
