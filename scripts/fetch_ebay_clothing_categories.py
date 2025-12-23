#!/usr/bin/env python3
"""
Fetch eBay Clothing Categories for all marketplaces.

This script retrieves the clothing category tree from eBay Taxonomy API
for each marketplace (FR, GB, DE, IT, ES, NL, BE, PL) and exports to JSON.

Usage:
    python scripts/fetch_ebay_clothing_categories.py

Requirements:
    - EBAY_CLIENT_ID and EBAY_CLIENT_SECRET in backend/.env
    - requests library

Output:
    - scripts/output/ebay_clothing_categories_{marketplace}.json (per marketplace)
    - scripts/output/ebay_clothing_categories_all.json (combined)

Author: Claude
Date: 2024-12-22
"""

import base64
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

# Load .env from backend
BACKEND_DIR = Path(__file__).parent.parent / "backend"
load_dotenv(BACKEND_DIR / ".env")

# eBay API Configuration
EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID")
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")
EBAY_SANDBOX = os.getenv("EBAY_SANDBOX", "false").lower() == "true"

# API URLs
AUTH_URL_PROD = "https://api.ebay.com/identity/v1/oauth2/token"
AUTH_URL_SANDBOX = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
API_BASE_PROD = "https://api.ebay.com"
API_BASE_SANDBOX = "https://api.sandbox.ebay.com"

# Category Tree IDs per marketplace
CATEGORY_TREE_IDS = {
    "EBAY_FR": "71",   # France
    "EBAY_GB": "3",    # UK
    "EBAY_DE": "77",   # Germany
    "EBAY_ES": "186",  # Spain
    "EBAY_IT": "101",  # Italy
    "EBAY_NL": "146",  # Netherlands
    "EBAY_BE": "23",   # Belgium (French)
    "EBAY_PL": "212",  # Poland
}

# Root Clothing category IDs per marketplace
# These are the "Vêtements, accessoires" or equivalent categories
CLOTHING_ROOT_IDS = {
    "EBAY_FR": "11450",   # Vêtements, accessoires
    "EBAY_GB": "11450",   # Clothes, Shoes & Accessories
    "EBAY_DE": "11450",   # Kleidung & Accessoires
    "EBAY_ES": "11450",   # Ropa, calzado y complementos
    "EBAY_IT": "11450",   # Abbigliamento e accessori
    "EBAY_NL": "11450",   # Kleding en accessoires
    "EBAY_BE": "11450",   # Vêtements, accessoires
    "EBAY_PL": "11450",   # Odzież, Buty i Dodatki
}

# Output directory
OUTPUT_DIR = Path(__file__).parent / "output"


def get_application_token() -> str:
    """
    Get eBay Application Token using Client Credentials Grant.

    This token is used for public APIs like Taxonomy.
    """
    if not EBAY_CLIENT_ID or not EBAY_CLIENT_SECRET:
        raise ValueError(
            "EBAY_CLIENT_ID and EBAY_CLIENT_SECRET must be set in backend/.env"
        )

    auth_url = AUTH_URL_SANDBOX if EBAY_SANDBOX else AUTH_URL_PROD

    # Base64 encode credentials
    credentials = f"{EBAY_CLIENT_ID}:{EBAY_CLIENT_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {encoded_credentials}",
    }

    data = {
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope",
    }

    print(f"[AUTH] Getting application token from {'sandbox' if EBAY_SANDBOX else 'production'}...")

    response = requests.post(auth_url, headers=headers, data=data)

    if response.status_code != 200:
        raise Exception(f"Failed to get token: {response.status_code} - {response.text}")

    token_data = response.json()
    print(f"[AUTH] Token obtained successfully (expires in {token_data.get('expires_in')}s)")

    return token_data["access_token"]


