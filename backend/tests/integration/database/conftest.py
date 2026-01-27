"""
Conftest for database validation tests.

These tests run against the DEV database (via get_db_context),
not the test database. Override root conftest autouse fixtures.
"""
import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Override: no test DB setup needed for mapping validation tests."""
    yield


@pytest.fixture(scope="function", autouse=True)
def cleanup_data():
    """Override: no cleanup needed for read-only mapping validation tests."""
    yield
