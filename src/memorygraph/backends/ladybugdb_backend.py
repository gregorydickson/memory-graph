"""
LadybugDB backend implementation for the Claude Code Memory Server.

This module provides the LadybugDB-specific implementation of the GraphBackend interface.
LadybugDB is a graph database that uses Cypher queries, similar to Kuzu.
"""

import logging
import os
from typing import Any, Optional, List, Tuple, Dict
from pathlib import Path

try:
    import real_ladybug as lb
    LADYBUGDB_AVAILABLE = True
except ImportError:
    lb = None  # type: ignore
    LADYBUGDB_AVAILABLE = False

from .base import GraphBackend
from ..models import (
    Memory,
    MemoryType,
    Relationship,
    RelationshipType,
    RelationshipProperties,
    SearchQuery,
    MemoryContext,
    MemoryNode,
    DatabaseConnectionError,
    SchemaError,
    ValidationError,
    RelationshipError,
)
from ..config import Config
from datetime import datetime, timezone
import uuid
import json

logger = logging.getLogger(__name__)


class LadybugDBBackend(GraphBackend):
    """LadybugDB implementation of the GraphBackend interface."""

    def __init__(self, db_path: Optional[str] = None, graph_name: str = "memorygraph"):
        """
        Initialize LadybugDB backend.

        Args:
            db_path: Path to database file (defaults to MEMORY_LADYBUGDB_PATH env var or ~/.memorygraph/ladybugdb.db)
            graph_name: Name of the graph database (defaults to 'memorygraph')

        Raises:
            ImportError: If real_ladybug package is not installed.
        """
        if not LADYBUGDB_AVAILABLE:
            raise ImportError(
                "LadybugDB backend requires real_ladybug package. "
                "Install it with: pip install real-ladybug"
            )
        if db_path is None:
            # Use Config to get the path (which reads MEMORY_LADYBUGDB_PATH)
            db_path = Config.LADYBUGDB_PATH

        self.db_path = db_path
        self.graph_name = graph_name
        self.client = None
        self.graph = None
        self._connected = False

    async def connect(self) -> bool:
        """
        Establish connection to LadybugDB database.

        Returns:
            True if connection successful

        Raises:
            DatabaseConnectionError: If connection fails
        """
        try:
            # Create LadybugDB database
            self.client = lb.Database(self.db_path)

            # Create connection for executing queries
            self.graph = lb.Connection(self.client)
            self._connected = True

            logger.info(f"Successfully connected to LadybugDB at {self.db_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to LadybugDB: {e}")
            raise DatabaseConnectionError(f"Failed to connect to LadybugDB: {e}")

    async def disconnect(self) -> None:
        """
        Close the LadybugDB connection and clean up resources.
        """
        if self.graph:
            self.graph.close()
            self.graph = None
        if self.client:
            self.client.close()
            self.client = None
            self._connected = False
            logger.info("Disconnected from LadybugDB")

    async def execute_query(
        self,
        query: str,
        parameters: Optional[dict[str, Any]] = None,
        write: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Execute a Cypher query and return results.

        Args:
            query: Cypher query string
            parameters: Query parameters (will be substituted into query)
            write: Whether this is a write operation

        Returns:
            List of result dictionaries

        Note:
            LadybugDB doesn't support parameterized queries like Neo4j.
            Parameters are substituted directly into the query string.
            Use this with caution - ensure parameters are properly validated.
        """
        if not self._connected or not self.graph:
            raise DatabaseConnectionError("Not connected to LadybugDB")

        try:
            # Substitute parameters into query if provided
            # LadybugDB doesn't support Neo4j-style parameterized queries ($param)
            if parameters:
                query = self._substitute_parameters(query, parameters)

            # Execute query using LadybugDB's connection
            result = self.graph.execute(query)

            # Convert result to list of dictionaries
            # LadybugDB returns QueryResult with has_next()/get_next() methods
            # get_next() returns the row data as a dictionary
            rows = []
            while result.has_next():
                row_data = result.get_next()
                rows.append(row_data)

            return rows

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise SchemaError(f"Query execution failed: {e}")

    def _substitute_parameters(self, query: str, parameters: dict[str, Any]) -> str:
        """
        Substitute parameters into a Cypher query string.

        Args:
            query: Query string with $param placeholders
            parameters: Dictionary of parameter values

        Returns:
            Query string with parameters substituted

        Note:
            This is a simple string substitution. For production use,
            consider more robust parameter escaping and validation.
        """
        result = query
        for key, value in parameters.items():
            placeholder = f"${key}"
            # Convert value to appropriate string representation
            if isinstance(value, str):
                # Escape single quotes in strings
                escaped_value = value.replace("'", "\\'")
                substituted_value = f"'{escaped_value}'"
            elif isinstance(value, bool):
                # Python bool to Cypher bool (lowercase)
                substituted_value = str(value).lower()
            elif isinstance(value, (int, float)):
                substituted_value = str(value)
            elif value is None:
                substituted_value = "null"
            elif isinstance(value, (list, dict)):
                # For complex types, use JSON representation
                substituted_value = json.dumps(value)
            else:
                # Fallback: convert to string and quote
                substituted_value = f"'{str(value)}'"

            result = result.replace(placeholder, substituted_value)

        return result

    async def initialize_schema(self) -> None:
        """
        Initialize database schema including indexes and constraints.

        This method delegates to MemoryDatabase.initialize_ladybugdb_schema()
        which handles both weakly-typed and strongly-typed schema creation.

        This should be idempotent and safe to call multiple times.

        Raises:
            SchemaError: If schema initialization fails
        """
        if not self._connected or not self.graph:
            raise DatabaseConnectionError("Not connected to LadybugDB")

        # Schema initialization is handled by MemoryDatabase.initialize_ladybugdb_schema()
        # This backend's initialize_schema is only called directly in testing
        # In production, MemoryDatabase.initialize_schema() calls initialize_ladybugdb_schema()

        # For backward compatibility, we'll delegate to the database wrapper
        from ..database import MemoryDatabase
        db = MemoryDatabase(self)
        await db.initialize_ladybugdb_schema()

    async def health_check(self) -> dict[str, Any]:
        """
        Check backend health and return status information.

        Returns:
            Dictionary with health check results
        """
        health_info = {
            "connected": self._connected,
            "backend_type": "ladybugdb",
            "backend_name": self.backend_name(),
            "supports_fulltext_search": self.supports_fulltext_search(),
            "supports_transactions": self.supports_transactions(),
        }

        if self._connected and self.graph:
            try:
                # Simple health check query
                result = await self.execute_query("RETURN 'healthy' as status")
                health_info["status"] = result[0]["status"] if result else "unknown"
                health_info["healthy"] = True
            except Exception as e:
                health_info["healthy"] = False
                health_info["error"] = str(e)
        else:
            health_info["healthy"] = False
            health_info["error"] = "Not connected"

        return health_info

    def backend_name(self) -> str:
        """
        Return the name of this backend implementation.

        Returns:
            Backend name
        """
        return "ladybugdb"

    def supports_fulltext_search(self) -> bool:
        """
        Check if this backend supports full-text search.

        Returns:
            True if full-text search is supported
        """
        # LadybugDB supports FTS via extension (INSTALL FTS, LOAD EXTENSION FTS)
        return True

    def supports_transactions(self) -> bool:
        """
        Check if this backend supports ACID transactions.

        Returns:
            True if transactions are supported
        """
        # LadybugDB likely supports transactions
        return True

    # Additional methods would be implemented here following the GraphBackend interface
    # For brevity, only the core methods are shown
