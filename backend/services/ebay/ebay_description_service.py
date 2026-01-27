"""
eBay Description Service.

Generates multilingual HTML descriptions for eBay listings with:
- Header + branding
- SEO intro paragraph
- Characteristics section
- Measurements section with category-aware labels
- Measurement guide image
- Shipping & Returns
- Footer
- 40 SEO tags

Ported from pythonApiWOO/services/ebay/ebay_description_multilang_service.py
"""

from sqlalchemy.orm import Session

from models.public.category import Category
from models.public.color import Color
from models.public.condition import Condition
from models.public.ebay_marketplace_config import MarketplaceConfig
from models.public.gender import Gender
from models.user.product import Product
from services.ebay.ebay_description_tags import build_ebay_tags
from services.ebay.ebay_description_translations import (
    MEASUREMENT_LABELS,
    TRANSLATIONS,
)
from shared.logging import get_logger

logger = get_logger(__name__)

MEASUREMENT_IMAGE_URL = (
    "https://shoptonoutfit.com/wp-content/uploads/2025/11/Mesures-site-scaled.png"
)
MAX_DESCRIPTION_LENGTH = 4000  # eBay Inventory API limit


class EbayDescriptionService:
    """Generate multilingual HTML descriptions for eBay listings."""

    def __init__(self, db: Session):
        self.db = db

    def generate_description(
        self,
        product: Product,
        marketplace_id: str,
        shop_name: str = "SHOP TON OUTFIT",
    ) -> str:
        """
        Generate full HTML description for an eBay listing.

        Args:
            product: StoFlow Product model.
            marketplace_id: eBay marketplace ID (e.g. "EBAY_FR").
            shop_name: Branding name for the header/footer.

        Returns:
            Complete HTML string for eBay description field.
        """
        lang = self._get_language(marketplace_id)
        t = TRANSLATIONS.get(lang, TRANSLATIONS["en"])

        category_type = self._get_category_type(product)
        seo_intro = self._generate_seo_intro(product, lang, t)
        characteristics_html = self._build_characteristics(product, lang, t)
        measurements_html = self._build_measurements(product, category_type, lang, t)
        tags_html = build_ebay_tags(product, lang)

        html = self._assemble_html(
            shop_name, t, seo_intro, characteristics_html,
            measurements_html, tags_html,
        )

        if len(html) > MAX_DESCRIPTION_LENGTH:
            html = html[: MAX_DESCRIPTION_LENGTH - 50] + "\n</div>\n</div>"

        return html

    # ========== PRIVATE METHODS ==========

    def _get_language(self, marketplace_id: str) -> str:
        """Get ISO 639-1 language code from marketplace config."""
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
        Translate an attribute value via DB lookup.

        Works with Color, Category, Gender models (all have name_en PK).
        Falls back to name_en if translation is missing.
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

    def _get_condition_text(self, condition_note: int | None, lang: str) -> str:
        """Get translated condition name from DB."""
        if condition_note is None:
            return ""
        condition_obj = (
            self.db.query(Condition)
            .filter(Condition.note == condition_note)
            .first()
        )
        if condition_obj:
            return condition_obj.get_name(lang)
        return ""

    def _get_category_type(self, product: Product) -> str:
        """
        Determine category type for measurement labels.

        Uses Category hierarchy (parent_category) to classify
        into 'jeans', 'shorts', or 'tops' (default).
        """
        if not product.category:
            return "tops"

        # Get category and its parent from DB
        category_obj = (
            self.db.query(Category)
            .filter(Category.name_en == product.category)
            .first()
        )
        parent_name = ""
        if category_obj and category_obj.parent_category:
            parent_name = category_obj.parent_category.lower()

        search_text = f"{parent_name} {product.category}".lower()

        if "short" in search_text:
            return "shorts"
        if any(kw in search_text for kw in ("jean", "pantalon", "pant", "trouser")):
            return "jeans"
        return "tops"

    def _generate_seo_intro(
        self, product: Product, lang: str, t: dict[str, str],
    ) -> str:
        """
        Generate SEO-critical introduction paragraph.

        Two sentences combining brand, model, decade, color, fit, condition, material.
        """
        brand = product.brand or ""
        model = product.model or ""
        decade = product.decade or ""
        fit = product.fit or ""
        color = product.colors[0] if product.colors else ""
        material = product.materials[0] if product.materials else ""
        size = product.size_normalized or product.size_original or ""

        # Translate category
        category_name = self._translate_attribute(
            Category, product.category, lang
        ) if product.category else "Item"

        # Condition text
        condition_text = self._get_condition_text(product.condition, lang)

        # SENTENCE 1: Product presentation
        parts1: list[str] = []
        if brand and brand.lower() != "unbranded":
            label = f"{category_name} {brand} {model}" if model else f"{category_name} {brand}"
            parts1.append(f"<strong>{label}</strong>")
        else:
            if decade:
                parts1.append(f"<strong>{category_name} {t['vintage']} {t['years']} {decade}</strong>")
            else:
                parts1.append(f"<strong>{category_name} {t['vintage']}</strong>")

        if decade and brand and brand.lower() != "unbranded":
            parts1.append(f"{t['years']} {decade}")
        if fit:
            parts1.append(t["in_cut"].format(fit))
        if condition_text:
            parts1.append(t["in_condition"].format(condition_text.lower()))

        sentence1 = " ".join(parts1) + "."

        # SENTENCE 2: Details
        parts2: list[str] = [f"{t['this']} {category_name.lower()}"]
        if color:
            parts2.append(color)
        if material:
            parts2.append(t["in_material"].format(material))
        if size:
            parts2.append(f"{t['size']} {size.upper()}")

        sentence2 = " ".join(parts2) + "."

        return f"{sentence1} {sentence2}"

    def _build_characteristics(
        self, product: Product, lang: str, t: dict[str, str],
    ) -> str:
        """Build HTML for the characteristics section."""
        lines: list[str] = []

        # Brand
        if product.brand and product.brand.lower() != "unbranded":
            lines.append(f'<p style="margin:5px 0;"><b>{t["brand"]}:</b> {product.brand}</p>')

        # Model
        if product.model:
            lines.append(f'<p style="margin:5px 0;"><b>{t["model"]}:</b> {product.model}</p>')

        # Fit
        if product.fit:
            lines.append(f'<p style="margin:5px 0;"><b>{t["fit"]}:</b> {product.fit.capitalize()}</p>')

        # Color (first, translated)
        if product.colors:
            color_translated = self._translate_attribute(Color, product.colors[0], lang)
            lines.append(f'<p style="margin:5px 0;"><b>{t["color"]}:</b> {color_translated.capitalize()}</p>')

        # Material (first)
        if product.materials:
            lines.append(f'<p style="margin:5px 0;"><b>{t["material"]}:</b> {product.materials[0].capitalize()}</p>')

        # Condition (with badge)
        condition_text = self._get_condition_text(product.condition, lang)
        if condition_text:
            badge_bg = self._get_condition_color(product.condition)
            lines.append(
                f'<p style="margin:5px 0;"><b>{t["condition"]}:</b> '
                f'<span style="background:{badge_bg};color:#fff;padding:2px 8px;'
                f'border-radius:10px;font-size:11px;">{condition_text}</span></p>'
            )

        # Era/Decade
        if product.decade:
            era_text = self._format_era(product.decade, lang, t)
            lines.append(f'<p style="margin:5px 0;"><b>{t["era"]}:</b> {era_text}</p>')

        # Gender (translated)
        if product.gender:
            gender_translated = self._translate_attribute(Gender, product.gender, lang)
            lines.append(f'<p style="margin:5px 0;"><b>{t["gender"]}:</b> {gender_translated.capitalize()}</p>')

        return "\n".join(lines)

    def _build_measurements(
        self,
        product: Product,
        category_type: str,
        lang: str,
        t: dict[str, str],
    ) -> str:
        """Build HTML for the measurements section."""
        lines: list[str] = []

        # Label size
        if product.size_original:
            lines.append(
                f'<p style="margin:5px 0;"><b>{t["label_size"]}:</b> '
                f'{product.size_original.upper()}</p>'
            )

        # Estimated size
        estimated = product.size_normalized or product.size_original or "N/A"
        lines.append(
            f'<p style="margin:5px 0;"><b>{t["estimated_size"]}:</b> '
            f'{estimated.upper()}</p>'
        )
        lines.append('<div style="border-top:1px solid #dee2e6;margin:10px 0;"></div>')

        # Dimension measurements
        measurement_labels = MEASUREMENT_LABELS.get(
            category_type, {}
        ).get(lang, MEASUREMENT_LABELS["tops"]["en"])

        counter = 1
        for dim_attr, label in measurement_labels:
            value = getattr(product, dim_attr, None)
            if value and value != 0:
                lines.append(
                    f'<p style="margin:5px 0;"><b>{counter}. {label}:</b> {value} cm</p>'
                )
                counter += 1

        if counter == 1:
            # No measurements found
            lines.append('<p style="margin:5px 0;">-</p>')

        lines.append(
            f'<p style="margin:10px 0 5px;font-size:12px;color:#666;">{t["see_guide"]}</p>'
        )

        return "\n".join(lines)

    @staticmethod
    def _get_condition_color(condition_note: int | None) -> str:
        """Get badge background color based on condition note (0-10)."""
        if condition_note is None:
            return "#28a745"
        if condition_note <= 3:
            return "#28a745"  # Green (excellent)
        if condition_note <= 5:
            return "#ffc107"  # Yellow (good)
        return "#ff9800"  # Orange (fair/worn)

    @staticmethod
    def _format_era(decade: str, lang: str, t: dict[str, str]) -> str:
        """Format era/decade string per language conventions."""
        era_formats: dict[str, str] = {
            "en": f"{decade}s",
            "fr": f"Années {decade}",
            "de": f"{decade}er Jahre",
            "it": f"Anni {decade}",
            "es": f"Años {decade}",
            "nl": f"Jaren {decade}",
            "pl": f"Lata {decade}",
        }
        return era_formats.get(lang, f"{decade}s")

    @staticmethod
    def _assemble_html(
        shop_name: str,
        t: dict[str, str],
        seo_intro: str,
        characteristics_html: str,
        measurements_html: str,
        tags_html: str,
    ) -> str:
        """Assemble all sections into the final HTML description."""
        return f'''<div style="max-width:1000px;margin:0 auto;font-family:Arial,sans-serif;color:#333;">

<!-- Header -->
<div style="background:#000;padding:25px;text-align:center;border-bottom:5px solid #FFC905;">
<h1 style="color:#FFC905;margin:0;font-size:26px;font-weight:700;text-transform:uppercase;">{shop_name}</h1>
<p style="color:#fff;margin:8px 0 0;font-size:13px;">{t['header_subtitle']}</p>
</div>

<!-- SEO Intro -->
<div style="background:#fff;padding:20px;margin:15px 0;border-left:5px solid #FFC905;">
<p style="margin:0;font-size:15px;line-height:1.7;">{seo_intro}</p>
</div>

<!-- Main Info -->
<div style="display:flex;gap:15px;margin:15px 0;flex-wrap:wrap;">

<div style="flex:1;min-width:280px;background:#f8f9fa;border:2px solid #e9ecef;border-radius:8px;padding:15px;">
<h2 style="color:#000;font-size:18px;margin:0 0 10px;border-bottom:3px solid #FFC905;padding-bottom:8px;">{t['characteristics']}</h2>
{characteristics_html}
</div>

<div style="flex:1;min-width:280px;background:#f8f9fa;border:2px solid #e9ecef;border-radius:8px;padding:15px;">
<h2 style="color:#000;font-size:18px;margin:0 0 10px;border-bottom:3px solid #FFC905;padding-bottom:8px;">{t['measurements_title']}</h2>
{measurements_html}
</div>

</div>

<!-- Measurement Guide -->
<div style="margin:15px 0;">
<img src="{MEASUREMENT_IMAGE_URL}" alt="Measurement guide" style="width:100%;max-width:800px;height:auto;border:2px solid #FFC905;border-radius:8px;display:block;margin:0 auto;">
</div>

<!-- Shipping & Returns -->
<div style="background:#f0fff0;border:2px solid #90ee90;border-radius:8px;padding:15px;margin:15px 0;">
<p style="margin:5px 0;text-align:center;">{t['shipping_text']}</p>
</div>

<!-- Footer -->
<div style="background:#000;color:#fff;padding:15px;text-align:center;border-radius:8px;margin:15px 0;border-top:5px solid #FFC905;">
<p style="margin:0;font-size:13px;">{t['footer_text']}</p>
</div>

<!-- SEO Tags -->
<div style="background:#f8f9fa;border:2px solid #e9ecef;border-radius:8px;padding:15px;margin:15px 0;">
<p style="margin:0 0 8px;font-weight:bold;font-size:14px;">SEO Tags:</p>
<p style="margin:0;font-size:12px;color:#666;line-height:1.8;">{tags_html}</p>
</div>

</div>'''
