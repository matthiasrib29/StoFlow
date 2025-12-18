"""
Stripe Configuration

Configuration centralisée pour Stripe:
- Clés API (Secret et Publishable)
- Webhook secret
- Configuration des produits (crédits IA)

Business Rules (2025-12-10):
- Les prix des abonnements viennent de la DB (subscription_quotas)
- Les prix des crédits IA sont définis ici
- Mode Test par défaut, Production via env var

Author: Claude
Date: 2025-12-10
"""

import os
import stripe
from decimal import Decimal

# Configuration Stripe API
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

# Initialiser Stripe
stripe.api_key = STRIPE_SECRET_KEY

# URLs de redirection (frontend)
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000")
STRIPE_SUCCESS_URL = f"{FRONTEND_BASE_URL}/dashboard/subscription/success?session_id={{CHECKOUT_SESSION_ID}}"
STRIPE_CANCEL_URL = f"{FRONTEND_BASE_URL}/dashboard/subscription/cancel"

# Configuration des packs de crédits IA
# Format: {nombre_credits: {"price": Decimal, "name": str, "description": str}}
AI_CREDIT_PACKS = {
    500: {
        "price": Decimal("9.00"),
        "name": "Pack 500 crédits IA",
        "description": "500 crédits pour générer des descriptions de produits",
    },
    1000: {
        "price": Decimal("15.00"),
        "name": "Pack 1000 crédits IA",
        "description": "1000 crédits pour générer des descriptions de produits",
    },
    2000: {
        "price": Decimal("25.00"),
        "name": "Pack 2000 crédits IA",
        "description": "2000 crédits pour générer des descriptions de produits",
    },
}

# Grace period pour échecs de paiement (en jours)
PAYMENT_GRACE_PERIOD_DAYS = 3


def get_stripe_price_for_credits(credits: int) -> Decimal:
    """
    Retourne le prix pour un pack de crédits donné.

    Args:
        credits: Nombre de crédits

    Returns:
        Decimal: Prix en EUR

    Raises:
        ValueError: Si le pack n'existe pas
    """
    if credits not in AI_CREDIT_PACKS:
        raise ValueError(f"Pack de {credits} crédits non disponible")

    return AI_CREDIT_PACKS[credits]["price"]


def validate_stripe_config():
    """
    Valide que la configuration Stripe est correcte.

    Raises:
        ValueError: Si la configuration est incomplète
    """
    if not STRIPE_SECRET_KEY:
        raise ValueError("STRIPE_SECRET_KEY n'est pas configurée dans les variables d'environnement")

    if not STRIPE_PUBLISHABLE_KEY:
        raise ValueError("STRIPE_PUBLISHABLE_KEY n'est pas configurée dans les variables d'environnement")

    if not STRIPE_WEBHOOK_SECRET:
        raise ValueError("STRIPE_WEBHOOK_SECRET n'est pas configurée dans les variables d'environnement")

    # Vérifier que les clés ont le bon format
    if not STRIPE_SECRET_KEY.startswith(("sk_test_", "sk_live_")):
        raise ValueError("STRIPE_SECRET_KEY doit commencer par 'sk_test_' ou 'sk_live_'")

    if not STRIPE_PUBLISHABLE_KEY.startswith(("pk_test_", "pk_live_")):
        raise ValueError("STRIPE_PUBLISHABLE_KEY doit commencer par 'pk_test_' ou 'pk_live_'")

    if not STRIPE_WEBHOOK_SECRET.startswith("whsec_"):
        raise ValueError("STRIPE_WEBHOOK_SECRET doit commencer par 'whsec_'")

    # Vérifier que les clés sont cohérentes (test ou prod)
    is_secret_test = STRIPE_SECRET_KEY.startswith("sk_test_")
    is_publishable_test = STRIPE_PUBLISHABLE_KEY.startswith("pk_test_")

    if is_secret_test != is_publishable_test:
        raise ValueError("Les clés Stripe doivent être toutes en mode Test ou toutes en mode Production")
