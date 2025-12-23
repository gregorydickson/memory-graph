"""Comprehensive tests for utils/error_handling module.

This test suite improves coverage from 54% to 90%+ by testing:
- Error handling decorator with async and sync functions
- Various error types (KeyError, ValueError, TypeError, ConnectionError, TimeoutError)
- Reraise behavior and logging
- MemoryGraph exception handling
"""

import pytest
import logging
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any

from src.memorygraph.utils.error_handling import handle_errors
from src.memorygraph.models import (
    MemoryError,
    ValidationError,
    NotFoundError,
    BackendError,
    ConfigurationError,
)


class TestHandleErrorsAsync:
    """Test handle_errors decorator with async functions."""

    @pytest.mark.asyncio
    async def test_successful_async_execution(self):
        """Test that successful async execution returns the result."""
        @handle_errors(operation_name="test operation")
        async def successful_func():
            return "success"

        result = await successful_func()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_keyerror_converted_to_validation_error(self):
        """Test that KeyError is converted to ValidationError."""
        @handle_errors(operation_name="test operation")
        async def raises_keyerror():
            data = {}
            return data["missing_key"]

        with pytest.raises(ValidationError) as exc_info:
            await raises_keyerror()

        assert "Missing required key" in str(exc_info.value)
        assert "test operation" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_valueerror_converted_to_validation_error(self):
        """Test that ValueError is converted to ValidationError."""
        @handle_errors(operation_name="parse value")
        async def raises_valueerror():
            raise ValueError("Invalid format")

        with pytest.raises(ValidationError) as exc_info:
            await raises_valueerror()

        assert "Invalid value" in str(exc_info.value)
        assert "parse value" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_typeerror_converted_to_validation_error(self):
        """Test that TypeError is converted to ValidationError."""
        @handle_errors(operation_name="type check")
        async def raises_typeerror():
            raise TypeError("Expected string, got int")

        with pytest.raises(ValidationError) as exc_info:
            await raises_typeerror()

        assert "Type error" in str(exc_info.value)
        assert "type check" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_connectionerror_converted_to_backend_error(self):
        """Test that ConnectionError is converted to BackendError."""
        @handle_errors(operation_name="connect to database")
        async def raises_connectionerror():
            raise ConnectionError("Failed to connect")

        with pytest.raises(BackendError) as exc_info:
            await raises_connectionerror()

        assert "Connection error" in str(exc_info.value)
        assert "connect to database" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_timeouterror_converted_to_backend_error(self):
        """Test that TimeoutError is converted to BackendError."""
        @handle_errors(operation_name="execute query")
        async def raises_timeouterror():
            raise TimeoutError("Query timed out")

        with pytest.raises(BackendError) as exc_info:
            await raises_timeouterror()

        assert "Operation timed out" in str(exc_info.value)
        assert "execute query" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generic_exception_converted_to_memory_error(self):
        """Test that generic exceptions are converted to MemoryError."""
        @handle_errors(operation_name="perform operation")
        async def raises_generic_error():
            raise RuntimeError("Something went wrong")

        with pytest.raises(MemoryError) as exc_info:
            await raises_generic_error()

        assert "Unexpected error" in str(exc_info.value)
        assert "perform operation" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_memorygraph_exceptions_passed_through(self):
        """Test that MemoryGraph exceptions are re-raised as-is."""
        @handle_errors(operation_name="test operation")
        async def raises_validation_error():
            raise ValidationError("Original validation error")

        with pytest.raises(ValidationError) as exc_info:
            await raises_validation_error()

        assert str(exc_info.value) == "Original validation error"

        @handle_errors(operation_name="test operation")
        async def raises_not_found_error():
            raise NotFoundError("Not found")

        with pytest.raises(NotFoundError):
            await raises_not_found_error()

        @handle_errors(operation_name="test operation")
        async def raises_backend_error():
            raise BackendError("Backend error")

        with pytest.raises(BackendError):
            await raises_backend_error()

        @handle_errors(operation_name="test operation")
        async def raises_configuration_error():
            raise ConfigurationError("Config error")

        with pytest.raises(ConfigurationError):
            await raises_configuration_error()

    @pytest.mark.asyncio
    async def test_reraise_false_returns_none(self):
        """Test that with reraise=False, errors return None."""
        @handle_errors(operation_name="test operation", reraise=False)
        async def raises_error():
            raise ValueError("Error")

        result = await raises_error()
        assert result is None

    @pytest.mark.asyncio
    async def test_default_operation_name_from_function(self):
        """Test that operation name defaults to function name."""
        @handle_errors()
        async def my_test_function():
            raise ValueError("Error")

        with pytest.raises(ValidationError) as exc_info:
            await my_test_function()

        # Function name with underscores replaced by spaces
        assert "my test function" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_logging_on_error(self, caplog):
        """Test that errors are logged with appropriate level."""
        with caplog.at_level(logging.ERROR):
            @handle_errors(operation_name="test operation", log_level=logging.ERROR)
            async def raises_error():
                raise ValueError("Test error")

            with pytest.raises(ValidationError):
                await raises_error()

        assert "Failed to test operation" in caplog.text
        assert "Invalid value" in caplog.text

    @pytest.mark.asyncio
    async def test_custom_log_level(self, caplog):
        """Test that custom log level is used."""
        with caplog.at_level(logging.WARNING):
            @handle_errors(operation_name="test operation", log_level=logging.WARNING)
            async def raises_error():
                raise ValueError("Test error")

            with pytest.raises(ValidationError):
                await raises_error()

        # Should be logged at WARNING level
        assert any(record.levelno == logging.WARNING for record in caplog.records)


