"""
AI Vision Service

Service pour analyser les images de produits via Google Gemini Vision API.

Business Rules:
- Vérifie les crédits IA avant analyse
- Télécharge les images depuis R2 CDN
- Log chaque génération dans AIGenerationLog
- Décrémente les crédits utilisés
"""

import time
from decimal import Decimal
from typing import TYPE_CHECKING

import httpx
from google import genai
from google.genai import types
from sqlalchemy.orm import Session

from models.public.user import User
from models.user.ai_generation_log import AIGenerationLog
from schemas.ai_schemas import VisionExtractedAttributes
from shared.config import settings
from shared.exceptions import AIGenerationError, AIQuotaExceededError
from shared.logging import get_logger

if TYPE_CHECKING:
    from models.user.product import Product

logger = get_logger(__name__)

# Mapping: DB attribute key -> (schema field name, prompt label)
ATTR_DB_TO_SCHEMA: dict[str, tuple[str, str]] = {
    "categories": ("category", "Categories"),
    "colors": ("color", "Colors"),
    "materials": ("material", "Materials"),
    "fits": ("fit", "Fits"),
    "genders": ("gender", "Genders"),
    "seasons": ("season", "Seasons"),
    "patterns": ("pattern", "Patterns"),
    "lengths": ("length", "Lengths"),
    "necklines": ("neckline", "Necklines"),
    "sports": ("sport", "Sports"),
    "closures": ("closure", "Closures"),
    "rises": ("rise", "Rises"),
    "sleeve_lengths": ("sleeve_length", "Sleeve Lengths"),
    "stretches": ("stretch", "Stretches"),
    "linings": ("lining", "Linings"),
    "decades": ("decade", "Decades"),
    "origins": ("origin", "Origins"),
    "trends": ("trend", "Trends"),
    "condition_sups": ("condition_sup", "Condition Details"),
    "unique_features": ("unique_feature", "Unique Features"),
}

# Attributes with fewer values than this threshold use schema enum (not prompt list)
ENUM_THRESHOLD = 16

# Fields that accept multiple comma-separated values (field_name -> max count or None)
MULTI_VALUE_FIELDS: dict[str, int | None] = {
    "color": 2,
    "material": None,
    "condition_sup": None,
    "unique_feature": None,
    "marking": None,
}

# Description of each attribute: what it is and what to extract
ATTR_DESCRIPTIONS: dict[str, str] = {
    "category": "Product category — determine from full garment shape across all images + label text",
    "brand": "Brand name — exact text as seen on logo, label, or tag",
    "condition": "Overall condition — be realistic and fair. 10=new with tags still attached, 9=new without tags (perfect, never worn), 8=like new (worn a few times, no notable defects visible), 7=very good (light signs of wear, no stains/holes), 6=good (minor pilling or light wear marks), 5=fair (small stain, minor fading, or visible pilling), 4=worn (clear signs of use, multiple minor defects), 3=very worn (multiple defects, fading, stains), 2=poor (heavy wear, holes, tears), 1=damaged. Only clear, visible defects should lower the score — do not penalize for normal light wear on used items",
    "label_size": "Size — exact text as shown on the size tag/label",
    "color": "Main colors visible on the product",
    "material": "Fabric/material composition — from label or visual texture",
    "fit": "Fit/cut type (e.g. slim, regular, oversized)",
    "gender": "Target gender for this product",
    "season": "Most appropriate season to wear this item",
    "sport": "Associated sport, if applicable",
    "neckline": "Neckline type (e.g. crew neck, V-neck, collar)",
    "length": "Garment length (e.g. short, midi, long)",
    "pattern": "Pattern/print type (e.g. solid, striped, checkered)",
    "condition_sup": "Specific condition details (e.g. pilling, stains, fading)",
    "rise": "Waist rise for pants/shorts (low, mid, high)",
    "closure": "Closure type (e.g. zipper, buttons, snap)",
    "sleeve_length": "Sleeve length (e.g. short, long, sleeveless)",
    "stretch": "Stretch/elasticity level of the fabric",
    "lining": "Lining type (lined, unlined, partial)",
    "origin": "Country of manufacture if visible on label",
    "decade": "Decade/era if vintage item",
    "trend": "Fashion trend this item belongs to",
    "model": "Model reference — exact text if visible on label",
    "unique_feature": "Distinctive characteristics (e.g. embroidery, distressed, rhinestones)",
    "marking": "Other visible texts/markings (dates, codes, inscriptions)",
    "confidence": "Your global confidence in this analysis — 0.0 to 1.0",
}


