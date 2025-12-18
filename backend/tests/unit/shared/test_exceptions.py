"""
Tests for custom exceptions module.

Tests the exception hierarchy and behavior.
"""
import pytest
from shared.exceptions import (
    StoflowError,
    DatabaseError,
    SchemaCreationError,
    SchemaNotFoundError,
    APIError,
    APIConnectionError,
    APIAuthenticationError,
    MarketplaceError,
    VintedError,
    VintedConnectionError,
    VintedPublishError,
    EbayError,
    EtsyError,
    FileError,
    ValidationError,
)


class TestStoflowError:
    """Tests for base StoflowError."""

    def test_basic_exception(self):
        """Test basic exception creation."""
        error = StoflowError("Test error")

        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.details == {}

    def test_exception_with_details(self):
        """Test exception with details dict."""
        error = StoflowError("Test error", details={"key": "value"})

        assert error.message == "Test error"
        assert error.details == {"key": "value"}

    def test_exception_inheritance(self):
        """Test that StoflowError inherits from Exception."""
        assert issubclass(StoflowError, Exception)


class TestDatabaseExceptions:
    """Tests for database-related exceptions."""

    def test_database_error_hierarchy(self):
        """Test DatabaseError hierarchy."""
        assert issubclass(DatabaseError, StoflowError)
        assert issubclass(SchemaCreationError, DatabaseError)
        assert issubclass(SchemaNotFoundError, DatabaseError)

    def test_schema_creation_error(self):
        """Test SchemaCreationError creation."""
        error = SchemaCreationError(
            "Failed to create schema",
            details={"schema": "user_123"}
        )

        assert "Failed to create schema" in str(error)
        assert error.details["schema"] == "user_123"

    def test_catch_database_error_catches_children(self):
        """Test that catching DatabaseError catches child exceptions."""
        try:
            raise SchemaCreationError("Test")
        except DatabaseError as e:
            assert isinstance(e, SchemaCreationError)


class TestAPIExceptions:
    """Tests for API-related exceptions."""

    def test_api_error_hierarchy(self):
        """Test APIError hierarchy."""
        assert issubclass(APIError, StoflowError)
        assert issubclass(APIConnectionError, APIError)
        assert issubclass(APIAuthenticationError, APIError)


class TestMarketplaceExceptions:
    """Tests for marketplace-related exceptions."""

    def test_marketplace_error_hierarchy(self):
        """Test MarketplaceError hierarchy."""
        assert issubclass(MarketplaceError, StoflowError)
        assert issubclass(VintedError, MarketplaceError)
        assert issubclass(EbayError, MarketplaceError)
        assert issubclass(EtsyError, MarketplaceError)

    def test_vinted_error_hierarchy(self):
        """Test VintedError hierarchy."""
        assert issubclass(VintedConnectionError, VintedError)
        assert issubclass(VintedPublishError, VintedError)

    def test_catch_marketplace_catches_all_platforms(self):
        """Test that catching MarketplaceError catches all platform errors."""
        for ErrorClass in [VintedError, EbayError, EtsyError]:
            try:
                raise ErrorClass("Test")
            except MarketplaceError as e:
                assert isinstance(e, ErrorClass)


class TestFileExceptions:
    """Tests for file-related exceptions."""

    def test_file_error_hierarchy(self):
        """Test FileError hierarchy."""
        assert issubclass(FileError, StoflowError)


class TestValidationExceptions:
    """Tests for validation-related exceptions."""

    def test_validation_error_hierarchy(self):
        """Test ValidationError hierarchy."""
        assert issubclass(ValidationError, StoflowError)


class TestExceptionUsagePatterns:
    """Tests for common exception usage patterns."""

    def test_raise_and_catch_with_details(self):
        """Test raising and catching exception with details."""
        try:
            raise VintedPublishError(
                "Failed to publish product",
                details={
                    "product_id": 123,
                    "error_code": "VALIDATION_ERROR"
                }
            )
        except VintedError as e:
            assert e.details["product_id"] == 123
            assert e.details["error_code"] == "VALIDATION_ERROR"

    def test_exception_str_representation(self):
        """Test string representation of exception."""
        error = SchemaCreationError("Schema creation failed")
        assert str(error) == "Schema creation failed"

    def test_exception_can_be_reraised(self):
        """Test that exceptions can be caught and reraised."""
        with pytest.raises(DatabaseError):
            try:
                raise SchemaCreationError("Inner error")
            except SchemaCreationError:
                raise DatabaseError("Outer error")
