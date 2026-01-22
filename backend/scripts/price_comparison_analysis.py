#!/usr/bin/env python3
"""
Price Comparison Analysis Script

Compares current product prices with calculated prices using the new pricing algorithm.
Generates detailed reports showing discrepancies and analysis.

Usage:
    cd backend
    source .venv/bin/activate
    python scripts/price_comparison_analysis.py [--user USER_ID] [--output OUTPUT_FILE] [--threshold 0.30]

Formula: PRICE = BASE_PRICE × MODEL_COEFF × CONDITION_MULT × (1 + ADJUSTMENTS)
Where ADJUSTMENTS = origin_adj + decade_adj + trend_adj + feature_adj

Created: 2026-01-22
"""

import argparse
import csv
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session, sessionmaker

from models.public.brand_group import BrandGroup
from models.public.condition import Condition
from models.public.decade import Decade
from models.public.origin import Origin
from models.public.trend import Trend
from models.public.unique_feature import UniqueFeature
from models.product_attributes.model import Model
from models.user.product import Product, ProductStatus
from services.pricing.group_determination import determine_group
from services.pricing.adjustment_calculators import (
    calculateConditionMultiplier,
    calculateDecadeAdjustment,
    calculateFeatureAdjustment,
    calculateOriginAdjustment,
    calculateTrendAdjustment,
)
from shared.config import settings


@dataclass
class PriceCalculationResult:
    """Result of price calculation for a single product."""
    product_id: int
    title: str
    brand: str
    category: str
    model_name: Optional[str]
    condition: Optional[int]
    origin: Optional[str]
    decade: Optional[str]
    trend: Optional[str]
    unique_features: list[str]
    materials: list[str]

    # Pricing components
    group: Optional[str]
    base_price: Optional[Decimal]
    model_coeff: Decimal
    condition_mult: Decimal
    origin_adj: Decimal
    decade_adj: Decimal
    trend_adj: Decimal
    feature_adj: Decimal
    total_adjustment: Decimal

    # Prices
    current_price: Decimal
    calculated_price: Optional[Decimal]

    # Analysis
    difference: Optional[Decimal]
    difference_pct: Optional[Decimal]
    status: str  # "OK", "TOO_LOW", "TOO_HIGH", "NO_BRAND_GROUP", "ERROR"
    error_message: Optional[str]


