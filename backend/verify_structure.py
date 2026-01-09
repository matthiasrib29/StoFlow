"""
Verification Script: Structure & Registry Check (No Dependencies)

Vérifie la structure des fichiers et registres sans importer les modules.

Author: Claude
Date: 2026-01-09
"""

import os
import re


def check_file_exists(path):
    """Check if file exists."""
    return os.path.isfile(path)


def check_handler_registry(file_path, expected_format):
    """Check handler registry format in a file."""
    if not os.path.isfile(file_path):
        return False, f"File not found: {file_path}"

    with open(file_path, 'r') as f:
        content = f.read()

    # Extract HANDLERS dict
    match = re.search(r'(HANDLERS|EBAY_HANDLERS|ETSY_HANDLERS)\s*=\s*\{([^}]+)\}', content, re.DOTALL)

    if not match:
        return False, "HANDLERS dict not found"

    handlers_content = match.group(2)

    # Check if keys match expected format
    keys = re.findall(r'"([^"]+)":', handlers_content)

    if not keys:
        return False, "No handler keys found"

    mismatches = []
    for key in keys:
        if not key.endswith(expected_format):
            mismatches.append(key)

    if mismatches:
        return False, f"Keys don't match format '{expected_format}': {mismatches}"

    return True, keys


def main():
    print("=" * 60)
    print("Structure & Registry Verification (No Imports)")
    print("=" * 60)

    base_dir = "/home/maribeiro/StoFlow-fix-endpoint/backend"

    tests_passed = 0
    tests_total = 0

    # Test 1: Check migrations exist
    print("\n=== Test 1: Migrations ===")
    tests_total += 1

    migrations = [
        "migrations/versions/20260109_0200_unify_action_types.py",
        "migrations/versions/20260109_0300_create_ebay_action_types.py",
        "migrations/versions/20260109_0400_create_etsy_action_types.py",
    ]

    all_exist = True
    for migration in migrations:
        full_path = os.path.join(base_dir, migration)
        if check_file_exists(full_path):
            print(f"✓ {migration}")
        else:
            print(f"✗ {migration} NOT FOUND")
            all_exist = False

    if all_exist:
        tests_passed += 1
        print("✓ All migrations exist")
    else:
        print("✗ Some migrations missing")

    # Test 2: Check Vinted handlers format
    print("\n=== Test 2: Vinted HANDLERS Format ===")
    tests_total += 1

    vinted_init = os.path.join(base_dir, "services/vinted/jobs/__init__.py")
    success, result = check_handler_registry(vinted_init, "_vinted")

    if success:
        print(f"✓ Vinted HANDLERS format correct")
        print(f"  Keys found: {result}")
        tests_passed += 1
    else:
        print(f"✗ Vinted HANDLERS format incorrect: {result}")

    # Test 3: Check eBay handlers format
    print("\n=== Test 3: eBay HANDLERS Format ===")
    tests_total += 1

    ebay_init = os.path.join(base_dir, "services/ebay/jobs/__init__.py")
    success, result = check_handler_registry(ebay_init, "_ebay")

    if success:
        print(f"✓ eBay HANDLERS format correct")
        print(f"  Keys found: {result}")
        tests_passed += 1
    else:
        print(f"✗ eBay HANDLERS format incorrect: {result}")

    # Test 4: Check Etsy handlers format
    print("\n=== Test 4: Etsy HANDLERS Format ===")
    tests_total += 1

    etsy_init = os.path.join(base_dir, "services/etsy/jobs/__init__.py")
    success, result = check_handler_registry(etsy_init, "_etsy")

    if success:
        print(f"✓ Etsy HANDLERS format correct")
        print(f"  Keys found: {result}")
        tests_passed += 1
    else:
        print(f"✗ Etsy HANDLERS format incorrect: {result}")

    # Test 5: Check handler files exist
    print("\n=== Test 5: Handler Files Exist ===")
    tests_total += 1

    handler_files = [
        # eBay
        "services/ebay/jobs/ebay_publish_job_handler.py",
        "services/ebay/jobs/ebay_update_job_handler.py",
        "services/ebay/jobs/ebay_delete_job_handler.py",
        "services/ebay/jobs/ebay_sync_job_handler.py",
        # Etsy
        "services/etsy/jobs/etsy_publish_job_handler.py",
        "services/etsy/jobs/etsy_update_job_handler.py",
        "services/etsy/jobs/etsy_delete_job_handler.py",
        "services/etsy/jobs/etsy_sync_job_handler.py",
        "services/etsy/jobs/etsy_orders_sync_job_handler.py",
        # Marketplace
        "services/marketplace/marketplace_job_processor.py",
        "services/marketplace/marketplace_job_service.py",
        "services/marketplace_http_helper.py",
    ]

    all_exist = True
    for handler_file in handler_files:
        full_path = os.path.join(base_dir, handler_file)
        if check_file_exists(full_path):
            print(f"✓ {handler_file}")
        else:
            print(f"✗ {handler_file} NOT FOUND")
            all_exist = False

    if all_exist:
        tests_passed += 1
        print(f"✓ All {len(handler_files)} handler files exist")
    else:
        print("✗ Some handler files missing")

    # Test 6: Check documentation
    print("\n=== Test 6: Documentation ===")
    tests_total += 1

    docs = [
        "MIGRATION_JOB_UNIFICATION.md",
        "CLAUDE.md",
    ]

    all_exist = True
    for doc in docs:
        full_path = os.path.join(base_dir, doc)
        if check_file_exists(full_path):
            print(f"✓ {doc}")
        else:
            print(f"✗ {doc} NOT FOUND")
            all_exist = False

    if all_exist:
        tests_passed += 1
        print("✓ All documentation exists")
    else:
        print("✗ Some documentation missing")

    # Test 7: Check full_action_code construction logic
    print("\n=== Test 7: Action Code Construction Logic ===")
    tests_total += 1

    marketplace = "vinted"
    action_code = "sync"
    full_action_code = f"{action_code}_{marketplace}"

    print(f"✓ Logic: '{action_code}' + '_' + '{marketplace}' = '{full_action_code}'")

    # Check if this matches Vinted HANDLERS
    with open(os.path.join(base_dir, "services/vinted/jobs/__init__.py"), 'r') as f:
        content = f.read()

    if f'"{full_action_code}"' in content:
        print(f"✓ Handler key '{full_action_code}' found in Vinted HANDLERS")
        tests_passed += 1
    else:
        print(f"✗ Handler key '{full_action_code}' NOT FOUND in Vinted HANDLERS")

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Tests passed: {tests_passed}/{tests_total}")

    if tests_passed == tests_total:
        print("\n🎉 All structure checks passed!")
        print("\nLe système est prêt. Pour tester avec la DB:")
        print("  1. cd backend")
        print("  2. source .venv/bin/activate")
        print("  3. alembic upgrade head")
        print("  4. python test_vinted_sync_flow.py")
        return 0
    else:
        print(f"\n⚠️  {tests_total - tests_passed} check(s) failed.")
        return 1


if __name__ == "__main__":
    import sys
    exit_code = main()
    sys.exit(exit_code)