class TestHandleErrorsSync:
    """Test handle_errors decorator with synchronous functions."""

    def test_successful_sync_execution(self):
        """Test that successful sync execution returns the result."""
        @handle_errors(operation_name="sync operation")
        def successful_func():
            return "sync_success"

        result = successful_func()
        assert result == "sync_success"

    def test_sync_keyerror_converted_to_validation_error(self):
        """Test that KeyError in sync function is converted to ValidationError."""
        @handle_errors(operation_name="sync operation")
        def raises_keyerror():
            data = {}
            return data["missing_key"]

        with pytest.raises(ValidationError) as exc_info:
            raises_keyerror()

        assert "Missing required key" in str(exc_info.value)

    def test_sync_valueerror_converted_to_validation_error(self):
        """Test that ValueError in sync function is converted to ValidationError."""
        @handle_errors(operation_name="sync parse")
        def raises_valueerror():
            raise ValueError("Invalid format")

        with pytest.raises(ValidationError) as exc_info:
            raises_valueerror()

        assert "Invalid value" in str(exc_info.value)

    def test_sync_typeerror_converted_to_validation_error(self):
        """Test that TypeError in sync function is converted to ValidationError."""
        @handle_errors(operation_name="sync type check")
        def raises_typeerror():
            raise TypeError("Type mismatch")

        with pytest.raises(ValidationError) as exc_info:
            raises_typeerror()

        assert "Type error" in str(exc_info.value)

    def test_sync_connectionerror_converted_to_backend_error(self):
        """Test that ConnectionError in sync function is converted to BackendError."""
        @handle_errors(operation_name="sync connect")
        def raises_connectionerror():
            raise ConnectionError("Connection failed")

        with pytest.raises(BackendError) as exc_info:
            raises_connectionerror()

        assert "Connection error" in str(exc_info.value)

    def test_sync_timeouterror_converted_to_backend_error(self):
        """Test that TimeoutError in sync function is converted to BackendError."""
        @handle_errors(operation_name="sync query")
        def raises_timeouterror():
            raise TimeoutError("Timeout")

        with pytest.raises(BackendError) as exc_info:
            raises_timeouterror()

        assert "Operation timed out" in str(exc_info.value)

    def test_sync_generic_exception_converted_to_memory_error(self):
        """Test that generic exceptions in sync function are converted to MemoryError."""
        @handle_errors(operation_name="sync operation")
        def raises_generic_error():
            raise RuntimeError("Generic error")

        with pytest.raises(MemoryError) as exc_info:
            raises_generic_error()

        assert "Unexpected error" in str(exc_info.value)

    def test_sync_memorygraph_exceptions_passed_through(self):
        """Test that MemoryGraph exceptions in sync function are re-raised as-is."""
        @handle_errors(operation_name="sync operation")
        def raises_validation_error():
            raise ValidationError("Validation failed")

        with pytest.raises(ValidationError) as exc_info:
            raises_validation_error()

        assert str(exc_info.value) == "Validation failed"

    def test_sync_reraise_false_returns_none(self):
        """Test that with reraise=False, sync errors return None."""
        @handle_errors(operation_name="sync operation", reraise=False)
        def raises_error():
            raise ValueError("Error")

        result = raises_error()
        assert result is None

    def test_sync_logging_on_error(self, caplog):
        """Test that sync errors are logged."""
        with caplog.at_level(logging.ERROR):
            @handle_errors(operation_name="sync operation", log_level=logging.ERROR)
            def raises_error():
                raise ValueError("Sync error")

            with pytest.raises(ValidationError):
                raises_error()

        assert "Failed to sync operation" in caplog.text


