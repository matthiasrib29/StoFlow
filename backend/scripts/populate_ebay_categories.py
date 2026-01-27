"""
Populate eBay categories from the Taxonomy API.

Fetches the category subtree for "Clothing, Shoes & Accessories" (ID 11450)
from the EBAY_GB marketplace, filters to keep only clothing subcategories
(excludes shoes, accessories, etc.), and upserts them into ebay.categories.

Usage:
    python scripts/populate_ebay_categories.py --user-id=1

Author: Claude
Date: 2026-01-23
"""

import argparse
import os
import sys
from typing import Any, Dict, List

from dotenv import load_dotenv

load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from shared.database import engine, get_tenant_session
from services.ebay.ebay_taxonomy_client import EbayTaxonomyClient


# Root category: Clothing, Shoes & Accessories
ROOT_CATEGORY_ID = "11450"

# Target clothing category IDs to recurse into (EBAY_GB tree 3)
# These are the L2 subcategories that contain clothing items only
# (excludes shoes, accessories, bags, etc.)
CLOTHING_TARGET_IDS = {
    "15724",   # Women's Clothing
    "1059",    # Men's Clothing
    "260013",  # Boys (under Kids)
    "260015",  # Girls (under Kids)
    "260017",  # Unisex Kids (under Kids)
    "260019",  # Baby & Toddler Clothing
}


def extract_categories(
    node: Dict[str, Any],
    parent_id: str | None = None,
    path_prefix: str = "",
    results: List[Dict] | None = None,
) -> List[Dict]:
    """
    Recursively extract categories from an eBay category tree node.

    Args:
        node: Category tree node from eBay API.
        parent_id: Parent category ID (None for root).
        path_prefix: Path prefix for building breadcrumb.
        results: Accumulator list.

    Returns:
        List of category dicts ready for insertion.
    """
    if results is None:
        results = []

    category = node.get("category", {})
    cat_id = category.get("categoryId", "")
    cat_name = category.get("categoryName", "")
    level = node.get("categoryTreeNodeLevel", 0)
    children = node.get("childCategoryTreeNodes", [])

    # Build path
    path = f"{path_prefix} > {cat_name}" if path_prefix else cat_name

    # A category is a leaf if it has no children
    is_leaf = len(children) == 0

    results.append({
        "category_id": cat_id,
        "category_name": cat_name,
        "parent_id": parent_id,
        "level": level,
        "is_leaf": is_leaf,
        "path": path,
    })

    # Process children recursively
    for child in children:
        extract_categories(child, parent_id=cat_id, path_prefix=path, results=results)

    return results


def topological_sort(categories: List[Dict]) -> List[Dict]:
    """
    Sort categories so parents always come before children.

    Args:
        categories: List of category dicts.

    Returns:
        Topologically sorted list.
    """
    by_id = {cat["category_id"]: cat for cat in categories}
    result = []
    visited = set()

    def visit(cat_id: str):
        if cat_id in visited:
            return
        cat = by_id.get(cat_id)
        if not cat:
            return
        # Visit parent first
        if cat["parent_id"] and cat["parent_id"] in by_id:
            visit(cat["parent_id"])
        visited.add(cat_id)
        result.append(cat)

    for cat in categories:
        visit(cat["category_id"])

    return result


def upsert_categories(categories: List[Dict]) -> int:
    """
    Upsert categories into ebay.categories table.

    Uses ON CONFLICT DO UPDATE for idempotency.

    Args:
        categories: List of category dicts.

    Returns:
        Number of categories upserted.
    """
    sorted_cats = topological_sort(categories)
    count = 0

    with engine.connect() as conn:
        for cat in sorted_cats:
            try:
                conn.execute(
                    text("""
                        INSERT INTO ebay.categories
                        (category_id, category_name, parent_id, level, is_leaf, path, created_at, updated_at)
                        VALUES (:category_id, :category_name, :parent_id, :level, :is_leaf, :path, NOW(), NOW())
                        ON CONFLICT (category_id) DO UPDATE SET
                            category_name = EXCLUDED.category_name,
                            parent_id = EXCLUDED.parent_id,
                            level = EXCLUDED.level,
                            is_leaf = EXCLUDED.is_leaf,
                            path = EXCLUDED.path,
                            updated_at = NOW()
                    """),
                    {
                        "category_id": cat["category_id"],
                        "category_name": cat["category_name"],
                        "parent_id": cat["parent_id"],
                        "level": cat["level"],
                        "is_leaf": cat["is_leaf"],
                        "path": cat["path"],
                    },
                )
                conn.commit()
                count += 1
            except Exception as e:
                conn.rollback()
                print(f"  Error upserting category {cat['category_id']}: {e}")

    return count


