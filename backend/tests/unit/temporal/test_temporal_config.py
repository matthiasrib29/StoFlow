"""
Tests for Temporal configuration module.
"""

import pytest
from temporal.config import TemporalConfig, get_temporal_config


class TestTemporalConfig:
    """Tests for TemporalConfig class."""

    def test_default_values(self):
        """Test that default config values are sensible."""
        config = TemporalConfig()

        assert config.temporal_host == "localhost:7233"
        assert config.temporal_namespace == "stoflow"
        assert config.temporal_task_queue == "stoflow-import-queue"
        assert config.temporal_enabled is True

    def test_worker_identity_auto_generated(self):
        """Test that worker identity is auto-generated when not set."""
        config = TemporalConfig()

        identity = config.worker_identity
        assert identity.startswith("stoflow-worker-")

    def test_worker_identity_custom(self, monkeypatch):
        """Test that custom worker identity is used when set."""
        monkeypatch.setenv("TEMPORAL_WORKER_IDENTITY", "custom-worker-1")

        # Need to create new config to pick up env var
        config = TemporalConfig()
        assert config.worker_identity == "custom-worker-1"

    def test_get_temporal_config_cached(self):
        """Test that get_temporal_config returns cached instance."""
        config1 = get_temporal_config()
        config2 = get_temporal_config()

        # Should be the same instance due to lru_cache
        assert config1 is config2

    def test_retry_defaults(self):
        """Test default retry configuration."""
        config = TemporalConfig()

        assert config.temporal_default_retry_max_attempts == 3
        assert config.temporal_default_retry_initial_interval_seconds == 1
        assert config.temporal_default_retry_max_interval_seconds == 60
        assert config.temporal_default_retry_backoff_coefficient == 2.0

    def test_timeout_defaults(self):
        """Test default timeout configuration."""
        config = TemporalConfig()

        assert config.temporal_workflow_execution_timeout_hours == 24
        assert config.temporal_workflow_run_timeout_hours == 1
        assert config.temporal_activity_start_to_close_timeout_minutes == 10
