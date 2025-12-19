"""
Tests Unitaires pour VintedJobProcessor

Tests de l'orchestrateur de jobs avec la nouvelle architecture handlers.
Utilise des mocks pour les handlers et VintedJobService.

Author: Claude
Date: 2025-12-19
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from models.user.vinted_job import JobStatus, VintedJob
from services.vinted.vinted_job_processor import VintedJobProcessor


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_db():
    """Mock de la session SQLAlchemy."""
    return MagicMock()


@pytest.fixture
def mock_job():
    """Mock d'un VintedJob."""
    job = MagicMock(spec=VintedJob)
    job.id = 1
    job.product_id = 100
    job.action_type_id = 1
    job.status = JobStatus.PENDING
    job.priority = 3
    job.retry_count = 0
    job.batch_id = None
    job.result_data = None
    job.created_at = datetime.now(timezone.utc)
    return job


@pytest.fixture
def mock_action_type():
    """Mock d'un VintedActionType."""
    action = MagicMock()
    action.id = 1
    action.code = "publish"
    action.name = "Publish product"
    action.priority = 3
    action.max_retries = 3
    return action


# =============================================================================
# TESTS - PROCESSOR INITIALIZATION
# =============================================================================


class TestProcessorInit:
    """Tests pour l'initialisation du processeur."""

    def test_init_with_shop_id(self, mock_db):
        """Test initialisation avec shop_id."""
        processor = VintedJobProcessor(mock_db, shop_id=123)

        assert processor.db == mock_db
        assert processor.shop_id == 123
        assert processor.job_service is not None

    def test_init_without_shop_id(self, mock_db):
        """Test initialisation sans shop_id."""
        processor = VintedJobProcessor(mock_db)

        assert processor.shop_id is None


# =============================================================================
# TESTS - PROCESS NEXT JOB
# =============================================================================


class TestProcessNextJob:
    """Tests pour process_next_job."""

    @pytest.mark.asyncio
    async def test_no_pending_jobs(self, mock_db):
        """Test quand aucun job n'est en attente."""
        processor = VintedJobProcessor(mock_db, shop_id=123)

        with patch.object(processor.job_service, 'expire_old_jobs', return_value=0):
            with patch.object(processor.job_service, 'get_next_pending_job', return_value=None):
                result = await processor.process_next_job()

        assert result is None

    @pytest.mark.asyncio
    async def test_process_pending_job_success(self, mock_db, mock_job, mock_action_type):
        """Test traitement réussi d'un job via handler."""
        processor = VintedJobProcessor(mock_db, shop_id=123)

        # Mock du handler
        mock_handler_instance = MagicMock()
        mock_handler_instance.execute = AsyncMock(return_value={
            "success": True,
            "vinted_id": 12345,
            "product_id": 100
        })
        mock_handler_class = MagicMock(return_value=mock_handler_instance)

        with patch.object(processor.job_service, 'expire_old_jobs', return_value=0):
            with patch.object(processor.job_service, 'get_next_pending_job', return_value=mock_job):
                with patch.object(processor.job_service, 'get_action_type_by_id', return_value=mock_action_type):
                    with patch.object(processor.job_service, 'start_job', return_value=mock_job):
                        with patch.object(processor.job_service, 'complete_job', return_value=mock_job):
                            with patch.dict('services.vinted.jobs.HANDLERS', {'publish': mock_handler_class}):
                                result = await processor.process_next_job()

        assert result is not None
        assert result["success"] is True
        assert result["job_id"] == 1
        assert result["action"] == "publish"
        mock_handler_instance.execute.assert_called_once_with(mock_job)

    @pytest.mark.asyncio
    async def test_process_pending_job_failure(self, mock_db, mock_job, mock_action_type):
        """Test traitement échoué d'un job via handler."""
        processor = VintedJobProcessor(mock_db, shop_id=123)

        # Mock du handler qui échoue
        mock_handler_instance = MagicMock()
        mock_handler_instance.execute = AsyncMock(return_value={
            "success": False,
            "error": "Network error"
        })
        mock_handler_class = MagicMock(return_value=mock_handler_instance)

        # Mock pour retry
        updated_job = MagicMock(spec=VintedJob)
        updated_job.id = 1
        updated_job.retry_count = 1
        updated_job.status = JobStatus.PENDING

        with patch.object(processor.job_service, 'expire_old_jobs', return_value=0):
            with patch.object(processor.job_service, 'get_next_pending_job', return_value=mock_job):
                with patch.object(processor.job_service, 'get_action_type_by_id', return_value=mock_action_type):
                    with patch.object(processor.job_service, 'start_job', return_value=mock_job):
                        with patch.object(processor.job_service, 'increment_retry', return_value=(updated_job, True)):
                            with patch.dict('services.vinted.jobs.HANDLERS', {'publish': mock_handler_class}):
                                result = await processor.process_next_job()

        assert result is not None
        assert result["success"] is False
        assert result["will_retry"] is True


