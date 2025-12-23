"""Comprehensive tests for temporal_tools module."""
import pytest
from unittest.mock import AsyncMock
from datetime import datetime, timezone, timedelta
from mcp.types import CallToolResult, TextContent

from memorygraph.tools.temporal_tools import (
    handle_query_as_of,
    handle_get_relationship_history,
    handle_what_changed
)
from memorygraph.models import (
    Memory,
    MemoryType,
    Relationship,
    RelationshipType,
    RelationshipProperties
)


class TestQueryAsOf:
    """Test query_as_of handler."""

    @pytest.mark.asyncio
    async def test_query_as_of_success(self):
        """Test successful point-in-time query."""
        mock_db = AsyncMock()

        # Mock memory exists
        mock_memory = Memory(
            id='mem-1',
            type=MemoryType.SOLUTION,
            title='Test Memory',
            content='Test content',
            created_at=datetime.now(timezone.utc)
        )
        mock_db.get_memory = AsyncMock(return_value=mock_memory)

        # Mock related memories at that time
        related_memory = Memory(
            id='mem-2',
            type=MemoryType.PROBLEM,
            title='Related Problem',
            content='Problem content',
            importance=0.8,
            created_at=datetime.now(timezone.utc)
        )

        relationship = Relationship(
            id='rel-1',
            from_memory_id='mem-1',
            to_memory_id='mem-2',
            type=RelationshipType.SOLVES,
            properties=RelationshipProperties(
                strength=0.9,
                valid_from=datetime.now(timezone.utc) - timedelta(days=10)
            )
        )

        mock_db.get_related_memories = AsyncMock(return_value=[
            (related_memory, relationship)
        ])

        result = await handle_query_as_of(mock_db, {
            'memory_id': 'mem-1',
            'as_of': '2024-12-01T00:00:00Z'
        })

        assert not result.isError
        text = result.content[0].text

        assert 'Relationships as of 2024-12-01T00:00:00Z' in text
        assert 'Related Problem' in text
        assert 'SOLVES' in text
        assert 'strength: 0.9' in text

    @pytest.mark.asyncio
    async def test_query_as_of_memory_not_found(self):
        """Test when memory doesn't exist."""
        mock_db = AsyncMock()
        mock_db.get_memory = AsyncMock(return_value=None)

        result = await handle_query_as_of(mock_db, {
            'memory_id': 'nonexistent',
            'as_of': '2024-12-01T00:00:00Z'
        })

        assert result.isError
        assert 'Memory not found: nonexistent' in result.content[0].text

    @pytest.mark.asyncio
    async def test_query_as_of_invalid_timestamp(self):
        """Test with invalid timestamp format."""
        mock_db = AsyncMock()

        result = await handle_query_as_of(mock_db, {
            'memory_id': 'mem-1',
            'as_of': 'invalid-timestamp'
        })

        assert result.isError
        assert 'Invalid timestamp format' in result.content[0].text
        assert 'ISO 8601' in result.content[0].text

    @pytest.mark.asyncio
    async def test_query_as_of_no_relationships(self):
        """Test when no relationships found at that time."""
        mock_db = AsyncMock()

        mock_memory = Memory(
            id='mem-1',
            type=MemoryType.TASK,
            title='Test Task',
            content='Task content',
            created_at=datetime.now(timezone.utc)
        )
        mock_db.get_memory = AsyncMock(return_value=mock_memory)
        mock_db.get_related_memories = AsyncMock(return_value=[])

        result = await handle_query_as_of(mock_db, {
            'memory_id': 'mem-1',
            'as_of': '2024-01-01T00:00:00Z'
        })

        assert not result.isError
        text = result.content[0].text
        assert "No relationships found" in text
        assert "as of 2024-01-01T00:00:00Z" in text

    @pytest.mark.asyncio
    async def test_query_as_of_with_relationship_filter(self):
        """Test with relationship type filter."""
        mock_db = AsyncMock()

        mock_memory = Memory(
            id='mem-1',
            type=MemoryType.SOLUTION,
            title='Solution',
            content='Content',
            created_at=datetime.now(timezone.utc)
        )
        mock_db.get_memory = AsyncMock(return_value=mock_memory)
        mock_db.get_related_memories = AsyncMock(return_value=[])

        result = await handle_query_as_of(mock_db, {
            'memory_id': 'mem-1',
            'as_of': '2024-12-01T00:00:00Z',
            'relationship_types': ['SOLVES', 'ADDRESSES']
        })

        assert not result.isError
        # Verify the relationship types were passed correctly
        call_args = mock_db.get_related_memories.call_args
        assert call_args[1]['relationship_types'] is not None

    @pytest.mark.asyncio
    async def test_query_as_of_with_valid_until(self):
        """Test displaying valid_until when present."""
        mock_db = AsyncMock()

        mock_memory = Memory(
            id='mem-1',
            type=MemoryType.SOLUTION,
            title='Test',
            content='Content',
            created_at=datetime.now(timezone.utc)
        )
        mock_db.get_memory = AsyncMock(return_value=mock_memory)

        related = Memory(
            id='mem-2',
            type=MemoryType.PROBLEM,
            title='Problem',
            content='Content',
            created_at=datetime.now(timezone.utc)
        )

        # Relationship that was later invalidated
        relationship = Relationship(
            id='rel-1',
            from_memory_id='mem-1',
            to_memory_id='mem-2',
            type=RelationshipType.SOLVES,
            properties=RelationshipProperties(
                strength=0.8,
                valid_from=datetime(2024, 1, 1, tzinfo=timezone.utc),
                valid_until=datetime(2024, 6, 1, tzinfo=timezone.utc)
            )
        )

        mock_db.get_related_memories = AsyncMock(return_value=[(related, relationship)])

        result = await handle_query_as_of(mock_db, {
            'memory_id': 'mem-1',
            'as_of': '2024-03-01T00:00:00Z'
        })

        assert not result.isError
        text = result.content[0].text
        assert 'Valid until: 2024-06-01' in text

    @pytest.mark.asyncio
    async def test_query_as_of_missing_memory_id(self):
        """Test error when memory_id is missing."""
        mock_db = AsyncMock()

        result = await handle_query_as_of(mock_db, {
            'as_of': '2024-12-01T00:00:00Z'
        })

        assert result.isError
        assert 'Missing required field' in result.content[0].text

    @pytest.mark.asyncio
    async def test_query_as_of_missing_as_of(self):
        """Test error when as_of is missing."""
        mock_db = AsyncMock()

        result = await handle_query_as_of(mock_db, {
            'memory_id': 'mem-1'
        })

        assert result.isError
        assert 'Missing required field' in result.content[0].text


