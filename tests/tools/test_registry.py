"""Tests for tool handler registry."""
import pytest
from memorygraph.tools.registry import TOOL_HANDLERS, get_handler


class TestToolRegistry:
    def test_all_core_tools_have_handlers(self):
        """Verify all core tools are registered."""
        expected_tools = {
            "store_memory", "get_memory", "update_memory", "delete_memory",
            "search_memories", "recall_memories", "contextual_search",
            "create_relationship", "get_related_memories",
            "get_memory_statistics", "get_recent_activity",
            "search_relationships_by_context"
        }
        assert set(TOOL_HANDLERS.keys()) == expected_tools

    def test_handler_names_are_callable(self):
        """Verify all handlers are callable."""
        for name, handler in TOOL_HANDLERS.items():
            assert callable(handler), f"Handler {name} is not callable"

    def test_get_handler_returns_handler(self):
        """Test get_handler returns correct handler."""
        handler = get_handler("store_memory")
        assert handler is not None
        assert callable(handler)

    def test_get_handler_returns_none_for_unknown(self):
        """Test get_handler returns None for unknown tools."""
        assert get_handler("unknown_tool") is None
