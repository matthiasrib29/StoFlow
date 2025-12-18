#!/usr/bin/env python3
"""
Test script pour l'intégration eBay.

Vérifie que tous les composants eBay sont fonctionnels.

Usage:
    python scripts/test_ebay_integration.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_imports():
    """Test que tous les imports eBay fonctionnent."""
    print("🧪 Test 1: Imports eBay...")

    try:
        from api.ebay import router as ebay_router
        from api.ebay_oauth import router as ebay_oauth_router
        from services.ebay import (
            EbayBaseClient,
            EbayInventoryClient,
            EbayOfferClient,
            EbayAccountClient,
            EbayProductConversionService,
            EbayPublicationService,
            ProductValidationError,
            EbayPublicationError
        )
        from models.public.ebay_marketplace_config import MarketplaceConfig
        from models.public.ebay_aspect_mapping import AspectMapping
        from models.user.ebay_product_marketplace import EbayProductMarketplace

        print("   ✅ Tous les imports OK")
        return True
    except Exception as e:
        print(f"   ❌ Erreur import: {e}")
        return False


def test_database_tables():
    """Test que les tables eBay existent."""
    print("\n🧪 Test 2: Tables base de données...")

    try:
        from shared.database import engine
        from sqlalchemy import inspect, text

        inspector = inspect(engine)

        # Tables PUBLIC
        public_tables = inspector.get_table_names(schema='public')
        required_public = ['marketplace_config', 'aspect_mappings', 'exchange_rate_config']

        for table in required_public:
            if table in public_tables:
                print(f"   ✅ public.{table} existe")
            else:
                print(f"   ❌ public.{table} manquante")
                return False

        # Vérifier template_tenant
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT COUNT(*) FROM public.marketplace_config")
            )
            count = result.scalar()
            print(f"   ✅ {count} marketplaces configurées")

            if count != 8:
                print(f"   ⚠️  Attendu 8 marketplaces, trouvé {count}")

        return True

    except Exception as e:
        print(f"   ❌ Erreur DB: {e}")
        return False


def test_models():
    """Test que les models SQLAlchemy fonctionnent."""
    print("\n🧪 Test 3: Models SQLAlchemy...")

    try:
        from models.public.ebay_marketplace_config import MarketplaceConfig
        from models.public.ebay_aspect_mapping import AspectMapping
        from models.user.ebay_product_marketplace import EbayProductMarketplace
        from shared.database import SessionLocal

        db = SessionLocal()

        # Test query marketplaces
        marketplaces = db.query(MarketplaceConfig).limit(3).all()
        print(f"   ✅ Récupéré {len(marketplaces)} marketplaces")

        for m in marketplaces[:2]:
            print(f"      - {m.marketplace_id} ({m.currency})")

        # Test query aspect mappings
        aspects = db.query(AspectMapping).limit(3).all()
        print(f"   ✅ Récupéré {len(aspects)} aspect mappings")

        db.close()
        return True

    except Exception as e:
        print(f"   ❌ Erreur models: {e}")
        return False


def test_api_routes():
    """Test que les routes API sont enregistrées."""
    print("\n🧪 Test 4: Routes API...")

    try:
        from main import app

        # Get all routes
        routes = []
        for route in app.routes:
            if hasattr(route, 'path'):
                routes.append(route.path)

        # Routes eBay attendues
        expected_routes = [
            '/api/ebay/publish',
            '/api/ebay/unpublish',
            '/api/ebay/marketplaces',
            '/api/ebay/products/{product_id}/status',
            '/api/ebay/policies',
            '/api/integrations/ebay/connect',
            '/api/integrations/ebay/callback',
            '/api/integrations/ebay/disconnect',
            '/api/integrations/ebay/status',
        ]

        for expected in expected_routes:
            if expected in routes:
                print(f"   ✅ {expected}")
            else:
                print(f"   ❌ {expected} manquante")
                return False

        return True

    except Exception as e:
        print(f"   ❌ Erreur routes: {e}")
        return False


def main():
    """Lance tous les tests."""
    print("=" * 60)
    print("🧪 Tests intégration eBay MVP")
    print("=" * 60)

    results = []

    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Database", test_database_tables()))
    results.append(("Models", test_models()))
    results.append(("API Routes", test_api_routes()))

    # Summary
    print("\n" + "=" * 60)
    print("📊 Résumé")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name:20} {status}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n🎉 Tous les tests passent ! L'intégration eBay est fonctionnelle.")
        return 0
    else:
        print("\n❌ Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
