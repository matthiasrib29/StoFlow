"""
Unit Tests for DispatcherConfig

Tests for dispatcher configuration:
- Default values
- Custom values
- Validation
- Factory methods (from_settings)

Created: 2026-01-21
"""

import os
import pytest
from unittest.mock import patch, MagicMock

from worker.dispatcher_config import DispatcherConfig


class TestDispatcherConfigDefaults:
    """Test default values."""

    def test_default_global_max_concurrent(self):
        """Should default to 150 concurrent jobs globally."""
        config = DispatcherConfig()
        assert config.global_max_concurrent == 150

    def test_default_per_client_max_concurrent(self):
        """Should default to 30 concurrent jobs per client."""
        config = DispatcherConfig()
        assert config.per_client_max_concurrent == 30

    def test_default_asyncpg_pool_min_size(self):
        """Should default to 2 connections minimum."""
        config = DispatcherConfig()
        assert config.asyncpg_pool_min_size == 2

    def test_default_asyncpg_pool_max_size(self):
        """Should default to 5 connections maximum."""
        config = DispatcherConfig()
        assert config.asyncpg_pool_max_size == 5

    def test_default_worker_idle_timeout_hours(self):
        """Should default to 2.0 hours idle timeout."""
        config = DispatcherConfig()
        assert config.worker_idle_timeout_hours == 2.0

    def test_default_worker_max_age_hours(self):
        """Should default to 24.0 hours max age."""
        config = DispatcherConfig()
        assert config.worker_max_age_hours == 24.0

    def test_default_poll_interval(self):
        """Should default to 30.0 seconds poll interval."""
        config = DispatcherConfig()
        assert config.poll_interval == 30.0

    def test_default_notify_channel(self):
        """Should default to 'marketplace_job' channel."""
        config = DispatcherConfig()
        assert config.notify_channel == "marketplace_job"

    def test_default_job_timeout(self):
        """Should default to 600.0 seconds (10 min) job timeout."""
        config = DispatcherConfig()
        assert config.job_timeout == 600.0

    def test_default_graceful_shutdown_timeout(self):
        """Should default to 60.0 seconds graceful shutdown."""
        config = DispatcherConfig()
        assert config.graceful_shutdown_timeout == 60.0


class TestDispatcherConfigCustomValues:
    """Test custom configuration values."""

    def test_custom_global_max_concurrent(self):
        """Should accept custom global_max_concurrent."""
        config = DispatcherConfig(global_max_concurrent=200)
        assert config.global_max_concurrent == 200

    def test_custom_per_client_max_concurrent(self):
        """Should accept custom per_client_max_concurrent."""
        config = DispatcherConfig(per_client_max_concurrent=50)
        assert config.per_client_max_concurrent == 50

    def test_custom_worker_idle_timeout_hours(self):
        """Should accept custom worker_idle_timeout_hours."""
        config = DispatcherConfig(worker_idle_timeout_hours=4.0)
        assert config.worker_idle_timeout_hours == 4.0

    def test_custom_worker_max_age_hours(self):
        """Should accept custom worker_max_age_hours."""
        config = DispatcherConfig(worker_max_age_hours=48.0)
        assert config.worker_max_age_hours == 48.0

    def test_custom_poll_interval(self):
        """Should accept custom poll_interval."""
        config = DispatcherConfig(poll_interval=60.0)
        assert config.poll_interval == 60.0

    def test_custom_notify_channel(self):
        """Should accept custom notify_channel."""
        config = DispatcherConfig(notify_channel="custom_channel")
        assert config.notify_channel == "custom_channel"

    def test_custom_db_url(self):
        """Should accept custom db_url."""
        config = DispatcherConfig(db_url="postgresql://custom:pass@host/db")
        assert config.db_url == "postgresql://custom:pass@host/db"