# =============================================================================
# TESTS - HANDLER DISPATCH
# =============================================================================


class TestHandlerDispatch:
    """Tests pour le dispatch vers les handlers."""

    @pytest.mark.asyncio
    async def test_dispatch_to_publish_handler(self, mock_db, mock_job, mock_action_type):
        """Test dispatch vers PublishJobHandler."""
        processor = VintedJobProcessor(mock_db, shop_id=123)

        mock_handler_instance = MagicMock()
        mock_handler_instance.execute = AsyncMock(return_value={"success": True})
        mock_handler_class = MagicMock(return_value=mock_handler_instance)

        with patch.object(processor.job_service, 'get_action_type_by_id', return_value=mock_action_type):
            with patch.object(processor.job_service, 'start_job', return_value=mock_job):
                with patch.object(processor.job_service, 'complete_job', return_value=mock_job):
                    with patch.dict('services.vinted.jobs.HANDLERS', {'publish': mock_handler_class}):
                        result = await processor._execute_job(mock_job)

        assert result["success"] is True
        # Vérifier que le handler a été créé avec les bons arguments
        mock_handler_class.assert_called_once_with(
            db=mock_db,
            shop_id=123,
            job_id=1
        )

    @pytest.mark.asyncio
    async def test_dispatch_to_update_handler(self, mock_db, mock_job):
        """Test dispatch vers UpdateJobHandler."""
        processor = VintedJobProcessor(mock_db, shop_id=123)

        # Action type update
        action_type = MagicMock()
        action_type.code = "update"

        mock_handler_instance = MagicMock()
        mock_handler_instance.execute = AsyncMock(return_value={"success": True})
        mock_handler_class = MagicMock(return_value=mock_handler_instance)

        with patch.object(processor.job_service, 'get_action_type_by_id', return_value=action_type):
            with patch.object(processor.job_service, 'start_job', return_value=mock_job):
                with patch.object(processor.job_service, 'complete_job', return_value=mock_job):
                    with patch.dict('services.vinted.jobs.HANDLERS', {'update': mock_handler_class}):
                        result = await processor._execute_job(mock_job)

        assert result["success"] is True
        assert result["action"] == "update"

    @pytest.mark.asyncio
    async def test_dispatch_to_delete_handler(self, mock_db, mock_job):
        """Test dispatch vers DeleteJobHandler."""
        processor = VintedJobProcessor(mock_db, shop_id=123)

        action_type = MagicMock()
        action_type.code = "delete"

        mock_handler_instance = MagicMock()
        mock_handler_instance.execute = AsyncMock(return_value={"success": True})
        mock_handler_class = MagicMock(return_value=mock_handler_instance)

        with patch.object(processor.job_service, 'get_action_type_by_id', return_value=action_type):
            with patch.object(processor.job_service, 'start_job', return_value=mock_job):
                with patch.object(processor.job_service, 'complete_job', return_value=mock_job):
                    with patch.dict('services.vinted.jobs.HANDLERS', {'delete': mock_handler_class}):
                        result = await processor._execute_job(mock_job)

        assert result["success"] is True
        assert result["action"] == "delete"

    @pytest.mark.asyncio
    async def test_dispatch_unknown_action(self, mock_db, mock_job):
        """Test dispatch action inconnue."""
        processor = VintedJobProcessor(mock_db, shop_id=123)

        action_type = MagicMock()
        action_type.code = "unknown_action"

        # Mock pour l'échec
        updated_job = MagicMock(spec=VintedJob)
        updated_job.id = 1
        updated_job.retry_count = 1
        updated_job.status = JobStatus.PENDING

        with patch.object(processor.job_service, 'get_action_type_by_id', return_value=action_type):
            with patch.object(processor.job_service, 'start_job', return_value=mock_job):
                with patch.object(processor.job_service, 'increment_retry', return_value=(updated_job, True)):
                    result = await processor._execute_job(mock_job)

        assert result["success"] is False
        assert "Unknown action code" in result["error"]


