"""
Script de test pour la génération de base_price via Gemini.

Récupère des produits publiés avec des marques uniques et génère
les BrandGroup pour analyser la qualité des prix générés.
Sauvegarde les résultats en BDD.

Usage:
    cd backend
    source .venv/bin/activate
    python scripts/test_pricing_generation.py --limit 20 --delay 15
"""

import argparse
import asyncio
import sys
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func, text
from sqlalchemy.orm import Session

from shared.database import get_tenant_session, engine
from shared.config import settings
from models.user.product import Product, ProductStatus
from models.public.brand_group import BrandGroup
from services.pricing.group_determination import determine_group
from services.pricing.pricing_generation_service import PricingGenerationService, GenerationResult
from repositories.brand_group_repository import BrandGroupRepository


def get_unique_brand_products(limit: int = 20) -> list[dict]:
    """
    Récupère des produits publiés avec des marques uniques.

    Returns:
        Liste de dicts avec brand, category, material pour chaque produit unique.
    """
    with get_tenant_session(user_id=1) as db:
        # Query distinct brands - simpler approach using distinct
        stmt = (
            select(Product)
            .where(Product.status == ProductStatus.PUBLISHED)
            .where(Product.brand.isnot(None))
            .where(Product.brand != '')
            .where(Product.category.isnot(None))
            .where(Product.category != '')
            .order_by(Product.id)
            .limit(500)  # Get more to filter unique brands
        )

        all_products = db.execute(stmt).scalars().all()

        # Filter unique brands
        seen_brands = set()
        products = []
        for product in all_products:
            if product.brand.lower() not in seen_brands and len(products) < limit:
                seen_brands.add(product.brand.lower())
                # Access materials property (triggers lazy load)
                materials_list = product.materials if product.product_materials else []
                products.append({
                    'brand': product.brand,
                    'category': product.category,
                    'materials': ', '.join(materials_list) if materials_list else '',
                })

        return products


def get_brands_from_attributes(limit: int = 100, default_category: str = 'jeans') -> list[dict]:
    """
    Récupère les marques depuis la table product_attributes.brands.

    Args:
        limit: Nombre de marques à récupérer.
        default_category: Catégorie par défaut pour le groupe pricing.

    Returns:
        Liste de dicts avec brand, category, materials.
    """
    with Session(engine) as db:
        result = db.execute(
            text('SELECT name FROM product_attributes.brands ORDER BY name LIMIT :limit'),
            {'limit': limit}
        )

        brands = []
        for row in result:
            brands.append({
                'brand': row[0],
                'category': default_category,
                'materials': '',
            })

        return brands


def get_all_brand_group_combinations(limit: int = 500) -> list[dict]:
    """
    Récupère toutes les combinaisons brand+group uniques depuis les produits user_1.
    Convertit category en group via determine_group().

    Args:
        limit: Nombre maximum de combinaisons.

    Returns:
        Liste de dicts avec brand, category (=group), materials.
    """
    with Session(engine) as db:
        result = db.execute(
            text('''
                SELECT DISTINCT brand, category
                FROM user_1.products
                WHERE brand IS NOT NULL
                  AND brand != ''
                  AND category IS NOT NULL
                  AND category != ''
            ''')
        )

        # Convert category to group and deduplicate
        brand_groups = {}
        for row in result:
            brand, category = row[0], row[1]
            try:
                group = determine_group(category, [])
                key = (brand, group)
                if key not in brand_groups:
                    brand_groups[key] = {
                        'brand': brand,
                        'category': category,  # Keep original for display
                        'group': group,        # Actual pricing group
                        'materials': '',
                    }
            except ValueError:
                # Skip unknown categories like "other"
                pass

        # Return as list, limited
        combinations = list(brand_groups.values())[:limit]
        return combinations


