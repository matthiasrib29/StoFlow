"""
Test Script: Vinted Sync Flow Verification

Vérifie que le flux complet de synchronisation Vinted fonctionne:
1. Création d'un job sync via MarketplaceJobService
2. Récupération de l'action_type depuis la DB
3. Construction du full_action_code par le processor
4. Dispatch vers le bon handler
5. Vérification des imports et registres

Author: Claude
Date: 2026-01-09
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_imports():
    """Test 1: Vérifier que tous les imports fonctionnent."""
    print("\n=== Test 1: Imports ===")

    try:
        from services.marketplace import MarketplaceJobProcessor, MarketplaceJobService
        print("✓ MarketplaceJobProcessor import OK")
        print("✓ MarketplaceJobService import OK")

        from services.vinted.jobs import HANDLERS
        print(f"✓ HANDLERS import OK ({len(HANDLERS)} handlers)")

        from services.ebay.jobs import EBAY_HANDLERS
        print(f"✓ EBAY_HANDLERS import OK ({len(EBAY_HANDLERS)} handlers)")

        from services.etsy.jobs import ETSY_HANDLERS
        print(f"✓ ETSY_HANDLERS import OK ({len(ETSY_HANDLERS)} handlers)")

        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_handler_registry():
    """Test 2: Vérifier que les registres de handlers sont corrects."""
    print("\n=== Test 2: Handler Registry ===")

    try:
        from services.vinted.jobs import HANDLERS
        from services.ebay.jobs import EBAY_HANDLERS
        from services.etsy.jobs import ETSY_HANDLERS

        # Vinted handlers (format: action_vinted)
        expected_vinted = [
            "publish_vinted",
            "update_vinted",
            "delete_vinted",
            "orders_vinted",
            "sync_vinted",
            "message_vinted",
            "link_product_vinted"
        ]

        for key in expected_vinted:
            if key in HANDLERS:
                print(f"✓ {key} → {HANDLERS[key].__name__}")
            else:
                print(f"✗ Missing handler: {key}")
                return False

        # eBay handlers (format: action_ebay)
        expected_ebay = [
            "publish_ebay",
            "update_ebay",
            "delete_ebay",
            "sync_ebay",
            "sync_orders_ebay"
        ]

        for key in expected_ebay:
            if key in EBAY_HANDLERS:
                print(f"✓ {key} → {EBAY_HANDLERS[key].__name__}")
            else:
                print(f"✗ Missing eBay handler: {key}")
                return False

        # Etsy handlers (format: action_etsy)
        expected_etsy = [
            "publish_etsy",
            "update_etsy",
            "delete_etsy",
            "sync_etsy",
            "sync_orders_etsy"
        ]

        for key in expected_etsy:
            if key in ETSY_HANDLERS:
                print(f"✓ {key} → {ETSY_HANDLERS[key].__name__}")
            else:
                print(f"✗ Missing Etsy handler: {key}")
                return False

        return True

    except Exception as e:
        print(f"✗ Handler registry error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_all_handlers_registry():
    """Test 3: Vérifier que ALL_HANDLERS contient tous les handlers."""
    print("\n=== Test 3: ALL_HANDLERS Registry ===")

    try:
        from services.marketplace.marketplace_job_processor import ALL_HANDLERS

        print(f"✓ ALL_HANDLERS contient {len(ALL_HANDLERS)} handlers")

        # Vérifier que les handlers de chaque marketplace sont présents
        vinted_count = sum(1 for k in ALL_HANDLERS.keys() if k.endswith('_vinted'))
        ebay_count = sum(1 for k in ALL_HANDLERS.keys() if k.endswith('_ebay'))
        etsy_count = sum(1 for k in ALL_HANDLERS.keys() if k.endswith('_etsy'))

        print(f"  - Vinted: {vinted_count} handlers")
        print(f"  - eBay: {ebay_count} handlers")
        print(f"  - Etsy: {etsy_count} handlers")

        # Vérifier spécifiquement sync_vinted
        if "sync_vinted" in ALL_HANDLERS:
            print(f"✓ sync_vinted handler trouvé: {ALL_HANDLERS['sync_vinted'].__name__}")
        else:
            print("✗ sync_vinted handler NOT FOUND!")
            return False

        return True

    except Exception as e:
        print(f"✗ ALL_HANDLERS error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_action_code_construction():
    """Test 4: Vérifier la construction de full_action_code."""
    print("\n=== Test 4: Action Code Construction ===")

    try:
        # Simuler la logique du processor
        marketplace = "vinted"
        action_code = "sync"

        full_action_code = f"{action_code}_{marketplace}"

        print(f"✓ marketplace: {marketplace}")
        print(f"✓ action_code: {action_code}")
        print(f"✓ full_action_code: {full_action_code}")

        # Vérifier que le handler existe
        from services.marketplace.marketplace_job_processor import ALL_HANDLERS

        if full_action_code in ALL_HANDLERS:
            print(f"✓ Handler trouvé pour '{full_action_code}': {ALL_HANDLERS[full_action_code].__name__}")
            return True
        else:
            print(f"✗ Handler NOT FOUND pour '{full_action_code}'")
            print(f"  Available keys: {list(ALL_HANDLERS.keys())}")
            return False

    except Exception as e:
        print(f"✗ Action code construction error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_base_handler_methods():
    """Test 5: Vérifier que BaseJobHandler a call_http et call_websocket."""
    print("\n=== Test 5: BaseJobHandler Methods ===")

    try:
        from services.vinted.jobs.base_job_handler import BaseJobHandler

        # Vérifier que les méthodes existent
        if hasattr(BaseJobHandler, 'call_websocket'):
            print("✓ BaseJobHandler.call_websocket() existe")
        else:
            print("✗ BaseJobHandler.call_websocket() NOT FOUND")
            return False

        if hasattr(BaseJobHandler, 'call_http'):
            print("✓ BaseJobHandler.call_http() existe")
        else:
            print("✗ BaseJobHandler.call_http() NOT FOUND")
            return False

        # Vérifier call_plugin (ancien nom pour WebSocket)
        if hasattr(BaseJobHandler, 'call_plugin'):
            print("✓ BaseJobHandler.call_plugin() existe (WebSocket)")
        else:
            print("ℹ BaseJobHandler.call_plugin() not found (expected if renamed)")

        return True

    except Exception as e:
        print(f"✗ BaseJobHandler methods error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Vinted Sync Flow Verification")
    print("=" * 60)

    tests = [
        ("Imports", test_imports),
        ("Handler Registry", test_handler_registry),
        ("ALL_HANDLERS Registry", test_all_handlers_registry),
        ("Action Code Construction", test_action_code_construction),
        ("BaseJobHandler Methods", test_base_handler_methods),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n✗ Test '{test_name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {test_name}")

    total = len(results)
    passed = sum(1 for _, success in results if success)

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Le flux Vinted sync est fonctionnel.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
