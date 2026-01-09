"""
Tests Unitaires pour VintedJobService

Tests de la logique de gestion des jobs Vinted sans requêtes réelles.
Utilise des mocks pour la base de données.

Author: Claude
Date: 2025-12-19
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch, PropertyMock
import pytest

from models.vinted.vinted_action_type import VintedActionType
from models.user.marketplace_job import MarketplaceJob, JobStatus
from models.user.vinted_job_stats import VintedJobStats
# REMOVED (2026-01-09): PluginTask system replaced by WebSocket communication
# from models.user.plugin_task import PluginTask, TaskStatus


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_db():
    """Mock de la session SQLAlchemy."""
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.filter.return_value.all.return_value = []
    db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
    db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
    db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
    db.query.return_value.filter.return_value.count.return_value = 0
    return db


@pytest.fixture
def mock_action_type_publish():
    """Mock d'un VintedActionType pour publication."""
    action = MagicMock(spec=VintedActionType)
    action.id = 1
    action.code = "publish"
    action.name = "Publish product"
    action.priority = 3
    action.is_batch = False
    action.rate_limit_ms = 2500
    action.max_retries = 3
    action.timeout_seconds = 120
    return action


@pytest.fixture
def mock_action_type_sync():
    """Mock d'un VintedActionType pour sync."""
    action = MagicMock(spec=VintedActionType)
    action.id = 2
    action.code = "sync"
    action.name = "Sync products"
    action.priority = 4
    action.is_batch = True
    action.rate_limit_ms = 1500
    action.max_retries = 3
    action.timeout_seconds = 300
    return action


@pytest.fixture
def mock_action_type_message():
    """Mock d'un VintedActionType pour messages (priorité critique)."""
    action = MagicMock(spec=VintedActionType)
    action.id = 3
    action.code = "message"
    action.name = "Respond to message"
    action.priority = 1
    action.is_batch = False
    action.rate_limit_ms = 1000
    action.max_retries = 3
    action.timeout_seconds = 30
    return action


@pytest.fixture
def sample_job():
    """Crée un job mock pour les tests."""
    job = MagicMock(spec=MarketplaceJob)
    job.id = 1
    job.batch_id = None
    job.action_type_id = 1
    job.product_id = 100
    job.status = JobStatus.PENDING
    job.priority = 3
    job.error_message = None
    job.retry_count = 0
    job.started_at = None
    job.completed_at = None
    job.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    job.created_at = datetime.now(timezone.utc)
    return job


# =============================================================================
# TESTS - JOB CREATION
# =============================================================================


class TestJobCreation:
    """Tests pour la création de jobs."""

    def test_create_job_success(self, mock_db, mock_action_type_publish):
        """Test création d'un job avec succès."""
        from services.vinted.vinted_job_service import VintedJobService

        # Setup mock
        mock_db.query.return_value.filter.return_value.first.return_value = mock_action_type_publish

        service = VintedJobService(mock_db)
        job = service.create_job(
            action_code="publish",
            product_id=123,
        )

        # Vérifications
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()

        # Vérifier que le job a les bonnes propriétés
        added_job = mock_db.add.call_args[0][0]
        assert added_job.action_type_id == 1
        assert added_job.product_id == 123
        assert added_job.status == JobStatus.PENDING
        assert added_job.priority == 3  # Hérité de l'action type
        assert added_job.expires_at is not None

    def test_create_job_with_priority_override(self, mock_db, mock_action_type_publish):
        """Test création d'un job avec priorité personnalisée."""
        from services.vinted.vinted_job_service import VintedJobService

        mock_db.query.return_value.filter.return_value.first.return_value = mock_action_type_publish

        service = VintedJobService(mock_db)
        service.create_job(
            action_code="publish",
            product_id=123,
            priority=1,  # Override priorité critique
        )

        added_job = mock_db.add.call_args[0][0]
        assert added_job.priority == 1

    def test_create_job_invalid_action_code(self, mock_db):
        """Test création d'un job avec code action invalide."""
        from services.vinted.vinted_job_service import VintedJobService

        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = VintedJobService(mock_db)

        with pytest.raises(ValueError, match="Invalid action code"):
            service.create_job(action_code="invalid_action")

    def test_create_batch_jobs(self, mock_db, mock_action_type_publish):
        """Test création de plusieurs jobs en batch."""
        from services.vinted.vinted_job_service import VintedJobService

        mock_db.query.return_value.filter.return_value.first.return_value = mock_action_type_publish

        service = VintedJobService(mock_db)
        batch_id, jobs = service.create_batch_jobs(
            action_code="publish",
            product_ids=[1, 2, 3, 4, 5],
        )

        # Vérifications
        assert batch_id.startswith("publish_")
        assert mock_db.add.call_count == 5
        mock_db.commit.assert_called_once()

        # Vérifier que chaque job a le même batch_id
        for call in mock_db.add.call_args_list:
            job = call[0][0]
            assert job.batch_id == batch_id