class TestDispatcherConfigValidate:
    """Test validate method."""

    def test_validate_success_with_valid_config(self):
        """Should not raise for valid configuration."""
        config = DispatcherConfig(
            global_max_concurrent=150,
            per_client_max_concurrent=30,
            worker_idle_timeout_hours=2.0,
            worker_max_age_hours=24.0,
            db_url="postgresql://test:test@localhost/db",
        )
        config.validate()  # Should not raise

    def test_validate_global_max_concurrent_zero(self):
        """Should raise ValueError for global_max_concurrent = 0."""
        config = DispatcherConfig(global_max_concurrent=0)
        with pytest.raises(ValueError, match="global_max_concurrent must be >= 1"):
            config.validate()

    def test_validate_global_max_concurrent_negative(self):
        """Should raise ValueError for negative global_max_concurrent."""
        config = DispatcherConfig(global_max_concurrent=-1)
        with pytest.raises(ValueError, match="global_max_concurrent must be >= 1"):
            config.validate()

    def test_validate_per_client_max_concurrent_zero(self):
        """Should raise ValueError for per_client_max_concurrent = 0."""
        config = DispatcherConfig(per_client_max_concurrent=0)
        with pytest.raises(ValueError, match="per_client_max_concurrent must be >= 1"):
            config.validate()

    def test_validate_per_client_max_concurrent_negative(self):
        """Should raise ValueError for negative per_client_max_concurrent."""
        config = DispatcherConfig(per_client_max_concurrent=-5)
        with pytest.raises(ValueError, match="per_client_max_concurrent must be >= 1"):
            config.validate()

    def test_validate_per_client_exceeds_global(self):
        """Should raise ValueError when per_client > global."""
        config = DispatcherConfig(
            global_max_concurrent=50,
            per_client_max_concurrent=100,
        )
        with pytest.raises(ValueError, match="cannot exceed global_max_concurrent"):
            config.validate()

    def test_validate_per_client_equals_global(self):
        """Should accept per_client == global."""
        config = DispatcherConfig(
            global_max_concurrent=50,
            per_client_max_concurrent=50,
            db_url="postgresql://test:test@localhost/db",
        )
        config.validate()  # Should not raise

    def test_validate_idle_timeout_zero(self):
        """Should raise ValueError for worker_idle_timeout_hours = 0."""
        config = DispatcherConfig(worker_idle_timeout_hours=0)
        with pytest.raises(ValueError, match="worker_idle_timeout_hours must be > 0"):
            config.validate()

    def test_validate_idle_timeout_negative(self):
        """Should raise ValueError for negative worker_idle_timeout_hours."""
        config = DispatcherConfig(worker_idle_timeout_hours=-1.0)
        with pytest.raises(ValueError, match="worker_idle_timeout_hours must be > 0"):
            config.validate()

    def test_validate_max_age_zero(self):
        """Should raise ValueError for worker_max_age_hours = 0."""
        config = DispatcherConfig(worker_max_age_hours=0)
        with pytest.raises(ValueError, match="worker_max_age_hours must be > 0"):
            config.validate()

    def test_validate_max_age_negative(self):
        """Should raise ValueError for negative worker_max_age_hours."""
        config = DispatcherConfig(worker_max_age_hours=-24.0)
        with pytest.raises(ValueError, match="worker_max_age_hours must be > 0"):
            config.validate()

    def test_validate_db_url_empty(self):
        """Should raise ValueError for empty db_url."""
        config = DispatcherConfig(db_url="")
        with pytest.raises(ValueError, match="DATABASE_URL"):
            config.validate()


class TestDispatcherConfigFromSettings:
    """Test from_settings class method."""

    def test_from_settings_creates_config(self):
        """Should create config from application settings."""
        mock_settings = MagicMock()
        mock_settings.dispatcher_global_max_concurrent = 100
        mock_settings.dispatcher_per_client_max_concurrent = 20
        mock_settings.dispatcher_worker_idle_timeout_hours = 1.5
        mock_settings.dispatcher_worker_max_age_hours = 12.0
        mock_settings.dispatcher_poll_interval = 45.0
        mock_settings.database_url = "postgresql://app:pass@host/appdb"

        # Patch where it's imported (inside the function)
        with patch("shared.config.settings", mock_settings):
            config = DispatcherConfig.from_settings()

        assert config.global_max_concurrent == 100
        assert config.per_client_max_concurrent == 20
        assert config.worker_idle_timeout_hours == 1.5
        assert config.worker_max_age_hours == 12.0
        assert config.poll_interval == 45.0
        assert "appdb" in config.db_url

    def test_from_settings_uses_correct_mapping(self):
        """Should map settings attributes to config fields correctly."""
        mock_settings = MagicMock()
        mock_settings.dispatcher_global_max_concurrent = 200
        mock_settings.dispatcher_per_client_max_concurrent = 40
        mock_settings.dispatcher_worker_idle_timeout_hours = 3.0
        mock_settings.dispatcher_worker_max_age_hours = 48.0
        mock_settings.dispatcher_poll_interval = 60.0
        mock_settings.database_url = "postgresql://test@host/testdb"

        # Patch where it's imported (inside the function)
        with patch("shared.config.settings", mock_settings):
            config = DispatcherConfig.from_settings()

        # Verify each mapping
        assert config.global_max_concurrent == mock_settings.dispatcher_global_max_concurrent
        assert config.per_client_max_concurrent == mock_settings.dispatcher_per_client_max_concurrent
        assert config.worker_idle_timeout_hours == mock_settings.dispatcher_worker_idle_timeout_hours
        assert config.worker_max_age_hours == mock_settings.dispatcher_worker_max_age_hours
        assert config.poll_interval == mock_settings.dispatcher_poll_interval


class TestDispatcherConfigDataclass:
    """Test dataclass behavior."""

    def test_equality(self):
        """Should be equal if all fields match."""
        config1 = DispatcherConfig(
            global_max_concurrent=100,
            per_client_max_concurrent=25,
            db_url="postgresql://test@host/db",
        )
        config2 = DispatcherConfig(
            global_max_concurrent=100,
            per_client_max_concurrent=25,
            db_url="postgresql://test@host/db",
        )
        assert config1 == config2

    def test_inequality(self):
        """Should not be equal if fields differ."""
        config1 = DispatcherConfig(global_max_concurrent=100)
        config2 = DispatcherConfig(global_max_concurrent=200)
        assert config1 != config2

    def test_repr_contains_key_info(self):
        """Should have readable repr."""
        config = DispatcherConfig(
            global_max_concurrent=100,
            per_client_max_concurrent=25,
        )
        repr_str = repr(config)
        assert "global_max_concurrent=100" in repr_str
        assert "per_client_max_concurrent=25" in repr_str
