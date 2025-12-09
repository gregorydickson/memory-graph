"""
Cloud-specific database implementation for MemoryGraph.

This module provides a CloudMemoryDatabase class that wraps the CloudBackend
to provide the same interface as MemoryDatabase for tool handlers.
"""

import logging
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone

from .models import (
    Memory, MemoryType, Relationship, RelationshipType,
    RelationshipProperties, SearchQuery, MemoryContext,
    MemoryError, MemoryNotFoundError, RelationshipError,
    ValidationError, DatabaseConnectionError, SchemaError, PaginatedResult
)
from .backends.cloud_backend import CloudBackend

logger = logging.getLogger(__name__)


class CloudMemoryDatabase:
    """Cloud-specific implementation of memory database operations.

    This class wraps CloudBackend to provide the same interface expected by
    the MCP tool handlers, delegating to the CloudBackend's REST API methods.
    """

    def __init__(self, backend: CloudBackend) -> None:
        """
        Initialize with a Cloud backend connection.

        Args:
            backend: CloudBackend instance
        """
        self.backend = backend

    async def close(self) -> None:
        """Close the backend connection."""
        if self.backend:
            await self.backend.disconnect()

    async def initialize_schema(self) -> None:
        """
        Initialize schema (no-op for cloud backend).

        Schema is managed by the cloud service.
        """
        logger.info("Schema initialization skipped - managed by cloud service")
        await self.backend.initialize_schema()

    async def store_memory(self, memory: Memory) -> str:
        """
        Store a memory in the cloud and return its ID.

        Args:
            memory: Memory object to store

        Returns:
            ID of the stored memory

        Raises:
            DatabaseConnectionError: If storage fails
        """
        if not memory.id:
            memory.id = str(uuid.uuid4())

        return await self.backend.store_memory(memory)

    async def get_memory(self, memory_id: str, include_relationships: bool = True) -> Optional[Memory]:
        """
        Retrieve a memory by ID.

        Args:
            memory_id: ID of the memory to retrieve
            include_relationships: Whether to include relationships (not currently used by cloud backend)

        Returns:
            Memory object if found, None otherwise

        Raises:
            DatabaseConnectionError: If query fails
        """
        return await self.backend.get_memory(memory_id)

    async def search_memories(self, search_query: SearchQuery) -> List[Memory]:
        """
        Search for memories based on query parameters.

        Args:
            search_query: SearchQuery object with filter criteria

        Returns:
            List of Memory objects matching the search criteria

        Raises:
            DatabaseConnectionError: If search fails
        """
        return await self.backend.search_memories(search_query)

    async def search_memories_paginated(self, search_query: SearchQuery) -> PaginatedResult:
        """
        Search for memories with pagination support.

        Note: Cloud API does not return total count, so total_count is set to -1
        to indicate unknown. Use has_more to determine if more pages exist.

        Args:
            search_query: SearchQuery object with filter criteria, limit, and offset

        Returns:
            PaginatedResult with memories and pagination metadata.
            total_count is -1 (unknown) since cloud API doesn't provide it.

        Raises:
            DatabaseConnectionError: If search fails
        """
        # CloudBackend's search_memories already handles pagination via limit/offset
        memories = await self.backend.search_memories(search_query)

        # Cloud API doesn't return total count - use -1 to indicate unknown
        # has_more is determined by whether we got a full page of results
        has_more = len(memories) == search_query.limit
        next_offset = (search_query.offset + search_query.limit) if has_more else None

        return PaginatedResult(
            results=memories,
            total_count=-1,  # Unknown - cloud API doesn't provide total count
            limit=search_query.limit,
            offset=search_query.offset,
            has_more=has_more,
            next_offset=next_offset
        )

    async def update_memory(self, memory: Memory) -> bool:
        """
        Update an existing memory.

        Args:
            memory: Memory object with updated fields

        Returns:
            True if update succeeded, False if memory not found

        Raises:
            ValidationError: If memory ID is missing
            DatabaseConnectionError: If update fails due to connection issues
        """
        if not memory.id:
            raise ValidationError("Memory must have an ID to update")

        # Convert memory to update dict
        updates = {
            "title": memory.title,
            "content": memory.content,
            "summary": memory.summary,
            "tags": memory.tags,
            "importance": memory.importance,
        }

        # Remove None values
        updates = {k: v for k, v in updates.items() if v is not None}

        try:
            result = await self.backend.update_memory(memory.id, updates)
            return result is not None
        except MemoryNotFoundError:
            # Memory doesn't exist - return False as per interface contract
            return False

    async def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory and all its relationships.

        Args:
            memory_id: ID of the memory to delete

        Returns:
            True if deletion succeeded, False otherwise

        Raises:
            DatabaseConnectionError: If deletion fails
        """
        return await self.backend.delete_memory(memory_id)

    async def create_relationship(
        self,
        from_memory_id: str,
        to_memory_id: str,
        relationship_type: RelationshipType,
        properties: RelationshipProperties = None
    ) -> str:
        """
        Create a relationship between two memories.

        Args:
            from_memory_id: Source memory ID
            to_memory_id: Target memory ID
            relationship_type: Type of relationship
            properties: Relationship properties (optional)

        Returns:
            ID of the created relationship

        Raises:
            RelationshipError: If relationship creation fails
            DatabaseConnectionError: If database operation fails
        """
        return await self.backend.create_relationship(
            from_memory_id=from_memory_id,
            to_memory_id=to_memory_id,
            relationship_type=relationship_type,
            properties=properties
        )

    async def get_related_memories(
        self,
        memory_id: str,
        relationship_types: List[RelationshipType] = None,
        max_depth: int = 2
    ) -> List[Tuple[Memory, Relationship]]:
        """
        Get memories related to a specific memory.

        Args:
            memory_id: ID of the memory to find relations for
            relationship_types: Filter by specific relationship types (optional)
            max_depth: Maximum depth for graph traversal

        Returns:
            List of tuples containing (Memory, Relationship)

        Raises:
            DatabaseConnectionError: If query fails
        """
        return await self.backend.get_related_memories(
            memory_id=memory_id,
            relationship_types=relationship_types,
            max_depth=max_depth
        )

    async def update_relationship_properties(
        self,
        from_memory_id: str,
        to_memory_id: str,
        relationship_type: RelationshipType,
        properties: RelationshipProperties
    ) -> bool:
        """
        Update properties of an existing relationship.

        Note: Cloud backend does not yet support updating relationship properties.

        Args:
            from_memory_id: Source memory ID
            to_memory_id: Target memory ID
            relationship_type: Type of relationship to update
            properties: Updated relationship properties

        Raises:
            NotImplementedError: Cloud backend does not support this operation
        """
        raise NotImplementedError(
            "Cloud backend does not yet support updating relationship properties. "
            f"Attempted to update: {from_memory_id} -{relationship_type.value}-> {to_memory_id}"
        )

    async def get_memory_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics and metrics.

        Returns:
            Dictionary containing various database statistics

        Raises:
            DatabaseConnectionError: If query fails
        """
        return await self.backend.get_statistics()

    async def get_recent_activity(
        self,
        days: int = 7,
        project: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get recent memory activity summary.

        Args:
            days: Number of days to look back
            project: Optional project filter

        Returns:
            Activity summary dictionary
        """
        return await self.backend.get_recent_activity(days=days, project=project)
