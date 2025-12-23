"""Comprehensive tests for activity_tools module."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from mcp.types import CallToolResult, TextContent
from datetime import datetime, timezone

from memorygraph.tools.activity_tools import (
    handle_get_memory_statistics,
    handle_get_recent_activity,
    handle_search_relationships_by_context,
    _get_memory_attr
)
from memorygraph.models import Memory, MemoryType, Relationship, RelationshipType, RelationshipProperties


class TestGetMemoryAttr:
    """Test _get_memory_attr helper function."""

    def test_get_attr_from_memory_object(self):
        """Test getting attribute from Memory object."""
        memory = Memory(
            id="test-123",
            type=MemoryType.SOLUTION,
            title="Test Memory",
            content="Test content"
        )

        assert _get_memory_attr(memory, 'title') == "Test Memory"
        assert _get_memory_attr(memory, 'id') == "test-123"

    def test_get_attr_from_dict(self):
        """Test getting attribute from dict representation."""
        memory_dict = {
            'id': 'test-123',
            'title': 'Test Memory',
            'type': 'solution'
        }

        assert _get_memory_attr(memory_dict, 'title') == "Test Memory"
        assert _get_memory_attr(memory_dict, 'id') == "test-123"

    def test_get_attr_with_default(self):
        """Test default value when attribute not found."""
        memory_dict = {'id': 'test-123'}

        assert _get_memory_attr(memory_dict, 'missing', 'default') == 'default'
        assert _get_memory_attr(memory_dict, 'missing') is None

    def test_get_type_with_value_attr(self):
        """Test handling type attribute with .value."""
        memory = Memory(
            type=MemoryType.SOLUTION,
            title="Test",
            content="Test content"
        )

        # Type has a .value attribute which should be returned
        result = _get_memory_attr(memory, 'type')
        assert result == 'solution'


class TestGetMemoryStatistics:
    """Test get_memory_statistics handler."""

    @pytest.mark.asyncio
    async def test_statistics_success(self):
        """Test successful statistics retrieval."""
        mock_db = AsyncMock()
        mock_db.get_memory_statistics = AsyncMock(return_value={
            'total_memories': {'count': 100},
            'memories_by_type': {'solution': 50, 'problem': 30, 'task': 20},
            'total_relationships': {'count': 200},
            'avg_importance': {'avg_importance': 0.75},
            'avg_confidence': {'avg_confidence': 0.85}
        })

        result = await handle_get_memory_statistics(mock_db, {})

        assert not result.isError
        assert isinstance(result.content[0], TextContent)
        text = result.content[0].text

        assert 'Total Memories: 100' in text
        assert 'solution: 50' in text
        assert 'problem: 30' in text
        assert 'Total Relationships: 200' in text
        assert 'Average Importance: 0.75' in text
        assert 'Average Confidence: 0.85' in text

    @pytest.mark.asyncio
    async def test_statistics_empty_db(self):
        """Test statistics on empty database."""
        mock_db = AsyncMock()
        mock_db.get_memory_statistics = AsyncMock(return_value={
            'total_memories': {'count': 0},
            'memories_by_type': {},
            'total_relationships': {'count': 0}
        })

        result = await handle_get_memory_statistics(mock_db, {})

        assert not result.isError
        text = result.content[0].text
        assert 'Total Memories: 0' in text
        assert 'Total Relationships: 0' in text

    @pytest.mark.asyncio
    async def test_statistics_with_partial_data(self):
        """Test statistics with partial data available."""
        mock_db = AsyncMock()
        mock_db.get_memory_statistics = AsyncMock(return_value={
            'total_memories': {'count': 10},
            'memories_by_type': {'solution': 10}
            # Missing other fields
        })

        result = await handle_get_memory_statistics(mock_db, {})

        assert not result.isError
        text = result.content[0].text
        assert 'Total Memories: 10' in text
        assert 'solution: 10' in text
        # Should not crash with missing fields

    @pytest.mark.asyncio
    async def test_statistics_database_error(self):
        """Test error handling when database fails."""
        mock_db = AsyncMock()
        mock_db.get_memory_statistics = AsyncMock(side_effect=Exception("Database connection failed"))

        result = await handle_get_memory_statistics(mock_db, {})

        assert result.isError
        assert "Failed to get memory statistics" in result.content[0].text


class TestGetRecentActivity:
    """Test get_recent_activity handler."""

    @pytest.mark.asyncio
    @patch('memorygraph.utils.project_detection.detect_project_context')
    async def test_recent_activity_success(self, mock_detect):
        """Test successful recent activity retrieval."""
        mock_detect.return_value = None  # No auto-detection for this test

        mock_db = AsyncMock()

        # Mock memories
        mock_memory = Memory(
            id='mem-1',
            type=MemoryType.SOLUTION,
            title='Test Solution',
            content='Test content',
            summary='Test summary',
            created_at=datetime.now(timezone.utc)
        )

        mock_problem = Memory(
            id='prob-1',
            type=MemoryType.PROBLEM,
            title='Unresolved Problem',
            content='Problem content',
            importance=0.8,
            created_at=datetime.now(timezone.utc)
        )

        mock_db.get_recent_activity = AsyncMock(return_value={
            'total_count': 2,
            'memories_by_type': {'solution': 1, 'problem': 1},
            'recent_memories': [mock_memory],
            'unresolved_problems': [mock_problem],
            'days': 7
        })

        result = await handle_get_recent_activity(mock_db, {'days': 7})

        assert not result.isError
        text = result.content[0].text

        assert 'Last 7 days' in text
        assert 'Total Memories**: 2' in text  # Note the ** formatting
        assert 'Solution: 1' in text
        assert 'Problem: 1' in text
        assert 'Unresolved Problems' in text
        assert 'Test Solution' in text
        assert 'Unresolved Problem' in text

    @pytest.mark.asyncio
    async def test_recent_activity_custom_days(self):
        """Test with custom days parameter."""
        mock_db = AsyncMock()
        mock_db.get_recent_activity = AsyncMock(return_value={
            'total_count': 5,
            'memories_by_type': {'task': 5},
            'recent_memories': [],
            'unresolved_problems': [],
            'days': 30
        })

        result = await handle_get_recent_activity(mock_db, {'days': 30})

        assert not result.isError
        text = result.content[0].text
        assert 'Last 30 days' in text

    @pytest.mark.asyncio
    async def test_recent_activity_with_project(self):
        """Test filtering by project."""
        mock_db = AsyncMock()
        mock_db.get_recent_activity = AsyncMock(return_value={
            'total_count': 3,
            'memories_by_type': {'solution': 3},
            'recent_memories': [],
            'unresolved_problems': [],
            'days': 7,
            'project': '/test/project'
        })

        result = await handle_get_recent_activity(mock_db, {
            'days': 7,
            'project': '/test/project'
        })

        assert not result.isError
        text = result.content[0].text
        assert '/test/project' in text

    @pytest.mark.asyncio
    async def test_recent_activity_no_problems(self):
        """Test when there are no unresolved problems."""
        mock_db = AsyncMock()
        mock_db.get_recent_activity = AsyncMock(return_value={
            'total_count': 10,
            'memories_by_type': {'solution': 10},
            'recent_memories': [],
            'unresolved_problems': [],
            'days': 7
        })

        result = await handle_get_recent_activity(mock_db, {'days': 7})

        assert not result.isError
        text = result.content[0].text
        assert 'All problems have been addressed!' in text

    @pytest.mark.asyncio
    async def test_recent_activity_with_dict_memories(self):
        """Test with dict representations of memories."""
        mock_db = AsyncMock()

        # Return dicts instead of Memory objects
        mock_db.get_recent_activity = AsyncMock(return_value={
            'total_count': 1,
            'memories_by_type': {'solution': 1},
            'recent_memories': [{
                'id': 'mem-1',
                'title': 'Dict Memory',
                'type': 'solution',
                'summary': 'Dict summary'
            }],
            'unresolved_problems': [{
                'id': 'prob-1',
                'title': 'Dict Problem',
                'type': 'problem',
                'importance': 0.7
            }],
            'days': 7
        })

        result = await handle_get_recent_activity(mock_db, {'days': 7})

        assert not result.isError
        text = result.content[0].text
        assert 'Dict Memory' in text
        assert 'Dict Problem' in text

    @pytest.mark.asyncio
    @patch('memorygraph.utils.project_detection.detect_project_context')
    async def test_recent_activity_unsupported_backend(self, mock_detect):
        """Test when backend doesn't support get_recent_activity."""
        mock_detect.return_value = None
        # Create a mock without get_recent_activity attribute
        mock_db = AsyncMock(spec=[])  # Empty spec = no methods

        result = await handle_get_recent_activity(mock_db, {'days': 7})

        assert result.isError
        assert 'not supported by this backend' in result.content[0].text

    @pytest.mark.asyncio
    @patch('memorygraph.utils.project_detection.detect_project_context')
    async def test_recent_activity_auto_detect_project(self, mock_detect):
        """Test auto-detection of project when not specified."""
        mock_detect.return_value = {'project_path': '/auto/detected/project'}

        mock_db = AsyncMock()
        mock_db.get_recent_activity = AsyncMock(return_value={
            'total_count': 0,
            'memories_by_type': {},
            'recent_memories': [],
            'unresolved_problems': [],
            'days': 7
        })

        result = await handle_get_recent_activity(mock_db, {})

        # Verify project was auto-detected and passed
        mock_db.get_recent_activity.assert_called_once_with(
            days=7,
            project='/auto/detected/project'
        )

    @pytest.mark.asyncio
    async def test_recent_activity_database_error(self):
        """Test error handling when database fails."""
        mock_db = AsyncMock()
        mock_db.get_recent_activity = AsyncMock(side_effect=Exception("Database error"))

        result = await handle_get_recent_activity(mock_db, {'days': 7})

        assert result.isError
        assert "Failed to get recent activity" in result.content[0].text


