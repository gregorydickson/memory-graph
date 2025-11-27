"""
Backend abstraction layer for the Claude Code Memory Server.

This package provides a unified interface for different graph database backends,
allowing the memory server to work with Neo4j, Memgraph, or SQLite.
"""

from .base import GraphBackend
from .factory import BackendFactory
from .neo4j_backend import Neo4jBackend
from .memgraph_backend import MemgraphBackend
from .sqlite_fallback import SQLiteFallbackBackend

__all__ = [
    "GraphBackend",
    "BackendFactory",
    "Neo4jBackend",
    "MemgraphBackend",
    "SQLiteFallbackBackend"
]