class TestGetRelationshipHistory:
    """Test get_relationship_history handler."""

    @pytest.mark.asyncio
    async def test_relationship_history_success(self):
        """Test successful history retrieval."""
        mock_db = AsyncMock()

        mock_memory = Memory(
            id='mem-1',
            type=MemoryType.SOLUTION,
            title='Test',
            content='Content',
            created_at=datetime.now(timezone.utc)
        )
        mock_db.get_memory = AsyncMock(return_value=mock_memory)

        # Current relationship
        current_rel = Relationship(
            id='rel-1',
            from_memory_id='mem-1',
            to_memory_id='mem-2',
            type=RelationshipType.SOLVES,
            properties=RelationshipProperties(
                strength=0.9,
                confidence=0.8,
                valid_from=datetime.now(timezone.utc),
                context='{"summary": "Current solution"}'
            )
        )

        # Historical (invalidated) relationship
        old_rel = Relationship(
            id='rel-2',
            from_memory_id='mem-1',
            to_memory_id='mem-3',
            type=RelationshipType.RELATED_TO,
            properties=RelationshipProperties(
                strength=0.5,
                valid_from=datetime.now(timezone.utc) - timedelta(days=30),
                valid_until=datetime.now(timezone.utc) - timedelta(days=10),
                invalidated_by='rel-1'
            )
        )

        mock_db.get_relationship_history = AsyncMock(return_value=[current_rel, old_rel])

        result = await handle_get_relationship_history(mock_db, {
            'memory_id': 'mem-1'
        })

        assert not result.isError
        text = result.content[0].text

        assert 'Relationship History for mem-1' in text
        assert '2 relationships' in text
        assert 'Current Relationships:' in text
        assert 'SOLVES' in text
        assert 'Strength: 0.9 | Confidence: 0.8' in text
        assert 'Context: Current solution' in text
        assert 'Historical (Invalidated) Relationships:' in text
        assert 'RELATED_TO' in text
        assert 'Superseded by: rel-1' in text

    @pytest.mark.asyncio
    async def test_relationship_history_memory_not_found(self):
        """Test when memory doesn't exist."""
        mock_db = AsyncMock()
        mock_db.get_memory = AsyncMock(return_value=None)

        result = await handle_get_relationship_history(mock_db, {
            'memory_id': 'nonexistent'
        })

        assert result.isError
        assert 'Memory not found: nonexistent' in result.content[0].text

    @pytest.mark.asyncio
    async def test_relationship_history_no_history(self):
        """Test when memory has no relationship history."""
        mock_db = AsyncMock()

        mock_memory = Memory(
            id='mem-1',
            type=MemoryType.TASK,
            title='Isolated Task',
            content='Content',
            created_at=datetime.now(timezone.utc)
        )
        mock_db.get_memory = AsyncMock(return_value=mock_memory)
        mock_db.get_relationship_history = AsyncMock(return_value=[])

        result = await handle_get_relationship_history(mock_db, {
            'memory_id': 'mem-1'
        })

        assert not result.isError
        text = result.content[0].text
        assert 'No relationship history found' in text

    @pytest.mark.asyncio
    async def test_relationship_history_with_type_filter(self):
        """Test with relationship type filter."""
        mock_db = AsyncMock()

        mock_memory = Memory(
            id='mem-1',
            type=MemoryType.SOLUTION,
            title='Test',
            content='Content',
            created_at=datetime.now(timezone.utc)
        )
        mock_db.get_memory = AsyncMock(return_value=mock_memory)
        mock_db.get_relationship_history = AsyncMock(return_value=[])

        result = await handle_get_relationship_history(mock_db, {
            'memory_id': 'mem-1',
            'relationship_types': ['SOLVES', 'ADDRESSES']
        })

        assert not result.isError
        # Verify type filter was passed
        call_args = mock_db.get_relationship_history.call_args
        assert call_args[1]['relationship_types'] is not None

    @pytest.mark.asyncio
    async def test_relationship_history_malformed_context(self):
        """Test handling of malformed JSON context."""
        mock_db = AsyncMock()

        mock_memory = Memory(
            id='mem-1',
            type=MemoryType.SOLUTION,
            title='Test',
            content='Content',
            created_at=datetime.now(timezone.utc)
        )
        mock_db.get_memory = AsyncMock(return_value=mock_memory)

        rel = Relationship(
            id='rel-1',
            from_memory_id='mem-1',
            to_memory_id='mem-2',
            type=RelationshipType.SOLVES,
            properties=RelationshipProperties(
                strength=0.9,
                confidence=0.8,
                valid_from=datetime.now(timezone.utc),
                context='invalid-json{'
            )
        )

        mock_db.get_relationship_history = AsyncMock(return_value=[rel])

        result = await handle_get_relationship_history(mock_db, {
            'memory_id': 'mem-1'
        })

        # Should not crash, just skip the malformed context
        assert not result.isError
        text = result.content[0].text
        assert 'SOLVES' in text

    @pytest.mark.asyncio
    async def test_relationship_history_missing_memory_id(self):
        """Test error when memory_id is missing."""
        mock_db = AsyncMock()

        result = await handle_get_relationship_history(mock_db, {})

        assert result.isError
        assert 'Missing required field' in result.content[0].text


