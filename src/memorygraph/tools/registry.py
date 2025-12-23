"""Tool handler registry for MCP server."""
from typing import Any, Awaitable, Callable, Dict

from mcp.types import CallToolResult

from .activity_tools import (
    handle_get_memory_statistics,
    handle_get_recent_activity,
    handle_search_relationships_by_context,
)
from .memory_tools import (
    handle_delete_memory,
    handle_get_memory,
    handle_store_memory,
    handle_update_memory,
)
from .relationship_tools import (
    handle_create_relationship,
    handle_get_related_memories,
)
from .search_tools import (
    handle_contextual_search,
    handle_recall_memories,
    handle_search_memories,
)

# Type alias for tool handlers
ToolHandler = Callable[[Any, Dict[str, Any]], Awaitable[CallToolResult]]

# Registry mapping tool names to handlers
TOOL_HANDLERS: Dict[str, ToolHandler] = {
    "store_memory": handle_store_memory,
    "get_memory": handle_get_memory,
    "update_memory": handle_update_memory,
    "delete_memory": handle_delete_memory,
    "search_memories": handle_search_memories,
    "recall_memories": handle_recall_memories,
    "contextual_search": handle_contextual_search,
    "create_relationship": handle_create_relationship,
    "get_related_memories": handle_get_related_memories,
    "get_memory_statistics": handle_get_memory_statistics,
    "get_recent_activity": handle_get_recent_activity,
    "search_relationships_by_context": handle_search_relationships_by_context,
}

def get_handler(tool_name: str) -> ToolHandler | None:
    """Get handler for a tool by name."""
    return TOOL_HANDLERS.get(tool_name)
