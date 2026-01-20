"""
Tests unitaires pour le model CeleryTaskRecord.

Ce model stocke les métadonnées des tâches Celery pour le monitoring
et le debugging.

Note: Ces tests utilisent des mocks pour éviter de déclencher les validations
SQLAlchemy qui nécessitent un contexte complet.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch


class TestCeleryTaskRecordTableConfig:
    """Tests pour la configuration de la table."""

    def test_table_name(self):
        """Test du nom de la table."""
        from models.public.celery_task_record import CeleryTaskRecord

        assert CeleryTaskRecord.__tablename__ == "celery_task_records"

    def test_schema_is_public(self):
        """Test que le schema est public."""
        from models.public.celery_task_record import CeleryTaskRecord

        assert CeleryTaskRecord.__table_args__["schema"] == "public"

    def test_primary_key_is_string(self):
        """Test que la PK est une string (UUID Celery)."""
        from models.public.celery_task_record import CeleryTaskRecord

        # Le champ id est de type String(36) pour stocker les UUID Celery
        id_column = CeleryTaskRecord.__table__.c.id
        assert str(id_column.type) == "VARCHAR(36)"

    def test_has_required_columns(self):
        """Test que toutes les colonnes requises existent."""
        from models.public.celery_task_record import CeleryTaskRecord

        table = CeleryTaskRecord.__table__

        # Colonnes requises
        required_columns = [
            "id", "name", "status", "user_id",
            "marketplace", "action_code", "product_id",
            "args", "kwargs", "result", "error", "traceback",
            "retries", "max_retries", "eta", "expires",
            "worker", "queue",
            "created_at", "started_at", "completed_at", "runtime_seconds"
        ]

        for col_name in required_columns:
            assert col_name in table.c, f"Column {col_name} missing"

    def test_user_id_foreign_key(self):
        """Test que user_id a une foreign key vers public.users."""
        from models.public.celery_task_record import CeleryTaskRecord

        user_id_col = CeleryTaskRecord.__table__.c.user_id

        # Vérifier qu'il y a une FK
        fks = list(user_id_col.foreign_keys)
        assert len(fks) == 1
        assert "public.users.id" in str(fks[0].target_fullname)

    def test_jsonb_columns(self):
        """Test que args, kwargs et result sont JSONB."""
        from models.public.celery_task_record import CeleryTaskRecord

        table = CeleryTaskRecord.__table__

        for col_name in ["args", "kwargs", "result"]:
            col = table.c[col_name]
            assert "JSONB" in str(col.type).upper()

    def test_nullable_columns(self):
        """Test des colonnes nullable."""
        from models.public.celery_task_record import CeleryTaskRecord

        table = CeleryTaskRecord.__table__

        # Colonnes qui peuvent être NULL
        nullable_columns = [
            "marketplace", "action_code", "product_id",
            "args", "kwargs", "result", "error", "traceback",
            "eta", "expires", "worker", "queue",
            "started_at", "completed_at", "runtime_seconds"
        ]

        for col_name in nullable_columns:
            col = table.c[col_name]
            assert col.nullable is True, f"Column {col_name} should be nullable"

    def test_not_nullable_columns(self):
        """Test des colonnes non-nullable."""
        from models.public.celery_task_record import CeleryTaskRecord

        table = CeleryTaskRecord.__table__

        # Colonnes qui ne peuvent pas être NULL
        not_nullable_columns = ["id", "name", "user_id", "created_at"]

        for col_name in not_nullable_columns:
            col = table.c[col_name]
            assert col.nullable is False, f"Column {col_name} should not be nullable"


class TestCeleryTaskRecordToDict:
    """Tests pour la méthode to_dict."""

    def test_to_dict_with_all_fields(self):
        """Test to_dict avec tous les champs remplis."""
        from models.public.celery_task_record import CeleryTaskRecord

        now = datetime.now(timezone.utc)

        # Créer un mock qui simule l'objet
        mock_task = MagicMock(spec=CeleryTaskRecord)
        mock_task.id = "task-123"
        mock_task.name = "tasks.marketplace_tasks.publish_product"
        mock_task.status = "SUCCESS"
        mock_task.marketplace = "vinted"
        mock_task.action_code = "publish"
        mock_task.product_id = 789
        mock_task.user_id = 1
        mock_task.result = {"job_id": 999}
        mock_task.error = None
        mock_task.retries = 1
        mock_task.max_retries = 3
        mock_task.worker = "worker1"
        mock_task.queue = "marketplace"
        mock_task.created_at = now
        mock_task.started_at = now
        mock_task.completed_at = now
        mock_task.runtime_seconds = 1.5

        # Appeler la vraie méthode to_dict
        result = CeleryTaskRecord.to_dict(mock_task)

        assert isinstance(result, dict)
        assert result["id"] == "task-123"
        assert result["name"] == "tasks.marketplace_tasks.publish_product"
        assert result["status"] == "SUCCESS"
        assert result["marketplace"] == "vinted"
        assert result["action_code"] == "publish"
        assert result["product_id"] == 789
        assert result["user_id"] == 1
        assert result["result"] == {"job_id": 999}
        assert result["retries"] == 1
        assert result["max_retries"] == 3
        assert result["worker"] == "worker1"
        assert result["queue"] == "marketplace"
        assert result["runtime_seconds"] == 1.5
        # Timestamps should be ISO format strings
        assert "created_at" in result
        assert "started_at" in result
        assert "completed_at" in result

    def test_to_dict_with_none_timestamps(self):
        """Test to_dict quand les timestamps sont None."""
        from models.public.celery_task_record import CeleryTaskRecord

        mock_task = MagicMock(spec=CeleryTaskRecord)
        mock_task.id = "task-123"
        mock_task.name = "test_task"
        mock_task.status = "PENDING"
        mock_task.marketplace = None
        mock_task.action_code = None
        mock_task.product_id = None
        mock_task.user_id = 1
        mock_task.result = None
        mock_task.error = None
        mock_task.retries = 0
        mock_task.max_retries = 3
        mock_task.worker = None
        mock_task.queue = None
        mock_task.created_at = datetime.now(timezone.utc)
        mock_task.started_at = None
        mock_task.completed_at = None
        mock_task.runtime_seconds = None

        result = CeleryTaskRecord.to_dict(mock_task)

        assert result["started_at"] is None
        assert result["completed_at"] is None
        assert result["marketplace"] is None


class TestCeleryTaskRecordRepr:
    """Tests pour __repr__."""

    def test_repr_format(self):
        """Test du format de __repr__."""
        from models.public.celery_task_record import CeleryTaskRecord

        mock_task = MagicMock(spec=CeleryTaskRecord)
        mock_task.id = "task-123"
        mock_task.name = "test_task"
        mock_task.status = "RUNNING"
        mock_task.user_id = 42

        # Appeler la vraie méthode __repr__
        repr_str = CeleryTaskRecord.__repr__(mock_task)

        assert "CeleryTaskRecord" in repr_str
        assert "task-123" in repr_str
        assert "test_task" in repr_str
        assert "RUNNING" in repr_str
        assert "42" in repr_str


class TestCeleryTaskRecordStatuses:
    """Tests pour les valeurs de status."""

    def test_valid_status_values(self):
        """Test que les status valides sont documentés."""
        # Les status Celery standards
        valid_statuses = ["PENDING", "STARTED", "SUCCESS", "FAILURE", "RETRY", "REVOKED"]

        # Vérifier dans la colonne comment
        from models.public.celery_task_record import CeleryTaskRecord

        status_col = CeleryTaskRecord.__table__.c.status

        # Vérifier que le comment mentionne les status
        if status_col.comment:
            for status in valid_statuses:
                assert status in status_col.comment, f"Status {status} not in column comment"


class TestCeleryTaskRecordDefaults:
    """Tests pour les valeurs par défaut."""

    def test_default_values_in_columns(self):
        """Test des valeurs par défaut définies dans les colonnes."""
        from models.public.celery_task_record import CeleryTaskRecord

        table = CeleryTaskRecord.__table__

        # status default = "PENDING"
        status_col = table.c.status
        assert status_col.default is not None
        assert status_col.default.arg == "PENDING"

        # retries default = 0
        retries_col = table.c.retries
        assert retries_col.default is not None
        assert retries_col.default.arg == 0

        # max_retries default = 3
        max_retries_col = table.c.max_retries
        assert max_retries_col.default is not None
        assert max_retries_col.default.arg == 3