def save_brand_group_to_db(brand_group: BrandGroup) -> bool:
    """
    Sauvegarde un BrandGroup en BDD (public schema).

    Returns:
        True si créé/mis à jour, False si erreur
    """
    with Session(engine) as db:
        try:
            # Check if already exists
            existing = BrandGroupRepository.get_by_brand_and_group(
                db, brand_group.brand, brand_group.group
            )

            if existing:
                # Update existing
                existing.base_price = brand_group.base_price
                existing.condition_sensitivity = brand_group.condition_sensitivity
                existing.expected_origins = brand_group.expected_origins
                existing.expected_decades = brand_group.expected_decades
                existing.expected_trends = brand_group.expected_trends
                existing.generated_by_ai = brand_group.generated_by_ai
                existing.ai_confidence = brand_group.ai_confidence
                existing.generation_cost = brand_group.generation_cost
                BrandGroupRepository.update(db, existing)
                db.commit()
                return True
            else:
                # Create new
                BrandGroupRepository.create(db, brand_group)
                db.commit()
                return True

        except Exception as e:
            db.rollback()
            print(f"   ❌ Erreur DB: {e}")
            return False


async def generate_and_display(products: list[dict], delay: int = 15) -> None:
    """
    Génère les BrandGroup et affiche les résultats.
    """
    print("\n" + "=" * 100)
    print("TEST GÉNÉRATION BASE_PRICE - PRICING ALGORITHM")
    print("=" * 100)
    print(f"\nModèle utilisé: gemini-3-flash-preview")
    print(f"Nombre de marques uniques: {len(products)}")
    print(f"Délai entre requêtes: {delay}s (rate limit free tier: 5/min)")
    print("\n" + "-" * 100)

    results = []
    saved_count = 0
    fallback_count = 0
    total_input_tokens = 0
    total_output_tokens = 0
    total_cost_usd = 0.0

    for i, product in enumerate(products, 1):
        brand = product['brand']
        category = product['category']
        materials = [m.strip() for m in product['materials'].split(',') if m.strip()] if product['materials'] else []

        # Use pre-calculated group if available, otherwise determine it
        if 'group' in product:
            group = product['group']
        else:
            try:
                group = determine_group(category, materials)
            except ValueError as e:
                print(f"\n[{i}/{len(products)}] ⚠️  {brand} | {category}")
                print(f"   Erreur: {e}")
                continue

        print(f"\n[{i}/{len(products)}] 🔄 {brand} | {category} → {group}")
        print(f"   Materials: {materials if materials else '(none)'}")

        # Generate BrandGroup
        try:
            gen_result = await PricingGenerationService.generate_brand_group(brand, group)
            brand_group = gen_result.brand_group
            input_tokens = gen_result.input_tokens
            output_tokens = gen_result.output_tokens
            cost_usd = gen_result.cost_usd
            is_fallback = gen_result.is_fallback

            # Track totals
            total_input_tokens += input_tokens
            total_output_tokens += output_tokens
            total_cost_usd += cost_usd

            # Extract values immediately (before any session operations)
            base_price = float(brand_group.base_price)
            condition_sensitivity = float(brand_group.condition_sensitivity)
            ai_confidence = float(brand_group.ai_confidence) if brand_group.ai_confidence else 0.0
            generated_by_ai = brand_group.generated_by_ai
            expected_origins = list(brand_group.expected_origins) if brand_group.expected_origins else []
            expected_decades = list(brand_group.expected_decades) if brand_group.expected_decades else []
            expected_trends = list(brand_group.expected_trends) if brand_group.expected_trends else []

            if is_fallback:
                fallback_count += 1
                print(f"   ⚠️  base_price: {base_price}€ (FALLBACK - rate limit?)")
                if input_tokens > 0:
                    print(f"      tokens: {input_tokens} in / {output_tokens} out | cost: ${cost_usd:.6f}")
            else:
                print(f"   ✅ base_price: {base_price}€ (confidence: {ai_confidence:.0%})")
                print(f"      condition_sensitivity: {condition_sensitivity}")
                print(f"      origins: {expected_origins}")
                print(f"      decades: {expected_decades}")
                print(f"      trends: {expected_trends}")
                print(f"      tokens: {input_tokens} in / {output_tokens} out | cost: ${cost_usd:.6f}")

                # Save to database (only if not fallback)
                if save_brand_group_to_db(brand_group):
                    print(f"   💾 Sauvegardé en BDD")
                    saved_count += 1

            result = {
                'brand': brand,
                'category': category,
                'group': group,
                'base_price': base_price,
                'condition_sensitivity': condition_sensitivity,
                'ai_confidence': ai_confidence,
                'expected_origins': expected_origins,
                'expected_decades': expected_decades,
                'expected_trends': expected_trends,
                'is_fallback': is_fallback,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'cost_usd': cost_usd,
            }
            results.append(result)

        except Exception as e:
            print(f"   ❌ Erreur: {e}")

        # Delay to respect rate limit (except for last item)
        if i < len(products) and delay > 0:
            print(f"   ⏳ Attente {delay}s...")
            time.sleep(delay)

    # Summary table
    print("\n" + "=" * 115)
    print("RÉSUMÉ DES PRIX GÉNÉRÉS")
    print("=" * 115)
    print(f"\n{'Brand':<20} {'Group':<15} {'Price':>7} {'Conf':>6} {'Sens':>5} {'In':>6} {'Out':>5} {'Cost $':>10} {'Status':>10}")
    print("-" * 115)

    for r in sorted(results, key=lambda x: x['base_price'], reverse=True):
        status = "FALLBACK" if r['is_fallback'] else "AI"
        conf_str = f"{r['ai_confidence']:.0%}" if r['ai_confidence'] else "-"
        in_tok = r['input_tokens'] if r['input_tokens'] > 0 else "-"
        out_tok = r['output_tokens'] if r['output_tokens'] > 0 else "-"
        cost_str = f"{r['cost_usd']:.6f}" if r['cost_usd'] > 0 else "-"
        print(f"{r['brand'][:19]:<20} {r['group'][:14]:<15} {r['base_price']:>5.0f}€ {conf_str:>6} {r['condition_sensitivity']:>5.2f} {str(in_tok):>6} {str(out_tok):>5} {cost_str:>10} {status:>10}")

    print("-" * 115)

    if results:
        # Stats only for non-fallback results
        real_results = [r for r in results if not r['is_fallback']]

        if real_results:
            avg_price = sum(r['base_price'] for r in real_results) / len(real_results)
            min_price = min(r['base_price'] for r in real_results)
            max_price = max(r['base_price'] for r in real_results)
            print(f"\nStatistiques (résultats réels uniquement):")
            print(f"  - Prix moyen: {avg_price:.2f}€")
            print(f"  - Prix min: {min_price:.2f}€")
            print(f"  - Prix max: {max_price:.2f}€")

        print(f"\nRésumé:")
        print(f"  - Total traité: {len(results)}/{len(products)}")
        print(f"  - Générés OK: {len(results) - fallback_count}")
        print(f"  - Fallbacks: {fallback_count}")
        print(f"  - Sauvegardés en BDD: {saved_count}")
        print(f"\nTokens & Coût:")
        print(f"  - Input tokens: {total_input_tokens:,}")
        print(f"  - Output tokens: {total_output_tokens:,}")
        print(f"  - Total tokens: {total_input_tokens + total_output_tokens:,}")
        print(f"  - Coût total: ${total_cost_usd:.6f}")


