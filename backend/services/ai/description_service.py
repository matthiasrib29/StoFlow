"""
AI Description Service

Service pour générer des descriptions de produits via Anthropic Claude API.

Business Rules:
- Vérifie les crédits IA avant génération
- Log chaque génération dans AIGenerationLog
- Décrémente les crédits utilisés
"""

import time
from decimal import Decimal
from typing import TYPE_CHECKING

import anthropic
from sqlalchemy.orm import Session

from models.public.ai_credit import AICredit
from models.user.ai_generation_log import AIGenerationLog
from shared.config import settings
from shared.exceptions import AIGenerationError, AIQuotaExceededError
from shared.logging_setup import get_logger

if TYPE_CHECKING:
    from models.user.product import Product

logger = get_logger(__name__)


class AIDescriptionService:
    """Service pour générer des descriptions produits via Claude."""

    # Pricing Claude (USD par million tokens) - Dec 2024
    MODEL_PRICING = {
        "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
        "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
        "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
    }

    @staticmethod
    def generate_description(
        db: Session,
        product: "Product",
        user_id: int,
        monthly_credits: int = 0,
    ) -> tuple[str, int, Decimal]:
        """
        Génère une description pour un produit.

        Args:
            db: Session SQLAlchemy
            product: Produit pour lequel générer la description
            user_id: ID de l'utilisateur
            monthly_credits: Crédits mensuels de l'abonnement

        Returns:
            tuple: (description, total_tokens, cost)

        Raises:
            AIQuotaExceededError: Si crédits insuffisants
            AIGenerationError: Si erreur API Anthropic
        """
        start_time = time.time()

        # 1. Vérifier les crédits
        AIDescriptionService._check_credits(db, user_id, monthly_credits)

        # 2. Construire le prompt
        prompt = AIDescriptionService._build_prompt(product)

        # 3. Appeler Claude API
        try:
            client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

            response = client.messages.create(
                model=settings.anthropic_model,
                max_tokens=settings.anthropic_max_tokens,
                temperature=settings.anthropic_temperature,
                messages=[{"role": "user", "content": prompt}],
            )

            description = response.content[0].text

            # 4. Calculer les métriques
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            total_tokens = input_tokens + output_tokens

            # 5. Calculer le coût
            pricing = AIDescriptionService.MODEL_PRICING.get(
                settings.anthropic_model, {"input": 3.0, "output": 15.0}
            )
            cost = Decimal(str(
                (input_tokens * pricing["input"] / 1_000_000)
                + (output_tokens * pricing["output"] / 1_000_000)
            ))

            generation_time_ms = int((time.time() - start_time) * 1000)

            # 6. Logger la génération
            log = AIGenerationLog(
                product_id=product.id,
                model=settings.anthropic_model,
                prompt_tokens=input_tokens,
                completion_tokens=output_tokens,
                total_tokens=total_tokens,
                total_cost=cost,
                cached=False,
                generation_time_ms=generation_time_ms,
            )
            db.add(log)

            # 7. Incrémenter les crédits utilisés
            AIDescriptionService._consume_credit(db, user_id)

            db.commit()

            logger.info(
                f"[AIDescriptionService] Generated description: product_id={product.id}, "
                f"tokens={total_tokens}, cost=${cost:.6f}, time={generation_time_ms}ms"
            )

            return description, total_tokens, cost

        except anthropic.AuthenticationError as e:
            logger.error(f"[AIDescriptionService] Anthropic auth error: {e}")
            raise AIGenerationError("Clé API Anthropic invalide ou expirée")
        except anthropic.RateLimitError as e:
            logger.error(f"[AIDescriptionService] Anthropic rate limit: {e}")
            raise AIGenerationError("Limite de requêtes Anthropic atteinte. Réessayez dans quelques minutes.")
        except anthropic.APIError as e:
            logger.error(f"[AIDescriptionService] Anthropic API error: {e}")
            raise AIGenerationError(f"Erreur API Claude: {str(e)}")

    @staticmethod
    def _check_credits(db: Session, user_id: int, monthly_credits: int) -> None:
        """Vérifie que l'utilisateur a des crédits disponibles."""
        ai_credit = (
            db.query(AICredit).filter(AICredit.user_id == user_id).first()
        )

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
        ai_credit = (
            db.query(AICredit).filter(AICredit.user_id == user_id).first()
        )
        if ai_credit:
            ai_credit.ai_credits_used_this_month += 1

    @staticmethod
    def _build_prompt(product: "Product") -> str:
        """Construit le prompt pour Claude."""
        # Collecter les attributs disponibles
        attributes = []

        if product.title:
            attributes.append(f"Titre: {product.title}")
        if product.brand:
            attributes.append(f"Marque: {product.brand}")
        if product.category:
            attributes.append(f"Catégorie: {product.category}")
        if product.condition is not None:
            condition_map = {
                10: "Neuf avec étiquettes",
                9: "Neuf sans étiquettes",
                8: "Excellent état",
                7: "Très bon état",
                6: "Bon état",
                5: "État correct",
                4: "Usure visible",
            }
            condition_text = condition_map.get(
                product.condition, f"Note {product.condition}/10"
            )
            attributes.append(f"État: {condition_text}")
        if product.color:
            attributes.append(f"Couleur: {product.color}")
        if product.material:
            attributes.append(f"Matière: {product.material}")
        if product.label_size:
            attributes.append(f"Taille: {product.label_size}")
        if product.fit:
            attributes.append(f"Coupe: {product.fit}")
        if product.gender:
            attributes.append(f"Genre: {product.gender}")
        if product.season:
            attributes.append(f"Saison: {product.season}")
        if product.unique_feature:
            attributes.append(f"Caractéristiques uniques: {product.unique_feature}")
        if product.marking:
            attributes.append(f"Marquages: {product.marking}")

        # Dimensions
        dimensions = []
        if product.dim1:
            dimensions.append(f"Poitrine/Épaules: {product.dim1}cm")
        if product.dim2:
            dimensions.append(f"Longueur: {product.dim2}cm")
        if product.dim3:
            dimensions.append(f"Manches: {product.dim3}cm")
        if product.dim4:
            dimensions.append(f"Taille: {product.dim4}cm")
        if product.dim5:
            dimensions.append(f"Hanches: {product.dim5}cm")
        if product.dim6:
            dimensions.append(f"Entrejambe: {product.dim6}cm")

        if dimensions:
            attributes.append(f"Dimensions: {', '.join(dimensions)}")

        attributes_text = "\n".join(f"- {attr}" for attr in attributes)

        prompt = f"""Tu es un expert en rédaction de descriptions pour la vente de vêtements et accessoires en ligne.

Rédige une description de produit attrayante et professionnelle en français pour ce produit:

{attributes_text}

Instructions:
- La description doit être entre 100 et 200 mots
- Utilise un ton professionnel mais engageant
- Mets en valeur les points forts du produit
- Mentionne l'état et les dimensions si disponibles
- Évite les clichés excessifs
- Ne répète pas le titre tel quel au début
- Termine par une phrase encourageant l'achat

Retourne UNIQUEMENT la description, sans titre ni formatage markdown."""

        return prompt