class TestWhatChanged:
    """Test what_changed handler."""

    @pytest.mark.asyncio
    async def test_what_changed_success(self):
        """Test successful change tracking."""
        mock_db = AsyncMock()

        # New relationship
        new_rel = Relationship(
            id='rel-new',
            from_memory_id='mem-1',
            to_memory_id='mem-2',
            type=RelationshipType.SOLVES,
            properties=RelationshipProperties(
                strength=0.9,
                recorded_at=datetime.now(timezone.utc),
                context='{"summary": "New solution found"}'
            )
        )

        # Invalidated relationship
        invalidated_rel = Relationship(
            id='rel-old',
            from_memory_id='mem-1',
            to_memory_id='mem-3',
            type=RelationshipType.RELATED_TO,
            properties=RelationshipProperties(
                strength=0.5,
                valid_from=datetime.now(timezone.utc) - timedelta(days=30),
                valid_until=datetime.now(timezone.utc),
                invalidated_by='rel-new'
            )
        )

        mock_db.what_changed = AsyncMock(return_value={
            'new_relationships': [new_rel],
            'invalidated_relationships': [invalidated_rel]
        })

        result = await handle_what_changed(mock_db, {
            'since': '2024-01-01T00:00:00Z'
        })

        assert not result.isError
        text = result.content[0].text

        assert 'Changes since 2024-01-01T00:00:00Z' in text
        assert 'New Relationships (1):' in text
        assert 'SOLVES' in text
        assert 'Strength: 0.9' in text
        assert 'Context: New solution found' in text
        assert 'Invalidated Relationships (1):' in text
        assert 'RELATED_TO' in text
        assert 'Superseded by: rel-new' in text

    @pytest.mark.asyncio
    async def test_what_changed_no_changes(self):
        """Test when no changes found."""
        mock_db = AsyncMock()
        mock_db.what_changed = AsyncMock(return_value={
            'new_relationships': [],
            'invalidated_relationships': []
        })

        result = await handle_what_changed(mock_db, {
            'since': '2024-12-01T00:00:00Z'
        })

        assert not result.isError
        text = result.content[0].text
        assert 'No relationship changes found since 2024-12-01T00:00:00Z' in text

    @pytest.mark.asyncio
    async def test_what_changed_only_new(self):
        """Test when only new relationships exist."""
        mock_db = AsyncMock()

        new_rel = Relationship(
            id='rel-1',
            from_memory_id='mem-1',
            to_memory_id='mem-2',
            type=RelationshipType.CAUSES,
            properties=RelationshipProperties(
                strength=0.8,
                recorded_at=datetime.now(timezone.utc)
            )
        )

        mock_db.what_changed = AsyncMock(return_value={
            'new_relationships': [new_rel],
            'invalidated_relationships': []
        })

        result = await handle_what_changed(mock_db, {
            'since': '2024-01-01T00:00:00Z'
        })

        assert not result.isError
        text = result.content[0].text
        assert 'New Relationships (1):' in text
        assert 'CAUSES' in text
        # Should not show invalidated section
        assert 'Invalidated Relationships' not in text

    @pytest.mark.asyncio
    async def test_what_changed_only_invalidated(self):
        """Test when only invalidated relationships exist."""
        mock_db = AsyncMock()

        invalidated_rel = Relationship(
            id='rel-1',
            from_memory_id='mem-1',
            to_memory_id='mem-2',
            type=RelationshipType.REQUIRES,
            properties=RelationshipProperties(
                strength=0.7,
                valid_from=datetime.now(timezone.utc) - timedelta(days=30),
                valid_until=datetime.now(timezone.utc)
            )
        )

        mock_db.what_changed = AsyncMock(return_value={
            'new_relationships': [],
            'invalidated_relationships': [invalidated_rel]
        })

        result = await handle_what_changed(mock_db, {
            'since': '2024-01-01T00:00:00Z'
        })

        assert not result.isError
        text = result.content[0].text
        assert 'Invalidated Relationships (1):' in text
        assert 'REQUIRES' in text
        # Should not show new relationships section
        assert 'New Relationships' not in text

    @pytest.mark.asyncio
    async def test_what_changed_invalid_timestamp(self):
        """Test with invalid timestamp format."""
        mock_db = AsyncMock()

        result = await handle_what_changed(mock_db, {
            'since': 'not-a-valid-timestamp'
        })

        assert result.isError
        assert 'Invalid timestamp format' in result.content[0].text
        assert 'ISO 8601' in result.content[0].text

    @pytest.mark.asyncio
    async def test_what_changed_malformed_context(self):
        """Test handling of malformed JSON context."""
        mock_db = AsyncMock()

        new_rel = Relationship(
            id='rel-1',
            from_memory_id='mem-1',
            to_memory_id='mem-2',
            type=RelationshipType.SOLVES,
            properties=RelationshipProperties(
                strength=0.9,
                recorded_at=datetime.now(timezone.utc),
                context='malformed-json['
            )
        )

        mock_db.what_changed = AsyncMock(return_value={
            'new_relationships': [new_rel],
            'invalidated_relationships': []
        })

        result = await handle_what_changed(mock_db, {
            'since': '2024-01-01T00:00:00Z'
        })

        # Should not crash, just skip the malformed context
        assert not result.isError
        text = result.content[0].text
        assert 'SOLVES' in text

    @pytest.mark.asyncio
    async def test_what_changed_missing_since(self):
        """Test error when since parameter is missing."""
        mock_db = AsyncMock()

        result = await handle_what_changed(mock_db, {})

        assert result.isError
        assert 'Missing required field' in result.content[0].text

    @pytest.mark.asyncio
    async def test_what_changed_database_error(self):
        """Test error handling when database fails."""
        mock_db = AsyncMock()
        mock_db.what_changed = AsyncMock(side_effect=Exception("Database error"))

        result = await handle_what_changed(mock_db, {
            'since': '2024-01-01T00:00:00Z'
        })

        assert result.isError
        assert 'Failed to get what changed' in result.content[0].text

    @pytest.mark.asyncio
    async def test_what_changed_multiple_new_relationships(self):
        """Test with multiple new relationships."""
        mock_db = AsyncMock()

        rels = [
            Relationship(
                id=f'rel-{i}',
                from_memory_id='mem-1',
                to_memory_id=f'mem-{i+2}',
                type=RelationshipType.SOLVES,
                properties=RelationshipProperties(
                    strength=0.9 - (i * 0.1),
                    recorded_at=datetime.now(timezone.utc)
                )
            )
            for i in range(5)
        ]

        mock_db.what_changed = AsyncMock(return_value={
            'new_relationships': rels,
            'invalidated_relationships': []
        })

        result = await handle_what_changed(mock_db, {
            'since': '2024-01-01T00:00:00Z'
        })

        assert not result.isError
        text = result.content[0].text
        assert 'New Relationships (5):' in text
        # Verify all relationships are listed
        for i in range(5):
            assert f'rel-{i}' not in text  # IDs aren't shown, but relationships are
