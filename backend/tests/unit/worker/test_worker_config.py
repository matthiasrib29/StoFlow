"""
Unit Tests for WorkerConfig

Tests for worker configuration, validation, and factory methods.

Created: 2026-01-20
"""

import os
import pytest
from argparse import Namespace
from unittest.mock import patch

from worker.config import WorkerConfig


class TestWorkerConfigDefaults:
    """Test default values."""

    def test_default_max_concurrent_jobs(self):
        """Should default to 4 concurrent jobs."""
        config = WorkerConfig(user_id=1)
        assert config.max_concurrent_jobs == 4

    def test_default_marketplace_filter(self):
        """Should default to None (all marketplaces)."""
        config = WorkerConfig(user_id=1)
        assert config.marketplace_filter is None

    def test_default_poll_interval(self):
        """Should default to 30 seconds."""
        config = WorkerConfig(user_id=1)
        assert config.poll_interval == 30.0

    def test_default_graceful_shutdown_timeout(self):
        """Should default to 60 seconds."""
        config = WorkerConfig(user_id=1)
        assert config.graceful_shutdown_timeout == 60.0

    def test_default_log_level(self):
        """Should default to INFO."""
        config = WorkerConfig(user_id=1)
        assert config.log_level == "INFO"

    def test_default_asyncpg_pool_min_size(self):
        """Should default to 2."""
        config = WorkerConfig(user_id=1)
        assert config.asyncpg_pool_min_size == 2

    def test_default_asyncpg_pool_max_size(self):
        """Should default to 10."""
        config = WorkerConfig(user_id=1)
        assert config.asyncpg_pool_max_size == 10

    def test_default_job_timeout(self):
        """Should default to 600 seconds (10 minutes)."""
        config = WorkerConfig(user_id=1)
        assert config.job_timeout == 600.0

    def test_default_retry_delay(self):
        """Should default to 5 seconds."""
        config = WorkerConfig(user_id=1)
        assert config.retry_delay == 5.0

    def test_default_max_retries(self):
        """Should default to 3."""
        config = WorkerConfig(user_id=1)
        assert config.max_retries == 3

    def test_default_notify_channel(self):
        """Should default to 'marketplace_job'."""
        config = WorkerConfig(user_id=1)
        assert config.notify_channel == "marketplace_job"


class TestWorkerConfigSchemaName:
    """Test schema_name property."""

    def test_schema_name_for_user_1(self):
        """Should return 'user_1' for user_id=1."""
        config = WorkerConfig(user_id=1)
        assert config.schema_name == "user_1"

    def test_schema_name_for_user_42(self):
        """Should return 'user_42' for user_id=42."""
        config = WorkerConfig(user_id=42)
        assert config.schema_name == "user_42"

    def test_schema_name_for_large_user_id(self):
        """Should handle large user IDs."""
        config = WorkerConfig(user_id=123456)
        assert config.schema_name == "user_123456"


class TestWorkerConfigFromArgs:
    """Test from_args class method."""

    def test_from_args_basic(self):
        """Should create config from argparse namespace."""
        args = Namespace(
            user_id=1,
            workers=4,
        )
        config = WorkerConfig.from_args(args)

        assert config.user_id == 1
        assert config.max_concurrent_jobs == 4
        assert config.marketplace_filter is None

    def test_from_args_with_marketplace(self):
        """Should include marketplace filter if present."""
        args = Namespace(
            user_id=2,
            workers=8,
            marketplace="ebay",
        )
        config = WorkerConfig.from_args(args)

        assert config.user_id == 2
        assert config.max_concurrent_jobs == 8
        assert config.marketplace_filter == "ebay"

    def test_from_args_with_poll_interval(self):
        """Should include poll_interval if present."""
        args = Namespace(
            user_id=1,
            workers=4,
            poll_interval=60.0,
        )
        config = WorkerConfig.from_args(args)

        assert config.poll_interval == 60.0

    def test_from_args_with_log_level(self):
        """Should include log_level if present."""
        args = Namespace(
            user_id=1,
            workers=4,
            log_level="DEBUG",
        )
        config = WorkerConfig.from_args(args)

        assert config.log_level == "DEBUG"

    def test_from_args_uses_defaults(self):
        """Should use defaults for missing optional args."""
        args = Namespace(
            user_id=1,
            workers=4,
        )
        config = WorkerConfig.from_args(args)

        assert config.poll_interval == 30.0
        assert config.log_level == "INFO"


