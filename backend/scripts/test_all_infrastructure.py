"""
Run all infrastructure tests.
"""
import sys
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from test_config import test_config
from test_db_connection import test_database


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("🚀 STOFLOW INFRASTRUCTURE TESTS")
    print("="*60)

    results = {
        "Configuration": False,
        "PostgreSQL": False,
    }

    # Test 1: Configuration
    try:
        test_config()
        results["Configuration"] = True
    except Exception as e:
        print(f"\n❌ Configuration test failed: {e}")

    # Test 2: PostgreSQL
    try:
        results["PostgreSQL"] = test_database()
    except Exception as e:
        print(f"\n❌ PostgreSQL test failed: {e}")

    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:.<40} {status}")

    all_passed = all(results.values())

    if all_passed:
        print("\n🎉 ALL TESTS PASSED - Infrastructure ready!")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED - Check errors above")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