class AIVisionService:
    """Service pour analyser les images produits via Gemini Vision."""

    # Pricing Gemini (USD par million tokens) - Jan 2026
    MODEL_PRICING = {
        "gemini-2.5-flash": {"input": 0.075, "output": 0.30},
        "gemini-2.5-pro": {"input": 1.25, "output": 5.00},
        "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
        "gemini-3-flash-preview": {"input": 0.50, "output": 3.00},
        "gemini-3-pro-preview": {"input": 2.00, "output": 12.00},
    }

    SYSTEM_INSTRUCTION = """ROLE: Elite Fashion Archivist & Product Authenticator.

PRIME DIRECTIVE (EVIDENCE HIERARCHY):
1. LABEL TEXT (OCR) IS AUTHORITY: Text read on tags (Brand, Size, Material, "Jeans", "Slim") overrides ANY visual ambiguity.
   - Example: If a garment is folded and looks short, but the label says "Straight Leg Jeans", categorize as JEANS, not Shorts.
   - Example: If visual texture looks like polyester but label says "100% Silk", output SILK.
2. CONTRADICTION RESOLUTION: If visual shape conflicts with label text, the label text wins.

OPERATIONAL RULES:
- ACCURACY OVER GUESSING: If a specific attribute (like material composition) is not clearly readable or visible, return null. DO NOT hallucinate percentages.
- CATEGORY MAPPING: You must map the item to the most specific matching path from the provided Reference Taxonomy.
- CONDITION GRADING: Be realistic and fair. Examine images carefully for stains, pilling, fading, holes, loose threads, discoloration. 10/10 is ONLY for items with visible tags still attached. 8 is appropriate for items worn a few times with no notable defects. Reserve 7 and below for items with clearly visible defects.

OUTPUT GOAL:
Generate a precise JSON object adhering strictly to the provided schema."""

    @staticmethod
    async def analyze_images(
        db: Session,
        product: "Product",
        user_id: int,
        monthly_credits: int = 0,
        max_images: int = 5,
    ) -> tuple[VisionExtractedAttributes, int, Decimal, int]:
        """
        Analyse les images d'un produit et extrait les attributs.

        Args:
            db: Session SQLAlchemy
            product: Produit avec images à analyser
            user_id: ID de l'utilisateur
            monthly_credits: Crédits mensuels de l'abonnement
            max_images: Nombre max d'images à analyser (selon abonnement)

        Returns:
            tuple: (attributes, tokens_used, cost, images_analyzed)

        Raises:
            AIQuotaExceededError: Si crédits insuffisants
            AIGenerationError: Si erreur API Gemini ou pas d'images
        """
        start_time = time.time()

        # Store product_id early to avoid issues after db.commit() expires the object
        # (SET LOCAL search_path is reset after commit, so lazy loading would fail)
        product_id = product.id

        # 1. Vérifier qu'il y a des images
        if not product.images:
            raise AIGenerationError("Le produit n'a pas d'images à analyser.")

        # 2. Vérifier les crédits
        AIVisionService._check_credits(db, user_id, monthly_credits)

        # 3. Récupérer les images (max selon abonnement)
        # Exclure les images label (is_label=True) - ne garder que les photos produit
        product_photos = [img for img in product.images if not img.get("is_label", False)]
        if not product_photos:
            raise AIGenerationError("Le produit n'a pas de photos à analyser (uniquement des labels).")

        images_to_analyze = product_photos[:max_images]
        images_analyzed = len(images_to_analyze)

        logger.info(
            f"[AIVisionService] Analyzing {images_analyzed} images "
            f"for product_id={product_id}"
        )

        # 4. Télécharger les images
        image_parts = await AIVisionService._download_images(images_to_analyze)

        if not image_parts:
            raise AIGenerationError("Impossible de télécharger les images du produit.")

        # 5. Call Gemini and process response
        return AIVisionService._call_gemini_and_process(
            db, image_parts, user_id, product_id, images_analyzed, start_time
        )

    @staticmethod
    def _check_credits(db: Session, user_id: int, monthly_credits: int) -> None:
        """Vérifie que l'utilisateur a des crédits disponibles."""
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise AIQuotaExceededError("Utilisateur non trouvé.")

        remaining = user.get_remaining_ai_credits(monthly_credits)

        if remaining <= 0:
            raise AIQuotaExceededError(
                "Crédits IA insuffisants. Veuillez upgrader votre abonnement "
                "ou acheter des crédits supplémentaires."
            )

    @staticmethod
    def _consume_credit(db: Session, user_id: int) -> None:
        """Décrémente les crédits utilisés."""
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.ai_credits_used_this_month += 1

    @staticmethod
    async def _download_images(
        images: list[dict],
    ) -> list[types.Part]:
        """
        Télécharge les images depuis les URLs R2 CDN.

        Args:
            images: Liste des images JSONB [{url, order, created_at}]

        Returns:
            Liste de types.Part contenant les images
        """
        image_parts = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            for idx, img in enumerate(images):
                try:
                    image_url = img.get("url", "")
                    if not image_url:
                        continue

                    response = await client.get(image_url)
                    response.raise_for_status()

                    # Détecter le type MIME
                    content_type = response.headers.get(
                        "content-type", "image/jpeg"
                    )

                    # Créer le Part pour Gemini
                    part = types.Part.from_bytes(
                        data=response.content,
                        mime_type=content_type,
                    )
                    image_parts.append(part)

                    logger.debug(
                        f"[AIVisionService] Downloaded image: {image_url}"
                    )

                except httpx.HTTPError as e:
                    logger.warning(
                        f"[AIVisionService] Failed to download image "
                        f"{img.get('url', 'unknown')}: {e}"
                    )
                    # Continue avec les autres images
                    continue

        return image_parts

    @staticmethod
    def _fetch_product_attributes(db: Session) -> dict[str, list[str]]:
        """
        Fetch all product attributes from database.

        Returns:
            Dictionary with attribute names as keys and list of valid values as values.
        """
        from models.public.brand import Brand
        from models.public.category import Category
        from models.public.color import Color
        from models.public.condition import Condition
        from models.public.fit import Fit
        from models.public.gender import Gender
        from models.public.length import Length
        from models.public.material import Material
        from models.public.neckline import Neckline
        from models.public.pattern import Pattern
        from models.public.season import Season
        from models.public.sport import Sport
        from models.public.closure import Closure
        from models.public.rise import Rise
        from models.public.sleeve_length import SleeveLength
        from models.public.stretch import Stretch
        from models.public.lining import Lining
        from models.public.decade import Decade
        from models.public.origin import Origin
        from models.public.trend import Trend
        from models.public.condition_sup import ConditionSup
        from models.public.unique_feature import UniqueFeature

        attributes = {}

        # Fetch each attribute type
        # Note: Brands are NOT sent to AI - post-processing will match/create them

        # Categories: only leaf categories (no children)
        # A leaf category is one whose name_en is NOT used as parent_category by any other category
        from sqlalchemy import select
        parent_subq = select(Category.parent_category).where(Category.parent_category.isnot(None)).distinct()
        attributes["categories"] = [
            c.name_en for c in db.query(Category.name_en)
            .filter(~Category.name_en.in_(parent_subq))
            .order_by(Category.name_en)
            .all()
        ]
        attributes["colors"] = [c.name_en for c in db.query(Color.name_en).order_by(Color.name_en).limit(100).all()]
        attributes["conditions"] = [str(c.name_en) for c in db.query(Condition.name_en).order_by(Condition.name_en).all()]
        attributes["fits"] = [f.name_en for f in db.query(Fit.name_en).order_by(Fit.name_en).all()]
        attributes["genders"] = [g.name_en for g in db.query(Gender.name_en).order_by(Gender.name_en).all()]
        attributes["lengths"] = [l.name_en for l in db.query(Length.name_en).order_by(Length.name_en).all()]
        attributes["materials"] = [m.name_en for m in db.query(Material.name_en).order_by(Material.name_en).limit(100).all()]
        attributes["necklines"] = [n.name_en for n in db.query(Neckline.name_en).order_by(Neckline.name_en).all()]
        attributes["patterns"] = [p.name_en for p in db.query(Pattern.name_en).order_by(Pattern.name_en).all()]
        attributes["seasons"] = [s.name_en for s in db.query(Season.name_en).order_by(Season.name_en).all()]
        attributes["sports"] = [s.name_en for s in db.query(Sport.name_en).order_by(Sport.name_en).all()]
        attributes["closures"] = [c.name_en for c in db.query(Closure.name_en).order_by(Closure.name_en).all()]
        attributes["rises"] = [r.name_en for r in db.query(Rise.name_en).order_by(Rise.name_en).all()]
        attributes["sleeve_lengths"] = [s.name_en for s in db.query(SleeveLength.name_en).order_by(SleeveLength.name_en).all()]
        attributes["stretches"] = [s.name_en for s in db.query(Stretch.name_en).order_by(Stretch.name_en).all()]
        attributes["linings"] = [l.name_en for l in db.query(Lining.name_en).order_by(Lining.name_en).all()]
        attributes["decades"] = [d.name_en for d in db.query(Decade.name_en).order_by(Decade.name_en).all()]
        attributes["origins"] = [o.name_en for o in db.query(Origin.name_en).order_by(Origin.name_en).all()]
        attributes["trends"] = [t.name_en for t in db.query(Trend.name_en).order_by(Trend.name_en).all()]
        attributes["condition_sups"] = [c.name_en for c in db.query(ConditionSup.name_en).order_by(ConditionSup.name_en).all()]
        attributes["unique_features"] = [u.name_en for u in db.query(UniqueFeature.name_en).order_by(UniqueFeature.name_en).all()]

        return attributes

    @staticmethod
    def _build_response_schema(attributes: dict[str, list[str]]) -> dict:
        """
        Build dynamic JSON schema with enum constraints for attributes with < ENUM_THRESHOLD values.
        Attributes with >= ENUM_THRESHOLD values are listed in the prompt text instead.
        """
        # Fields that MUST have a value (Gemini cannot return null)
        non_nullable = {"category", "gender", "condition", "confidence", "color"}

        properties = {
            # Fixed fields (not from DB attribute lists)
            "brand": {"type": "STRING", "nullable": True},
            "condition": {"type": "INTEGER"},
            "label_size": {"type": "STRING", "nullable": True},
            "model": {"type": "STRING", "nullable": True},
            "marking": {"type": "STRING", "nullable": True},
            "confidence": {"type": "NUMBER"},
        }

        enum_attrs = []
        for db_key, (field_name, _) in ATTR_DB_TO_SCHEMA.items():
            values = attributes.get(db_key, [])
            nullable = field_name not in non_nullable
            prop: dict = {"type": "STRING"}
            if nullable:
                prop["nullable"] = True
            if 0 < len(values) < ENUM_THRESHOLD:
                prop["enum"] = values
                enum_attrs.append(f"{field_name}({len(values)})")
            properties[field_name] = prop

        if enum_attrs:
            logger.info(
                f"[AIVisionService] Schema enums: {', '.join(enum_attrs)}"
            )

        return {
            "type": "OBJECT",
            "properties": properties,
            "required": list(properties.keys()),
        }

    @staticmethod
    def _build_prompt(attributes: dict[str, list[str]]) -> str:
        """
        Build the analysis prompt for Gemini Vision with database attributes.
        Only lists attributes with >= ENUM_THRESHOLD values in the prompt.
        Attributes with fewer values are enforced via schema enum constraints.

        Args:
            attributes: Dictionary of valid attribute values from database
        """
        # Build valid values section (only attributes with >= ENUM_THRESHOLD values)
        valid_values_lines = []
        for db_key, (_, label) in ATTR_DB_TO_SCHEMA.items():
            values = attributes.get(db_key, [])
            if len(values) >= ENUM_THRESHOLD:
                valid_values_lines.append(f"**{label}:** {', '.join(values)}")

        # Always include conditions (reference for 0-10 scale, not a schema enum)
        conditions = attributes.get("conditions", [])
        if conditions:
            valid_values_lines.append(f"**Conditions:** {', '.join(conditions)}")

        valid_values_section = "\n".join(valid_values_lines)

        # Build multi-value fields rule dynamically
        multi_parts = []
        for field, max_count in MULTI_VALUE_FIELDS.items():
            if max_count:
                multi_parts.append(f"{field} (max {max_count})")
            else:
                multi_parts.append(field)
        multi_value_rule = ", ".join(multi_parts)

        # Build attribute descriptions dynamically
        attr_desc_lines = "\n".join(
            f"- {field}: {desc}" for field, desc in ATTR_DESCRIPTIONS.items()
        )

        return f"""Analyze the following product images and extract ALL visible attributes.

RULES:
- Return null for any attribute NOT VISIBLE or UNCERTAIN
- ONLY use valid values (from the reference lists below or enforced by the response schema)
- If visible value is not valid, use the closest match or null
- SINGLE VALUE per attribute, except: {multi_value_rule} (comma-separated if multiple)
- If multiple values could apply, choose the MOST PROMINENT one

ATTRIBUTES TO EXTRACT:
{attr_desc_lines}

REFERENCE VALUES (use exact names):
{valid_values_section}

Analyze ALL provided images."""

    @staticmethod
    def _call_gemini_and_process(
        db: Session,
        image_parts: list,
        user_id: int,
        product_id: int | None,
        images_analyzed: int,
        start_time: float,
    ) -> tuple[VisionExtractedAttributes, int, Decimal, int]:
        """
        Common Gemini API call: build prompt/schema, call API, parse response,
        calculate metrics, log generation, consume credit.

        Args:
            db: SQLAlchemy session
            image_parts: List of Gemini Part objects (images)
            user_id: User ID for credit tracking
            product_id: Product ID (None for direct upload analysis)
            images_analyzed: Number of images being analyzed
            start_time: time.time() at the start of the analysis

        Returns:
            tuple: (attributes, tokens_used, cost, images_analyzed)
        """
        import json

        attributes = AIVisionService._fetch_product_attributes(db)
        prompt = AIVisionService._build_prompt(attributes)
        response_schema = AIVisionService._build_response_schema(attributes)

        try:
            client = genai.Client(
                api_key=settings.gemini_api_key,
                http_options=types.HttpOptions(
                    timeout=settings.gemini_timeout_seconds * 1000
                ),
            )

            contents = image_parts + [prompt]

            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=AIVisionService.SYSTEM_INSTRUCTION,
                    response_mime_type="application/json",
                    response_schema=response_schema,
                    temperature=0.1,
                    media_resolution=types.MediaResolution.MEDIA_RESOLUTION_HIGH,
                    thinking_config=types.ThinkingConfig(
                        thinking_level="MEDIUM",
                    ),
                ),
            )

            # Check for empty response
            if not response.text:
                logger.warning(
                    f"[AIVisionService] Empty response from Gemini. "
                    f"Candidates: {response.candidates if hasattr(response, 'candidates') else 'N/A'}"
                )
                raise AIGenerationError(
                    "L'IA n'a pas pu analyser les images. Réessayez ou vérifiez les images."
                )

            response_data = json.loads(response.text)
            response_data = AIVisionService._clean_ai_response(response_data)
            response_data = AIVisionService._process_brand(db, response_data)
            extracted_attributes = VisionExtractedAttributes(**response_data)

            # Calculate metrics
            input_tokens = response.usage_metadata.prompt_token_count
            output_tokens = response.usage_metadata.candidates_token_count
            total_tokens = input_tokens + output_tokens

            pricing = AIVisionService.MODEL_PRICING.get(
                settings.gemini_model, {"input": 0.075, "output": 0.30}
            )
            cost = Decimal(
                str(
                    (input_tokens * pricing["input"] / 1_000_000)
                    + (output_tokens * pricing["output"] / 1_000_000)
                )
            )

            generation_time_ms = int((time.time() - start_time) * 1000)

            # Log generation
            log = AIGenerationLog(
                product_id=product_id,
                model=settings.gemini_model,
                prompt_tokens=input_tokens,
                completion_tokens=output_tokens,
                total_tokens=total_tokens,
                total_cost=cost,
                cached=False,
                generation_time_ms=generation_time_ms,
                response_data=response_data,
            )
            db.add(log)

            AIVisionService._consume_credit(db, user_id)
            db.commit()

            logger.info(
                f"[AIVisionService] Analysis complete: product_id={product_id}, "
                f"images={images_analyzed}, tokens={total_tokens}, "
                f"cost=${cost:.6f}, time={generation_time_ms}ms, "
                f"confidence={extracted_attributes.confidence:.2f}"
            )

            return extracted_attributes, total_tokens, cost, images_analyzed

        except genai.errors.ClientError as e:
            logger.error(f"[AIVisionService] Gemini client error: {e}", exc_info=True)
            raise AIGenerationError("Clé API Gemini invalide ou erreur client")
        except genai.errors.ServerError as e:
            logger.error(f"[AIVisionService] Gemini server error: {e}", exc_info=True)
            raise AIGenerationError(
                "Erreur serveur Gemini. Réessayez dans quelques minutes."
            )
        except genai.errors.APIError as e:
            logger.error(f"[AIVisionService] Gemini API error: {e}", exc_info=True)
            raise AIGenerationError(f"Erreur API Gemini: {str(e)}")
        except Exception as e:
            logger.error(
                f"[AIVisionService] Unexpected error: {e}", exc_info=True
            )
            raise AIGenerationError(f"Erreur inattendue: {str(e)}")

    @staticmethod
    def _clean_ai_response(data: dict) -> dict:
        """
        Clean AI response:
        1. Single-value fields: extract first value if multiple were returned
        2. Array fields: convert comma-separated string to list

        Args:
            data: Raw AI response dictionary

        Returns:
            Cleaned dictionary with proper types for each field
        """
        # Fields that should have a single value (not comma-separated)
        single_value_fields = {
            'category', 'brand', 'fit', 'gender',
            'season', 'sport', 'neckline', 'length', 'pattern',
            'rise', 'closure', 'sleeve_length', 'stretch', 'lining',
            'origin', 'decade', 'trend', 'model', 'label_size'
        }

        # Fields that should be arrays (comma-separated string -> list)
        array_fields = {
            'condition_sup', 'unique_feature', 'marking', 'color', 'material'
        }

        cleaned = {}
        for key, value in data.items():
            if value is None:
                cleaned[key] = None
            elif key in array_fields and isinstance(value, str):
                # Convert comma-separated string to list
                items = [item.strip() for item in value.split(',') if item.strip()]
                cleaned[key] = items if items else None
                logger.debug(f"[AIVisionService] Converted '{key}' to array: {items}")
            elif key in single_value_fields and isinstance(value, str):
                # If value contains comma, take the first part
                if ',' in value:
                    first_value = value.split(',')[0].strip()
                    logger.debug(
                        f"[AIVisionService] Cleaned '{key}': '{value}' -> '{first_value}'"
                    )
                    cleaned[key] = first_value
                else:
                    cleaned[key] = value.strip()
            else:
                cleaned[key] = value

        return cleaned

    @staticmethod
    def _process_brand(db: Session, data: dict) -> dict:
        """
        Post-process brand: match existing brand in DB or create new one.

        This allows AI to return any brand name, then we:
        1. Search for case-insensitive match in database
        2. If found, use exact DB name (proper casing)
        3. If not found, create new brand entry

        Args:
            db: SQLAlchemy session
            data: AI response dictionary with 'brand' field

        Returns:
            Updated dictionary with processed brand name
        """
        from models.public.brand import Brand
        from sqlalchemy import func

        brand_name = data.get('brand')
        if not brand_name or not isinstance(brand_name, str):
            return data

        brand_name = brand_name.strip()
        if not brand_name:
            return data

        # Search for case-insensitive match
        existing_brand = db.query(Brand).filter(
            func.lower(Brand.name) == func.lower(brand_name)
        ).first()

        if existing_brand:
            # Use exact name from DB (proper casing)
            data['brand'] = existing_brand.name
            logger.debug(f"[AIVisionService] Brand matched: '{brand_name}' -> '{existing_brand.name}'")
        else:
            # Create new brand with AI-provided name (capitalize first letter of each word)
            normalized_name = brand_name.title()
            new_brand = Brand(name=normalized_name)
            db.add(new_brand)
            db.flush()  # Get the brand in session without committing
            data['brand'] = normalized_name
            logger.info(f"[AIVisionService] New brand created: '{normalized_name}'")

        return data

    @staticmethod
    async def analyze_images_direct(
        db: Session,
        image_files: list[tuple[bytes, str]],
        user_id: int,
        monthly_credits: int = 0,
    ) -> tuple[VisionExtractedAttributes, int, Decimal, int]:
        """
        Analyse des images uploadées directement (sans produit existant).

        Utilisé pour la création de produit avec pré-remplissage IA.

        Note: La limitation du nombre d'images est faite dans l'endpoint API
        selon l'abonnement de l'utilisateur (ai_max_images_per_analysis).

        Args:
            db: Session SQLAlchemy
            image_files: Liste de tuples (contenu_bytes, mime_type) - déjà limité par l'API
            user_id: ID de l'utilisateur
            monthly_credits: Crédits mensuels de l'abonnement

        Returns:
            tuple: (attributes, tokens_used, cost, images_analyzed)

        Raises:
            AIQuotaExceededError: Si crédits insuffisants
            AIGenerationError: Si erreur API Gemini ou pas d'images
        """
        start_time = time.time()

        # 1. Vérifier qu'il y a des images
        if not image_files:
            raise AIGenerationError("Aucune image fournie pour l'analyse.")

        # 2. Vérifier les crédits
        AIVisionService._check_credits(db, user_id, monthly_credits)

        # 3. Utiliser les images fournies (déjà limitées par l'API selon abonnement)
        images_to_analyze = image_files
        images_analyzed = len(images_to_analyze)

        logger.info(
            f"[AIVisionService] Analyzing {images_analyzed} images directly "
            f"for user_id={user_id}"
        )

        # 4. Créer les Parts Gemini à partir des bytes
        image_parts = []
        for content, mime_type in images_to_analyze:
            part = types.Part.from_bytes(
                data=content,
                mime_type=mime_type,
            )
            image_parts.append(part)

        if not image_parts:
            raise AIGenerationError("Impossible de traiter les images.")

        # 5. Call Gemini and process response
        return AIVisionService._call_gemini_and_process(
            db, image_parts, user_id, None, images_analyzed, start_time
        )
