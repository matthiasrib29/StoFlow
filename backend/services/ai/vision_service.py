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

from models.public.ai_credit import AICredit
from models.user.ai_generation_log import AIGenerationLog
from schemas.ai_schemas import GeminiVisionSchema, VisionExtractedAttributes
from shared.config import settings
from shared.exceptions import AIGenerationError, AIQuotaExceededError
from shared.logging_setup import get_logger

if TYPE_CHECKING:
    from models.user.product import Product

logger = get_logger(__name__)


class AIVisionService:
    """Service pour analyser les images produits via Gemini Vision."""

    # Pricing Gemini (USD par million tokens) - Jan 2026
    MODEL_PRICING = {
        "gemini-2.5-flash": {"input": 0.075, "output": 0.30},
        "gemini-2.5-pro": {"input": 1.25, "output": 5.00},
        "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
        "gemini-3-flash-preview": {"input": 0.075, "output": 0.30},  # Preview model (pricing assumed)
    }

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
        images_to_analyze = product.images[:max_images]
        images_analyzed = len(images_to_analyze)

        logger.info(
            f"[AIVisionService] Analyzing {images_analyzed} images "
            f"for product_id={product_id}"
        )

        # 4. Télécharger les images
        image_parts = await AIVisionService._download_images(images_to_analyze)

        if not image_parts:
            raise AIGenerationError("Impossible de télécharger les images du produit.")

        # 5. Fetch product attributes from database
        attributes = AIVisionService._fetch_product_attributes(db)

        # 6. Construire le prompt
        prompt = AIVisionService._build_prompt(attributes)

        # 7. Appeler Gemini Vision API
        try:
            # Configure Gemini client with timeout
            client = genai.Client(
                api_key=settings.gemini_api_key,
                http_options=httpx.Timeout(timeout=settings.gemini_timeout_seconds),
            )

            # Construire le contenu multimodal
            contents = [prompt] + image_parts

            # Appeler avec structured output (using GeminiVisionSchema without defaults)
            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=GeminiVisionSchema,
                    temperature=0.0,  # Deterministic for accurate analysis
                    mediaResolution=types.MediaResolution.MEDIA_RESOLUTION_HIGH,  # Better detail recognition (1120 tokens/image)
                ),
            )

            # Parser la réponse
            import json

            response_data = json.loads(response.text)

            # Clean AI response: extract first value if multiple were returned
            response_data = AIVisionService._clean_ai_response(response_data)

            # Post-process brand: match existing or create new
            response_data = AIVisionService._process_brand(db, response_data)

            # Convert to VisionExtractedAttributes (with defaults for missing fields)
            extracted_attributes = VisionExtractedAttributes(**response_data)

            # 8. Calculer les métriques
            input_tokens = response.usage_metadata.prompt_token_count
            output_tokens = response.usage_metadata.candidates_token_count
            total_tokens = input_tokens + output_tokens

            # 9. Calculer le coût
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

            # 10. Logger la génération
            log = AIGenerationLog(
                product_id=product_id,
                model=settings.gemini_model,
                prompt_tokens=input_tokens,
                completion_tokens=output_tokens,
                total_tokens=total_tokens,
                total_cost=cost,
                cached=False,
                generation_time_ms=generation_time_ms,
                response_data=response_data,  # Store raw AI response
            )
            db.add(log)

            # 11. Incrémenter les crédits utilisés
            AIVisionService._consume_credit(db, user_id)

            db.commit()

            logger.info(
                f"[AIVisionService] Analyzed images: product_id={product_id}, "
                f"images={images_analyzed}, tokens={total_tokens}, "
                f"cost=${cost:.6f}, time={generation_time_ms}ms, "
                f"confidence={extracted_attributes.confidence:.2f}"
            )

            return extracted_attributes, total_tokens, cost, images_analyzed

        except genai.errors.ClientError as e:
            logger.error(f"[AIVisionService] Gemini client error: {e}")
            raise AIGenerationError("Clé API Gemini invalide ou erreur client")
        except genai.errors.ServerError as e:
            logger.error(f"[AIVisionService] Gemini server error: {e}")
            raise AIGenerationError(
                "Erreur serveur Gemini. Réessayez dans quelques minutes."
            )
        except genai.errors.APIError as e:
            logger.error(f"[AIVisionService] Gemini API error: {e}")
            raise AIGenerationError(f"Erreur API Gemini: {str(e)}")
        except Exception as e:
            logger.error(f"[AIVisionService] Unexpected error: {e}", exc_info=True)
            raise AIGenerationError(f"Erreur inattendue: {str(e)}")

    @staticmethod
    def _check_credits(db: Session, user_id: int, monthly_credits: int) -> None:
        """Vérifie que l'utilisateur a des crédits disponibles."""
        ai_credit = db.query(AICredit).filter(AICredit.user_id == user_id).first()

        if not ai_credit:
            # Créer l'enregistrement si n'existe pas
            ai_credit = AICredit(user_id=user_id)
            db.add(ai_credit)
            db.flush()

        remaining = ai_credit.get_remaining_credits(monthly_credits)

        if remaining <= 0:
            raise AIQuotaExceededError(
                "Crédits IA insuffisants. Veuillez upgrader votre abonnement "
                "ou acheter des crédits supplémentaires."
            )

    @staticmethod
    def _consume_credit(db: Session, user_id: int) -> None:
        """Décrémente les crédits utilisés."""
        ai_credit = db.query(AICredit).filter(AICredit.user_id == user_id).first()
        if ai_credit:
            ai_credit.ai_credits_used_this_month += 1

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
            for img in images:
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
    def _build_prompt(attributes: dict[str, list[str]]) -> str:
        """
        Build the analysis prompt for Gemini Vision with database attributes.

        Args:
            attributes: Dictionary of valid attribute values from database
        """
        return f"""You are an expert in analyzing product images for online sales (clothing and accessories).

Analyze the following product images and extract ALL visible attributes.

CRITICAL RULES:
- Return null for any attribute NOT VISIBLE or UNCERTAIN
- DO NOT GUESS - only analyze what is clearly visible
- condition: Rating from 0 to 10 (10=new with tags, 8=excellent, 5=good, 2=worn)
- confidence: Your GLOBAL confidence in the analysis (0.0 to 1.0)
- For attributes with predefined values, ONLY use values from the provided lists
- If visible value is not in the list, use the closest match or null
- IMPORTANT: For each attribute, return ONLY ONE value (not multiple values separated by commas)
  - Exceptions that CAN have multiple comma-separated values: color, material, unique_feature, marking
- If multiple values could apply (e.g., "Regular" and "Straight" for fit), choose the MOST PROMINENT one

VALID ATTRIBUTE VALUES (MUST USE THESE):

**Categories:** {', '.join(attributes.get('categories', []))}
**Colors:** {', '.join(attributes.get('colors', []))}
**Conditions:** {', '.join(attributes.get('conditions', []))}
**Materials:** {', '.join(attributes.get('materials', []))}
**Fits:** {', '.join(attributes.get('fits', []))}
**Genders:** {', '.join(attributes.get('genders', []))}
**Seasons:** {', '.join(attributes.get('seasons', []))}
**Patterns:** {', '.join(attributes.get('patterns', []))}
**Lengths:** {', '.join(attributes.get('lengths', []))}
**Necklines:** {', '.join(attributes.get('necklines', []))}
**Sports:** {', '.join(attributes.get('sports', []))}
**Closures:** {', '.join(attributes.get('closures', []))}
**Rises:** {', '.join(attributes.get('rises', []))}
**Sleeve Lengths:** {', '.join(attributes.get('sleeve_lengths', []))}
**Stretches:** {', '.join(attributes.get('stretches', []))}
**Linings:** {', '.join(attributes.get('linings', []))}
**Decades:** {', '.join(attributes.get('decades', []))}
**Origins:** {', '.join(attributes.get('origins', []))}
**Trends:** {', '.join(attributes.get('trends', []))}
**Condition Details:** {', '.join(attributes.get('condition_sups', []))}
**Unique Features:** {', '.join(attributes.get('unique_features', []))}

ATTRIBUTES TO EXTRACT:
- category: Product category (use exact name from list above)
- brand: Visible brand name (logo, label, tag) - return exact brand name as seen
- condition: Product condition (0-10 scale)
- label_size: Size label text (exact as shown on tag)
- color: Colors visible (use exact names from list, comma-separated if multiple)
- material: Materials visible or estimated (use exact names from list, comma-separated if multiple)
- fit: Fit type (use exact name from list above)
- gender: Gender (use exact name from list above)
- season: Appropriate season (use exact name from list above)
- sport: Associated sport if applicable (use exact name from list above)
- neckline: Neckline type (use exact name from list above)
- length: Length (use exact name from list above)
- pattern: Pattern type (use exact name from list above)
- condition_sup: Condition details (use exact names from Condition Details list, comma-separated if multiple)
- rise: Waist height for pants (use exact name from list above)
- closure: Closure type (use exact name from list above)
- sleeve_length: Sleeve length (use exact name from list above)
- stretch: Stretch/elasticity level (use exact name from list above)
- lining: Lining type (use exact name from list above)
- origin: Origin/country of manufacture (use exact name from list above)
- decade: Decade/era if vintage (use exact name from list above)
- trend: Fashion trend (use exact name from list above)
- model: Model reference if visible
- unique_feature: Unique characteristics (use exact names from Unique Features list, comma-separated if multiple)
- marking: Visible texts/markings (dates, codes, inscriptions...)

Analyze ALL provided images for complete extraction."""

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

        # 5. Fetch product attributes from database
        attributes = AIVisionService._fetch_product_attributes(db)

        # 6. Construire le prompt
        prompt = AIVisionService._build_prompt(attributes)

        # 7. Appeler Gemini Vision API
        try:
            # Configure Gemini client with timeout
            client = genai.Client(
                api_key=settings.gemini_api_key,
                http_options=httpx.Timeout(timeout=settings.gemini_timeout_seconds),
            )

            # Construire le contenu multimodal
            contents = [prompt] + image_parts

            # Appeler avec structured output (using GeminiVisionSchema without defaults)
            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=GeminiVisionSchema,
                    temperature=0.0,  # Deterministic for accurate analysis
                    mediaResolution=types.MediaResolution.MEDIA_RESOLUTION_HIGH,  # Better detail recognition (1120 tokens/image)
                ),
            )

            # Parser la réponse
            import json

            response_data = json.loads(response.text)

            # Clean AI response: extract first value if multiple were returned
            response_data = AIVisionService._clean_ai_response(response_data)

            # Post-process brand: match existing or create new
            response_data = AIVisionService._process_brand(db, response_data)

            # Convert to VisionExtractedAttributes (with defaults for missing fields)
            extracted_attributes = VisionExtractedAttributes(**response_data)

            # 8. Calculer les métriques
            input_tokens = response.usage_metadata.prompt_token_count
            output_tokens = response.usage_metadata.candidates_token_count
            total_tokens = input_tokens + output_tokens

            # 9. Calculer le coût
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

            # 10. Logger la génération (sans product_id)
            log = AIGenerationLog(
                product_id=None,  # Pas de produit associé
                model=settings.gemini_model,
                prompt_tokens=input_tokens,
                completion_tokens=output_tokens,
                total_tokens=total_tokens,
                total_cost=cost,
                cached=False,
                generation_time_ms=generation_time_ms,
                response_data=response_data,  # Store raw AI response
            )
            db.add(log)

            # 11. Incrémenter les crédits utilisés
            AIVisionService._consume_credit(db, user_id)

            db.commit()

            logger.info(
                f"[AIVisionService] Analyzed images direct: user_id={user_id}, "
                f"images={images_analyzed}, tokens={total_tokens}, "
                f"cost=${cost:.6f}, time={generation_time_ms}ms, "
                f"confidence={extracted_attributes.confidence:.2f}"
            )

            return extracted_attributes, total_tokens, cost, images_analyzed

        except genai.errors.ClientError as e:
            logger.error(f"[AIVisionService] Gemini client error: {e}")
            raise AIGenerationError("Clé API Gemini invalide ou erreur client")
        except genai.errors.ServerError as e:
            logger.error(f"[AIVisionService] Gemini server error: {e}")
            raise AIGenerationError(
                "Erreur serveur Gemini. Réessayez dans quelques minutes."
            )
        except genai.errors.APIError as e:
            logger.error(f"[AIVisionService] Gemini API error: {e}")
            raise AIGenerationError(f"Erreur API Gemini: {str(e)}")
        except Exception as e:
            logger.error(f"[AIVisionService] Unexpected error: {e}", exc_info=True)
            raise AIGenerationError(f"Erreur inattendue: {str(e)}")