# =============================================================================
# TESTS - PROCESS BATCH
# =============================================================================


class TestProcessBatch:
    """Tests pour process_batch."""

    @pytest.mark.asyncio
    async def test_process_batch_empty(self, mock_db):
        """Test batch vide."""
        processor = VintedJobProcessor(mock_db, shop_id=123)

        with patch.object(processor.job_service, 'get_batch_jobs', return_value=[]):
            result = await processor.process_batch("batch_123")

        assert "error" in result
        assert result["error"] == "Batch not found"

    @pytest.mark.asyncio
    async def test_process_batch_with_jobs(self, mock_db, mock_action_type):
        """Test batch avec jobs."""
        processor = VintedJobProcessor(mock_db, shop_id=123)

        # Créer plusieurs jobs mock
        jobs = []
        for i in range(3):
            job = MagicMock(spec=VintedJob)
            job.id = i + 1
            job.product_id = 100 + i
            job.action_type_id = 1
            job.status = JobStatus.PENDING
            job.priority = 3
            job.retry_count = 0
            job.result_data = None
            jobs.append(job)

        # Mock handler
        mock_handler_instance = MagicMock()
        mock_handler_instance.execute = AsyncMock(return_value={"success": True})
        mock_handler_class = MagicMock(return_value=mock_handler_instance)

        with patch.object(processor.job_service, 'get_batch_jobs', return_value=jobs):
            with patch.object(processor.job_service, 'get_action_type_by_id', return_value=mock_action_type):
                with patch.object(processor.job_service, 'start_job', side_effect=lambda x: jobs[x-1]):
                    with patch.object(processor.job_service, 'complete_job', side_effect=lambda x: jobs[x-1]):
                        with patch.dict('services.vinted.jobs.HANDLERS', {'publish': mock_handler_class}):
                            result = await processor.process_batch("batch_123")

        assert result["batch_id"] == "batch_123"
        assert result["total"] == 3
        assert result["processed"] == 3
        assert result["success_count"] == 3


# =============================================================================
# TESTS - RETRY LOGIC
# =============================================================================


class TestRetryLogic:
    """Tests pour la logique de retry."""

    @pytest.mark.asyncio
    async def test_retry_on_failure(self, mock_db, mock_job, mock_action_type):
        """Test retry après échec."""
        processor = VintedJobProcessor(mock_db, shop_id=123)
        mock_job.retry_count = 0

        # Simuler un échec avec retry possible
        updated_job = MagicMock(spec=VintedJob)
        updated_job.id = 1
        updated_job.retry_count = 1
        updated_job.status = JobStatus.PENDING

        with patch.object(processor.job_service, 'increment_retry', return_value=(updated_job, True)):
            result = await processor._handle_job_failure(
                mock_job, "publish", "Network error", 0
            )

        assert result["success"] is False
        assert result["will_retry"] is True
        assert result["retry_count"] == 1

    @pytest.mark.asyncio
    async def test_max_retries_reached(self, mock_db, mock_job, mock_action_type):
        """Test max retries atteint."""
        processor = VintedJobProcessor(mock_db, shop_id=123)
        mock_job.retry_count = 3

        # Simuler max retries atteint
        updated_job = MagicMock(spec=VintedJob)
        updated_job.id = 1
        updated_job.retry_count = 3
        updated_job.status = JobStatus.FAILED

        with patch.object(processor.job_service, 'increment_retry', return_value=(updated_job, False)):
            with patch.object(processor.job_service, 'fail_job', return_value=updated_job):
                result = await processor._handle_job_failure(
                    mock_job, "publish", "Persistent error", 0
                )

        assert result["success"] is False
        assert result["will_retry"] is False