# =============================================================================
# TESTS - JOB STATUS MANAGEMENT
# =============================================================================


class TestJobStatusManagement:
    """Tests pour la gestion des statuts de jobs."""

    def test_start_job(self, mock_db, sample_job):
        """Test démarrage d'un job."""
        from services.vinted.vinted_job_service import VintedJobService

        mock_db.query.return_value.filter.return_value.first.return_value = sample_job

        service = VintedJobService(mock_db)
        result = service.start_job(job_id=1)

        assert result is not None
        assert sample_job.status == JobStatus.RUNNING
        assert sample_job.started_at is not None
        mock_db.commit.assert_called_once()

    def test_complete_job(self, mock_db, sample_job, mock_action_type_publish):
        """Test complétion réussie d'un job."""
        from services.vinted.vinted_job_service import VintedJobService

        sample_job.started_at = datetime.now(timezone.utc) - timedelta(seconds=30)

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == MarketplaceJob:
                mock_query.filter.return_value.first.return_value = sample_job
            elif model == VintedJobStats:
                mock_query.filter.return_value.first.return_value = None
            elif model == VintedActionType:
                mock_query.filter.return_value.first.return_value = mock_action_type_publish
            return mock_query

        mock_db.query.side_effect = query_side_effect

        service = VintedJobService(mock_db)
        result = service.complete_job(job_id=1)

        assert result is not None
        assert sample_job.status == JobStatus.COMPLETED
        assert sample_job.completed_at is not None

    def test_fail_job(self, mock_db, sample_job, mock_action_type_publish):
        """Test échec d'un job."""
        from services.vinted.vinted_job_service import VintedJobService

        sample_job.started_at = datetime.now(timezone.utc)

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == MarketplaceJob:
                mock_query.filter.return_value.first.return_value = sample_job
            elif model == VintedJobStats:
                mock_query.filter.return_value.first.return_value = None
            elif model == VintedActionType:
                mock_query.filter.return_value.first.return_value = mock_action_type_publish
            return mock_query

        mock_db.query.side_effect = query_side_effect

        service = VintedJobService(mock_db)
        result = service.fail_job(job_id=1, error_message="Upload failed")

        assert result is not None
        assert sample_job.status == JobStatus.FAILED
        assert sample_job.error_message == "Upload failed"
        assert sample_job.completed_at is not None

    def test_pause_job(self, mock_db, sample_job):
        """Test mise en pause d'un job."""
        from services.vinted.vinted_job_service import VintedJobService

        sample_job.status = JobStatus.RUNNING
        mock_db.query.return_value.filter.return_value.first.return_value = sample_job

        service = VintedJobService(mock_db)
        result = service.pause_job(job_id=1)

        assert result is not None
        assert sample_job.status == JobStatus.PAUSED
        mock_db.commit.assert_called()

    def test_pause_job_already_completed(self, mock_db, sample_job):
        """Test pause d'un job déjà terminé (doit échouer)."""
        from services.vinted.vinted_job_service import VintedJobService

        sample_job.status = JobStatus.COMPLETED
        mock_db.query.return_value.filter.return_value.first.return_value = sample_job

        service = VintedJobService(mock_db)
        result = service.pause_job(job_id=1)

        assert result is None  # Ne peut pas pause un job terminé

    def test_resume_job(self, mock_db, sample_job):
        """Test reprise d'un job en pause."""
        from services.vinted.vinted_job_service import VintedJobService

        sample_job.status = JobStatus.PAUSED
        old_expires = sample_job.expires_at
        mock_db.query.return_value.filter.return_value.first.return_value = sample_job

        service = VintedJobService(mock_db)
        result = service.resume_job(job_id=1)

        assert result is not None
        assert sample_job.status == JobStatus.PENDING
        # L'expiration doit être réinitialisée
        assert sample_job.expires_at != old_expires
        mock_db.commit.assert_called()

    def test_cancel_job(self, mock_db, sample_job):
        """Test annulation d'un job."""
        from services.vinted.vinted_job_service import VintedJobService

        sample_job.status = JobStatus.PENDING
        # Mock is_terminal property to return False (job can be cancelled)
        type(sample_job).is_terminal = PropertyMock(return_value=False)

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == MarketplaceJob:
                mock_query.filter.return_value.first.return_value = sample_job
            elif model == PluginTask:
                mock_query.filter.return_value.all.return_value = []
            return mock_query

        mock_db.query.side_effect = query_side_effect

        service = VintedJobService(mock_db)
        result = service.cancel_job(job_id=1)

        assert result is not None
        assert sample_job.status == JobStatus.CANCELLED
        assert sample_job.completed_at is not None