def main():
    parser = argparse.ArgumentParser(description='Test pricing generation with Gemini')
    parser.add_argument('--limit', type=int, default=20, help='Number of unique brands to test')
    parser.add_argument('--delay', type=int, default=15, help='Delay in seconds between API calls (default: 15)')
    parser.add_argument('--source', type=str, default='products', choices=['products', 'attributes', 'combinations'],
                        help='Source: "products" (published), "attributes" (brand table), "combinations" (all brand+group from user products)')
    parser.add_argument('--category', type=str, default='jeans',
                        help='Default category for attributes source (default: jeans)')
    args = parser.parse_args()

    if args.source == 'attributes':
        print(f"Récupération de {args.limit} marques depuis product_attributes.brands...")
        products = get_brands_from_attributes(limit=args.limit, default_category=args.category)
    elif args.source == 'combinations':
        print(f"Récupération des couples brand+group depuis user_1.products...")
        products = get_all_brand_group_combinations(limit=args.limit)
    else:
        print(f"Récupération de {args.limit} produits avec marques uniques...")
        products = get_unique_brand_products(limit=args.limit)

    if not products:
        print("Aucune marque trouvée")
        return

    print(f"Trouvé {len(products)} couples brand+group")

    # Run async generation
    asyncio.run(generate_and_display(products, delay=args.delay))


if __name__ == "__main__":
    main()
