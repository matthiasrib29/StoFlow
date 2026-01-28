"""
Export all product attributes from the database to a text file.

Usage:
    cd backend
    source .venv/bin/activate
    python scripts/export_product_attributes.py
    # Output: ../product_attributes_reference.txt
"""

import sys
from pathlib import Path
from datetime import datetime
from textwrap import fill

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from shared.config import settings

# Tables to skip
SKIP_TABLES = {
    "brands", "sizes", "size_normalized", "sizes_normalized",
    "sizes_original", "models",
    "dim1", "dim2", "dim3", "dim4", "dim5", "dim6",
    "vw_dimension_info",
}

OUTPUT_PATH = Path(__file__).parent.parent.parent / "product_attributes_reference.txt"


def export_attributes():
    engine = create_engine(settings.database_url)

    # Get all tables in product_attributes schema
    with engine.connect() as conn:
        tables = conn.execute(text("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'product_attributes'
            ORDER BY table_name
        """)).fetchall()
        table_names = [t[0] for t in tables if t[0] not in SKIP_TABLES]

    # Collect categories with hierarchy
    categories_tree = {}
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT name_en, parent_category FROM product_attributes.categories "
            "ORDER BY parent_category NULLS FIRST, name_en"
        )).fetchall()
        all_cats = {r[0]: r[1] for r in rows}

        # Build tree: parent -> [children]
        for name, parent in all_cats.items():
            if parent not in categories_tree:
                categories_tree[parent] = []
            categories_tree[parent].append(name)

    # Collect data from each table (except categories, handled above)
    results = {}
    for table in table_names:
        if table == "categories":
            continue
        with engine.connect() as conn:
            try:
                has_name_en = conn.execute(text(
                    "SELECT EXISTS ("
                    "  SELECT 1 FROM information_schema.columns"
                    "  WHERE table_schema = 'product_attributes'"
                    f"  AND table_name = '{table}'"
                    "  AND column_name = 'name_en'"
                    ")"
                )).scalar()

                if has_name_en:
                    rows = conn.execute(text(
                        f"SELECT name_en FROM product_attributes.{table} ORDER BY name_en"
                    )).fetchall()
                    results[table] = [r[0] for r in rows]
                else:
                    rows = conn.execute(text(
                        f"SELECT * FROM product_attributes.{table} ORDER BY 1"
                    )).fetchall()
                    results[table] = [str(r) for r in rows]
            except Exception as e:
                results[table] = [f"ERROR: {e}"]

    # Write output file
    lines = []
    sep = "=" * 80
    lines.append(sep)
    lines.append("               StoFlow - Product Attributes Reference (from DB)")
    lines.append(sep)
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"Source: product_attributes schema (PostgreSQL)")
    lines.append(f"Excludes: brands, sizes, dim*, models")
    lines.append("")

    # --- Categories with hierarchy ---
    total_cats = len(all_cats)
    lines.append("")
    lines.append(f"=== CATEGORIES ({total_cats} total) ===")
    lines.append("")

    # Root categories (parent_category IS NULL)
    roots = categories_tree.get(None, [])
    for root in roots:
        lines.append(f"  {root} (root)")
        # Level 1: parent categories
        parents = sorted(categories_tree.get(root, []))
        for parent in parents:
            children = sorted(categories_tree.get(parent, []))
            if children:
                lines.append(f"    {parent} (parent) [{len(children)} children]")
                lines.append(f"      {fill(', '.join(children), width=64, subsequent_indent='      ')}")
            else:
                lines.append(f"    {parent} (leaf)")

    # Categories without known parent (orphans)
    known_parents = {None} | set(all_cats.keys())
    for parent_key in categories_tree:
        if parent_key not in known_parents:
            lines.append(f"  [unknown parent: {parent_key}]")
            for child in sorted(categories_tree[parent_key]):
                lines.append(f"    {child}")

    # --- Other tables ---
    for table, values in results.items():
        lines.append("")
        lines.append(f"=== {table.upper()} ({len(values)} values) ===")
        joined = ", ".join(values)
        lines.append(fill(joined, width=72))

    lines.append("")

    OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Exported {len(results)} tables to {OUTPUT_PATH}")
    for table, values in results.items():
        print(f"  {table}: {len(values)} values")


if __name__ == "__main__":
    export_attributes()