# =============================================================================
# TESTS - RETRY LOGIC
# =============================================================================


class TestRetryLogic:
    """Tests pour la logique de retry."""

    def test_increment_retry_can_retry(self, mock_db, sample_job, mock_action_type_publish):
        """Test increment retry quand on peut encore réessayer."""
        from services.vinted.vinted_job_service import VintedJobService

        sample_job.retry_count = 0

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == MarketplaceJob:
                mock_query.filter.return_value.first.return_value = sample_job
            elif model == VintedActionType:
                mock_query.filter.return_value.first.return_value = mock_action_type_publish
            return mock_query

        mock_db.query.side_effect = query_side_effect

        service = VintedJobService(mock_db)
        job, can_retry = service.increment_retry(job_id=1)

        assert job is not None
        assert can_retry is True
        assert sample_job.retry_count == 1
        assert sample_job.status == JobStatus.PENDING  # Pas changé

    def test_increment_retry_max_reached(self, mock_db, sample_job, mock_action_type_publish):
        """Test increment retry quand max atteint."""
        from services.vinted.vinted_job_service import VintedJobService

        sample_job.retry_count = 2  # Déjà 2 essais, max = 3

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == MarketplaceJob:
                mock_query.filter.return_value.first.return_value = sample_job
            elif model == VintedActionType:
                mock_query.filter.return_value.first.return_value = mock_action_type_publish
            return mock_query

        mock_db.query.side_effect = query_side_effect

        service = VintedJobService(mock_db)
        job, can_retry = service.increment_retry(job_id=1)

        assert job is not None
        assert can_retry is False
        assert sample_job.retry_count == 3
        assert sample_job.status == JobStatus.FAILED
        assert "Max retries" in sample_job.error_message


# =============================================================================
# TESTS - PRIORITY
# =============================================================================


class TestPriority:
    """Tests pour la gestion des priorités."""

    def test_get_next_pending_job_by_priority(self, mock_db):
        """Test récupération du prochain job par priorité."""
        from services.vinted.vinted_job_service import VintedJobService

        # Créer des jobs avec différentes priorités
        job_low = MagicMock(spec=MarketplaceJob)
        job_low.id = 1
        job_low.priority = 4
        job_low.status = JobStatus.PENDING

        job_high = MagicMock(spec=MarketplaceJob)
        job_high.id = 2
        job_high.priority = 1
        job_high.status = JobStatus.PENDING

        # Le job avec priorité 1 doit être retourné en premier
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = job_high

        service = VintedJobService(mock_db)
        next_job = service.get_next_pending_job()

        assert next_job is not None
        assert next_job.id == 2
        assert next_job.priority == 1

    def test_message_priority_is_critical(self, mock_action_type_message):
        """Test que les messages ont une priorité critique (1)."""
        assert mock_action_type_message.priority == 1
        assert mock_action_type_message.code == "message"


# =============================================================================
# TESTS - BATCH OPERATIONS
# =============================================================================


class TestBatchOperations:
    """Tests pour les opérations batch."""

    def test_get_batch_summary(self, mock_db):
        """Test récupération du résumé d'un batch."""
        from services.vinted.vinted_job_service import VintedJobService

        # Créer des jobs mockés
        jobs = []
        for i, status in enumerate([
            JobStatus.COMPLETED, JobStatus.COMPLETED, JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.PENDING, JobStatus.PENDING
        ]):
            job = MagicMock(spec=MarketplaceJob)
            job.id = i + 1
            job.batch_id = "batch_123"
            job.status = status
            jobs.append(job)

        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = jobs

        service = VintedJobService(mock_db)
        summary = service.get_batch_summary("batch_123")

        assert summary["batch_id"] == "batch_123"
        assert summary["total"] == 6
        assert summary["completed"] == 3
        assert summary["failed"] == 1
        assert summary["pending"] == 2
        assert summary["progress_percent"] == 50.0

    def test_get_batch_summary_empty(self, mock_db):
        """Test résumé d'un batch inexistant."""
        from services.vinted.vinted_job_service import VintedJobService

        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        service = VintedJobService(mock_db)
        summary = service.get_batch_summary("nonexistent")

        assert summary["total"] == 0


# =============================================================================
# TESTS - EXPIRATION
# =============================================================================


