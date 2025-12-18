"""
Import Vinted categories from catalog.json

Parses the Vinted catalog JSON and imports only clothing categories into
the public.vinted_categories table.

Filter criteria - only import categories under:
- Femmes > Vêtements (id: 4) → gender: women
- Hommes > Vêtements (id: 2050) → gender: men
- Enfants > Vêtements pour filles (id: 1195) → gender: girls
- Enfants > Vêtements pour garçons (id: 1194) → gender: boys

Usage:
    python scripts/import_vinted_categories.py

Author: Claude
Date: 2025-12-17
"""
import json
import os
import sys
from typing import Optional, List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from shared.database import engine


# Target category IDs and their gender mappings
CLOTHING_ROOTS = {
    4: "women",      # Femmes > Vêtements
    2050: "men",     # Hommes > Vêtements
    1195: "girls",   # Enfants > Vêtements pour filles
    1194: "boys",    # Enfants > Vêtements pour garçons
}


def find_category_by_id(catalogs: List[Dict], target_id: int) -> Optional[Dict]:
    """
    Recursively find a category by its ID.

    Args:
        catalogs: List of category dictionaries
        target_id: The category ID to find

    Returns:
        The category dict if found, None otherwise
    """
    for cat in catalogs:
        if cat.get("id") == target_id:
            return cat
        # Search in children
        children = cat.get("catalogs", [])
        if children:
            found = find_category_by_id(children, target_id)
            if found:
                return found
    return None


def extract_categories(
    category: Dict,
    gender: str,
    parent_id: Optional[int] = None,
    path_prefix: str = "",
    results: Optional[List[Dict]] = None
) -> List[Dict]:
    """
    Recursively extract all categories from a root category.

    Args:
        category: The category dict to process
        gender: The gender for all categories under this root
        parent_id: The parent category ID (None for root)
        path_prefix: The path prefix for building full path
        results: List to accumulate results

    Returns:
        List of category dicts ready for insertion
    """
    if results is None:
        results = []

    cat_id = category.get("id")
    title = category.get("title", "")
    code = category.get("code")
    children = category.get("catalogs", [])

    # Build path
    if path_prefix:
        path = f"{path_prefix} > {title}"
    else:
        path = title

    # A category is a leaf if it has no children
    is_leaf = len(children) == 0

    # Add this category
    results.append({
        "id": cat_id,
        "code": code,
        "title": title,
        "parent_id": parent_id,
        "path": path,
        "is_leaf": is_leaf,
        "gender": gender
    })

    # Process children recursively
    for child in children:
        extract_categories(child, gender, cat_id, path, results)

    return results


def load_catalog(filepath: str) -> Dict:
    """Load the catalog JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def topological_sort(categories: List[Dict]) -> List[Dict]:
    """
    Sort categories so that parents always come before children.

    Args:
        categories: List of category dicts

    Returns:
        Topologically sorted list
    """
    # Build lookup maps
    by_id = {cat["id"]: cat for cat in categories}
    result = []
    visited = set()

    def visit(cat_id: int):
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

    # Visit all categories
    for cat in categories:
        visit(cat["id"])

    return result


def import_categories_to_db(categories: List[Dict]) -> int:
    """
    Insert categories into the database.

    Args:
        categories: List of category dicts

    Returns:
        Number of categories inserted
    """
    # Topological sort ensures parents are inserted before children
    categories_sorted = topological_sort(categories)

    inserted_count = 0

    with engine.connect() as conn:
        # First, truncate the table to start fresh
        conn.execute(text("TRUNCATE TABLE public.vinted_categories CASCADE"))
        conn.commit()

        # Insert categories one by one in topological order
        for cat in categories_sorted:
            try:
                conn.execute(
                    text("""
                        INSERT INTO public.vinted_categories
                        (id, code, title, parent_id, path, is_leaf, gender)
                        VALUES (:id, :code, :title, :parent_id, :path, :is_leaf, :gender)
                        ON CONFLICT (id) DO UPDATE SET
                            code = EXCLUDED.code,
                            title = EXCLUDED.title,
                            parent_id = EXCLUDED.parent_id,
                            path = EXCLUDED.path,
                            is_leaf = EXCLUDED.is_leaf,
                            gender = EXCLUDED.gender
                    """),
                    {
                        "id": cat["id"],
                        "code": cat["code"],
                        "title": cat["title"],
                        "parent_id": cat["parent_id"],
                        "path": cat["path"],
                        "is_leaf": cat["is_leaf"],
                        "gender": cat["gender"]
                    }
                )
                conn.commit()  # Commit after each insert
                inserted_count += 1
            except Exception as e:
                conn.rollback()
                print(f"  ⚠️  Error inserting category {cat['id']}: {e}")

    return inserted_count


def main():
    """Main entry point."""
    print("=" * 60)
    print("IMPORT VINTED CATEGORIES")
    print("=" * 60)

    # Path to catalog.json
    script_dir = os.path.dirname(os.path.abspath(__file__))
    catalog_path = os.path.join(os.path.dirname(script_dir), "catalog.json")

    if not os.path.exists(catalog_path):
        print(f"❌ Catalog file not found: {catalog_path}")
        sys.exit(1)

    print(f"\n📁 Loading catalog from: {catalog_path}")
    catalog = load_catalog(catalog_path)

    root_catalogs = catalog.get("catalogs", [])
    print(f"   Found {len(root_catalogs)} root categories")

    # Extract clothing categories for each gender
    all_categories = []

    for root_id, gender in CLOTHING_ROOTS.items():
        print(f"\n🔍 Searching for category ID {root_id} ({gender})...")
        root_category = find_category_by_id(root_catalogs, root_id)

        if root_category:
            print(f"   ✓ Found: {root_category['title']}")
            categories = extract_categories(root_category, gender)
            print(f"   → Extracted {len(categories)} categories")
            all_categories.extend(categories)
        else:
            print(f"   ⚠️  Category ID {root_id} not found!")

    print(f"\n📊 Total categories to import: {len(all_categories)}")

    # Show sample
    print("\n📋 Sample categories:")
    for cat in all_categories[:5]:
        leaf_marker = "🍃" if cat["is_leaf"] else "📁"
        print(f"   {leaf_marker} [{cat['id']}] {cat['path']} ({cat['gender']})")
    print("   ...")

    # Count by gender
    print("\n📈 Categories by gender:")
    gender_counts = {}
    for cat in all_categories:
        gender_counts[cat["gender"]] = gender_counts.get(cat["gender"], 0) + 1
    for gender, count in sorted(gender_counts.items()):
        print(f"   • {gender}: {count}")

    # Count leaves vs parents
    leaves = sum(1 for c in all_categories if c["is_leaf"])
    parents = len(all_categories) - leaves
    print(f"\n📊 Leaves: {leaves}, Parents: {parents}")

    # Import to database
    print("\n💾 Importing to database...")
    inserted = import_categories_to_db(all_categories)
    print(f"   ✓ Inserted {inserted} categories")

    # Verify
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM public.vinted_categories")).scalar()
        print(f"\n✅ Verification: {result} categories in database")

        # Show leaf count by gender
        result = conn.execute(text("""
            SELECT gender, COUNT(*) as total, SUM(CASE WHEN is_leaf THEN 1 ELSE 0 END) as leaves
            FROM public.vinted_categories
            GROUP BY gender
            ORDER BY gender
        """)).fetchall()
        print("\n📊 Database stats by gender:")
        for row in result:
            print(f"   • {row[0]}: {row[1]} total, {row[2]} leaves")

    print("\n" + "=" * 60)
    print("IMPORT COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
