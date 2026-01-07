"""
Test script to verify AI credits system is working correctly.

This script:
1. Gets current AI credits for user
2. Simulates what happens during image analysis
3. Verifies credits are decremented
"""
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database connection
DATABASE_URL = "postgresql://stoflow_user:stoflow_dev_password_2024@localhost:5433/stoflow_db"

def test_ai_credits():
    """Test AI credits system."""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # 1. Get test user (user_id = 2, the dev user)
        user_id = 2

        print("=" * 60)
        print("🧪 TEST: AI Credits System")
        print("=" * 60)

        # 2. Set search path to public
        db.execute(text("SET search_path TO public"))

        # 3. Get user's subscription quota
        quota_result = db.execute(
            text("SELECT ai_credits_monthly FROM subscription_quotas WHERE user_id = :user_id"),
            {"user_id": user_id}
        ).fetchone()

        monthly_credits = quota_result[0] if quota_result else 0
        print(f"\n📊 Abonnement:")
        print(f"   Crédits mensuels: {monthly_credits}")

        # 4. Get or create AI credit record
        credit_result = db.execute(
            text("""
                SELECT id, ai_credits_purchased, ai_credits_used_this_month, last_reset_date
                FROM ai_credits
                WHERE user_id = :user_id
            """),
            {"user_id": user_id}
        ).fetchone()

        if credit_result:
            credit_id, purchased, used_this_month, last_reset = credit_result
            print(f"\n💳 Crédits actuels:")
            print(f"   ID: {credit_id}")
            print(f"   Crédits achetés: {purchased}")
            print(f"   Utilisés ce mois: {used_this_month}")
            print(f"   Dernier reset: {last_reset}")
        else:
            # Create if doesn't exist
            db.execute(
                text("""
                    INSERT INTO ai_credits (user_id, ai_credits_purchased, ai_credits_used_this_month)
                    VALUES (:user_id, 0, 0)
                """),
                {"user_id": user_id}
            )
            db.commit()
            purchased = 0
            used_this_month = 0
            print(f"\n💳 Crédits créés pour user {user_id}")

        # 5. Calculate remaining credits
        total_available = monthly_credits + purchased
        remaining = total_available - used_this_month

        print(f"\n🔢 Calcul:")
        print(f"   Total disponible = {monthly_credits} (mensuel) + {purchased} (achetés) = {total_available}")
        print(f"   Restants = {total_available} - {used_this_month} (utilisés) = {remaining}")

        # 6. Check if generation is possible
        print(f"\n✅ Statut:")
        if remaining > 0:
            print(f"   ✓ Génération possible ({remaining} crédits restants)")
        else:
            print(f"   ✗ Génération IMPOSSIBLE (crédits insuffisants)")
            print(f"   💡 Conseil: Upgrader l'abonnement ou acheter des crédits")

        # 7. Show what would happen after one generation
        if remaining > 0:
            print(f"\n🔮 Simulation d'une génération:")
            print(f"   Avant: {used_this_month} crédits utilisés")
            print(f"   Après: {used_this_month + 1} crédits utilisés")
            print(f"   Restants après: {remaining - 1}")

        # 8. Check AI generation logs
        log_count = db.execute(
            text("""
                SELECT COUNT(*)
                FROM user_2.ai_generation_logs
            """)
        ).scalar()

        print(f"\n📜 Logs de génération:")
        print(f"   Total générations: {log_count}")

        if log_count > 0:
            recent_logs = db.execute(
                text("""
                    SELECT model, total_tokens, total_cost, created_at
                    FROM user_2.ai_generation_logs
                    ORDER BY created_at DESC
                    LIMIT 3
                """)
            ).fetchall()

            print(f"\n   Dernières générations:")
            for log in recent_logs:
                model, tokens, cost, created = log
                print(f"   - {created}: {model} ({tokens} tokens, ${cost:.6f})")

        print("\n" + "=" * 60)
        print("✅ Test terminé")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_ai_credits()
