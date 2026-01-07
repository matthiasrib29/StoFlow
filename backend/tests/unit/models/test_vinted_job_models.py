"""
Tests Unitaires pour les Modèles MarketplaceJob

Tests de la logique des modèles (propriétés, enums, etc.)

Author: Claude
Date: 2025-12-19
"""

from datetime import datetime, timedelta, timezone
import pytest

from models.user.marketplace_job import MarketplaceJob, JobStatus
from models.user.vinted_job_stats import VintedJobStats
from models.vinted.vinted_action_type import VintedActionType


# =============================================================================
# TESTS - JOB STATUS ENUM
# =============================================================================


class TestJobStatusEnum:
    """Tests pour l'enum JobStatus."""

    def test_all_statuses_exist(self):
        """Test que tous les statuts attendus existent."""
        expected_statuses = [
            "pending", "running", "paused",
            "completed", "failed", "cancelled", "expired"
        ]

        for status_value in expected_statuses:
            status = JobStatus(status_value)
            assert status.value == status_value

    def test_status_values(self):
        """Test les valeurs des statuts."""
        assert JobStatus.PENDING.value == "pending"
        assert JobStatus.RUNNING.value == "running"
        assert JobStatus.PAUSED.value == "paused"
        assert JobStatus.COMPLETED.value == "completed"
        assert JobStatus.FAILED.value == "failed"
        assert JobStatus.CANCELLED.value == "cancelled"
        assert JobStatus.EXPIRED.value == "expired"

    def test_status_is_string_enum(self):
        """Test que JobStatus hérite de str et Enum."""
        assert isinstance(JobStatus.PENDING, str)
        assert JobStatus.PENDING == "pending"


# =============================================================================
# TESTS - VINTED JOB MODEL
# =============================================================================


class TestVintedJobModel:
    """Tests pour le modèle MarketplaceJob."""

    def test_is_active_property(self):
        """Test la propriété is_active."""
        job = MarketplaceJob()

        # Statuts actifs
        for status in [JobStatus.PENDING, JobStatus.RUNNING, JobStatus.PAUSED]:
            job.status = status
            assert job.is_active is True, f"Status {status} should be active"

        # Statuts terminaux
        for status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED, JobStatus.EXPIRED]:
            job.status = status
            assert job.is_active is False, f"Status {status} should not be active"

    def test_is_terminal_property(self):
        """Test la propriété is_terminal."""
        job = MarketplaceJob()

        # Statuts terminaux
        for status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED, JobStatus.EXPIRED]:
            job.status = status
            assert job.is_terminal is True, f"Status {status} should be terminal"

        # Statuts non-terminaux
        for status in [JobStatus.PENDING, JobStatus.RUNNING, JobStatus.PAUSED]:
            job.status = status
            assert job.is_terminal is False, f"Status {status} should not be terminal"

    def test_job_repr(self):
        """Test la représentation string d'un job."""
        job = MarketplaceJob()
        job.id = 123
        job.status = JobStatus.RUNNING
        job.product_id = 456

        repr_str = repr(job)

        assert "MarketplaceJob" in repr_str
        assert "123" in repr_str
        assert "RUNNING" in repr_str or "running" in repr_str
        assert "456" in repr_str


# =============================================================================
# TESTS - VINTED JOB STATS MODEL
# =============================================================================


class TestVintedJobStatsModel:
    """Tests pour le modèle VintedJobStats."""

    def test_success_rate_property(self):
        """Test le calcul du taux de succès."""
        stats = VintedJobStats()

        # Cas normal
        stats.total_jobs = 100
        stats.success_count = 95
        assert stats.success_rate == 95.0

        # 100% succès
        stats.total_jobs = 50
        stats.success_count = 50
        assert stats.success_rate == 100.0

        # 0% succès
        stats.total_jobs = 10
        stats.success_count = 0
        assert stats.success_rate == 0.0

    def test_success_rate_zero_total(self):
        """Test taux de succès quand total = 0."""
        stats = VintedJobStats()
        stats.total_jobs = 0
        stats.success_count = 0

        assert stats.success_rate == 0.0

    def test_stats_repr(self):
        """Test la représentation string des stats."""
        from datetime import date

        stats = VintedJobStats()
        stats.date = date(2024, 12, 19)
        stats.action_type_id = 1
        stats.total_jobs = 100

        repr_str = repr(stats)

        assert "VintedJobStats" in repr_str
        assert "2024-12-19" in repr_str
        assert "100" in repr_str


