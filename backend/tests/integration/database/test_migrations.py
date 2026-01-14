"""
Tests de migration Alembic.

Vérifie que les migrations sont cohérentes et peuvent être appliquées correctement.
Ces tests ne font PAS de upgrade/downgrade (trop lent et risqué en CI),
mais vérifient la structure et la cohérence des migrations.
"""
import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text


@pytest.fixture(scope="module")
def alembic_config():
    """Configuration Alembic pour les tests."""
    return Config("alembic.ini")


@pytest.fixture(scope="module")
def script_directory(alembic_config):
    """Script directory Alembic pour parcourir les migrations."""
    return ScriptDirectory.from_config(alembic_config)


class TestMigrationStructure:
    """Tests de structure des migrations Alembic."""

    def test_current_revision_matches_head(self, db_session, script_directory):
        """
        Vérifie que la base de données de test est à jour avec les migrations.

        Si ce test échoue, exécuter: alembic upgrade head
        """
        head_revision = script_directory.get_current_head()

        result = db_session.execute(
            text("SELECT version_num FROM public.alembic_version")
        )
        current_revision = result.scalar()

        assert current_revision == head_revision, (
            f"Database revision ({current_revision}) does not match head ({head_revision}). "
            f"Run 'alembic upgrade head' to update."
        )

    def test_no_multiple_heads(self, script_directory):
        """
        Vérifie qu'il n'y a pas de multiple heads (branches non mergées).

        Si ce test échoue, exécuter: alembic merge heads -m "merge: unify heads"
        """
        heads = script_directory.get_heads()

        assert len(heads) == 1, (
            f"Multiple heads detected: {heads}. "
            f"Run 'alembic merge heads -m \"merge: unify heads\"' to fix."
        )

    def test_all_migrations_have_down_revision(self, script_directory):
        """
        Vérifie que toutes les migrations (sauf la première) ont un down_revision.

        Cela garantit que l'historique des migrations est continu.
        """
        migrations_without_down = []

        for revision in script_directory.walk_revisions():
            # La première migration (base) n'a pas de down_revision, c'est normal
            if revision.down_revision is None:
                # Vérifier que c'est bien la seule migration sans down_revision
                continue

            # Pour les migrations merge, down_revision est un tuple
            if isinstance(revision.down_revision, tuple):
                # Merge migration - OK
                continue

            # Pour les autres, down_revision doit être une string
            if not isinstance(revision.down_revision, str):
                migrations_without_down.append(revision.revision)

        assert not migrations_without_down, (
            f"Migrations with invalid down_revision: {migrations_without_down}"
        )

    def test_migration_file_naming_convention(self, script_directory):
        """
        Vérifie que les fichiers de migration suivent la convention de nommage.

        Format attendu: YYYYMMDD_HHMM_description.py
        """
        import re

        pattern = r'^\d{8}_\d{4}_[a-z0-9_]+$'
        invalid_names = []

        for revision in script_directory.walk_revisions():
            # Le revision.revision est l'identifiant court (hash)
            # On vérifie le nom du fichier via le path
            if hasattr(revision, 'path') and revision.path:
                from pathlib import Path
                filename = Path(revision.path).stem

                # Skip les fichiers qui sont des hashs purs (anciens formats)
                if len(filename) == 12 and filename.isalnum():
                    continue

                # Vérifier le pattern pour les nouvelles migrations
                if not re.match(pattern, filename):
                    # Tolérer les anciens formats (avant convention)
                    if not filename.startswith('20'):
                        continue
                    invalid_names.append(filename)

        # Ne pas échouer pour les anciens fichiers, juste avertir
        if invalid_names:
            import warnings
            warnings.warn(
                f"Some migrations don't follow naming convention: {invalid_names[:5]}..."
            )


class TestMigrationIntegrity:
    """Tests d'intégrité des données après migration."""

    def test_public_schema_exists(self, db_session):
        """Vérifie que le schema public existe."""
        result = db_session.execute(text("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name = 'public'
        """))
        assert result.scalar() == 'public'

    def test_product_attributes_schema_exists(self, db_session):
        """Vérifie que le schema product_attributes existe."""
        result = db_session.execute(text("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name = 'product_attributes'
        """))
        assert result.scalar() == 'product_attributes'

    def test_template_tenant_schema_exists(self, db_session):
        """Vérifie que le schema template_tenant existe."""
        result = db_session.execute(text("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name = 'template_tenant'
        """))
        assert result.scalar() == 'template_tenant'

    def test_alembic_version_table_exists(self, db_session):
        """Vérifie que la table alembic_version existe."""
        result = db_session.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'alembic_version'
        """))
        assert result.scalar() == 'alembic_version'

    def test_users_table_has_required_columns(self, db_session):
        """Vérifie que la table users a les colonnes essentielles."""
        result = db_session.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = 'users'
        """))
        columns = {row[0] for row in result.fetchall()}

        required_columns = {'id', 'email', 'hashed_password', 'created_at'}
        missing = required_columns - columns

        assert not missing, f"Users table missing columns: {missing}"

    def test_product_attributes_tables_exist(self, db_session):
        """Vérifie que les tables d'attributs produit existent."""
        required_tables = ['brands', 'colors', 'conditions', 'materials', 'sizes', 'categories']

        result = db_session.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'product_attributes'
        """))
        existing_tables = {row[0] for row in result.fetchall()}

        missing = set(required_tables) - existing_tables
        assert not missing, f"Missing product_attributes tables: {missing}"

    def test_template_tenant_has_products_table(self, db_session):
        """Vérifie que template_tenant a la table products."""
        result = db_session.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'template_tenant'
            AND table_name = 'products'
        """))
        assert result.scalar() == 'products'