def main():
    parser = argparse.ArgumentParser(description="Populate eBay categories from Taxonomy API")
    parser.add_argument("--user-id", type=int, required=True, help="User ID with eBay credentials")
    args = parser.parse_args()

    print("=" * 60)
    print("POPULATE EBAY CATEGORIES (Clothing)")
    print("=" * 60)

    # Fetch category subtree from eBay API
    print(f"\nFetching category subtree for root ID {ROOT_CATEGORY_ID} (EBAY_GB)...")

    db = get_tenant_session(args.user_id)
    try:
        client = EbayTaxonomyClient(db, user_id=args.user_id, marketplace_id="EBAY_GB")
        tree = client.get_category_tree(category_id=ROOT_CATEGORY_ID)
    finally:
        db.close()

    if not tree:
        print("ERROR: Failed to fetch category tree from eBay API.")
        sys.exit(1)

    # The response has a categorySubtreeNode at the root
    root_node = tree.get("categorySubtreeNode", {})
    if not root_node:
        print("ERROR: No categorySubtreeNode in API response.")
        sys.exit(1)

    root_category = root_node.get("category", {})
    print(f"  Root: {root_category.get('categoryName')} (ID: {root_category.get('categoryId')})")

    # Find target clothing categories at L2 level
    # Structure: 11450 > Women/Men/Kids/Baby > Women's Clothing / Men's Clothing / etc.
    l1_children = root_node.get("childCategoryTreeNodes", [])
    print(f"  Level-1 children: {len(l1_children)}")

    clothing_nodes = []
    for l1 in l1_children:
        l1_name = l1.get("category", {}).get("categoryName", "")
        l2_children = l1.get("childCategoryTreeNodes", [])
        for l2 in l2_children:
            l2_cat = l2.get("category", {})
            l2_id = l2_cat.get("categoryId", "")
            l2_name = l2_cat.get("categoryName", "")
            if l2_id in CLOTHING_TARGET_IDS:
                clothing_nodes.append((l1, l2))
                print(f"    KEEP: {l1_name} > {l2_name} (ID: {l2_id})")

    if not clothing_nodes:
        print("ERROR: No clothing categories found in target IDs.")
        sys.exit(1)

    # Extract all categories recursively from clothing nodes
    # Include the L1 parent nodes as well for hierarchy
    all_categories = []
    seen_l1_ids = set()

    for l1_node, l2_node in clothing_nodes:
        l1_cat = l1_node.get("category", {})
        l1_id = l1_cat.get("categoryId", "")

        # Add L1 parent once (Women, Men, Kids, Baby)
        if l1_id not in seen_l1_ids:
            seen_l1_ids.add(l1_id)
            all_categories.append({
                "category_id": l1_id,
                "category_name": l1_cat.get("categoryName", ""),
                "parent_id": ROOT_CATEGORY_ID,
                "level": l1_node.get("categoryTreeNodeLevel", 1),
                "is_leaf": False,
                "path": l1_cat.get("categoryName", ""),
            })

        # Recurse into L2 clothing node
        l1_name = l1_cat.get("categoryName", "")
        categories = extract_categories(l2_node, parent_id=l1_id, path_prefix=l1_name)
        all_categories.extend(categories)

    # Also add the root category (11450) as top-level entry
    all_categories.insert(0, {
        "category_id": ROOT_CATEGORY_ID,
        "category_name": root_category.get("categoryName", ""),
        "parent_id": None,
        "level": root_node.get("categoryTreeNodeLevel", 0),
        "is_leaf": False,
        "path": root_category.get("categoryName", ""),
    })

    print(f"\nTotal clothing categories extracted: {len(all_categories)}")

    # Stats
    leaves = sum(1 for c in all_categories if c["is_leaf"])
    parents = len(all_categories) - leaves
    print(f"  Leaves: {leaves}, Parents: {parents}")

    # Show sample
    print("\nSample categories:")
    for cat in all_categories[:8]:
        marker = "  LEAF" if cat["is_leaf"] else ""
        print(f"  [{cat['category_id']}] L{cat['level']} {cat['path']}{marker}")
    if len(all_categories) > 8:
        print("  ...")

    # Upsert to database
    print("\nUpserting to database...")
    count = upsert_categories(all_categories)
    print(f"  Upserted {count} categories")

    # Verify
    with engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM ebay.categories")).scalar()
        leaf_count = conn.execute(text("SELECT COUNT(*) FROM ebay.categories WHERE is_leaf = true")).scalar()
        print(f"\nVerification: {total} total categories, {leaf_count} leaves in database")

    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)


if __name__ == "__main__":
    main()