class TestSearchRelationshipsByContext:
    """Test search_relationships_by_context handler."""

    @pytest.mark.asyncio
    async def test_search_by_context_success(self):
        """Test successful context search."""
        mock_db = AsyncMock()

        # Create mock relationships
        rel1 = Relationship(
            id='rel-1',
            from_memory_id='mem-1',
            to_memory_id='mem-2',
            type=RelationshipType.SOLVES,
            properties=RelationshipProperties(
                strength=0.9,
                context='Test context'
            )
        )

        rel2 = Relationship(
            id='rel-2',
            from_memory_id='mem-3',
            to_memory_id='mem-4',
            type=RelationshipType.CAUSES,
            properties=RelationshipProperties(
                strength=0.7
            )
        )

        mock_db.search_relationships_by_context = AsyncMock(return_value=[rel1, rel2])

        result = await handle_search_relationships_by_context(mock_db, {
            'scope': 'full',
            'limit': 20
        })

        assert not result.isError
        text = result.content[0].text

        assert 'Found 2 relationships' in text
        assert 'SOLVES' in text
        assert 'CAUSES' in text
        assert 'Strength: 0.90' in text
        assert 'Strength: 0.70' in text
        assert 'Context: Test context' in text

    @pytest.mark.asyncio
    async def test_search_by_context_no_results(self):
        """Test when no relationships found."""
        mock_db = AsyncMock()
        mock_db.search_relationships_by_context = AsyncMock(return_value=[])

        result = await handle_search_relationships_by_context(mock_db, {})

        assert not result.isError
        text = result.content[0].text
        assert 'No relationships found' in text

    @pytest.mark.asyncio
    async def test_search_by_context_with_filters(self):
        """Test with multiple filter parameters."""
        mock_db = AsyncMock()

        rel = Relationship(
            id='rel-1',
            from_memory_id='mem-1',
            to_memory_id='mem-2',
            type=RelationshipType.REQUIRES,
            properties=RelationshipProperties(strength=0.8)
        )

        mock_db.search_relationships_by_context = AsyncMock(return_value=[rel])

        result = await handle_search_relationships_by_context(mock_db, {
            'scope': 'partial',
            'conditions': ['when A', 'when B'],
            'has_evidence': True,
            'evidence': ['empirical', 'theoretical'],
            'components': ['component1', 'component2'],
            'temporal': 'during development',
            'limit': 50
        })

        assert not result.isError
        text = result.content[0].text

        # Verify filters are displayed
        assert 'Filters Applied:' in text
        assert 'Scope: partial' in text
        assert 'Conditions: when A, when B' in text
        assert 'Has Evidence: True' in text
        assert 'Evidence: empirical, theoretical' in text
        assert 'Components: component1, component2' in text
        assert 'Temporal: during development' in text

    @pytest.mark.asyncio
    async def test_search_by_context_unsupported_backend(self):
        """Test when backend doesn't support context search."""
        # Create a mock without the search_relationships_by_context attribute
        mock_db = AsyncMock(spec=[])  # Empty spec means no methods

        result = await handle_search_relationships_by_context(mock_db, {})

        assert result.isError
        assert 'not supported by this backend' in result.content[0].text

    @pytest.mark.asyncio
    async def test_search_by_context_database_error(self):
        """Test error handling when database fails."""
        mock_db = AsyncMock()
        mock_db.search_relationships_by_context = AsyncMock(
            side_effect=Exception("Database error")
        )

        result = await handle_search_relationships_by_context(mock_db, {})

        assert result.isError
        assert "Failed to search relationships by context" in result.content[0].text

    @pytest.mark.asyncio
    async def test_search_by_context_no_filters(self):
        """Test search with no filters applied."""
        mock_db = AsyncMock()

        rel = Relationship(
            id='rel-1',
            from_memory_id='mem-1',
            to_memory_id='mem-2',
            type=RelationshipType.RELATED_TO,
            properties=RelationshipProperties(strength=0.5)
        )

        mock_db.search_relationships_by_context = AsyncMock(return_value=[rel])

        result = await handle_search_relationships_by_context(mock_db, {'limit': 20})

        assert not result.isError
        text = result.content[0].text

        # Should not show "Filters Applied:" section when no filters
        assert 'Found 1 relationship' in text
        # Filters section should not appear or should be empty

    @pytest.mark.asyncio
    async def test_search_by_context_partial_filters(self):
        """Test with only some filters specified."""
        mock_db = AsyncMock()

        # Return at least one relationship so filters are shown
        rel = Relationship(
            id='rel-1',
            from_memory_id='mem-1',
            to_memory_id='mem-2',
            type=RelationshipType.RELATED_TO,
            properties=RelationshipProperties(strength=0.5)
        )
        mock_db.search_relationships_by_context = AsyncMock(return_value=[rel])

        result = await handle_search_relationships_by_context(mock_db, {
            'scope': 'conditional',
            'has_evidence': False
        })

        assert not result.isError
        text = result.content[0].text

        # Should show only the filters that were applied
        assert 'Scope: conditional' in text
        assert 'Has Evidence: False' in text