class PriceComparisonAnalyzer:
    """Analyzes price discrepancies between current and calculated prices."""

    def __init__(self, db_url: str):
        """Initialize with database connection."""
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        self._current_user_id: Optional[int] = None

        # Coefficient caches
        self._condition_coeffs: dict[int, Decimal] = {}
        self._origin_coeffs: dict[str, Decimal] = {}
        self._decade_coeffs: dict[str, Decimal] = {}
        self._trend_coeffs: dict[str, Decimal] = {}
        self._feature_coeffs: dict[str, Decimal] = {}

    def _load_coefficients(self, db: Session) -> None:
        """Load all pricing coefficients from database."""
        # Conditions (note -> coefficient)
        conditions = db.execute(select(Condition)).scalars().all()
        self._condition_coeffs = {
            c.note: c.coefficient for c in conditions if c.coefficient is not None
        }

        # Origins (name_en -> pricing_coefficient)
        origins = db.execute(select(Origin)).scalars().all()
        self._origin_coeffs = {
            o.name_en: o.pricing_coefficient for o in origins
        }

        # Decades (name_en -> pricing_coefficient)
        decades = db.execute(select(Decade)).scalars().all()
        self._decade_coeffs = {
            d.name_en: d.pricing_coefficient for d in decades
        }

        # Trends (name_en -> pricing_coefficient)
        trends = db.execute(select(Trend)).scalars().all()
        self._trend_coeffs = {
            t.name_en: t.pricing_coefficient for t in trends
        }

        # Unique features (name_en -> pricing_coefficient)
        features = db.execute(select(UniqueFeature)).scalars().all()
        self._feature_coeffs = {
            f.name_en: f.pricing_coefficient for f in features
        }

        print(f"  Loaded coefficients: {len(self._condition_coeffs)} conditions, "
              f"{len(self._origin_coeffs)} origins, {len(self._decade_coeffs)} decades, "
              f"{len(self._trend_coeffs)} trends, {len(self._feature_coeffs)} features")

    def _get_user_schemas(self, db: Session) -> list[int]:
        """Get list of user IDs that have schemas."""
        result = db.execute(text("""
            SELECT schema_name FROM information_schema.schemata
            WHERE schema_name LIKE 'user_%'
            ORDER BY schema_name
        """))
        schemas = [row[0] for row in result]
        user_ids = []
        for schema in schemas:
            try:
                user_id = int(schema.replace("user_", ""))
                user_ids.append(user_id)
            except ValueError:
                continue
        return user_ids

    def _get_published_products(self, user_id: int) -> list[Product]:
        """Get all published products for a user using schema_translate_map."""
        # Create execution options with schema translation
        schema_map = {"tenant": f"user_{user_id}"}

        # Create a connection with schema translation
        with self.engine.connect() as conn:
            # Use execution options to translate schema
            conn = conn.execution_options(schema_translate_map=schema_map)

            # Set search path for FKs resolution
            conn.execute(text(f"SET search_path TO user_{user_id}, product_attributes, public"))

            # Create session with this connection
            session = Session(bind=conn)

            try:
                # Query products with status PUBLISHED
                stmt = select(Product).where(
                    Product.status == ProductStatus.PUBLISHED,
                    Product.deleted_at.is_(None)
                )
                results = list(session.execute(stmt).scalars().all())

                # Eager load M2M relationships while session is active
                for p in results:
                    # Access properties to trigger lazy loading
                    _ = p.materials
                    _ = p.unique_feature

                return results
            finally:
                session.close()

    def _get_brand_group(self, db: Session, brand: str, group: str) -> Optional[BrandGroup]:
        """Fetch BrandGroup from database."""
        stmt = select(BrandGroup).where(
            BrandGroup.brand == brand,
            BrandGroup.group == group
        )
        return db.execute(stmt).scalar_one_or_none()

    def _get_model(self, db: Session, brand: str, group: str, model_name: str) -> Optional[Model]:
        """Fetch Model from database."""
        stmt = select(Model).where(
            Model.brand == brand,
            Model.group == group,
            Model.name == model_name
        )
        return db.execute(stmt).scalar_one_or_none()

    def calculate_product_price(
        self,
        db: Session,
        product: Product
    ) -> PriceCalculationResult:
        """
        Calculate price for a single product using the new algorithm.

        Formula: PRICE = BASE_PRICE × MODEL_COEFF × CONDITION_MULT × (1 + ADJUSTMENTS)
        """
        # Extract product attributes
        brand = product.brand or "Unknown"
        category = product.category
        model_name = product.model
        condition = product.condition
        origin = product.origin
        decade = product.decade
        trend = product.trend
        unique_features = product.unique_feature or []
        materials = product.materials  # Property from M2M relationship

        result = PriceCalculationResult(
            product_id=product.id,
            title=product.title[:50] if product.title else "",
            brand=brand,
            category=category,
            model_name=model_name,
            condition=condition,
            origin=origin,
            decade=decade,
            trend=trend,
            unique_features=unique_features,
            materials=materials,
            group=None,
            base_price=None,
            model_coeff=Decimal("1.0"),
            condition_mult=Decimal("1.0"),
            origin_adj=Decimal("0.0"),
            decade_adj=Decimal("0.0"),
            trend_adj=Decimal("0.0"),
            feature_adj=Decimal("0.0"),
            total_adjustment=Decimal("0.0"),
            current_price=product.price,
            calculated_price=None,
            difference=None,
            difference_pct=None,
            status="OK",
            error_message=None
        )

        try:
            # Step 1: Determine group
            try:
                group = determine_group(category, materials)
                result.group = group
            except ValueError as e:
                result.status = "ERROR"
                result.error_message = f"Group determination failed: {e}"
                return result

            # Step 2: Get BrandGroup
            brand_group = self._get_brand_group(db, brand, group)
            if not brand_group:
                result.status = "NO_BRAND_GROUP"
                result.error_message = f"No BrandGroup for {brand} + {group}"
                return result

            result.base_price = brand_group.base_price

            # Step 3: Get Model (if provided)
            model = None
            if model_name:
                model = self._get_model(db, brand, group, model_name)
                if model:
                    result.model_coeff = model.coefficient

            # Step 4: Calculate condition multiplier
            if condition is not None:
                condition_coeff = self._condition_coeffs.get(condition, Decimal("1.0"))
                result.condition_mult = calculateConditionMultiplier(condition_coeff)

            # Step 5: Calculate adjustments using DIFF logic
            # Adjustment = actual - MAX(expected)

            # Origin adjustment
            expected_origins = brand_group.expected_origins or []
            result.origin_adj = calculateOriginAdjustment(
                origin,
                expected_origins,
                self._origin_coeffs
            )

            # Decade adjustment
            expected_decades = brand_group.expected_decades or []
            result.decade_adj = calculateDecadeAdjustment(
                decade,
                expected_decades,
                self._decade_coeffs
            )

            # Trend adjustment
            expected_trends = brand_group.expected_trends or []
            actual_trends = [trend] if trend else []
            result.trend_adj = calculateTrendAdjustment(
                actual_trends,
                expected_trends,
                self._trend_coeffs
            )

            # Feature adjustment
            expected_features = []
            if model:
                expected_features = model.expected_features or []
            result.feature_adj = calculateFeatureAdjustment(
                unique_features,
                expected_features,
                self._feature_coeffs
            )

            # Step 6: Calculate total adjustment and final price
            result.total_adjustment = (
                result.origin_adj +
                result.decade_adj +
                result.trend_adj +
                result.feature_adj
            )

            # Formula: PRICE = BASE_PRICE × MODEL_COEFF × CONDITION_MULT × (1 + ADJUSTMENTS)
            result.calculated_price = (
                result.base_price *
                result.model_coeff *
                result.condition_mult *
                (1 + result.total_adjustment)
            ).quantize(Decimal("0.01"))

            # Step 7: Compare with current price
            if result.current_price > 0:
                result.difference = result.calculated_price - result.current_price
                result.difference_pct = (result.difference / result.current_price * 100).quantize(Decimal("0.01"))

        except Exception as e:
            result.status = "ERROR"
            result.error_message = str(e)

        return result

    def analyze_user_products(
        self,
        user_id: int,
        threshold_pct: float = 30.0
    ) -> list[PriceCalculationResult]:
        """
        Analyze all published products for a user.

        Args:
            user_id: User ID to analyze
            threshold_pct: Percentage threshold for flagging discrepancies

        Returns:
            List of PriceCalculationResult for all products
        """
        results = []

        # Load coefficients once (from public/product_attributes schemas)
        with self.Session() as db:
            self._load_coefficients(db)

        # Get products using separate connection with schema translation
        products = self._get_published_products(user_id)
        print(f"  Found {len(products)} published products for user {user_id}")

        # Calculate prices using a new session
        with self.Session() as db:
            for product in products:
                result = self.calculate_product_price(db, product)

                # Determine status based on threshold
                if result.calculated_price and result.difference_pct:
                    if result.difference_pct > threshold_pct:
                        result.status = "TOO_LOW"  # Current price is too low
                    elif result.difference_pct < -threshold_pct:
                        result.status = "TOO_HIGH"  # Current price is too high
                    else:
                        result.status = "OK"

                results.append(result)

        return results

    def analyze_all_users(self, threshold_pct: float = 30.0) -> dict[int, list[PriceCalculationResult]]:
        """
        Analyze products for all users.

        Returns:
            Dict mapping user_id to list of results
        """
        all_results = {}

        with self.Session() as db:
            user_ids = self._get_user_schemas(db)
            print(f"Found {len(user_ids)} user schemas")

        for user_id in user_ids:
            print(f"\nAnalyzing user {user_id}...")
            results = self.analyze_user_products(user_id, threshold_pct)
            if results:
                all_results[user_id] = results

        return all_results