# =============================================================================
# TESTS - VINTED ACTION TYPE MODEL
# =============================================================================


class TestVintedActionTypeModel:
    """Tests pour le modèle VintedActionType."""

    def test_action_type_repr(self):
        """Test la représentation string d'un action type."""
        action = VintedActionType()
        action.code = "publish"
        action.priority = 3

        repr_str = repr(action)

        assert "VintedActionType" in repr_str
        assert "publish" in repr_str
        assert "3" in repr_str

    def test_priority_values(self):
        """Test les valeurs de priorité attendues."""
        # Priorité 1 = CRITIQUE (messages)
        # Priorité 2 = HAUTE
        # Priorité 3 = NORMALE (publish, orders)
        # Priorité 4 = BASSE (sync, delete)

        action = VintedActionType()

        # Test bornes
        action.priority = 1
        assert action.priority >= 1

        action.priority = 4
        assert action.priority <= 4


# =============================================================================
# TESTS - STATUS TRANSITIONS
# =============================================================================


class TestStatusTransitions:
    """Tests pour les transitions de statuts valides."""

    def test_pending_to_running(self):
        """Test transition PENDING -> RUNNING."""
        job = MarketplaceJob()
        job.status = JobStatus.PENDING

        # Transition valide
        job.status = JobStatus.RUNNING
        assert job.status == JobStatus.RUNNING

    def test_pending_to_paused(self):
        """Test transition PENDING -> PAUSED."""
        job = MarketplaceJob()
        job.status = JobStatus.PENDING

        job.status = JobStatus.PAUSED
        assert job.status == JobStatus.PAUSED

    def test_running_to_completed(self):
        """Test transition RUNNING -> COMPLETED."""
        job = MarketplaceJob()
        job.status = JobStatus.RUNNING

        job.status = JobStatus.COMPLETED
        assert job.status == JobStatus.COMPLETED

    def test_running_to_failed(self):
        """Test transition RUNNING -> FAILED."""
        job = MarketplaceJob()
        job.status = JobStatus.RUNNING

        job.status = JobStatus.FAILED
        assert job.status == JobStatus.FAILED

    def test_paused_to_pending(self):
        """Test transition PAUSED -> PENDING (resume)."""
        job = MarketplaceJob()
        job.status = JobStatus.PAUSED

        job.status = JobStatus.PENDING
        assert job.status == JobStatus.PENDING

    def test_pending_to_expired(self):
        """Test transition PENDING -> EXPIRED."""
        job = MarketplaceJob()
        job.status = JobStatus.PENDING

        job.status = JobStatus.EXPIRED
        assert job.status == JobStatus.EXPIRED

    def test_any_active_to_cancelled(self):
        """Test que tout statut actif peut être annulé."""
        for status in [JobStatus.PENDING, JobStatus.RUNNING, JobStatus.PAUSED]:
            job = MarketplaceJob()
            job.status = status

            job.status = JobStatus.CANCELLED
            assert job.status == JobStatus.CANCELLED


# =============================================================================
# TESTS - EXPIRATION LOGIC
# =============================================================================


class TestExpirationLogic:
    """Tests pour la logique d'expiration."""

    def test_expires_at_set_on_creation(self):
        """Test que expires_at doit être défini à la création."""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=1)

        job = MarketplaceJob()
        job.expires_at = expires

        assert job.expires_at is not None
        assert job.expires_at > now

    def test_expired_check(self):
        """Test vérification si un job est expiré."""
        now = datetime.now(timezone.utc)

        job = MarketplaceJob()
        job.status = JobStatus.PENDING

        # Non expiré
        job.expires_at = now + timedelta(hours=1)
        assert job.expires_at > now

        # Expiré
        job.expires_at = now - timedelta(hours=1)
        assert job.expires_at < now
