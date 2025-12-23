"""Centralized error handling for tool handlers."""
import logging
from functools import wraps
from typing import Any, Callable

from mcp.types import CallToolResult, TextContent
from pydantic import ValidationError as PydanticValidationError

from ..models import MemoryNotFoundError, RelationshipError, ValidationError

logger = logging.getLogger(__name__)

def handle_tool_errors(operation_name: str):
    """Decorator for consistent tool error handling.

    Usage:
        @handle_tool_errors("store memory")
        async def handle_store_memory(memory_db, arguments):
            # Just the happy path - errors handled by decorator
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(memory_db: Any, arguments: dict) -> CallToolResult:
            try:
                return await func(memory_db, arguments)
            except KeyError as e:
                msg = f"Error: Missing required field: {e}"
                return CallToolResult(
                    content=[TextContent(type="text", text=msg)],
                    isError=True
                )
            except (PydanticValidationError, ValidationError, ValueError) as e:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Validation error: {e}")],
                    isError=True
                )
            except MemoryNotFoundError as e:
                return CallToolResult(
                    content=[TextContent(type="text", text=str(e))],
                    isError=True
                )
            except RelationshipError as e:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Relationship error: {e}")],
                    isError=True
                )
            except Exception as e:
                logger.error(f"Failed to {operation_name}: {e}", exc_info=True)
                msg = f"Failed to {operation_name}: {e}"
                return CallToolResult(
                    content=[TextContent(type="text", text=msg)],
                    isError=True
                )
        return wrapper
    return decorator