def get_category_subtree(
    token: str,
    category_tree_id: str,
    category_id: str,
) -> Dict[str, Any]:
    """
    Fetch category subtree from eBay Taxonomy API.

    Args:
        token: Application access token
        category_tree_id: Tree ID for the marketplace
        category_id: Root category ID to fetch subtree from

    Returns:
        Category subtree data
    """
    api_base = API_BASE_SANDBOX if EBAY_SANDBOX else API_BASE_PROD
    url = f"{api_base}/commerce/taxonomy/v1/category_tree/{category_tree_id}/get_category_subtree"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }

    params = {
        "category_id": category_id,
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        print(f"[ERROR] Failed to fetch subtree: {response.status_code}")
        print(f"[ERROR] Response: {response.text[:500]}")
        return {}

    return response.json()


def flatten_categories(
    node: Dict[str, Any],
    path: str = "",
    result: Optional[List[Dict]] = None,
) -> List[Dict]:
    """
    Flatten category tree into a list with paths.

    Args:
        node: Category tree node
        path: Current path (for building full path)
        result: Accumulator list

    Returns:
        Flattened list of categories
    """
    if result is None:
        result = []

    category = node.get("category", {})
    category_id = category.get("categoryId")
    category_name = category.get("categoryName", "")

    # Build path
    current_path = f"{path} > {category_name}" if path else category_name

    # Add this category
    if category_id:
        result.append({
            "category_id": category_id,
            "category_name": category_name,
            "category_path": current_path,
            "is_leaf": node.get("leafCategoryTreeNode", False),
            "parent_category_id": node.get("parentCategoryTreeNodeHref", "").split("/")[-1] if node.get("parentCategoryTreeNodeHref") else None,
        })

    # Process children
    for child in node.get("childCategoryTreeNodes", []):
        flatten_categories(child, current_path, result)

    return result


def filter_clothing_only(categories: List[Dict]) -> List[Dict]:
    """
    Filter to keep only clothing-related categories (not shoes, bags, accessories).

    We want:
    - Jeans, Pants, T-shirts, Shirts, Jackets, Sweaters, etc.

    We exclude:
    - Shoes, Bags, Watches, Jewelry, etc.
    """
    # Keywords to INCLUDE (clothing)
    include_keywords = [
        "jean", "jeans", "pantalon", "pants", "trousers", "hosen",
        "t-shirt", "tee", "top", "chemise", "shirt", "hemd", "camicia",
        "veste", "jacket", "jacke", "giacca", "manteau", "coat",
        "pull", "sweater", "pullover", "sweat", "hoodie", "cardigan",
        "short", "bermuda",
        "robe", "dress", "kleid", "vestito",
        "jupe", "skirt", "rock", "gonna",
        "polo", "blouse", "gilet", "vest",
        "jogging", "survêtement", "tracksuit",
        "combinaison", "jumpsuit", "overall",
        # Gender sections
        "homme", "men", "herren", "uomo", "hombre",
        "femme", "women", "damen", "donna", "mujer",
        "vêtements", "clothing", "kleidung", "abbigliamento", "ropa",
    ]

    # Keywords to EXCLUDE
    exclude_keywords = [
        "chaussure", "shoe", "schuh", "scarpe", "zapato",
        "sneaker", "basket", "boot", "sandale", "sandal",
        "sac", "bag", "tasche", "borsa", "bolso",
        "montre", "watch", "uhr", "orologio", "reloj",
        "bijou", "jewelry", "schmuck", "gioielli", "joya",
        "lunette", "sunglasses", "brille", "occhiali", "gafas",
        "ceinture", "belt", "gürtel", "cintura", "cinturón",
        "chapeau", "hat", "hut", "cappello", "sombrero",
        "écharpe", "scarf", "schal", "sciarpa", "bufanda",
        "gant", "glove", "handschuh", "guanto", "guante",
        "sous-vêtement", "underwear", "unterwäsche", "intimo", "ropa interior",
        "maillot de bain", "swimwear", "bademode", "costume",
        "accessoire", "accessories", "zubehör", "accessori", "accesorios",
        "bébé", "baby", "enfant", "kids", "kinder", "bambini", "niño",
    ]

    filtered = []

    for cat in categories:
        name_lower = cat["category_name"].lower()
        path_lower = cat["category_path"].lower()

        # Check exclusions first
        excluded = any(kw in name_lower or kw in path_lower for kw in exclude_keywords)

        if excluded:
            continue

        # Check inclusions (be more permissive - include if path contains clothing keywords)
        included = any(kw in path_lower for kw in include_keywords)

        if included:
            filtered.append(cat)

    return filtered


def fetch_marketplace_categories(
    token: str,
    marketplace_id: str,
    skip_filter: bool = False,
) -> Dict[str, Any]:
    """
    Fetch and process clothing categories for a marketplace.

    Args:
        token: eBay access token
        marketplace_id: Marketplace ID (EBAY_FR, etc.)
        skip_filter: If True, return all categories without filtering

    Returns:
        Dict with marketplace info and categories
    """
    print(f"\n{'='*60}")
    print(f"[{marketplace_id}] Fetching categories...")

    tree_id = CATEGORY_TREE_IDS.get(marketplace_id)
    root_id = CLOTHING_ROOT_IDS.get(marketplace_id)

    if not tree_id or not root_id:
        print(f"[{marketplace_id}] Unknown marketplace, skipping")
        return {"marketplace_id": marketplace_id, "categories": [], "error": "Unknown marketplace"}

    print(f"[{marketplace_id}] Tree ID: {tree_id}, Root ID: {root_id}")

    # Fetch subtree
    subtree = get_category_subtree(token, tree_id, root_id)

    if not subtree:
        return {"marketplace_id": marketplace_id, "categories": [], "error": "Failed to fetch"}

    # Flatten
    all_categories = flatten_categories(subtree.get("categorySubtreeNode", {}))
    print(f"[{marketplace_id}] Total categories in tree: {len(all_categories)}")

    # Get all leaf categories
    all_leaf_categories = [c for c in all_categories if c["is_leaf"]]
    print(f"[{marketplace_id}] Total leaf categories: {len(all_leaf_categories)}")

    if skip_filter:
        # Return ALL categories without filtering
        return {
            "marketplace_id": marketplace_id,
            "category_tree_id": tree_id,
            "root_category_id": root_id,
            "total_count": len(all_categories),
            "leaf_count": len(all_leaf_categories),
            "categories": all_categories,
            "leaf_categories": all_leaf_categories,
        }

    # Filter clothing only
    clothing_categories = filter_clothing_only(all_categories)
    print(f"[{marketplace_id}] Clothing categories after filter: {len(clothing_categories)}")

    # Get leaf categories only (for mapping)
    leaf_categories = [c for c in clothing_categories if c["is_leaf"]]
    print(f"[{marketplace_id}] Leaf categories (usable for listing): {len(leaf_categories)}")

    return {
        "marketplace_id": marketplace_id,
        "category_tree_id": tree_id,
        "root_category_id": root_id,
        "total_count": len(all_categories),
        "clothing_count": len(clothing_categories),
        "leaf_count": len(leaf_categories),
        "categories": clothing_categories,
        "leaf_categories": leaf_categories,
    }


def main():
    """Main function to fetch all marketplaces."""
    import argparse

    parser = argparse.ArgumentParser(description="Fetch eBay Clothing Categories")
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Skip filtering, export ALL categories from clothing root"
    )
    parser.add_argument(
        "--marketplace",
        type=str,
        default=None,
        help="Fetch only specific marketplace (e.g., EBAY_FR)"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("eBay Clothing Categories Fetcher")
    print(f"Mode: {'RAW (no filter)' if args.raw else 'FILTERED (clothing only)'}")
    print("=" * 60)

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Get token
    try:
        token = get_application_token()
    except Exception as e:
        print(f"[ERROR] Failed to get token: {e}")
        sys.exit(1)

    # Determine which marketplaces to fetch
    marketplaces = [args.marketplace] if args.marketplace else list(CATEGORY_TREE_IDS.keys())

    # Fetch marketplaces
    all_results = {}

    for marketplace_id in marketplaces:
        if marketplace_id not in CATEGORY_TREE_IDS:
            print(f"[ERROR] Unknown marketplace: {marketplace_id}")
            continue

        result = fetch_marketplace_categories(token, marketplace_id, skip_filter=args.raw)
        all_results[marketplace_id] = result

        # Save individual file
        suffix = "_raw" if args.raw else ""
        output_file = OUTPUT_DIR / f"ebay_categories_{marketplace_id.lower()}{suffix}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"[{marketplace_id}] Saved to {output_file}")

    # Save combined file if multiple marketplaces
    if len(marketplaces) > 1:
        suffix = "_raw" if args.raw else ""
        combined_file = OUTPUT_DIR / f"ebay_categories_all{suffix}.json"
        with open(combined_file, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        print(f"\n[COMBINED] Saved to {combined_file}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for mp_id, data in all_results.items():
        if "error" in data:
            print(f"  {mp_id}: ERROR - {data['error']}")
        else:
            leaf_count = data.get('leaf_count', 0)
            total = data.get('total_count', 0)
            if args.raw:
                print(f"  {mp_id}: {leaf_count} leaf categories (from {total} total)")
            else:
                clothing = data.get('clothing_count', 0)
                print(f"  {mp_id}: {leaf_count} leaf categories (from {clothing} clothing)")

    print("\nDone!")


if __name__ == "__main__":
    main()
