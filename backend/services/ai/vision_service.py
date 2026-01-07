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
from schemas.ai_schemas import VisionExtractedAttributes
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
    ) -> tuple[VisionExtractedAttributes, int, Decimal, int]:
        """
        Analyse les images d'un produit et extrait les attributs.

        Args:
            db: Session SQLAlchemy
            product: Produit avec images à analyser
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
        if not product.images:
            raise AIGenerationError("Le produit n'a pas d'images à analyser.")

        # 2. Vérifier les crédits
        AIVisionService._check_credits(db, user_id, monthly_credits)

        # 3. Récupérer les images (max selon config)
        images_to_analyze = product.images[: settings.gemini_max_images]
        images_analyzed = len(images_to_analyze)

        logger.info(
            f"[AIVisionService] Analyzing {images_analyzed} images "
            f"for product_id={product.id}"
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
            client = genai.Client(api_key=settings.gemini_api_key)

            # Construire le contenu multimodal
            contents = [prompt] + image_parts

            # Appeler avec structured output
            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=VisionExtractedAttributes,
                ),
            )

            # Parser la réponse
            import json

            response_data = json.loads(response.text)
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
                product_id=product.id,
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
                f"[AIVisionService] Analyzed images: product_id={product.id}, "
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

        attributes = {}

        # Fetch each attribute type
        # Note: Brand uses 'name' as PK, others use 'name_en'
        attributes["brands"] = [b.name for b in db.query(Brand.name).order_by(Brand.name).limit(500).all()]
        attributes["categories"] = [c.name_en for c in db.query(Category.name_en).order_by(Category.name_en).limit(100).all()]
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
- unique_feature and marking: Separate multiple values with commas

VALID ATTRIBUTE VALUES (MUST USE THESE):

**Categories:** {', '.join(attributes.get('categories', [])[:50])}
**Brands:** {', '.join(attributes.get('brands', [])[:100])}
**Colors:** {', '.join(attributes.get('colors', [])[:50])}
**Conditions:** {', '.join(attributes.get('conditions', []))}
**Materials:** {', '.join(attributes.get('materials', [])[:50])}
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

ATTRIBUTES TO EXTRACT:
- price: Suggested price in EUR based on brand, condition, and type
- category: Product category (use exact name from list above)
- brand: Visible brand (logo, label) - use exact name from list above
- condition: Product condition (0-10 scale)
- size: Size visible on label (exact text)
- label_size: Size label text (exact as shown)
- color: Main color (use exact name from list above)
- material: Visible or estimated material (use exact name from list above)
- fit: Fit type (use exact name from list above)
- gender: Gender (use exact name from list above)
- season: Appropriate season (use exact name from list above)
- sport: Associated sport if applicable (use exact name from list above)
- neckline: Neckline type (use exact name from list above)
- length: Length (use exact name from list above)
- pattern: Pattern type (use exact name from list above)
- condition_sup: Condition details (visible defects, wear, etc.)
- rise: Waist height for pants (use exact name from list above)
- closure: Closure type (use exact name from list above)
- sleeve_length: Sleeve length (use exact name from list above)
- origin: Origin if visible
- decade: Decade/era if vintage
- trend: Associated trend
- model: Model reference if visible
- unique_feature: Unique characteristics (embroidered logo, vintage, limited edition...)
- marking: Visible texts/markings (dates, codes, inscriptions...)

Analyze ALL provided images for complete extraction."""

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

        Args:
            db: Session SQLAlchemy
            image_files: Liste de tuples (contenu_bytes, mime_type)
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

        # 3. Limiter le nombre d'images selon config
        images_to_analyze = image_files[: settings.gemini_max_images]
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
            client = genai.Client(api_key=settings.gemini_api_key)

            # Construire le contenu multimodal
            contents = [prompt] + image_parts

            # Appeler avec structured output
            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=VisionExtractedAttributes,
                ),
            )

            # Parser la réponse
            import json

            response_data = json.loads(response.text)
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
