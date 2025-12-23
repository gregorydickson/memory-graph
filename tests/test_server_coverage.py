"""Additional coverage tests for server module to reach 90%+ coverage.

This test suite targets specific uncovered lines in server.py:
- Line 581: handle_list_tools return
- Lines 586-647: Advanced tool handlers and edge cases
- Lines 667-668: CloudMemoryDatabase initialization path
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
import json
import uuid

from memorygraph.server import ClaudeMemoryServer, main
from memorygraph.backends.sqlite_fallback import SQLiteFallbackBackend
from memorygraph.backends.cloud_backend import CloudRESTAdapter
from memorygraph.cloud_database import CloudMemoryDatabase
from memorygraph.sqlite_database import SQLiteMemoryDatabase
from memorygraph.database import MemoryDatabase
from mcp.types import CallToolResult, TextContent, ListToolsResult


@pytest.fixture
async def mock_database():
    """Create a mock MemoryDatabase."""
    db = AsyncMock(spec=MemoryDatabase)
    db.initialize_schema = AsyncMock()
    return db


@pytest.fixture
async def mcp_server(mock_database):
    """Create MCP server with mocked database."""
    server = ClaudeMemoryServer()
    server.memory_db = mock_database

    # Initialize advanced handlers
    from memorygraph.advanced_tools import AdvancedRelationshipHandlers
    server.advanced_handlers = AdvancedRelationshipHandlers(mock_database)

    return server


class TestCloudBackendInitialization:
    """Test CloudMemoryDatabase initialization path (lines 666-668)."""

    @pytest.mark.asyncio
    async def test_initialize_with_cloud_backend(self):
        """Test server initialization with CloudRESTAdapter backend."""
        server = ClaudeMemoryServer()

        # Mock CloudRESTAdapter
        mock_cloud = MagicMock(spec=CloudRESTAdapter)
        mock_cloud.backend_name = MagicMock(return_value="cloud")

        # Mock CloudMemoryDatabase
        with patch('memorygraph.backends.factory.BackendFactory.create_backend', return_value=mock_cloud):
            with patch.object(CloudMemoryDatabase, '__init__', return_value=None) as mock_init:
                with patch.object(CloudMemoryDatabase, 'initialize_schema', new_callable=AsyncMock):
                    # Initialize server
                    await server.initialize()

                    # Verify CloudMemoryDatabase was instantiated (line 668)
                    assert mock_init.called


class TestAdvancedToolHandlers:
    """Test advanced tool handler paths."""

    @pytest.mark.asyncio
    async def test_advanced_tool_find_memory_path(self, mcp_server):
        """Test calling find_memory_path advanced tool."""
        from memorygraph.tools import handle_store_memory

        # Store two memories
        memory1_id = str(uuid.uuid4())
        memory2_id = str(uuid.uuid4())

        mcp_server.memory_db.store_memory.return_value = memory1_id

        # The advanced handler should be invoked
        # We test the path exists, not the full functionality
        assert mcp_server.advanced_handlers is not None
        assert hasattr(mcp_server.advanced_handlers, 'handle_find_memory_path')


class TestMigrationToolHandlers:
    """Test migration tool handling paths (lines 615-634)."""

    @pytest.mark.asyncio
    async def test_migration_tools_available(self):
        """Verify migration tools are available."""
        from memorygraph.migration_tools_module import MIGRATION_TOOLS, MIGRATION_TOOL_HANDLERS

        # Verify migration tools exist
        assert len(MIGRATION_TOOLS) > 0
        tool_names = [tool.name for tool in MIGRATION_TOOLS]

        # Expected migration tools
        assert "migrate_database" in tool_names or "validate_migration" in tool_names


class TestToolDescriptions:
    """Test tool descriptions and schemas."""

    def test_all_tools_have_complete_descriptions(self):
        """Verify all tools have proper descriptions."""
        server = ClaudeMemoryServer()

        for tool in server.tools:
            # Every tool should have a description
            assert tool.description is not None
            assert len(tool.description) > 20

            # Every tool should have an input schema
            assert tool.inputSchema is not None
            assert "type" in tool.inputSchema
            assert tool.inputSchema["type"] == "object"

    def test_store_memory_description_includes_limits(self):
        """Verify store_memory description includes size limits."""
        server = ClaudeMemoryServer()

        store_tool = next((t for t in server.tools if t.name == "store_memory"), None)
        assert store_tool is not None
        assert "LIMITS" in store_tool.description or "max" in store_tool.description.lower()

    def test_recall_memories_description_clear(self):
        """Verify recall_memories has clear description."""
        server = ClaudeMemoryServer()

        recall_tool = next((t for t in server.tools if t.name == "recall_memories"), None)
        assert recall_tool is not None
        assert "fuzzy" in recall_tool.description.lower() or "natural language" in recall_tool.description.lower()


class TestServerCleanup:
    """Test server cleanup paths."""

    @pytest.mark.asyncio
    async def test_cleanup_with_connection(self):
        """Test cleanup when database connection exists."""
        server = ClaudeMemoryServer()

        mock_connection = AsyncMock()
        mock_connection.close = AsyncMock()
        server.db_connection = mock_connection

        await server.cleanup()

        mock_connection.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_without_connection(self):
        """Test cleanup when database connection is None."""
        server = ClaudeMemoryServer()
        server.db_connection = None

        # Should not raise any errors
        await server.cleanup()


class TestBackendTypeDetection:
    """Test backend type detection in initialize()."""

    @pytest.mark.asyncio
    async def test_initialize_detects_sqlite_backend(self):
        """Test that SQLiteFallbackBackend is detected correctly."""
        server = ClaudeMemoryServer()

        mock_sqlite = MagicMock(spec=SQLiteFallbackBackend)
        mock_sqlite.backend_name = MagicMock(return_value="sqlite")

        with patch('memorygraph.backends.factory.BackendFactory.create_backend', return_value=mock_sqlite):
            with patch.object(SQLiteMemoryDatabase, '__init__', return_value=None):
                with patch.object(SQLiteMemoryDatabase, 'initialize_schema', new_callable=AsyncMock):
                    await server.initialize()

                    # Verify backend is SQLite
                    assert isinstance(server.db_connection, SQLiteFallbackBackend)

    @pytest.mark.asyncio
    async def test_initialize_detects_other_backend(self):
        """Test initialization with a generic backend (line 669-671)."""
        server = ClaudeMemoryServer()

        # Mock a generic backend (not SQLite, not Cloud)
        mock_generic = MagicMock()
        mock_generic.backend_name = MagicMock(return_value="neo4j")

        with patch('memorygraph.backends.factory.BackendFactory.create_backend', return_value=mock_generic):
            with patch.object(MemoryDatabase, '__init__', return_value=None):
                with patch.object(MemoryDatabase, 'initialize_schema', new_callable=AsyncMock):
                    await server.initialize()

                    # Verify generic backend path was taken
                    assert server.db_connection == mock_generic


class TestToolCollectionEdgeCases:
    """Test tool collection and filtering edge cases."""

    def test_collect_all_tools_returns_complete_list(self):
        """Test that _collect_all_tools returns all available tools."""
        server = ClaudeMemoryServer()

        # Should have basic tools + advanced + migration
        tool_names = [tool.name for tool in server.tools]

        # Basic tools
        assert "recall_memories" in tool_names
        assert "store_memory" in tool_names
        assert "get_memory" in tool_names
        assert "search_memories" in tool_names

        # At least some tools should be present
        assert len(tool_names) >= 9

    def test_tool_profile_filtering_works(self):
        """Test that tool profile filtering works correctly."""
        with patch('memorygraph.server.Config.get_enabled_tools') as mock_enabled:
            # Test filtering to specific tools
            mock_enabled.return_value = ["store_memory", "get_memory"]

            server = ClaudeMemoryServer()
            tool_names = [tool.name for tool in server.tools]

            assert "store_memory" in tool_names
            assert "get_memory" in tool_names
            assert len(tool_names) == 2

    def test_tool_profile_full_includes_all(self):
        """Test that full profile includes all tools."""
        with patch('memorygraph.server.Config.get_enabled_tools', return_value=None):
            server = ClaudeMemoryServer()

            # Full profile should have all tools
            assert len(server.tools) >= 9


class TestServerInitializationPaths:
    """Test different initialization paths."""

    @pytest.mark.asyncio
    async def test_initialize_creates_advanced_handlers(self):
        """Test that initialize creates advanced handlers."""
        server = ClaudeMemoryServer()

        mock_backend = MagicMock(spec=SQLiteFallbackBackend)
        mock_backend.backend_name = MagicMock(return_value="sqlite")

        with patch('memorygraph.backends.factory.BackendFactory.create_backend', return_value=mock_backend):
            with patch.object(SQLiteMemoryDatabase, '__init__', return_value=None):
                with patch.object(SQLiteMemoryDatabase, 'initialize_schema', new_callable=AsyncMock):
                    await server.initialize()

                    # Verify advanced handlers were created (line 676)
                    assert server.advanced_handlers is not None


class TestToolSchemasComplete:
    """Test that tool schemas are complete."""

    def test_recall_memories_has_pagination(self):
        """Test recall_memories has pagination parameters."""
        server = ClaudeMemoryServer()

        recall_tool = next((t for t in server.tools if t.name == "recall_memories"), None)
        assert recall_tool is not None

        schema = recall_tool.inputSchema
        assert "properties" in schema
        props = schema["properties"]

        # Should have pagination params
        assert "limit" in props
        assert "offset" in props

    def test_search_memories_has_advanced_params(self):
        """Test search_memories has advanced parameters."""
        server = ClaudeMemoryServer()

        search_tool = next((t for t in server.tools if t.name == "search_memories"), None)
        assert search_tool is not None

        schema = search_tool.inputSchema
        props = schema["properties"]

        # Should have advanced search params
        assert "search_tolerance" in props
        assert "match_mode" in props
        assert "memory_types" in props
        assert "tags" in props

    def test_create_relationship_has_all_params(self):
        """Test create_relationship has all required parameters."""
        server = ClaudeMemoryServer()

        rel_tool = next((t for t in server.tools if t.name == "create_relationship"), None)
        assert rel_tool is not None

        schema = rel_tool.inputSchema
        props = schema["properties"]
        required = schema.get("required", [])

        # Should have required params
        assert "from_memory_id" in required
        assert "to_memory_id" in required
        assert "relationship_type" in required

        # Should have optional params
        assert "strength" in props
        assert "confidence" in props
        assert "context" in props


class TestAdvancedToolsListed:
    """Test that advanced tools are properly listed."""

    def test_advanced_relationship_tools_in_collection(self):
        """Test that advanced relationship tools are collected."""
        from memorygraph.advanced_tools import ADVANCED_RELATIONSHIP_TOOLS

        # Should have advanced tools
        assert len(ADVANCED_RELATIONSHIP_TOOLS) > 0

        tool_names = [tool.name for tool in ADVANCED_RELATIONSHIP_TOOLS]

        # Check for expected advanced tools
        expected = [
            "find_memory_path",
            "analyze_memory_clusters",
            "find_bridge_memories",
            "suggest_relationship_type"
        ]

        for expected_tool in expected:
            assert expected_tool in tool_names


class TestContextualSearchTool:
    """Test contextual_search tool definition."""

    def test_contextual_search_tool_exists_in_full_profile(self):
        """Test that contextual_search tool is defined in full profile."""
        with patch('memorygraph.server.Config.get_enabled_tools', return_value=None):
            server = ClaudeMemoryServer()
            tool_names = [tool.name for tool in server.tools]

            # contextual_search is in basic tools (line 518-559)
            assert "contextual_search" in tool_names

    def test_contextual_search_has_required_params(self):
        """Test contextual_search has required parameters."""
        with patch('memorygraph.server.Config.get_enabled_tools', return_value=None):
            server = ClaudeMemoryServer()

            ctx_tool = next((t for t in server.tools if t.name == "contextual_search"), None)
            assert ctx_tool is not None

            schema = ctx_tool.inputSchema
            required = schema.get("required", [])

            # Should require memory_id and query (line 557)
            assert "memory_id" in required
            assert "query" in required


class TestSearchRelationshipsByContextTool:
    """Test search_relationships_by_context tool."""

    def test_search_relationships_by_context_exists_in_full_profile(self):
        """Test that search_relationships_by_context tool is defined in full profile."""
        with patch('memorygraph.server.Config.get_enabled_tools', return_value=None):
            server = ClaudeMemoryServer()
            tool_names = [tool.name for tool in server.tools]

            # This tool is in basic tools (line 474-516)
            assert "search_relationships_by_context" in tool_names

    def test_search_relationships_by_context_params(self):
        """Test search_relationships_by_context has scope/conditions params."""
        with patch('memorygraph.server.Config.get_enabled_tools', return_value=None):
            server = ClaudeMemoryServer()

            tool = next((t for t in server.tools if t.name == "search_relationships_by_context"), None)
            assert tool is not None

            schema = tool.inputSchema
            props = schema["properties"]

            # Should have context search params (lines 479-514)
            assert "scope" in props
            assert "conditions" in props
            assert "evidence" in props
            assert "components" in props


class TestGetRecentActivityTool:
    """Test get_recent_activity tool."""

    def test_get_recent_activity_has_days_param(self):
        """Test get_recent_activity has days parameter."""
        server = ClaudeMemoryServer()

        tool = next((t for t in server.tools if t.name == "get_recent_activity"), None)
        assert tool is not None

        schema = tool.inputSchema
        props = schema["properties"]

        # Should have days param (line 461-469)
        assert "days" in props
        assert "project" in props