class TestExpiration:
    """Tests pour l'expiration des jobs."""

    def test_expire_old_jobs(self, mock_db):
        """Test expiration des jobs anciens."""
        from services.vinted.vinted_job_service import VintedJobService

        # Créer des jobs expirés
        expired_jobs = []
        for i in range(3):
            job = MagicMock(spec=MarketplaceJob)
            job.id = i + 1
            job.status = JobStatus.PENDING
            job.expires_at = datetime.now(timezone.utc) - timedelta(hours=2)
            expired_jobs.append(job)

        mock_db.query.return_value.filter.return_value.all.return_value = expired_jobs

        service = VintedJobService(mock_db)
        count = service.expire_old_jobs()

        assert count == 3
        for job in expired_jobs:
            assert job.status == JobStatus.EXPIRED
            assert job.completed_at is not None
            assert "expired" in job.error_message.lower()

        mock_db.commit.assert_called()

    def test_expire_old_jobs_none_expired(self, mock_db):
        """Test quand aucun job n'est expiré."""
        from services.vinted.vinted_job_service import VintedJobService

        mock_db.query.return_value.filter.return_value.all.return_value = []

        service = VintedJobService(mock_db)
        count = service.expire_old_jobs()

        assert count == 0


# =============================================================================
# TESTS - INTERRUPTED JOBS
# =============================================================================


class TestInterruptedJobs:
    """Tests pour les jobs interrompus."""

    def test_get_interrupted_jobs(self, mock_db):
        """Test récupération des jobs interrompus."""
        from services.vinted.vinted_job_service import VintedJobService

        # Créer des jobs en cours/pause
        interrupted_jobs = []
        for i, status in enumerate([JobStatus.RUNNING, JobStatus.PAUSED]):
            job = MagicMock(spec=MarketplaceJob)
            job.id = i + 1
            job.status = status
            job.expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
            interrupted_jobs.append(job)

        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = interrupted_jobs

        service = VintedJobService(mock_db)
        jobs = service.get_interrupted_jobs()

        assert len(jobs) == 2


# =============================================================================
# TESTS - TASK MANAGEMENT (REMOVED 2026-01-09)
# =============================================================================

# REMOVED (2026-01-09): TestTaskManagement class
# This class tested the PluginTask system which has been replaced by WebSocket communication.
# Tests included:
# - test_cancel_job_tasks: Tested cancelling plugin tasks when a job is cancelled
# - test_get_job_progress: Tested getting job progress from plugin tasks
#
# These tests are no longer relevant as VintedJob now communicates directly via WebSocket
# without creating intermediate PluginTask records in the database.


# =============================================================================
# TESTS - ACTION TYPE CACHING
# =============================================================================


class TestActionTypeCaching:
    """Tests pour le cache des types d'actions."""

    def test_action_type_is_cached(self, mock_db, mock_action_type_publish):
        """Test que les types d'action sont mis en cache."""
        from services.vinted.vinted_job_service import VintedJobService

        mock_db.query.return_value.filter.return_value.first.return_value = mock_action_type_publish

        service = VintedJobService(mock_db)

        # Premier appel - doit faire une requête DB
        result1 = service.get_action_type("publish")
        assert result1 is not None

        # Deuxième appel - doit utiliser le cache
        result2 = service.get_action_type("publish")
        assert result2 is not None

        # La DB ne doit être appelée qu'une fois
        assert mock_db.query.call_count == 1


# =============================================================================
# TESTS - STATISTICS
# =============================================================================


class TestStatistics:
    """Tests pour les statistiques via VintedJobStatsService."""

    def test_update_job_stats_creates_new(self, mock_db, sample_job, mock_action_type_publish):
        """Test création de stats quand elles n'existent pas."""
        from services.vinted.vinted_job_stats_service import VintedJobStatsService

        sample_job.started_at = datetime.now(timezone.utc) - timedelta(seconds=5)
        sample_job.completed_at = datetime.now(timezone.utc)

        mock_db.query.return_value.filter.return_value.first.return_value = None

        VintedJobStatsService.update_job_stats(mock_db, sample_job, success=True)

        # Vérifier qu'un nouveau stats a été ajouté
        mock_db.add.assert_called()
        added_stats = mock_db.add.call_args[0][0]
        assert added_stats.total_jobs == 1
        assert added_stats.success_count == 1
        assert added_stats.failure_count == 0

    def test_update_job_stats_increments_existing(self, mock_db, sample_job, mock_action_type_publish):
        """Test incrémentation de stats existantes."""
        from services.vinted.vinted_job_stats_service import VintedJobStatsService

        sample_job.started_at = datetime.now(timezone.utc) - timedelta(seconds=5)
        sample_job.completed_at = datetime.now(timezone.utc)

        # Stats existantes
        existing_stats = MagicMock(spec=VintedJobStats)
        existing_stats.total_jobs = 10
        existing_stats.success_count = 8
        existing_stats.failure_count = 2
        existing_stats.avg_duration_ms = 5000

        mock_db.query.return_value.filter.return_value.first.return_value = existing_stats

        VintedJobStatsService.update_job_stats(mock_db, sample_job, success=False)

        assert existing_stats.total_jobs == 11
        assert existing_stats.success_count == 8
        assert existing_stats.failure_count == 3
