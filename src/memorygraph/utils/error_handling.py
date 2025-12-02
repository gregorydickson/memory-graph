"""
Error handling utilities for MemoryGraph.

This module provides a decorator for standardized error handling across the codebase,
ensuring consistent error messages, proper logging, and error type conversion.
"""

import functools
import logging
from typing import Any, Callable, TypeVar, cast

from ..models import (
    MemoryError,
    ValidationError,
    NotFoundError,
    BackendError,
    ConfigurationError,
)

logger = logging.getLogger(__name__)

F = TypeVar('F', bound=Callable[..., Any])


def handle_errors(
    operation_name: str | None = None,
    reraise: bool = True,
    log_level: int = logging.ERROR
) -> Callable[[F], F]:
    """
    Decorator for standardized error handling across backend operations.

    This decorator wraps common exceptions into MemoryGraph-specific exception types,
    adds context to error messages, preserves stack traces, and logs errors appropriately.

    Args:
        operation_name: Human-readable name of the operation (e.g., "store memory").
            If not provided, uses the function name.
        reraise: Whether to re-raise the exception after logging. Default is True.
        log_level: Logging level for errors. Default is logging.ERROR.

    Returns:
        Decorator function that wraps the target function with error handling.

    Example:
        >>> @handle_errors(operation_name="store memory")
        ... async def store_memory(self, memory: Memory) -> str:
        ...     # Implementation
        ...     pass
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            op_name = operation_name or func.__name__.replace('_', ' ')
            try:
                return await func(*args, **kwargs)
            except (ValidationError, NotFoundError, BackendError, ConfigurationError):
                # Re-raise MemoryGraph exceptions as-is
                raise
            except KeyError as e:
                msg = f"Failed to {op_name}: Missing required key {e}"
                logger.log(log_level, msg, exc_info=True)
                if reraise:
                    raise ValidationError(msg) from e
                return None
            except ValueError as e:
                msg = f"Failed to {op_name}: Invalid value - {e}"
                logger.log(log_level, msg, exc_info=True)
                if reraise:
                    raise ValidationError(msg) from e
                return None
            except TypeError as e:
                msg = f"Failed to {op_name}: Type error - {e}"
                logger.log(log_level, msg, exc_info=True)
                if reraise:
                    raise ValidationError(msg) from e
                return None
            except ConnectionError as e:
                msg = f"Failed to {op_name}: Connection error - {e}"
                logger.log(log_level, msg, exc_info=True)
                if reraise:
                    raise BackendError(msg) from e
                return None
            except TimeoutError as e:
                msg = f"Failed to {op_name}: Operation timed out - {e}"
                logger.log(log_level, msg, exc_info=True)
                if reraise:
                    raise BackendError(msg) from e
                return None
            except Exception as e:
                msg = f"Failed to {op_name}: Unexpected error - {e}"
                logger.log(log_level, msg, exc_info=True)
                if reraise:
                    raise MemoryError(msg) from e
                return None

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            op_name = operation_name or func.__name__.replace('_', ' ')
            try:
                return func(*args, **kwargs)
            except (ValidationError, NotFoundError, BackendError, ConfigurationError):
                # Re-raise MemoryGraph exceptions as-is
                raise
            except KeyError as e:
                msg = f"Failed to {op_name}: Missing required key {e}"
                logger.log(log_level, msg, exc_info=True)
                if reraise:
                    raise ValidationError(msg) from e
                return None
            except ValueError as e:
                msg = f"Failed to {op_name}: Invalid value - {e}"
                logger.log(log_level, msg, exc_info=True)
                if reraise:
                    raise ValidationError(msg) from e
                return None
            except TypeError as e:
                msg = f"Failed to {op_name}: Type error - {e}"
                logger.log(log_level, msg, exc_info=True)
                if reraise:
                    raise ValidationError(msg) from e
                return None
            except ConnectionError as e:
                msg = f"Failed to {op_name}: Connection error - {e}"
                logger.log(log_level, msg, exc_info=True)
                if reraise:
                    raise BackendError(msg) from e
                return None
            except TimeoutError as e:
                msg = f"Failed to {op_name}: Operation timed out - {e}"
                logger.log(log_level, msg, exc_info=True)
                if reraise:
                    raise BackendError(msg) from e
                return None
            except Exception as e:
                msg = f"Failed to {op_name}: Unexpected error - {e}"
                logger.log(log_level, msg, exc_info=True)
                if reraise:
                    raise MemoryError(msg) from e
                return None

        # Return appropriate wrapper based on whether function is async
        if asyncio.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        return cast(F, sync_wrapper)

    return decorator


# Import asyncio after type checking to avoid circular imports
import asyncio