class TestWorkerConfigValidate:
    """Test validate method."""

    def test_validate_valid_config(self):
        """Should not raise for valid config."""
        config = WorkerConfig(user_id=1)
        config.validate()  # Should not raise

    def test_validate_invalid_user_id_zero(self):
        """Should raise ValueError for user_id=0."""
        config = WorkerConfig(user_id=0)
        with pytest.raises(ValueError, match="Invalid user_id"):
            config.validate()

    def test_validate_invalid_user_id_negative(self):
        """Should raise ValueError for negative user_id."""
        config = WorkerConfig(user_id=-1)
        with pytest.raises(ValueError, match="Invalid user_id"):
            config.validate()

    def test_validate_invalid_max_concurrent_jobs_zero(self):
        """Should raise ValueError for max_concurrent_jobs=0."""
        config = WorkerConfig(user_id=1, max_concurrent_jobs=0)
        with pytest.raises(ValueError, match="max_concurrent_jobs must be between 1 and 32"):
            config.validate()

    def test_validate_invalid_max_concurrent_jobs_too_high(self):
        """Should raise ValueError for max_concurrent_jobs > 32."""
        config = WorkerConfig(user_id=1, max_concurrent_jobs=100)
        with pytest.raises(ValueError, match="max_concurrent_jobs must be between 1 and 32"):
            config.validate()

    def test_validate_valid_max_concurrent_jobs_boundary(self):
        """Should accept boundary values for max_concurrent_jobs."""
        config1 = WorkerConfig(user_id=1, max_concurrent_jobs=1)
        config1.validate()  # Should not raise

        config32 = WorkerConfig(user_id=1, max_concurrent_jobs=32)
        config32.validate()  # Should not raise

    def test_validate_invalid_marketplace_filter(self):
        """Should raise ValueError for invalid marketplace."""
        config = WorkerConfig(user_id=1, marketplace_filter="amazon")
        with pytest.raises(ValueError, match="Invalid marketplace_filter"):
            config.validate()

    def test_validate_valid_marketplace_vinted(self):
        """Should accept 'vinted' as marketplace_filter."""
        config = WorkerConfig(user_id=1, marketplace_filter="vinted")
        config.validate()  # Should not raise

    def test_validate_valid_marketplace_ebay(self):
        """Should accept 'ebay' as marketplace_filter."""
        config = WorkerConfig(user_id=1, marketplace_filter="ebay")
        config.validate()  # Should not raise

    def test_validate_valid_marketplace_etsy(self):
        """Should accept 'etsy' as marketplace_filter."""
        config = WorkerConfig(user_id=1, marketplace_filter="etsy")
        config.validate()  # Should not raise

    def test_validate_empty_db_url(self):
        """Should raise ValueError for empty db_url."""
        config = WorkerConfig(user_id=1, db_url="")
        with pytest.raises(ValueError, match="DATABASE_URL"):
            config.validate()


class TestWorkerConfigDatabaseUrl:
    """Test database URL handling."""

    @patch.dict(os.environ, {"DATABASE_URL": "postgresql://test:test@localhost:5432/testdb"})
    def test_db_url_from_environment(self):
        """Should read DATABASE_URL from environment."""
        config = WorkerConfig(user_id=1)
        assert "testdb" in config.db_url

    def test_db_url_override(self):
        """Should allow explicit db_url override."""
        config = WorkerConfig(
            user_id=1,
            db_url="postgresql://custom:custom@localhost:5432/customdb"
        )
        assert "customdb" in config.db_url


class TestWorkerConfigCustomValues:
    """Test custom configuration values."""

    def test_custom_poll_interval(self):
        """Should accept custom poll_interval."""
        config = WorkerConfig(user_id=1, poll_interval=60.0)
        assert config.poll_interval == 60.0

    def test_custom_graceful_shutdown_timeout(self):
        """Should accept custom graceful_shutdown_timeout."""
        config = WorkerConfig(user_id=1, graceful_shutdown_timeout=120.0)
        assert config.graceful_shutdown_timeout == 120.0

    def test_custom_job_timeout(self):
        """Should accept custom job_timeout."""
        config = WorkerConfig(user_id=1, job_timeout=300.0)
        assert config.job_timeout == 300.0

    def test_custom_retry_delay(self):
        """Should accept custom retry_delay."""
        config = WorkerConfig(user_id=1, retry_delay=10.0)
        assert config.retry_delay == 10.0

    def test_custom_max_retries(self):
        """Should accept custom max_retries."""
        config = WorkerConfig(user_id=1, max_retries=5)
        assert config.max_retries == 5

    def test_custom_notify_channel(self):
        """Should accept custom notify_channel."""
        config = WorkerConfig(user_id=1, notify_channel="custom_channel")
        assert config.notify_channel == "custom_channel"


class TestWorkerConfigDataclass:
    """Test dataclass behavior."""

    def test_equality(self):
        """Should be equal if all fields match."""
        config1 = WorkerConfig(user_id=1, max_concurrent_jobs=4)
        config2 = WorkerConfig(user_id=1, max_concurrent_jobs=4)
        assert config1 == config2

    def test_inequality(self):
        """Should not be equal if fields differ."""
        config1 = WorkerConfig(user_id=1, max_concurrent_jobs=4)
        config2 = WorkerConfig(user_id=1, max_concurrent_jobs=8)
        assert config1 != config2

    def test_repr_contains_key_info(self):
        """Should have readable repr."""
        config = WorkerConfig(user_id=42, max_concurrent_jobs=8)
        repr_str = repr(config)
        assert "user_id=42" in repr_str
        assert "max_concurrent_jobs=8" in repr_str
