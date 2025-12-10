"""
Unit tests for LadybugDB backend implementation.

These tests use mocked real_ladybug client to verify backend logic without
requiring a running LadybugDB instance.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime, timezone
import uuid
import sys
import os

# Check if real_ladybug is available
try:
    import real_ladybug
    LADYBUGDB_AVAILABLE = True
except ImportError:
    LADYBUGDB_AVAILABLE = False
    # Mock it for testing
    sys.modules['real_ladybug'] = Mock()

# Always import since we mock it
from memorygraph.backends.ladybugdb_backend import LadybugDBBackend

from memorygraph.models import (
    Memory,
    MemoryType,
    RelationshipType,
    RelationshipProperties,
    DatabaseConnectionError,
    SchemaError,
    ValidationError,
    RelationshipError,
)


def setup_mock_ladybug(result_set=None):
    """
    Helper to set up mock LadybugDB client with proper result handling.

    Args:
        result_set: The result set to return from queries

    Returns:
        Tuple of (mock_client, mock_connection, mock_Database_class)
    """
    mock_client = Mock()
    mock_connection = Mock()
    mock_result = Mock()

    # Set up the result to behave like LadybugDB QueryResult
    if result_set:
        mock_result.has_next.side_effect = [True] * len(result_set) + [False]
        mock_result.get_next.side_effect = result_set
    else:
        mock_result.has_next.return_value = False

    mock_connection.execute.return_value = mock_result

    mock_Database_class = Mock(return_value=mock_client)
    mock_Connection_class = Mock(return_value=mock_connection)

    return (
        mock_client,
        mock_connection,
        mock_Database_class,
        mock_Database_class,
        mock_Connection_class,
    )


class TestLadybugDBConnection:
    """Test LadybugDB connection management."""

    @pytest.mark.asyncio
    @patch("memorygraph.backends.ladybugdb_backend.lb")
    async def test_connect_success(self, mock_lb):
        """Test successful connection to LadybugDB."""
        (
            mock_client,
            mock_connection,
            mock_Database,
            mock_Database_class,
            mock_Connection_class,
        ) = setup_mock_ladybug()

        mock_lb.Database = mock_Database_class
        mock_lb.Connection = mock_Connection_class

        backend = LadybugDBBackend(db_path="/tmp/test.db")
        result = await backend.connect()

        assert result is True
        assert backend._connected is True
        # Verify connection was created with file path
        mock_Database_class.assert_called_once_with("/tmp/test.db")
        # Verify Connection was created with the database
        mock_Connection_class.assert_called_once_with(mock_client)

    @pytest.mark.asyncio
    @patch("memorygraph.backends.ladybugdb_backend.lb")
    async def test_connect_failure(self, mock_lb):
        """Test connection failure handling."""
        mock_Database = Mock(side_effect=Exception("Database file not accessible"))
        mock_lb.Database = mock_Database

        backend = LadybugDBBackend(db_path="/invalid/path/test.db")

        with pytest.raises(
            DatabaseConnectionError, match="Database file not accessible"
        ):
            await backend.connect()

    @pytest.mark.asyncio
    @patch("memorygraph.backends.ladybugdb_backend.lb")
    async def test_disconnect(self, mock_lb):
        """Test disconnection from LadybugDB."""
        (
            mock_client,
            mock_connection,
            mock_Database,
            mock_Database_class,
            mock_Connection_class,
        ) = setup_mock_ladybug()

        mock_lb.Database = mock_Database_class
        mock_lb.Connection = mock_Connection_class

        backend = LadybugDBBackend(db_path="/tmp/test.db")
        await backend.connect()
        await backend.disconnect()

        assert backend._connected is False
        mock_client.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("memorygraph.backends.ladybugdb_backend.lb")
    async def test_default_path(self, mock_lb):
        """Test default database path is used when none specified."""
        (
            mock_client,
            mock_connection,
            mock_Database,
            mock_Database_class,
            mock_Connection_class,
        ) = setup_mock_ladybug()

        mock_lb.Database = mock_Database_class
        mock_lb.Connection = mock_Connection_class

        backend = LadybugDBBackend()
        await backend.connect()

        # Should use default path
        mock_Database_class.assert_called_once()
        call_args = mock_Database_class.call_args[0]
        assert call_args[0].endswith(".memorygraph/ladybugdb.db")

    @pytest.mark.asyncio
    @patch("memorygraph.backends.ladybugdb_backend.lb")
    async def test_custom_graph_name(self, mock_lb):
        """Test custom graph name is stored (though not currently used in connection)."""
        (
            mock_client,
            mock_connection,
            mock_Database,
            mock_Database_class,
            mock_Connection_class,
        ) = setup_mock_ladybug()

        mock_lb.Database = mock_Database_class
        mock_lb.Connection = mock_Connection_class

        backend = LadybugDBBackend(db_path="/tmp/test.db", graph_name="custom_graph")
        await backend.connect()

        assert backend.graph_name == "custom_graph"
        # Connection is still made normally
        mock_Database_class.assert_called_once_with("/tmp/test.db")
        mock_Connection_class.assert_called_once_with(mock_client)


class TestLadybugDBQueryExecution:
    """Test LadybugDB query execution."""

    @pytest.mark.asyncio
    @patch("memorygraph.backends.ladybugdb_backend.lb")
    async def test_execute_query_success(self, mock_lb):
        """Test successful query execution."""
        mock_result_data = [{"id": 1, "name": "test"}, {"id": 2, "name": "test2"}]
        (
            mock_client,
            mock_connection,
            mock_Database,
            mock_Database_class,
            mock_Connection_class,
        ) = setup_mock_ladybug(mock_result_data)

        mock_lb.Database = mock_Database_class
        mock_lb.Connection = mock_Connection_class

        backend = LadybugDBBackend(db_path="/tmp/test.db")
        await backend.connect()

        result = await backend.execute_query("MATCH (n) RETURN n", write=False)

        assert result == mock_result_data
        mock_connection.execute.assert_called_once_with("MATCH (n) RETURN n")

    @pytest.mark.asyncio
    @patch("memorygraph.backends.ladybugdb_backend.lb")
    async def test_execute_query_with_parameters(self, mock_lb):
        """Test query execution with parameters (note: LadybugDB doesn't support parameterized queries)."""
        mock_result_data = [{"count": 5}]
        (
            mock_client,
            mock_connection,
            mock_Database,
            mock_Database_class,
            mock_Connection_class,
        ) = setup_mock_ladybug(mock_result_data)

        mock_lb.Database = mock_Database_class
        mock_lb.Connection = mock_Connection_class

        backend = LadybugDBBackend(db_path="/tmp/test.db")
        await backend.connect()

        # LadybugDB doesn't support parameters, so they are ignored
        params = {"name": "test_node"}
        result = await backend.execute_query(
            "MATCH (n {name: 'test_node'}) RETURN count(n) as count",
            params,
            write=False,
        )

        assert result == mock_result_data
        mock_connection.execute.assert_called_once_with(
            "MATCH (n {name: 'test_node'}) RETURN count(n) as count"
        )

    @pytest.mark.asyncio
    @patch("memorygraph.backends.ladybugdb_backend.lb")
    async def test_execute_query_write_operation(self, mock_lb):
        """Test write query execution."""
        mock_result_data = []
        (
            mock_client,
            mock_connection,
            mock_Database,
            mock_Database_class,
            mock_Connection_class,
        ) = setup_mock_ladybug(mock_result_data)

        mock_lb.Database = mock_Database_class
        mock_lb.Connection = mock_Connection_class

        backend = LadybugDBBackend(db_path="/tmp/test.db")
        await backend.connect()

        result = await backend.execute_query(
            "CREATE (n:Node {name: 'test'})", write=True
        )

        assert result == mock_result_data
        mock_connection.execute.assert_called_once_with(
            "CREATE (n:Node {name: 'test'})"
        )

    @pytest.mark.asyncio
    async def test_execute_query_not_connected(self):
        """Test query execution when not connected."""
        backend = LadybugDBBackend(db_path="/tmp/test.db")

        with pytest.raises(DatabaseConnectionError, match="Not connected to LadybugDB"):
            await backend.execute_query("MATCH (n) RETURN n")

    @pytest.mark.asyncio
    @patch("memorygraph.backends.ladybugdb_backend.lb")
    async def test_execute_query_error(self, mock_lb):
        """Test query execution error handling."""
        (
            mock_client,
            mock_connection,
            mock_Database,
            mock_Database_class,
            mock_Connection_class,
        ) = setup_mock_ladybug()

        mock_lb.Database = mock_Database_class
        mock_lb.Connection = mock_Connection_class

        mock_connection.execute.side_effect = Exception("Query syntax error")

        backend = LadybugDBBackend(db_path="/tmp/test.db")
        await backend.connect()

        with pytest.raises(
            SchemaError, match="Query execution failed: Query syntax error"
        ):
            await backend.execute_query("INVALID QUERY")


class TestLadybugDBBackendInitialization:
    """Test LadybugDB backend initialization."""

    def test_init_with_path(self):
        """Test initialization with custom path."""
        backend = LadybugDBBackend(
            db_path="/custom/path/db.db", graph_name="test_graph"
        )

        assert backend.db_path == "/custom/path/db.db"
        assert backend.graph_name == "test_graph"
        assert backend._connected is False
        assert backend.client is None
        assert backend.graph is None

    def test_init_defaults(self):
        """Test initialization with defaults."""
        backend = LadybugDBBackend()

        assert backend.graph_name == "memorygraph"
        assert backend._connected is False
        assert backend.client is None
        assert backend.graph is None
        # db_path will be set to default in connect()

    @pytest.mark.asyncio
    @patch("memorygraph.backends.ladybugdb_backend.lb")
    async def test_connect_sets_default_path(self, mock_lb):
        """Test that connect sets default path when none provided."""
        (
            mock_client,
            mock_connection,
            mock_Database,
            mock_Database_class,
            mock_Connection_class,
        ) = setup_mock_ladybug()

        mock_lb.Database = mock_Database_class
        mock_lb.Connection = mock_Connection_class

        backend = LadybugDBBackend()
        await backend.connect()

        # Should have set a default path
        assert backend.db_path is not None
        assert ".memorygraph/ladybugdb.db" in backend.db_path


class TestLadybugDBParameterPassing:
    """Test parameter passing in queries (CRITICAL BUG)."""

    @pytest.mark.asyncio
    @patch("memorygraph.backends.ladybugdb_backend.lb")
    async def test_execute_query_parameters_are_used(self, mock_lb):
        """Test that parameters are properly passed to queries.

        CRITICAL: This test verifies the fix for the parameter passing bug.
        Currently, execute_query() accepts parameters but never uses them.
        """
        mock_result_data = [{"id": "123", "name": "test"}]
        (
            mock_client,
            mock_connection,
            mock_Database,
            mock_Database_class,
            mock_Connection_class,
        ) = setup_mock_ladybug(mock_result_data)

        mock_lb.Database = mock_Database_class
        mock_lb.Connection = mock_Connection_class

        backend = LadybugDBBackend(db_path="/tmp/test.db")
        await backend.connect()

        # Execute query with parameters
        # Parameters should be substituted into the query
        params = {"node_id": "123", "node_name": "test"}
        query = "MATCH (n) WHERE n.id = $node_id AND n.name = $node_name RETURN n"

        result = await backend.execute_query(query, params, write=False)

        # Verify the query was transformed to use actual values
        # Since LadybugDB doesn't support parameterized queries like Neo4j,
        # we need to substitute parameters into the query string
        expected_query = "MATCH (n) WHERE n.id = '123' AND n.name = 'test' RETURN n"
        mock_connection.execute.assert_called_once_with(expected_query)
        assert result == mock_result_data

    @pytest.mark.asyncio
    @patch("memorygraph.backends.ladybugdb_backend.lb")
    async def test_execute_query_handles_different_param_types(self, mock_lb):
        """Test parameter substitution with different data types."""
        mock_result_data = [{"count": 5}]
        (
            mock_client,
            mock_connection,
            mock_Database,
            mock_Database_class,
            mock_Connection_class,
        ) = setup_mock_ladybug(mock_result_data)

        mock_lb.Database = mock_Database_class
        mock_lb.Connection = mock_Connection_class

        backend = LadybugDBBackend(db_path="/tmp/test.db")
        await backend.connect()

        # Test with integer, string, and float parameters
        params = {
            "int_val": 42,
            "str_val": "test",
            "float_val": 3.14,
            "bool_val": True
        }
        query = "MATCH (n) WHERE n.age = $int_val AND n.name = $str_val RETURN n"

        await backend.execute_query(query, params, write=False)

        # Verify parameter substitution
        call_args = mock_connection.execute.call_args[0][0]
        assert "42" in call_args  # Integer substituted
        assert "'test'" in call_args  # String quoted


class TestLadybugDBStronglyTypedSchema:
    """Test strongly-typed schema initialization (12 NODE + 35 REL tables)."""

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"MEMORY_LADYBUGDB_STRONGLY_TYPED": "true"})
    @patch("memorygraph.backends.ladybugdb_backend.lb")
    async def test_strongly_typed_schema_creates_12_node_tables(self, mock_lb):
        """Test that strongly-typed mode creates 12 separate NODE tables."""
        # Reload config to pick up the patched environment variable
        from importlib import reload
        import memorygraph.config as config_module
        reload(config_module)

        queries_executed = []

        def track_query(query):
            queries_executed.append(query)
            mock_result = Mock()
            mock_result.has_next.return_value = False
            return mock_result

        mock_client = Mock()
        mock_connection = Mock()
        mock_connection.execute.side_effect = track_query

        mock_lb.Database = Mock(return_value=mock_client)
        mock_lb.Connection = Mock(return_value=mock_connection)

        backend = LadybugDBBackend(db_path="/tmp/test.db")
        await backend.connect()
        await backend.initialize_schema()

        # Verify 12 NODE TABLEs were created (one for each MemoryType)
        expected_node_types = [
            "TASK", "CODE_PATTERN", "PROBLEM", "SOLUTION", "PROJECT",
            "TECHNOLOGY", "ERROR", "FIX", "COMMAND", "FILE_CONTEXT",
            "WORKFLOW", "GENERAL"
        ]

        for node_type in expected_node_types:
            create_table_found = any(
                f"CREATE NODE TABLE IF NOT EXISTS {node_type}" in query
                for query in queries_executed
            )
            assert create_table_found, f"Missing NODE TABLE for {node_type}"

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"MEMORY_LADYBUGDB_STRONGLY_TYPED": "true"})
    @patch("memorygraph.backends.ladybugdb_backend.lb")
    async def test_strongly_typed_schema_creates_35_rel_tables(self, mock_lb):
        """Test that strongly-typed mode creates 35 separate REL tables."""
        # Reload config to pick up the patched environment variable
        from importlib import reload
        import memorygraph.config as config_module
        reload(config_module)

        queries_executed = []

        def track_query(query):
            queries_executed.append(query)
            mock_result = Mock()
            mock_result.has_next.return_value = False
            return mock_result

        mock_client = Mock()
        mock_connection = Mock()
        mock_connection.execute.side_effect = track_query

        mock_lb.Database = Mock(return_value=mock_client)
        mock_lb.Connection = Mock(return_value=mock_connection)

        backend = LadybugDBBackend(db_path="/tmp/test.db")
        await backend.connect()
        await backend.initialize_schema()

        # Verify all 35 REL TABLEs were created
        expected_rel_types = [
            "CAUSES", "TRIGGERS", "LEADS_TO", "PREVENTS", "BREAKS",
            "SOLVES", "ADDRESSES", "ALTERNATIVE_TO", "IMPROVES", "REPLACES",
            "OCCURS_IN", "APPLIES_TO", "WORKS_WITH", "REQUIRES", "USED_IN",
            "BUILDS_ON", "CONTRADICTS", "CONFIRMS", "GENERALIZES", "SPECIALIZES",
            "SIMILAR_TO", "VARIANT_OF", "RELATED_TO", "ANALOGY_TO", "OPPOSITE_OF",
            "FOLLOWS", "DEPENDS_ON", "ENABLES", "BLOCKS", "PARALLEL_TO",
            "EFFECTIVE_FOR", "INEFFECTIVE_FOR", "PREFERRED_OVER", "DEPRECATED_BY", "VALIDATED_BY"
        ]

        for rel_type in expected_rel_types:
            create_rel_found = any(
                f"CREATE REL TABLE IF NOT EXISTS {rel_type}" in query
                for query in queries_executed
            )
            assert create_rel_found, f"Missing REL TABLE for {rel_type}"

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"MEMORY_LADYBUGDB_STRONGLY_TYPED": "false"})
    @patch("memorygraph.backends.ladybugdb_backend.lb")
    async def test_weakly_typed_schema_creates_single_tables(self, mock_lb):
        """Test that weakly-typed mode (default) creates single Memory NODE and REL table."""
        # Reload config to pick up the patched environment variable
        from importlib import reload
        import memorygraph.config as config_module
        reload(config_module)

        queries_executed = []

        def track_query(query):
            queries_executed.append(query)
            mock_result = Mock()
            mock_result.has_next.return_value = False
            return mock_result

        mock_client = Mock()
        mock_connection = Mock()
        mock_connection.execute.side_effect = track_query

        mock_lb.Database = Mock(return_value=mock_client)
        mock_lb.Connection = Mock(return_value=mock_connection)

        backend = LadybugDBBackend(db_path="/tmp/test.db")
        await backend.connect()
        await backend.initialize_schema()

        # Verify single Memory NODE TABLE
        memory_table_found = any(
            "CREATE NODE TABLE IF NOT EXISTS Memory" in query
            for query in queries_executed
        )
        assert memory_table_found, "Missing Memory NODE TABLE in weakly-typed mode"

        # Verify single generic REL TABLE
        rel_table_found = any(
            "CREATE REL TABLE IF NOT EXISTS REL" in query
            for query in queries_executed
        )
        assert rel_table_found, "Missing REL TABLE in weakly-typed mode"