# =============================================================================
# TESTS - QUEUE STATUS
# =============================================================================


class TestQueueStatus:
    """Tests pour get_queue_status."""

    def test_queue_status_empty(self, mock_db):
        """Test status queue vide."""
        processor = VintedJobProcessor(mock_db, shop_id=123)

        with patch.object(processor.job_service, 'get_pending_jobs', return_value=[]):
            with patch.object(processor.job_service, 'get_interrupted_jobs', return_value=[]):
                status = processor.get_queue_status()

        assert status["pending_count"] == 0
        assert status["interrupted_count"] == 0
        assert status["next_job"] is None

    def test_queue_status_with_jobs(self, mock_db, mock_job, mock_action_type):
        """Test status queue avec jobs."""
        processor = VintedJobProcessor(mock_db, shop_id=123)

        with patch.object(processor.job_service, 'get_pending_jobs', return_value=[mock_job]):
            with patch.object(processor.job_service, 'get_interrupted_jobs', return_value=[]):
                with patch.object(processor.job_service, 'get_action_type_by_id', return_value=mock_action_type):
                    status = processor.get_queue_status()

        assert status["pending_count"] == 1
        assert status["next_job"] is not None
        assert status["next_job"]["id"] == 1


# =============================================================================
# TESTS - PROCESS ALL PENDING
# =============================================================================


class TestProcessAllPending:
    """Tests pour process_all_pending_jobs."""

    @pytest.mark.asyncio
    async def test_process_all_empty(self, mock_db):
        """Test traitement queue vide."""
        processor = VintedJobProcessor(mock_db, shop_id=123)

        with patch.object(processor, 'process_next_job', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = None

            results = await processor.process_all_pending_jobs(max_jobs=10)

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_process_all_with_jobs(self, mock_db):
        """Test traitement de plusieurs jobs."""
        processor = VintedJobProcessor(mock_db, shop_id=123)

        call_count = 0
        async def mock_process_next():
            nonlocal call_count
            call_count += 1
            if call_count <= 3:
                return {"job_id": call_count, "success": True}
            return None

        with patch.object(processor, 'process_next_job', side_effect=mock_process_next):
            results = await processor.process_all_pending_jobs(max_jobs=10)

        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_process_all_stop_on_error(self, mock_db):
        """Test arrêt sur erreur."""
        processor = VintedJobProcessor(mock_db, shop_id=123)

        call_count = 0
        async def mock_process_next():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {"job_id": 1, "success": True}
            elif call_count == 2:
                return {"job_id": 2, "success": False, "error": "Some error"}
            return {"job_id": 3, "success": True}

        with patch.object(processor, 'process_next_job', side_effect=mock_process_next):
            results = await processor.process_all_pending_jobs(max_jobs=10, stop_on_error=True)

        # Doit s'arrêter après l'erreur
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_process_all_max_jobs_limit(self, mock_db):
        """Test limite max_jobs."""
        processor = VintedJobProcessor(mock_db, shop_id=123)

        call_count = 0
        async def mock_process_next():
            nonlocal call_count
            call_count += 1
            return {"job_id": call_count, "success": True}

        with patch.object(processor, 'process_next_job', side_effect=mock_process_next):
            results = await processor.process_all_pending_jobs(max_jobs=5)

        assert len(results) == 5