def generate_report(
    results: dict[int, list[PriceCalculationResult]],
    threshold_pct: float,
    output_file: Optional[str] = None
) -> None:
    """Generate analysis report."""

    # Flatten results
    all_results = []
    for user_id, user_results in results.items():
        for r in user_results:
            r.user_id = user_id  # Add user_id to result
            all_results.append(r)

    # Statistics
    total = len(all_results)
    ok_count = sum(1 for r in all_results if r.status == "OK")
    too_low_count = sum(1 for r in all_results if r.status == "TOO_LOW")
    too_high_count = sum(1 for r in all_results if r.status == "TOO_HIGH")
    no_bg_count = sum(1 for r in all_results if r.status == "NO_BRAND_GROUP")
    error_count = sum(1 for r in all_results if r.status == "ERROR")

    # Print summary
    print("\n" + "="*80)
    print("PRICE COMPARISON ANALYSIS REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Threshold: ±{threshold_pct}%")
    print("="*80)

    print(f"\n📊 SUMMARY")
    print(f"  Total products analyzed: {total}")
    print(f"  ✅ OK (within ±{threshold_pct}%): {ok_count} ({ok_count/total*100:.1f}%)" if total else "")
    print(f"  ⬇️  Too LOW (calculated > current + {threshold_pct}%): {too_low_count}")
    print(f"  ⬆️  Too HIGH (calculated < current - {threshold_pct}%): {too_high_count}")
    print(f"  ❌ No BrandGroup found: {no_bg_count}")
    print(f"  ⚠️  Errors: {error_count}")

    # Top 20 products with price too low
    too_low_results = sorted(
        [r for r in all_results if r.status == "TOO_LOW"],
        key=lambda r: r.difference_pct or 0,
        reverse=True
    )[:20]

    if too_low_results:
        print(f"\n📉 TOP 20 PRODUCTS WITH PRICE TOO LOW")
        print("-"*80)
        print(f"{'ID':>6} | {'Brand':<20} | {'Category':<15} | {'Current':>10} | {'Calculated':>10} | {'Diff %':>8}")
        print("-"*80)
        for r in too_low_results:
            print(f"{r.product_id:>6} | {r.brand[:20]:<20} | {r.category[:15]:<15} | "
                  f"{r.current_price:>10.2f} | {r.calculated_price:>10.2f} | {r.difference_pct:>+7.1f}%")

    # Top 20 products with price too high
    too_high_results = sorted(
        [r for r in all_results if r.status == "TOO_HIGH"],
        key=lambda r: r.difference_pct or 0
    )[:20]

    if too_high_results:
        print(f"\n📈 TOP 20 PRODUCTS WITH PRICE TOO HIGH")
        print("-"*80)
        print(f"{'ID':>6} | {'Brand':<20} | {'Category':<15} | {'Current':>10} | {'Calculated':>10} | {'Diff %':>8}")
        print("-"*80)
        for r in too_high_results:
            print(f"{r.product_id:>6} | {r.brand[:20]:<20} | {r.category[:15]:<15} | "
                  f"{r.current_price:>10.2f} | {r.calculated_price:>10.2f} | {r.difference_pct:>+7.1f}%")

    # Missing BrandGroups analysis
    no_bg_results = [r for r in all_results if r.status == "NO_BRAND_GROUP"]
    if no_bg_results:
        # Group by brand+group
        missing_bg = {}
        for r in no_bg_results:
            key = f"{r.brand} + {r.group or r.category}"
            if key not in missing_bg:
                missing_bg[key] = 0
            missing_bg[key] += 1

        sorted_missing = sorted(missing_bg.items(), key=lambda x: x[1], reverse=True)[:20]

        print(f"\n❌ TOP 20 MISSING BRANDGROUPS")
        print("-"*60)
        print(f"{'Brand + Group':<45} | {'Count':>10}")
        print("-"*60)
        for bg, count in sorted_missing:
            print(f"{bg[:45]:<45} | {count:>10}")

    # Adjustment analysis for discrepant products
    discrepant = [r for r in all_results if r.status in ["TOO_LOW", "TOO_HIGH"]]
    if discrepant:
        print(f"\n🔍 ADJUSTMENT ANALYSIS FOR DISCREPANT PRODUCTS")
        print("-"*80)

        # Average adjustments
        avg_origin = sum(r.origin_adj for r in discrepant) / len(discrepant)
        avg_decade = sum(r.decade_adj for r in discrepant) / len(discrepant)
        avg_trend = sum(r.trend_adj for r in discrepant) / len(discrepant)
        avg_feature = sum(r.feature_adj for r in discrepant) / len(discrepant)

        print(f"  Average adjustments:")
        print(f"    Origin:  {avg_origin:+.3f}")
        print(f"    Decade:  {avg_decade:+.3f}")
        print(f"    Trend:   {avg_trend:+.3f}")
        print(f"    Feature: {avg_feature:+.3f}")

        # Count products with null origin
        null_origin = sum(1 for r in discrepant if not r.origin)
        print(f"\n  Products with NULL origin: {null_origin}/{len(discrepant)} ({null_origin/len(discrepant)*100:.1f}%)")

        # Count products with null decade
        null_decade = sum(1 for r in discrepant if not r.decade)
        print(f"  Products with NULL decade: {null_decade}/{len(discrepant)} ({null_decade/len(discrepant)*100:.1f}%)")

    # Export to CSV if output file specified
    if output_file:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'user_id', 'product_id', 'brand', 'category', 'model', 'condition',
                'origin', 'decade', 'trend', 'features', 'materials',
                'group', 'base_price', 'model_coeff', 'condition_mult',
                'origin_adj', 'decade_adj', 'trend_adj', 'feature_adj', 'total_adj',
                'current_price', 'calculated_price', 'difference', 'difference_pct',
                'status', 'error_message'
            ])

            for r in all_results:
                writer.writerow([
                    getattr(r, 'user_id', ''),
                    r.product_id, r.brand, r.category, r.model_name or '', r.condition or '',
                    r.origin or '', r.decade or '', r.trend or '',
                    ','.join(r.unique_features), ','.join(r.materials),
                    r.group or '', r.base_price or '', r.model_coeff, r.condition_mult,
                    r.origin_adj, r.decade_adj, r.trend_adj, r.feature_adj, r.total_adjustment,
                    r.current_price, r.calculated_price or '', r.difference or '', r.difference_pct or '',
                    r.status, r.error_message or ''
                ])

        print(f"\n📁 Results exported to: {output_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Analyze price discrepancies")
    parser.add_argument("--user", type=int, help="Specific user ID to analyze")
    parser.add_argument("--output", type=str, help="Output CSV file path")
    parser.add_argument("--threshold", type=float, default=30.0, help="Percentage threshold (default: 30)")
    args = parser.parse_args()

    # Get database URL
    db_url = settings.database_url
    print(f"Connecting to database...")

    analyzer = PriceComparisonAnalyzer(db_url)

    if args.user:
        print(f"Analyzing user {args.user}...")
        results = {args.user: analyzer.analyze_user_products(args.user, args.threshold)}
    else:
        print("Analyzing all users...")
        results = analyzer.analyze_all_users(args.threshold)

    generate_report(results, args.threshold, args.output)


if __name__ == "__main__":
    main()
