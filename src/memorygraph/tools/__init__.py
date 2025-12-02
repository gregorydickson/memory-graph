"""
Tool handlers for the MCP server.

This package contains modular tool handlers organized by functionality:
- memory_tools: CRUD operations for memories
- relationship_tools: Create and query relationships
- search_tools: Search and recall memories
- activity_tools: Activity summaries and statistics
"""

from .memory_tools import (
    handle_store_memory,
    handle_get_memory,
    handle_update_memory,
    handle_delete_memory,
)
from .relationship_tools import (
    handle_create_relationship,
    handle_get_related_memories,
)
from .search_tools import (
    handle_search_memories,
    handle_recall_memories,
)
from .activity_tools import (
    handle_get_memory_statistics,
    handle_get_recent_activity,
    handle_search_relationships_by_context,
)

__all__ = [
    # Memory CRUD operations
    "handle_store_memory",
    "handle_get_memory",
    "handle_update_memory",
    "handle_delete_memory",
    # Relationship operations
    "handle_create_relationship",
    "handle_get_related_memories",
    # Search operations
    "handle_search_memories",
    "handle_recall_memories",
    # Activity and statistics
    "handle_get_memory_statistics",
    "handle_get_recent_activity",
    "handle_search_relationships_by_context",
]
