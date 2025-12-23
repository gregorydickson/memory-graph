"""Tests for tool error handling decorator."""
import pytest
from mcp.types import CallToolResult, TextContent
from pydantic import ValidationError as PydanticValidationError

from memorygraph.tools.error_handling import handle_tool_errors
from memorygraph.models import MemoryNotFoundError, RelationshipError, ValidationError as CustomValidationError


class TestErrorHandlingDecorator:
    """Test suite for handle_tool_errors decorator."""

    @pytest.mark.asyncio
    async def test_successful_function_passes_through(self):
        """Test that successful functions return their result unchanged."""
        @handle_tool_errors("test operation")
        async def successful_handler(memory_db, arguments):
            return CallToolResult(
                content=[TextContent(type="text", text="Success!")]
            )

        result = await successful_handler(None, {})
        assert isinstance(result, CallToolResult)
        assert result.content[0].text == "Success!"
        assert not result.isError

    @pytest.mark.asyncio
    async def test_keyerror_caught_and_formatted(self):
        """Test that KeyError is caught and returns proper error message."""
        @handle_tool_errors("test operation")
        async def handler_with_keyerror(memory_db, arguments):
            raise KeyError("'memory_id'")

        result = await handler_with_keyerror(None, {})
        assert isinstance(result, CallToolResult)
        assert result.isError is True
        assert "Missing required field" in result.content[0].text
        assert "'memory_id'" in result.content[0].text

    @pytest.mark.asyncio
    async def test_validation_error_caught(self):
        """Test that Pydantic ValidationError is caught and formatted."""
        @handle_tool_errors("store memory")
        async def handler_with_validation_error(memory_db, arguments):
            # Raise a Pydantic ValidationError by creating an invalid model
            from memorygraph.models import Memory
            # This will raise ValidationError because title is missing
            Memory(type="task", content="test")

        result = await handler_with_validation_error(None, {})
        assert isinstance(result, CallToolResult)
        assert result.isError is True
        assert "Validation error" in result.content[0].text

    @pytest.mark.asyncio
    async def test_custom_validation_error_caught(self):
        """Test that custom ValidationError from models.py is caught and formatted."""
        @handle_tool_errors("validate input")
        async def handler_with_custom_validation_error(memory_db, arguments):
            raise CustomValidationError("Title exceeds 200 characters")

        result = await handler_with_custom_validation_error(None, {})
        assert isinstance(result, CallToolResult)
        assert result.isError is True
        assert "Validation error" in result.content[0].text
        assert "Title exceeds 200 characters" in result.content[0].text

    @pytest.mark.asyncio
    async def test_value_error_caught(self):
        """Test that ValueError is caught and formatted."""
        @handle_tool_errors("update memory")
        async def handler_with_value_error(memory_db, arguments):
            raise ValueError("Invalid importance score")

        result = await handler_with_value_error(None, {})
        assert isinstance(result, CallToolResult)
        assert result.isError is True
        assert "Validation error" in result.content[0].text
        assert "Invalid importance score" in result.content[0].text

    @pytest.mark.asyncio
    async def test_memory_not_found_error_caught(self):
        """Test that MemoryNotFoundError is caught and formatted."""
        @handle_tool_errors("get memory")
        async def handler_with_not_found(memory_db, arguments):
            raise MemoryNotFoundError("test-memory-123")

        result = await handler_with_not_found(None, {})
        assert isinstance(result, CallToolResult)
        assert result.isError is True
        assert "Memory not found" in result.content[0].text
        assert "test-memory-123" in result.content[0].text

    @pytest.mark.asyncio
    async def test_relationship_error_caught(self):
        """Test that RelationshipError is caught and formatted."""
        @handle_tool_errors("create relationship")
        async def handler_with_relationship_error(memory_db, arguments):
            raise RelationshipError("Cannot create relationship: memory not found")

        result = await handler_with_relationship_error(None, {})
        assert isinstance(result, CallToolResult)
        assert result.isError is True
        assert "Relationship error" in result.content[0].text
        assert "Cannot create relationship" in result.content[0].text

    @pytest.mark.asyncio
    async def test_general_exception_caught_and_logged(self, caplog):
        """Test that general exceptions are caught, logged, and formatted."""
        @handle_tool_errors("delete memory")
        async def handler_with_exception(memory_db, arguments):
            raise RuntimeError("Unexpected database error")

        with caplog.at_level("ERROR"):
            result = await handler_with_exception(None, {})

        assert isinstance(result, CallToolResult)
        assert result.isError is True
        assert "Failed to delete memory" in result.content[0].text
        assert "Unexpected database error" in result.content[0].text

        # Verify logging occurred
        assert len(caplog.records) > 0
        assert any("Failed to delete memory" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_decorator_preserves_function_name(self):
        """Test that @wraps preserves the original function name."""
        @handle_tool_errors("test operation")
        async def my_custom_handler(memory_db, arguments):
            return CallToolResult(content=[TextContent(type="text", text="OK")])

        assert my_custom_handler.__name__ == "my_custom_handler"

    @pytest.mark.asyncio
    async def test_operation_name_used_in_error_message(self):
        """Test that operation_name parameter is used in error messages."""
        @handle_tool_errors("search memories")
        async def handler_that_fails(memory_db, arguments):
            raise Exception("Database timeout")

        result = await handler_that_fails(None, {})
        assert "Failed to search memories" in result.content[0].text
        assert "Database timeout" in result.content[0].text

    @pytest.mark.asyncio
    async def test_multiple_decorators_on_same_function(self):
        """Test that the decorator can be applied to multiple functions."""
        @handle_tool_errors("operation A")
        async def handler_a(memory_db, arguments):
            return CallToolResult(content=[TextContent(type="text", text="A")])

        @handle_tool_errors("operation B")
        async def handler_b(memory_db, arguments):
            return CallToolResult(content=[TextContent(type="text", text="B")])

        result_a = await handler_a(None, {})
        result_b = await handler_b(None, {})

        assert result_a.content[0].text == "A"
        assert result_b.content[0].text == "B"

    @pytest.mark.asyncio
    async def test_arguments_passed_correctly(self):
        """Test that arguments are passed correctly to the wrapped function."""
        @handle_tool_errors("test operation")
        async def handler_with_args(memory_db, arguments):
            assert arguments["key"] == "value"
            assert memory_db == "mock_db"
            return CallToolResult(content=[TextContent(type="text", text="OK")])

        result = await handler_with_args("mock_db", {"key": "value"})
        assert result.content[0].text == "OK"

    @pytest.mark.asyncio
    async def test_keyerror_with_different_keys(self):
        """Test KeyError handling with various key names."""
        @handle_tool_errors("test operation")
        async def handler_missing_field(memory_db, arguments):
            raise KeyError("'title'")

        result = await handler_missing_field(None, {})
        assert result.isError is True
        assert "'title'" in result.content[0].text

        @handle_tool_errors("test operation")
        async def handler_missing_another_field(memory_db, arguments):
            raise KeyError("'content'")

        result2 = await handler_missing_another_field(None, {})
        assert result2.isError is True
        assert "'content'" in result2.content[0].text


class TestNoTracebackLeakage:
    """Test suite for ensuring error responses don't leak tracebacks."""

    @pytest.mark.asyncio
    async def test_error_response_contains_no_traceback(self):
        """Verify error responses don't leak tracebacks to users."""
        from memorygraph.tools.error_handling import handle_tool_errors
        from mcp.types import CallToolResult

        @handle_tool_errors("test operation")
        async def failing_handler(memory_db, arguments):
            raise RuntimeError("Something went wrong internally")

        result = await failing_handler(None, {})

        assert result.isError is True
        error_text = result.content[0].text

        # Should NOT contain traceback indicators
        assert "Traceback" not in error_text
        assert "File \"" not in error_text
        assert "line " not in error_text.lower() or "line" in "Failed to test operation"

        # Should contain user-friendly message
        assert "Failed to test operation" in error_text

    @pytest.mark.asyncio
    async def test_validation_error_no_traceback(self):
        """Verify validation errors don't leak tracebacks."""
        from memorygraph.tools.error_handling import handle_tool_errors
        from memorygraph.models import ValidationError as CustomValidationError

        @handle_tool_errors("validate")
        async def validation_handler(memory_db, arguments):
            raise CustomValidationError("Title too long")

        result = await validation_handler(None, {})
        error_text = result.content[0].text

        assert "Traceback" not in error_text
        assert "Title too long" in error_text
