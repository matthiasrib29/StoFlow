"""
eBay SEO Title Service.

Generates SEO-optimized titles for eBay listings, translated per marketplace language.

Title structure (by priority, 80 chars max):
    [Brand] [Model] [Category] [Size] [Color] [Condition] [Gender] [Decade] (location)

Examples:
    EBAY_FR: "Levi's 501 Jean W32/L34 Bleu Tres bon etat Homme 1990s"
    EBAY_DE: "Levi's 501 Jeans W32/L34 Blau Sehr gut Herren 1990s"
    EBAY_GB: "Levi's 501 Jeans W32/L34 Blue Very good Men 1990s"
"""

from sqlalchemy.orm import Session

from models.public.category import Category
from models.public.color import Color
from models.public.condition import Condition
from models.public.ebay_marketplace_config import MarketplaceConfig
from models.public.gender import Gender
from models.user.product import Product
from shared.logging import get_logger

logger = get_logger(__name__)

MAX_TITLE_LENGTH = 80


class EbaySeoTitleService:
    """Generate SEO-optimized eBay titles per marketplace language."""

    def __init__(self, db: Session):
        self.db = db

    def generate_seo_title(self, product: Product, marketplace_id: str) -> str:
        """
        Generate SEO title from product attributes, translated per marketplace.

        Priority order: Brand > Model > Category > Size > Color > Condition > Gender > Decade.
        Lower-priority components are dropped if the title exceeds 80 characters.

        Args:
            product: Product entity with attributes.
            marketplace_id: eBay marketplace ID (e.g. "EBAY_FR").

        Returns:
            SEO-optimized title string (max 80 chars).
        """
        lang = self._get_language(marketplace_id)
        components: list[str] = []

        # 1. Brand (no translation, skip "unbranded")
        if product.brand and product.brand.lower() != "unbranded":
            components.append(product.brand)

        # 2. Model (free text, no translation)
        if product.model:
            components.append(product.model)

        # 3. Category (translated)
        if product.category:
            translated = self._translate_attribute(Category, product.category, lang)
            components.append(translated)

        # 4. Size (international code, no translation)
        if product.size_original:
            components.append(product.size_original)

        # 5. Color (first color only, translated)
        if product.colors:
            translated = self._translate_attribute(Color, product.colors[0], lang)
            components.append(translated)

        # 6. Condition (lookup by note int, translated via get_name)
        if product.condition is not None:
            condition_obj = (
                self.db.query(Condition)
                .filter(Condition.note == product.condition)
                .first()
            )
            if condition_obj:
                components.append(condition_obj.get_name(lang))

        # 7. Gender (translated)
        if product.gender:
            translated = self._translate_attribute(Gender, product.gender, lang)
            components.append(translated)

        # 8. Decade (international code, no translation)
        if product.decade:
            components.append(product.decade)

        # Assemble with priority truncation
        title = self._assemble_title(components)

        # Add location if space permits
        if product.location:
            with_location = f"{title} ({product.location})"
            if len(with_location) <= MAX_TITLE_LENGTH:
                title = with_location

        return title

    def _get_language(self, marketplace_id: str) -> str:
        """
        Get ISO 639-1 language code from marketplace config.

        Falls back to "en" if marketplace not found.
        """
        config = (
            self.db.query(MarketplaceConfig)
            .filter(MarketplaceConfig.marketplace_id == marketplace_id)
            .first()
        )
        if config:
            return config.get_language()

        logger.warning(
            f"Marketplace config not found for {marketplace_id}, "
            f"falling back to English"
        )
        return "en"

    def _translate_attribute(self, model_class, name_en_value: str, lang: str) -> str:
        """
        Translate an attribute value to the target language via DB lookup.

        Works with Color, Category, Gender (all have name_en as PK).
        Falls back to name_en if translation column is missing or empty.

        Args:
            model_class: SQLAlchemy model with name_en PK and name_{lang} columns.
            name_en_value: English value (PK) to look up.
            lang: Target language code (e.g. "fr", "de").

        Returns:
            Translated string, or name_en_value as fallback.
        """
        if lang == "en":
            return name_en_value

        obj = (
            self.db.query(model_class)
            .filter(model_class.name_en == name_en_value)
            .first()
        )

        if obj:
            translated = getattr(obj, f"name_{lang}", None)
            if translated:
                return translated

        return name_en_value

    @staticmethod
    def _assemble_title(components: list[str]) -> str:
        """
        Join components with spaces, dropping lowest-priority items if too long.

        Components are ordered by priority (highest first).
        When the assembled title exceeds MAX_TITLE_LENGTH, the last (lowest priority)
        component is removed until the title fits.
        """
        while components:
            title = " ".join(components)
            if len(title) <= MAX_TITLE_LENGTH:
                return title
            components.pop()
        return ""