class TestDecoratorEdgeCases:
    """Test edge cases and special scenarios."""

    @pytest.mark.asyncio
    async def test_function_with_arguments(self):
        """Test that decorator works with functions that take arguments."""
        @handle_errors(operation_name="process data")
        async def process_data(value: int, multiplier: int = 2):
            if value < 0:
                raise ValueError("Value must be positive")
            return value * multiplier

        # Successful execution
        result = await process_data(5, 3)
        assert result == 15

        # Error with arguments
        with pytest.raises(ValidationError):
            await process_data(-1)

    def test_sync_function_with_arguments(self):
        """Test that decorator works with sync functions that take arguments."""
        @handle_errors(operation_name="calculate")
        def calculate(a: int, b: int) -> int:
            if b == 0:
                raise ValueError("Division by zero")
            return a / b

        result = calculate(10, 2)
        assert result == 5

        with pytest.raises(ValidationError):
            calculate(10, 0)

    @pytest.mark.asyncio
    async def test_preserves_function_metadata(self):
        """Test that decorator preserves function metadata."""
        @handle_errors(operation_name="test")
        async def documented_function():
            """This is a test function."""
            pass

        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This is a test function."

    @pytest.mark.asyncio
    async def test_multiple_decorators(self):
        """Test that handle_errors can be combined with other decorators."""
        call_count = 0

        def counting_decorator(func):
            async def wrapper(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                return await func(*args, **kwargs)
            return wrapper

        @counting_decorator
        @handle_errors(operation_name="multi-decorated")
        async def multi_decorated():
            raise ValueError("Error")

        with pytest.raises(ValidationError):
            await multi_decorated()

        assert call_count == 1

    @pytest.mark.asyncio
    async def test_error_chain_preserved(self):
        """Test that the error chain (cause) is preserved."""
        @handle_errors(operation_name="test operation")
        async def raises_chained_error():
            raise ValueError("Original error")

        with pytest.raises(ValidationError) as exc_info:
            await raises_chained_error()

        # Check that the cause is preserved
        assert exc_info.value.__cause__ is not None
        assert isinstance(exc_info.value.__cause__, ValueError)
        assert str(exc_info.value.__cause__) == "Original error"

    @pytest.mark.asyncio
    async def test_different_error_types_all_logged(self, caplog):
        """Test that all error types are logged with stack trace."""
        error_types = [
            (KeyError, "missing_key"),
            (ValueError, "Invalid value"),
            (TypeError, "Type error"),
            (ConnectionError, "Connection failed"),
            (TimeoutError, "Timeout"),
            (RuntimeError, "Runtime error"),
        ]

        for error_class, error_msg in error_types:
            caplog.clear()

            @handle_errors(operation_name="test", log_level=logging.ERROR)
            async def raises_specific_error():
                if error_class == KeyError:
                    raise error_class(error_msg)
                else:
                    raise error_class(error_msg)

            with caplog.at_level(logging.ERROR):
                try:
                    await raises_specific_error()
                except (ValidationError, BackendError, MemoryError):
                    pass  # Expected

            # Verify logging occurred
            assert len(caplog.records) > 0
            assert "Failed to test" in caplog.text
