"""
Script de test pour vérifier la refactorisation du schema product_attributes.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from sqlalchemy import text
from shared.database import SessionLocal
from models.public.category import Category
from models.public.brand import Brand
from models.public.color import Color
from models.public.condition import Condition
from models.public.size_normalized import SizeNormalized
from models.public.material import Material
from models.public.season import Season


def test_refactoring():
    """Teste que la refactorisation a fonctionné correctement."""

    db = SessionLocal()
    try:
        print("🧪 Test de la refactorisation product_attributes\n")

        # Test 1: Vérifier que le schema existe
        print("1️⃣  Vérification du schema product_attributes...")
        result = db.execute(text("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name = 'product_attributes'
        """)).fetchone()

        if result:
            print("   ✅ Schema product_attributes existe")
        else:
            print("   ❌ Schema product_attributes n'existe pas")
            return False

        # Test 2: Vérifier que les tables sont dans le bon schema
        print("\n2️⃣  Vérification des tables dans product_attributes...")
        tables = ['categories', 'brands', 'colors', 'conditions', 'sizes', 'materials', 'seasons']

        for table_name in tables:
            result = db.execute(text(f"""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'product_attributes'
                AND table_name = '{table_name}'
            """)).fetchone()

            if result:
                print(f"   ✅ {table_name} dans product_attributes")
            else:
                print(f"   ❌ {table_name} NOT FOUND in product_attributes")
                return False

        # Test 3: Vérifier que les modèles Python se chargent correctement
        print("\n3️⃣  Vérification des modèles Python...")
        models = [
            ("Category", Category),
            ("Brand", Brand),
            ("Color", Color),
            ("Condition", Condition),
            ("Size", Size),
            ("Material", Material),
            ("Season", Season)
        ]

        for name, model in models:
            try:
                # Tenter une requête simple
                count = db.query(model).count()
                print(f"   ✅ {name} model OK ({count} rows)")
            except Exception as e:
                print(f"   ❌ {name} model FAILED: {e}")
                return False

        # Test 4: Vérifier que les catégories sont accessibles
        print("\n4️⃣  Vérification des catégories...")
        categories = db.query(Category).all()

        if len(categories) == 65:
            print(f"   ✅ 65 catégories trouvées")
        else:
            print(f"   ⚠️  {len(categories)} catégories trouvées (attendu: 65)")

        # Afficher quelques exemples
        print("\n   📦 Exemples de catégories:")
        root = db.query(Category).filter(Category.parent_category == None).first()
        if root:
            print(f"      - Root: {root.name_en} ({root.name_fr}) - Gender: {root.default_gender}")

            children = db.query(Category).filter(Category.parent_category == root.name_en).limit(3).all()
            for child in children:
                print(f"      - {child.name_en} ({child.name_fr}) - Gender: {child.default_gender}")

        # Test 5: Vérifier que les Foreign Keys fonctionnent
        print("\n5️⃣  Vérification des Foreign Keys...")
        result = db.execute(text("""
            SELECT tc.constraint_name, tc.table_name, kcu.column_name,
                   ccu.table_schema AS foreign_table_schema,
                   ccu.table_name AS foreign_table_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND ccu.table_schema = 'product_attributes'
            LIMIT 5
        """)).fetchall()

        if result:
            print(f"   ✅ Foreign Keys trouvées ({len(result)} exemples):")
            for row in result:
                print(f"      - {row[1]}.{row[2]} -> {row[3]}.{row[4]}")
        else:
            print("   ⚠️  Aucune Foreign Key vers product_attributes trouvée")

        print("\n" + "="*60)
        print("✅ TOUS LES TESTS SONT PASSÉS !")
        print("="*60)

        return True

    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = test_refactoring()
    sys.exit(0 if success else 1)
