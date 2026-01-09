"""
Tests Unitaires: Création User et Schema

Vérifie que lors de la création d'un user:
1. Le user est créé dans public.users
2. Le schema user_X est créé
3. Toutes les tables sont créées dans le schema user_X
4. Les tables ont la bonne structure

Author: Claude
Date: 2025-12-08
"""
import os
import pytest
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import Session

# Utiliser la vraie DB pour ces tests (pas de mock)
from shared.config import settings
from shared.database import get_db
from models.public.user import User, UserRole, AccountType
from services.auth_service import AuthService
from services.user_schema_service import UserSchemaService


# Tables attendues dans chaque schema user_X
# Note (2026-01-09): plugin_tasks removed - replaced by WebSocket communication
EXPECTED_USER_TABLES = [
    "ai_generation_logs",
    "product_images",
    "products",
    "publication_history",
    "vinted_products"
]


class TestUserCreation:
    """Tests de création d'utilisateur et de son schema."""

    @pytest.fixture(scope="function")
    def test_user_email(self):
        """Email unique pour le test."""
        import uuid
        return f"test-user-{uuid.uuid4()}@stoflow.com"

    @pytest.fixture(scope="function")
    def db_connection(self):
        """Connexion directe à PostgreSQL pour vérifier les schemas."""
        # Utiliser la database_url des settings
        engine = create_engine(settings.database_url)
        conn = engine.connect()
        yield conn
        conn.close()

    def test_user_creation_creates_schema(self, test_user_email, db_connection):
        """
        Test: Créer un user doit créer son schema user_X.

        Steps:
        1. Créer un user
        2. Vérifier que le schema user_X existe
        3. Cleanup
        """
        db = next(get_db())

        # 1. Créer le user
        user = User(
            email=test_user_email,
            hashed_password=AuthService.hash_password("Test123456!"),
            full_name="Test User Schema",
            role=UserRole.USER,
            account_type=AccountType.INDIVIDUAL
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        user_id = user.id
        expected_schema = f"user_{user_id}"

        # 1b. Créer le schema pour ce user (simule le comportement de /api/auth/register)
        UserSchemaService.create_user_schema(db, user_id)

        try:
            # 2. Vérifier que le schema existe
            result = db_connection.execute(text(f"""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.schemata
                    WHERE schema_name = '{expected_schema}'
                )
            """))
            schema_exists = result.scalar()

            assert schema_exists, f"Schema {expected_schema} devrait exister après création du user"

        finally:
            # Cleanup
            db.delete(user)
            db.commit()
            # Supprimer le schema
            db_connection.execute(text(f"DROP SCHEMA IF EXISTS {expected_schema} CASCADE"))
            db_connection.commit()

    def test_user_schema_contains_all_tables(self, test_user_email, db_connection):
        """
        Test: Le schema user_X doit contenir toutes les tables requises.

        Tables attendues:
        - ai_generation_logs
        - product_images
        - products
        - publication_history
        - vinted_products

        Note: plugin_tasks removed (2026-01-09) - replaced by WebSocket
        """
        db = next(get_db())

        # Créer le user
        user = User(
            email=test_user_email,
            hashed_password=AuthService.hash_password("Test123456!"),
            full_name="Test User Tables",
            role=UserRole.USER,
            account_type=AccountType.INDIVIDUAL
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        user_id = user.id
        expected_schema = f"user_{user_id}"

        # Créer le schema pour ce user
        UserSchemaService.create_user_schema(db, user_id)

        try:
            # Vérifier chaque table
            result = db_connection.execute(text(f"""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = '{expected_schema}'
                ORDER BY table_name
            """))

            actual_tables = [row[0] for row in result.fetchall()]

            # Vérifier que toutes les tables attendues sont présentes
            for table in EXPECTED_USER_TABLES:
                assert table in actual_tables, \
                    f"Table {table} manquante dans schema {expected_schema}. Tables trouvées: {actual_tables}"

            # Vérifier qu'on a exactement 5 tables
            assert len(actual_tables) == 5, \
                f"Devrait avoir 5 tables, trouvé {len(actual_tables)}: {actual_tables}"

        finally:
            # Cleanup
            db.delete(user)
            db.commit()
            db_connection.execute(text(f"DROP SCHEMA IF EXISTS {expected_schema} CASCADE"))
            db_connection.commit()

    def test_products_table_structure(self, test_user_email, db_connection):
        """
        Test: La table products doit avoir la structure correcte.

        Colonnes essentielles:
        - id, sku, title, description, price
        - category, brand, condition
        - status, stock_quantity
        - created_at, updated_at
        """
        db = next(get_db())

        # Créer le user
        user = User(
            email=test_user_email,
            hashed_password=AuthService.hash_password("Test123456!"),
            full_name="Test Products Structure",
            role=UserRole.USER,
            account_type=AccountType.INDIVIDUAL
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        user_id = user.id
        expected_schema = f"user_{user_id}"

        # Créer le schema pour ce user
        UserSchemaService.create_user_schema(db, user_id)

        try:
            # Vérifier les colonnes de la table products
            result = db_connection.execute(text(f"""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = '{expected_schema}'
                AND table_name = 'products'
                ORDER BY ordinal_position
            """))

            columns = [row[0] for row in result.fetchall()]

            # Colonnes essentielles requises
            required_columns = [
                'id', 'sku', 'title', 'description', 'price',
                'category', 'brand', 'condition', 'status',
                'stock_quantity', 'created_at', 'updated_at'
            ]

            for col in required_columns:
                assert col in columns, \
                    f"Colonne {col} manquante dans products. Colonnes trouvées: {columns}"

        finally:
            # Cleanup
            db.delete(user)
            db.commit()
            db_connection.execute(text(f"DROP SCHEMA IF EXISTS {expected_schema} CASCADE"))
            db_connection.commit()

    # REMOVED (2026-01-09): test_plugin_tasks_table_exists
    # plugin_tasks table no longer exists - replaced by WebSocket communication
    # Old test verified plugin_tasks table structure, now obsolete

    def test_user_schema_isolation(self, db_connection):
        """
        Test: Chaque user doit avoir son propre schema isolé.

        Steps:
        1. Créer user_1
        2. Créer user_2
        3. Vérifier que user_1.schema_name != user_2.schema_name
        4. Vérifier que les deux schemas existent
        """
        db = next(get_db())

        import uuid

        # Créer user 1
        user1 = User(
            email=f"test-isolation-1-{uuid.uuid4()}@stoflow.com",
            hashed_password=AuthService.hash_password("Test123456!"),
            full_name="User 1",
            role=UserRole.USER,
            account_type=AccountType.INDIVIDUAL
        )
        db.add(user1)
        db.commit()
        db.refresh(user1)

        # Créer user 2
        user2 = User(
            email=f"test-isolation-2-{uuid.uuid4()}@stoflow.com",
            hashed_password=AuthService.hash_password("Test123456!"),
            full_name="User 2",
            role=UserRole.USER,
            account_type=AccountType.INDIVIDUAL
        )
        db.add(user2)
        db.commit()
        db.refresh(user2)

        schema1 = f"user_{user1.id}"
        schema2 = f"user_{user2.id}"

        # Créer les schemas pour les deux users
        UserSchemaService.create_user_schema(db, user1.id)
        UserSchemaService.create_user_schema(db, user2.id)

        try:
            # Vérifier que les schemas sont différents
            assert schema1 != schema2, "Les schemas doivent être différents"

            # Vérifier que les deux schemas existent
            result = db_connection.execute(text(f"""
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name IN ('{schema1}', '{schema2}')
            """))

            schemas = [row[0] for row in result.fetchall()]

            assert schema1 in schemas, f"Schema {schema1} devrait exister"
            assert schema2 in schemas, f"Schema {schema2} devrait exister"

        finally:
            # Cleanup
            db.delete(user1)
            db.delete(user2)
            db.commit()
            db_connection.execute(text(f"DROP SCHEMA IF EXISTS {schema1} CASCADE"))
            db_connection.execute(text(f"DROP SCHEMA IF EXISTS {schema2} CASCADE"))
            db_connection.commit()


class TestUserSchemaProperty:
    """Tests de la propriété schema_name."""

    def test_schema_name_format(self):
        """Test: user.schema_name doit retourner 'user_{id}'."""
        user = User(
            id=42,
            email="test@stoflow.com",
            hashed_password="hashed",
            full_name="Test",
            role=UserRole.USER,
            account_type=AccountType.INDIVIDUAL
        )

        assert user.schema_name == "user_42"

    def test_schema_name_dynamic(self):
        """Test: schema_name doit être dynamique selon l'ID."""
        user1 = User(id=1, email="u1@test.com", hashed_password="h", full_name="U1",
                     role=UserRole.USER, account_type=AccountType.INDIVIDUAL)
        user2 = User(id=999, email="u2@test.com", hashed_password="h", full_name="U2",
                     role=UserRole.USER, account_type=AccountType.INDIVIDUAL)

        assert user1.schema_name == "user_1"
        assert user2.schema_name == "user_999"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
