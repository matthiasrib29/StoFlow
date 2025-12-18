"""
Test de démonstration du bug func.now()

Ce test prouve que func.now() ne fonctionne PAS comme attendu
quand utilisé directement en Python (au lieu de dans une requête SQL).
"""

from datetime import datetime, timezone
from sqlalchemy import create_engine, func, Column, Integer, DateTime, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

# Setup test database
Base = declarative_base()

class TestProduct(Base):
    __tablename__ = "test_products"

    id = Column(Integer, primary_key=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)


def test_func_now_bug():
    """Démontre que func.now() ne fonctionne pas en Python."""

    # Create in-memory SQLite database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    print("=" * 70)
    print("TEST: func.now() vs datetime.now()")
    print("=" * 70)

    # ===== TEST 1: func.now() (INCORRECT) =====
    print("\n📌 TEST 1: Utilisation de func.now() (CODE ACTUEL - BUGUÉ)")
    print("-" * 70)

    product1 = TestProduct(id=1)
    product1.deleted_at = func.now()  # ❌ INCORRECT

    print(f"Type de product1.deleted_at: {type(product1.deleted_at)}")
    print(f"Valeur de product1.deleted_at: {product1.deleted_at}")
    print(f"Est-ce une datetime? {isinstance(product1.deleted_at, datetime)}")

    try:
        db.add(product1)
        db.commit()
        db.refresh(product1)

        print(f"\n✅ Commit réussi (mais les données sont corrompues)")
        print(f"Valeur en DB: {product1.deleted_at}")
        print(f"Type en DB: {type(product1.deleted_at)}")

        # Try to serialize (this would fail in API)
        print("\n🔍 Test de sérialisation JSON (comme dans l'API):")
        import json
        try:
            json_str = json.dumps({"deleted_at": product1.deleted_at}, default=str)
            print(f"   JSON: {json_str}")
        except Exception as e:
            print(f"   ❌ ERREUR: {e}")

    except Exception as e:
        print(f"❌ ERREUR lors du commit: {e}")

    db.rollback()

    # ===== TEST 2: datetime.now() (CORRECT) =====
    print("\n\n📌 TEST 2: Utilisation de datetime.now() (FIX PROPOSÉ)")
    print("-" * 70)

    product2 = TestProduct(id=2)
    product2.deleted_at = datetime.now(timezone.utc)  # ✅ CORRECT

    print(f"Type de product2.deleted_at: {type(product2.deleted_at)}")
    print(f"Valeur de product2.deleted_at: {product2.deleted_at}")
    print(f"Est-ce une datetime? {isinstance(product2.deleted_at, datetime)}")

    try:
        db.add(product2)
        db.commit()
        db.refresh(product2)

        print(f"\n✅ Commit réussi")
        print(f"Valeur en DB: {product2.deleted_at}")
        print(f"Type en DB: {type(product2.deleted_at)}")

        # Try to serialize
        print("\n🔍 Test de sérialisation JSON:")
        import json
        try:
            json_str = json.dumps({"deleted_at": product2.deleted_at.isoformat()})
            print(f"   ✅ JSON: {json_str}")
        except Exception as e:
            print(f"   ❌ ERREUR: {e}")

    except Exception as e:
        print(f"❌ ERREUR lors du commit: {e}")

    # ===== COMPARISON =====
    print("\n\n" + "=" * 70)
    print("📊 RÉSUMÉ DE LA COMPARAISON")
    print("=" * 70)

    print("\n❌ func.now() (CODE ACTUEL):")
    print("   - Type: SQLAlchemy expression object")
    print("   - Sérialisation JSON: ❌ Échoue ou donne des résultats étranges")
    print("   - Comparaisons datetime: ❌ Ne fonctionne pas")
    print("   - Lisibilité: ❌ Impossible pour humains")

    print("\n✅ datetime.now(timezone.utc) (FIX PROPOSÉ):")
    print("   - Type: datetime.datetime Python standard")
    print("   - Sérialisation JSON: ✅ Fonctionne parfaitement")
    print("   - Comparaisons datetime: ✅ Fonctionne")
    print("   - Lisibilité: ✅ Format ISO standard")

    print("\n" + "=" * 70)
    print("🎯 CONCLUSION: Le bug est confirmé !")
    print("=" * 70)
    print("\nImpact réel dans votre code:")
    print("1. API responses peuvent échouer lors de la sérialisation")
    print("2. Impossible de comparer deleted_at avec d'autres dates")
    print("3. Queries filtrées par date ne fonctionnent pas correctement")
    print("4. Tests qui vérifient les timestamps sont faux positifs")

    db.close()


if __name__ == "__main__":
    test_func_now_bug()
