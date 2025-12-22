"""
Modèle pour la configuration des marketplaces eBay.

Stocke les informations statiques de chaque marketplace (FR, GB, DE, IT, ES, NL, BE, PL).
Cette table est partagée entre tous les users (schema public).

Les credentials et settings par user sont dans public.platform_mappings.

Author: Claude
Date: 2025-12-10
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from shared.database import Base


class MarketplaceConfig(Base):
    """Configuration statique des 8 marketplaces eBay supportées"""

    __tablename__ = 'marketplace_config'
    __table_args__ = {'schema': 'ebay'}

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    marketplace_id = Column(String(20), unique=True, nullable=False, index=True, comment="EBAY_FR, EBAY_GB, etc.")
    country_code = Column(String(2), nullable=False, comment="FR, UK, DE, IT, ES, NL, BE, PL")
    site_id = Column(Integer, nullable=False, comment="Site ID eBay (71=FR, 3=UK, 77=DE, etc.)")
    currency = Column(String(3), nullable=False, comment="EUR, GBP, PLN")
    is_active = Column(Boolean, default=True, nullable=False, comment="Activer/désactiver marketplace")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def get_language(self) -> str:
        """
        Retourne le code langue ISO 639-1 dérivé du country_code.

        Returns:
            str: Code langue (fr, de, it, en, pl, es, nl)

        Examples:
            >>> config = MarketplaceConfig(country_code='FR')
            >>> config.get_language()
            'fr'
            >>> config = MarketplaceConfig(country_code='UK')
            >>> config.get_language()
            'en'
        """
        # Mapping des country_codes vers langues
        language_map = {
            'UK': 'en',  # Royaume-Uni
            'BE': 'fr',  # Belgique: français majoritaire
        }

        # Si cas spécial, utiliser mapping, sinon dériver du country_code
        if self.country_code in language_map:
            return language_map[self.country_code]

        # Règle par défaut: country_code en minuscule
        return self.country_code.lower()

    def get_content_language(self) -> str:
        """
        Retourne le Content-Language header pour cette marketplace.

        Le Content-Language doit correspondre à la locale eBay exacte
        pour que l'inventory item soit trouvé lors de la création de l'offre.

        Returns:
            str: Content-Language au format ISO (ex: fr-FR, de-DE, en-GB)

        Examples:
            >>> config = MarketplaceConfig(marketplace_id='EBAY_FR', country_code='FR')
            >>> config.get_content_language()
            'fr-FR'
            >>> config = MarketplaceConfig(marketplace_id='EBAY_GB', country_code='UK')
            >>> config.get_content_language()
            'en-GB'
        """
        lang = self.get_language()

        # Correction pour UK → GB (standard ISO 3166-1)
        country = 'GB' if self.country_code == 'UK' else self.country_code

        return f"{lang}-{country}"

    def __repr__(self):
        return f"<MarketplaceConfig(marketplace_id='{self.marketplace_id}', country='{self.country_code}', active={self.is_active})>"
