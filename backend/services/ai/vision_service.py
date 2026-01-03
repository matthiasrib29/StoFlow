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

    # Pricing Gemini (USD par million tokens) - Jan 2025
    MODEL_PRICING = {
        "gemini-2.5-flash": {"input": 0.075, "output": 0.30},
        "gemini-2.5-pro": {"input": 1.25, "output": 5.00},
        "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
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
        if not product.product_images:
            raise AIGenerationError("Le produit n'a pas d'images à analyser.")

        # 2. Vérifier les crédits
        AIVisionService._check_credits(db, user_id, monthly_credits)

        # 3. Récupérer les images (max selon config)
        images_to_analyze = product.product_images[: settings.gemini_max_images]
        images_analyzed = len(images_to_analyze)

        logger.info(
            f"[AIVisionService] Analyzing {images_analyzed} images "
            f"for product_id={product.id}"
        )

        # 4. Télécharger les images
        image_parts = await AIVisionService._download_images(images_to_analyze)

        if not image_parts:
            raise AIGenerationError("Impossible de télécharger les images du produit.")

        # 5. Construire le prompt
        prompt = AIVisionService._build_prompt()

        # 6. Appeler Gemini Vision API
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
            attributes = VisionExtractedAttributes(**response_data)

            # 7. Calculer les métriques
            input_tokens = response.usage_metadata.prompt_token_count
            output_tokens = response.usage_metadata.candidates_token_count
            total_tokens = input_tokens + output_tokens

            # 8. Calculer le coût
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

            # 9. Logger la génération
            log = AIGenerationLog(
                product_id=product.id,
                model=settings.gemini_model,
                prompt_tokens=input_tokens,
                completion_tokens=output_tokens,
                total_tokens=total_tokens,
                total_cost=cost,
                cached=False,
                generation_time_ms=generation_time_ms,
            )
            db.add(log)

            # 10. Incrémenter les crédits utilisés
            AIVisionService._consume_credit(db, user_id)

            db.commit()

            logger.info(
                f"[AIVisionService] Analyzed images: product_id={product.id}, "
                f"images={images_analyzed}, tokens={total_tokens}, "
                f"cost=${cost:.6f}, time={generation_time_ms}ms, "
                f"confidence={attributes.confidence:.2f}"
            )

            return attributes, total_tokens, cost, images_analyzed

        except genai.errors.AuthenticationError as e:
            logger.error(f"[AIVisionService] Gemini auth error: {e}")
            raise AIGenerationError("Clé API Gemini invalide ou expirée")
        except genai.errors.ResourceExhausted as e:
            logger.error(f"[AIVisionService] Gemini rate limit: {e}")
            raise AIGenerationError(
                "Limite de requêtes Gemini atteinte. Réessayez dans quelques minutes."
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
        product_images: list,
    ) -> list[types.Part]:
        """
        Télécharge les images depuis les URLs R2 CDN.

        Args:
            product_images: Liste des ProductImage

        Returns:
            Liste de types.Part contenant les images
        """
        image_parts = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            for img in product_images:
                try:
                    response = await client.get(img.image_path)
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
                        f"[AIVisionService] Downloaded image: {img.image_path}"
                    )

                except httpx.HTTPError as e:
                    logger.warning(
                        f"[AIVisionService] Failed to download image "
                        f"{img.image_path}: {e}"
                    )
                    # Continue avec les autres images
                    continue

        return image_parts

    @staticmethod
    def _build_prompt() -> str:
        """Construit le prompt d'analyse pour Gemini Vision."""
        return """Tu es un expert en analyse d'images de produits pour la vente en ligne (vêtements et accessoires).

Analyse les images suivantes d'un produit et extrait TOUS les attributs visibles.

RÈGLES IMPORTANTES:
- Retourne null pour tout attribut NON VISIBLE ou INCERTAIN
- Ne devine PAS - analyse uniquement ce qui est clairement visible
- condition: Note de 0 à 10 (10=neuf avec étiquettes, 8=excellent état, 5=bon état, 2=usé)
- confidence: Ta confiance GLOBALE dans l'analyse (0.0 à 1.0)
- unique_feature et marking: Sépare les valeurs par des virgules

ATTRIBUTS À EXTRAIRE:
- title: Titre suggéré (marque + type + caractéristiques clés)
- description: Description courte et vendeuse (100-150 mots)
- price: Prix suggéré en EUR basé sur la marque, l'état et le type
- category: Catégorie du produit
- brand: Marque visible (logo, étiquette)
- condition: État du produit (0-10)
- size/label_size: Taille visible sur l'étiquette
- color: Couleur principale
- material: Matière visible ou estimée
- fit: Coupe (Regular, Slim, Oversize, etc.)
- gender: Genre (Homme, Femme, Mixte)
- season: Saison appropriée
- sport: Sport associé si applicable
- neckline: Type d'encolure
- length: Longueur (Court, Standard, Long)
- pattern: Motif (Uni, Rayé, À carreaux, etc.)
- condition_sup: Détails sur l'état (défauts visibles, etc.)
- rise: Hauteur de taille pour pantalons
- closure: Type de fermeture
- sleeve_length: Longueur des manches
- origin: Origine si visible
- decade: Décennie/époque si vintage
- trend: Tendance associée
- model: Référence modèle si visible
- unique_feature: Caractéristiques uniques (logo brodé, vintage, édition limitée...)
- marking: Textes/marquages visibles (dates, codes, inscriptions...)

Analyse TOUTES les images fournies pour une extraction complète."""
