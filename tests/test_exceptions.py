"""Tests for custom exception hierarchy."""

import pytest
from memorygraph.models import (
    MemoryError,
    MemoryNotFoundError,
    RelationshipError,
    ValidationError,
    DatabaseConnectionError,
    SchemaError,
)


def test_memory_error_base():
    """Test base MemoryError exception."""
    error = MemoryError("Test error message")
    assert str(error) == "Test error message"
    assert error.message == "Test error message"
    assert error.details == {}


def test_memory_error_with_details():
    """Test MemoryError with details."""
    details = {"key": "value", "number": 42}
    error = MemoryError("Error with details", details)
    assert "Error with details" in str(error)
    assert "Details:" in str(error)
    assert error.details == details


def test_memory_not_found_error():
    """Test MemoryNotFoundError exception."""
    error = MemoryNotFoundError("test-id-123")
    assert "test-id-123" in str(error)
    assert error.memory_id == "test-id-123"
    assert isinstance(error, MemoryError)


def test_relationship_error():
    """Test RelationshipError exception."""
    error = RelationshipError("Relationship creation failed")
    assert "Relationship creation failed" in str(error)
    assert isinstance(error, MemoryError)


def test_validation_error():
    """Test ValidationError exception."""
    error = ValidationError("Invalid memory data")
    assert "Invalid memory data" in str(error)
    assert isinstance(error, MemoryError)


def test_database_connection_error():
    """Test DatabaseConnectionError exception."""
    error = DatabaseConnectionError("Connection failed")
    assert "Connection failed" in str(error)
    assert isinstance(error, MemoryError)


def test_schema_error():
    """Test SchemaError exception."""
    error = SchemaError("Schema initialization failed")
    assert "Schema initialization failed" in str(error)
    assert isinstance(error, MemoryError)


def test_exception_hierarchy():
    """Test that all custom exceptions inherit from MemoryError."""
    exceptions = [
        MemoryNotFoundError("test"),
        RelationshipError("test"),
        ValidationError("test"),
        DatabaseConnectionError("test"),
        SchemaError("test"),
    ]

    for exc in exceptions:
        assert isinstance(exc, MemoryError)
        assert isinstance(exc, Exception)


class TestErrorHandlingDecorator:
    """Test the @handle_errors decorator."""

    @pytest.mark.asyncio
    async def test_async_function_success(self) -> None:
        """Decorator should not interfere with successful async function execution."""
        from memorygraph.utils.error_handling import handle_errors

        @handle_errors()
        async def successful_operation() -> str:
            return "success"

        result = await successful_operation()
        assert result == "success"

    def test_sync_function_success(self) -> None:
        """Decorator should not interfere with successful sync function execution."""
        from memorygraph.utils.error_handling import handle_errors

        @handle_errors()
        def successful_operation() -> str:
            return "success"

        result = successful_operation()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_async_key_error_conversion(self) -> None:
        """KeyError should be converted to ValidationError."""
        from memorygraph.utils.error_handling import handle_errors

        @handle_errors(operation_name="test operation")
        async def failing_operation() -> None:
            data = {}
            _ = data["missing_key"]

        with pytest.raises(ValidationError) as exc_info:
            await failing_operation()

        assert "Missing required key" in str(exc_info.value)
        assert "test operation" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_async_value_error_conversion(self) -> None:
        """ValueError should be converted to ValidationError."""
        from memorygraph.utils.error_handling import handle_errors

        @handle_errors(operation_name="parse value")
        async def failing_operation() -> None:
            int("not a number")

        with pytest.raises(ValidationError) as exc_info:
            await failing_operation()

        assert "Invalid value" in str(exc_info.value)
        assert "parse value" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_async_connection_error_conversion(self) -> None:
        """ConnectionError should be converted to BackendError."""
        from memorygraph.utils.error_handling import handle_errors
        from memorygraph.models import BackendError

        @handle_errors(operation_name="connect")
        async def failing_operation() -> None:
            raise ConnectionError("Connection failed")

        with pytest.raises(BackendError) as exc_info:
            await failing_operation()

        assert "Connection error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_async_timeout_error_conversion(self) -> None:
        """TimeoutError should be converted to BackendError."""
        from memorygraph.utils.error_handling import handle_errors
        from memorygraph.models import BackendError

        @handle_errors(operation_name="query")
        async def failing_operation() -> None:
            raise TimeoutError("Operation timed out")

        with pytest.raises(BackendError) as exc_info:
            await failing_operation()

        assert "timed out" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_async_memory_error_passthrough(self) -> None:
        """MemoryError subclasses should pass through unchanged."""
        from memorygraph.utils.error_handling import handle_errors

        @handle_errors()
        async def failing_operation() -> None:
            raise ValidationError("Original validation error")

        with pytest.raises(ValidationError) as exc_info:
            await failing_operation()

        assert str(exc_info.value) == "Original validation error"

    @pytest.mark.asyncio
    async def test_decorator_preserves_stack_trace(self) -> None:
        """Decorator should preserve the original exception's stack trace."""
        from memorygraph.utils.error_handling import handle_errors

        @handle_errors()
        async def failing_operation() -> None:
            raise ValueError("Original error")

        with pytest.raises(ValidationError) as exc_info:
            await failing_operation()

        # Check that the original exception is preserved in the chain
        assert exc_info.value.__cause__ is not None
        assert isinstance(exc_info.value.__cause__, ValueError)
        assert str(exc_info.value.__cause__) == "Original error"

    @pytest.mark.asyncio
    async def test_decorator_with_custom_operation_name(self) -> None:
        """Decorator should use custom operation name in error messages."""
        from memorygraph.utils.error_handling import handle_errors

        @handle_errors(operation_name="custom action")
        async def failing_operation() -> None:
            raise ValueError("Error")

        with pytest.raises(ValidationError) as exc_info:
            await failing_operation()

        assert "custom action" in str(exc_info.value)

    def test_sync_key_error_conversion(self) -> None:
        """KeyError should be converted to ValidationError in sync functions."""
        from memorygraph.utils.error_handling import handle_errors

        @handle_errors(operation_name="test operation")
        def failing_operation() -> None:
            data = {}
            _ = data["missing_key"]

        with pytest.raises(ValidationError) as exc_info:
            failing_operation()

        assert "Missing required key" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_no_reraise_returns_none(self) -> None:
        """When reraise=False, decorator should return None on error."""
        from memorygraph.utils.error_handling import handle_errors

        @handle_errors(reraise=False)
        async def failing_operation() -> str:
            raise ValueError("Error")

        result = await failing_operation()
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__])
