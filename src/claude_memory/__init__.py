"""
Claude Code Memory Server

A Neo4j-based MCP server that provides intelligent memory capabilities for Claude Code,
enabling persistent knowledge tracking, relationship mapping, and contextual development assistance.
"""

__version__ = "0.1.0"
__author__ = "Claude Code"
__email__ = "claude@anthropic.com"

from .server import ClaudeMemoryServer
from .models import (
    Memory,
    MemoryType,
    Relationship,
    RelationshipType,
    MemoryNode,
    MemoryContext,
    MemoryError,
    MemoryNotFoundError,
    RelationshipError,
    ValidationError,
    DatabaseConnectionError,
    SchemaError,
)

__all__ = [
    "ClaudeMemoryServer",
    "Memory",
    "MemoryType",
    "Relationship",
    "RelationshipType",
    "MemoryNode",
    "MemoryContext",
    "MemoryError",
    "MemoryNotFoundError",
    "RelationshipError",
    "ValidationError",
    "DatabaseConnectionError",
    "SchemaError",
]