class TestLadybugDBCRUDOperations:
    """Test CRUD operations with strongly-typed schema.

    NOTE: These tests verify that queries use strongly-typed node/rel types
    when strongly-typed mode is enabled. The actual query generation happens
    in MemoryDatabase, which currently uses generic Memory/RELATIONSHIP syntax.
    Full strongly-typed CRUD support would require updating MemoryDatabase
    query generation logic to use the specific node type (SOLUTION vs Memory).

    For now, these tests are marked as expected to fail until we implement
    query generation changes in MemoryDatabase.
    """

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="CRUD with strongly-typed schema requires MemoryDatabase query generation updates")
    @patch.dict(os.environ, {"MEMORY_LADYBUGDB_STRONGLY_TYPED": "true"})
    @patch("memorygraph.backends.ladybugdb_backend.lb")
    async def test_store_memory_uses_correct_node_type(self, mock_lb):
        """Test that storing a memory uses the correct strongly-typed NODE table.

        This test is currently skipped because implementing this requires:
        1. Updating MemoryDatabase.store_memory() to detect backend type
        2. Generating queries with specific node types (e.g., SOLUTION vs Memory)
        3. Handling schema differences between strongly/weakly typed modes
        """
        queries_executed = []

        def track_query(query):
            queries_executed.append(query)
            mock_result = Mock()
            mock_result.has_next.return_value = False
            # For MERGE queries, return a result
            if "MERGE" in query or "CREATE" in query:
                mock_result.has_next.side_effect = [True, False]
                mock_result.get_next.return_value = {"id": "test-id"}
            return mock_result

        mock_client = Mock()
        mock_connection = Mock()
        mock_connection.execute.side_effect = track_query

        mock_lb.Database = Mock(return_value=mock_client)
        mock_lb.Connection = Mock(return_value=mock_connection)

        backend = LadybugDBBackend(db_path="/tmp/test.db")
        await backend.connect()

        # Import MemoryDatabase to use store_memory
        from memorygraph.database import MemoryDatabase
        db = MemoryDatabase(backend)

        # Store a SOLUTION memory
        memory = Memory(
            type=MemoryType.SOLUTION,
            title="Test Solution",
            content="This is a test solution"
        )

        await db.store_memory(memory)

        # In strongly-typed mode, should use SOLUTION NODE table, not Memory
        solution_query_found = any(
            "SOLUTION" in query and "MERGE" in query
            for query in queries_executed
        )
        assert solution_query_found, "Should use SOLUTION node type in strongly-typed mode"

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="CRUD with strongly-typed schema requires MemoryDatabase query generation updates")
    @patch.dict(os.environ, {"MEMORY_LADYBUGDB_STRONGLY_TYPED": "true"})
    @patch("memorygraph.backends.ladybugdb_backend.lb")
    async def test_create_relationship_uses_correct_rel_type(self, mock_lb):
        """Test that relationships use strongly-typed REL tables.

        This test is currently skipped for the same reason as test_store_memory_uses_correct_node_type.
        """
        queries_executed = []

        def track_query(query):
            queries_executed.append(query)
            mock_result = Mock()
            mock_result.has_next.return_value = False
            if "CREATE" in query and "-[" in query:
                mock_result.has_next.side_effect = [True, False]
                mock_result.get_next.return_value = {"id": "rel-id"}
            return mock_result

        mock_client = Mock()
        mock_connection = Mock()
        mock_connection.execute.side_effect = track_query

        mock_lb.Database = Mock(return_value=mock_client)
        mock_lb.Connection = Mock(return_value=mock_connection)

        backend = LadybugDBBackend(db_path="/tmp/test.db")
        await backend.connect()

        from memorygraph.database import MemoryDatabase
        db = MemoryDatabase(backend)

        # Create a SOLVES relationship
        await db.create_relationship(
            from_memory_id="problem-1",
            to_memory_id="solution-1",
            relationship_type=RelationshipType.SOLVES,
            properties=RelationshipProperties()
        )

        # Should use SOLVES REL table
        solves_query_found = any(
            "SOLVES" in query
            for query in queries_executed
        )
        assert solves_query_found, "Should use SOLVES relationship type"


