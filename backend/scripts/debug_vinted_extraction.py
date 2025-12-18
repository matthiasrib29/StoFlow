"""
Debug script to analyze Vinted HTML extraction.

Usage:
    python scripts/debug_vinted_extraction.py <vinted_url_or_id>

Example:
    python scripts/debug_vinted_extraction.py 7739675823
    python scripts/debug_vinted_extraction.py https://www.vinted.fr/items/7739675823-...
"""

import re
import sys
import httpx


def analyze_html(html: str) -> dict:
    """Analyze HTML and show what patterns match."""

    results = {}

    # 1. Check if HTML is valid
    results['html_length'] = len(html)
    results['has_next_f'] = 'self.__next_f.push' in html

    # 2. Check for item pattern
    item_pattern = r'"item":\s*\{[^}]*"id":\s*(\d+)[^}]*"title"'
    item_match = re.search(item_pattern, html)
    results['item_id_from_pattern'] = item_match.group(1) if item_match else None

    # 3. Check for brand_dto pattern
    brand_pattern = r'"brand_dto":\s*\{\s*"id":\s*(\d+)\s*,\s*"title":\s*"([^"]+)"'
    brand_match = re.search(brand_pattern, html)
    if brand_match:
        results['brand_id'] = int(brand_match.group(1))
        results['brand_name'] = brand_match.group(2)
    else:
        results['brand_id'] = None
        results['brand_name'] = None

    # Alternative brand patterns
    alt_brand_patterns = [
        r'"brand":\s*\{\s*"id":\s*(\d+)',
        r'"brand_id":\s*(\d+)',
        r'"brand":\s*\{[^}]*"title":\s*"([^"]+)"',
    ]
    results['alt_brand_matches'] = []
    for pat in alt_brand_patterns:
        matches = re.findall(pat, html)
        if matches:
            results['alt_brand_matches'].append({
                'pattern': pat[:50],
                'matches': matches[:3]
            })

    # 4. Check for catalog_id pattern
    catalog_pattern = r'"catalog_id":\s*(\d+)'
    catalog_matches = re.findall(catalog_pattern, html)
    results['catalog_id_matches'] = catalog_matches[:5] if catalog_matches else None

    # 5. Check for size pattern
    size_pattern = r'"size"\s*:\s*\{\s*"id"\s*:\s*(\d+)\s*,\s*"title"\s*:\s*"([^"]+)"'
    size_match = re.search(size_pattern, html)
    if size_match:
        results['size_id'] = int(size_match.group(1))
        results['size_title'] = size_match.group(2)
    else:
        results['size_id'] = None
        results['size_title'] = None

    # 6. Check for status/condition pattern
    status_pattern = r'"status"\s*:\s*\{\s*"id"\s*:\s*(\d+)\s*,\s*"title"\s*:\s*"([^"]+)"'
    status_match = re.search(status_pattern, html)
    if status_match:
        results['condition_id'] = int(status_match.group(1))
        results['condition_title'] = status_match.group(2)
    else:
        results['condition_id'] = None
        results['condition_title'] = None

    # 7. Check for material pattern
    material_patterns = [
        r'"code"\s*:\s*"material"[^}]*"value"\s*:\s*"([^"]*)"',
        r'"material"\s*:\s*\{\s*[^}]*"title"\s*:\s*"([^"]+)"',
        r'"material"\s*:\s*"([^"]+)"',
    ]
    results['material_matches'] = []
    for pat in material_patterns:
        matches = re.findall(pat, html)
        if matches:
            results['material_matches'].append({
                'pattern': pat[:50],
                'matches': matches[:3]
            })

    # 8. Find all attribute codes
    attr_codes_pattern = r'"code"\s*:\s*"([^"]+)"'
    codes = re.findall(attr_codes_pattern, html)
    results['attribute_codes'] = list(set(codes))[:20]

    # 9. Look for raw brand mentions
    raw_brand = re.findall(r'"brand[^"]*":\s*[{\[]?[^,\]]*', html)
    results['raw_brand_snippets'] = raw_brand[:5] if raw_brand else None

    # 10. Check seller_id
    seller_pattern = r'"seller_id":\s*(\d+)'
    seller_match = re.search(seller_pattern, html)
    results['seller_id'] = int(seller_match.group(1)) if seller_match else None

    return results


def fetch_html(vinted_id: str) -> str:
    """Fetch HTML from Vinted."""
    if vinted_id.startswith('http'):
        url = vinted_id
    else:
        url = f"https://www.vinted.fr/items/{vinted_id}"

    response = httpx.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        },
        follow_redirects=True,
        timeout=30.0
    )
    return response.text


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/debug_vinted_extraction.py <vinted_url_or_id>")
        sys.exit(1)

    vinted_id = sys.argv[1]
    print(f"Fetching HTML for: {vinted_id}")

    html = fetch_html(vinted_id)
    print(f"HTML length: {len(html)} chars")

    print("\n" + "="*60)
    print("ANALYSIS RESULTS")
    print("="*60)

    results = analyze_html(html)

    for key, value in results.items():
        if value:
            print(f"\n{key}:")
            if isinstance(value, list):
                for item in value:
                    print(f"  - {item}")
            else:
                print(f"  {value}")
        else:
            print(f"\n{key}: None/Empty")

    # Save HTML for debugging
    with open('/tmp/vinted_debug.html', 'w') as f:
        f.write(html)
    print(f"\n\nFull HTML saved to /tmp/vinted_debug.html")


if __name__ == '__main__':
    main()
