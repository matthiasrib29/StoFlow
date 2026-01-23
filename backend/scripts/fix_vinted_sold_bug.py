"""
Restauration apres bug _mark_missing_products_as_sold (2026-01-22).

Ce script restaure les produits qui ont ete marques comme "sold" par erreur
a cause d'un sync incomplet (seulement page 1/18 synchronisee).

Le probleme:
1. Le sync Vinted legacy n'a synchronise que 96 produits (page 1/18)
2. _mark_missing_products_as_sold() a marque ~1500 produits comme is_closed=true
3. _sync_existing_sold_status() a propage le statut SOLD aux Products Stoflow lies

Usage:
    cd backend
    source .venv/bin/activate
    python scripts/fix_vinted_sold_bug.py

Author: Claude
Date: 2026-01-22
"""

from shared.database import SessionLocal
from sqlalchemy import text


def restore_products():
    """Restore products affected by the bug."""
    db = SessionLocal()

    try:
        # Set user schema
        db.execute(text("SET search_path TO user_1, public"))

        # 1. Count before restoration
        before_vinted_closed = db.execute(text(
            "SELECT COUNT(*) FROM vinted_products WHERE is_closed = true"
        )).scalar()
        before_stoflow_sold = db.execute(text(
            "SELECT COUNT(*) FROM products WHERE status = 'SOLD'"
        )).scalar()

        print(f"=== AVANT RESTAURATION ===")
        print(f"VintedProducts is_closed=true: {before_vinted_closed}")
        print(f"Products status=SOLD: {before_stoflow_sold}")
        print()

        # 2. Restore VintedProducts
        # Target: products updated between 17:00 and 20:30 UTC on 2026-01-22
        result_vinted = db.execute(text("""
            UPDATE vinted_products
            SET is_closed = false,
                status = 'published',
                updated_at = NOW()
            WHERE is_closed = true
              AND updated_at >= '2026-01-22 17:00:00+00'
              AND updated_at <= '2026-01-22 20:30:00+00'
        """))
        print(f"VintedProducts restaures: {result_vinted.rowcount}")

        # 3. Restore Stoflow Products linked to affected VintedProducts
        result_stoflow = db.execute(text("""
            UPDATE products p
            SET status = 'PUBLISHED',
                updated_at = NOW()
            FROM vinted_products vp
            WHERE vp.product_id = p.id
              AND p.status = 'SOLD'
              AND vp.updated_at >= '2026-01-22 17:00:00+00'
              AND vp.updated_at <= '2026-01-22 20:30:00+00'
        """))
        print(f"Products Stoflow restaures: {result_stoflow.rowcount}")

        # 4. Commit
        db.commit()
        print()
        print("=== RESTAURATION TERMINEE ===")

        # 5. Count after restoration
        after_vinted_closed = db.execute(text(
            "SELECT COUNT(*) FROM vinted_products WHERE is_closed = true"
        )).scalar()
        after_stoflow_sold = db.execute(text(
            "SELECT COUNT(*) FROM products WHERE status = 'SOLD'"
        )).scalar()

        print(f"=== APRES RESTAURATION ===")
        print(f"VintedProducts is_closed=true: {after_vinted_closed}")
        print(f"Products status=SOLD: {after_stoflow_sold}")
        print()

        # Summary
        print("=== RESUME ===")
        print(f"VintedProducts restaures: {before_vinted_closed - after_vinted_closed}")
        print(f"Products Stoflow restaures: {before_stoflow_sold - after_stoflow_sold}")

    except Exception as e:
        db.rollback()
        print(f"ERREUR: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    restore_products()
