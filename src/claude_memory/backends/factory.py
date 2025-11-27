"""
Backend factory for automatic backend selection.

This module provides a factory class that automatically selects the best available
graph database backend based on environment configuration and availability.
"""

import logging
import os
from typing import Optional

from .base import GraphBackend
from .neo4j_backend import Neo4jBackend
from .memgraph_backend import MemgraphBackend
from .sqlite_fallback import SQLiteFallbackBackend
from ..models import DatabaseConnectionError

logger = logging.getLogger(__name__)


class BackendFactory:
    """
    Factory class for creating and selecting graph database backends.

    Selection priority:
    1. If MEMORY_BACKEND env var is set, use that specific backend
    2. Try Neo4j connection (if NEO4J_PASSWORD or MEMORY_NEO4J_PASSWORD is set)
    3. Try Memgraph connection (if available at default URI)
    4. Fall back to SQLite + NetworkX
    """

    @staticmethod
    async def create_backend() -> GraphBackend:
        """
        Create and connect to the best available backend.

        Returns:
            Connected GraphBackend instance

        Raises:
            DatabaseConnectionError: If no backend can be connected

        Selection logic:
        - Explicit: Use MEMORY_BACKEND env var if set
        - Auto: Try backends in order until one connects successfully
        """
        backend_type = os.getenv("MEMORY_BACKEND", "auto").lower()

        if backend_type == "neo4j":
            logger.info("Explicit backend selection: Neo4j")
            return await BackendFactory._create_neo4j()

        elif backend_type == "memgraph":
            logger.info("Explicit backend selection: Memgraph")
            return await BackendFactory._create_memgraph()

        elif backend_type == "sqlite":
            logger.info("Explicit backend selection: SQLite")
            return await BackendFactory._create_sqlite()

        elif backend_type == "auto":
            logger.info("Auto-selecting backend...")
            return await BackendFactory._auto_select_backend()

        else:
            raise DatabaseConnectionError(
                f"Unknown backend type: {backend_type}. "
                f"Valid options: neo4j, memgraph, sqlite, auto"
            )

    @staticmethod
    async def _auto_select_backend() -> GraphBackend:
        """
        Automatically select the best available backend.

        Returns:
            Connected GraphBackend instance

        Raises:
            DatabaseConnectionError: If no backend can be connected
        """
        # Try Neo4j first (if password is configured)
        neo4j_password = os.getenv("MEMORY_NEO4J_PASSWORD") or os.getenv("NEO4J_PASSWORD")
        if neo4j_password:
            try:
                logger.info("Attempting to connect to Neo4j...")
                backend = await BackendFactory._create_neo4j()
                logger.info("✓ Successfully connected to Neo4j backend")
                return backend
            except DatabaseConnectionError as e:
                logger.warning(f"Neo4j connection failed: {e}")

        # Try Memgraph (Community Edition typically has no auth)
        memgraph_uri = os.getenv("MEMORY_MEMGRAPH_URI")
        if memgraph_uri:
            try:
                logger.info("Attempting to connect to Memgraph...")
                backend = await BackendFactory._create_memgraph()
                logger.info("✓ Successfully connected to Memgraph backend")
                return backend
            except DatabaseConnectionError as e:
                logger.warning(f"Memgraph connection failed: {e}")

        # Fall back to SQLite
        try:
            logger.info("Falling back to SQLite backend...")
            backend = await BackendFactory._create_sqlite()
            logger.info("✓ Successfully connected to SQLite backend")
            return backend
        except DatabaseConnectionError as e:
            logger.error(f"SQLite backend failed: {e}")
            raise DatabaseConnectionError(
                "Could not connect to any backend. "
                "Please configure Neo4j, Memgraph, or ensure NetworkX is installed for SQLite fallback."
            )

    @staticmethod
    async def _create_neo4j() -> Neo4jBackend:
        """
        Create and connect to Neo4j backend.

        Returns:
            Connected Neo4jBackend instance

        Raises:
            DatabaseConnectionError: If connection fails
        """
        uri = os.getenv("MEMORY_NEO4J_URI") or os.getenv("NEO4J_URI")
        user = os.getenv("MEMORY_NEO4J_USER") or os.getenv("NEO4J_USER")
        password = os.getenv("MEMORY_NEO4J_PASSWORD") or os.getenv("NEO4J_PASSWORD")

        if not password:
            raise DatabaseConnectionError(
                "Neo4j password not configured. "
                "Set MEMORY_NEO4J_PASSWORD or NEO4J_PASSWORD environment variable."
            )

        backend = Neo4jBackend(uri=uri, user=user, password=password)
        await backend.connect()
        return backend

    @staticmethod
    async def _create_memgraph() -> MemgraphBackend:
        """
        Create and connect to Memgraph backend.

        Returns:
            Connected MemgraphBackend instance

        Raises:
            DatabaseConnectionError: If connection fails
        """
        uri = os.getenv("MEMORY_MEMGRAPH_URI")
        user = os.getenv("MEMORY_MEMGRAPH_USER", "")
        password = os.getenv("MEMORY_MEMGRAPH_PASSWORD", "")

        backend = MemgraphBackend(uri=uri, user=user, password=password)
        await backend.connect()
        return backend

    @staticmethod
    async def _create_sqlite() -> SQLiteFallbackBackend:
        """
        Create and connect to SQLite fallback backend.

        Returns:
            Connected SQLiteFallbackBackend instance

        Raises:
            DatabaseConnectionError: If connection fails
        """
        db_path = os.getenv("MEMORY_SQLITE_PATH")
        backend = SQLiteFallbackBackend(db_path=db_path)
        await backend.connect()
        return backend

    @staticmethod
    def get_configured_backend_type() -> str:
        """
        Get the configured backend type without connecting.

        Returns:
            Backend type string: "neo4j", "memgraph", "sqlite", or "auto"
        """
        return os.getenv("MEMORY_BACKEND", "auto").lower()

    @staticmethod
    def is_backend_configured(backend_type: str) -> bool:
        """
        Check if a specific backend is configured via environment variables.

        Args:
            backend_type: Backend type to check ("neo4j", "memgraph", "sqlite")

        Returns:
            True if backend appears to be configured
        """
        if backend_type == "neo4j":
            return bool(
                os.getenv("MEMORY_NEO4J_PASSWORD") or
                os.getenv("NEO4J_PASSWORD")
            )
        elif backend_type == "memgraph":
            return bool(os.getenv("MEMORY_MEMGRAPH_URI"))
        elif backend_type == "sqlite":
            return True  # SQLite is always available if NetworkX is installed
        else:
            return False