class TestLadybugDBEnvironmentVariables:
    """Test environment variable handling."""

    def test_env_var_memory_ladybugdb_path(self, tmp_path, monkeypatch):
        """Test MEMORY_LADYBUGDB_PATH environment variable is respected."""
        custom_path = str(tmp_path / "custom.db")
        monkeypatch.setenv("MEMORY_LADYBUGDB_PATH", custom_path)

        # Re-import Config and backend to pick up the env var
        from importlib import reload
        import memorygraph.config as config_module
        reload(config_module)

        # Reload backend module to pick up new Config
        import memorygraph.backends.ladybugdb_backend as backend_module
        reload(backend_module)

        # Import the reloaded backend class
        from memorygraph.backends.ladybugdb_backend import LadybugDBBackend as ReloadedBackend

        # Verify Config picked up the env var
        from memorygraph.config import Config
        assert Config.LADYBUGDB_PATH == custom_path

        # Create backend (it reads from Config)
        backend = ReloadedBackend()

        assert backend.db_path == custom_path

    @patch.dict(os.environ, {"MEMORY_LADYBUGDB_STRONGLY_TYPED": "true"})
    def test_env_var_strongly_typed_enabled(self):
        """Test MEMORY_LADYBUGDB_STRONGLY_TYPED=true is recognized."""
        from importlib import reload
        import memorygraph.config as config_module
        reload(config_module)

        from memorygraph.config import Config
        assert Config.LADYBUGDB_STRONGLY_TYPED is True

    @patch.dict(os.environ, {"MEMORY_LADYBUGDB_STRONGLY_TYPED": "false"})
    def test_env_var_strongly_typed_disabled(self):
        """Test MEMORY_LADYBUGDB_STRONGLY_TYPED=false is recognized."""
        from importlib import reload
        import memorygraph.config as config_module
        reload(config_module)

        from memorygraph.config import Config
        assert Config.LADYBUGDB_STRONGLY_TYPED is False
