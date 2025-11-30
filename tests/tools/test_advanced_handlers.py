"""Tests for advanced MCP tool handlers.

This module tests all handlers in advanced_tools.py with comprehensive
coverage of success cases, error cases, and edge cases.
"""

import pytest
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from memorygraph.advanced_tools import AdvancedRelationshipHandlers
from memorygraph.models import (
    Memory,
    MemoryType,
    Relationship,
    RelationshipType,
    RelationshipProperties,
)
from memorygraph.relationships import RelationshipCategory


@pytest.fixture
def mock_memory_db():
    """Create a mock memory database."""
    db = AsyncMock()
    return db


@pytest.fixture
def handlers(mock_memory_db):
    """Create handlers instance with mock database."""
    return AdvancedRelationshipHandlers(mock_memory_db)


@pytest.fixture
def sample_memory_1():
    """Create first sample memory."""
    return Memory(
        id="mem-1",
        type=MemoryType.PROBLEM,
        title="Test Problem",
        content="A test problem description",
        tags=["test", "problem"],
        importance=0.8,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def sample_memory_2():
    """Create second sample memory."""
    return Memory(
        id="mem-2",
        type=MemoryType.SOLUTION,
        title="Test Solution",
        content="A test solution description",
        tags=["test", "solution"],
        importance=0.9,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def sample_relationship():
    """Create sample relationship."""
    return Relationship(
        from_memory_id="mem-1",
        to_memory_id="mem-2",
        type=RelationshipType.SOLVES,
        strength=0.8,
        confidence=0.9,
        context="Solution addresses problem",
        properties=RelationshipProperties(
            strength=0.8,
            confidence=0.9,
            evidence_count=1,
            success_rate=1.0,
        ),
    )


class TestFindMemoryPath:
    """Tests for find_memory_path handler."""

    async def test_find_memory_path_success(
        self, handlers, mock_memory_db, sample_memory_2, sample_relationship
    ):
        """Test finding path between two memories successfully."""
        # Setup mock to return related memories
        mock_memory_db.get_related_memories.return_value = [
            (sample_memory_2, sample_relationship)
        ]

        # Execute
        result = await handlers.handle_find_memory_path({
            "from_memory_id": "mem-1",
            "to_memory_id": "mem-2",
            "max_depth": 5,
        })

        # Verify
        assert result.isError is None or not result.isError
        content_text = result.content[0].text
        path_info = json.loads(content_text)
        assert path_info["found"] is True
        assert path_info["from_memory_id"] == "mem-1"
        assert path_info["to_memory_id"] == "mem-2"
        mock_memory_db.get_related_memories.assert_called_once()

    async def test_find_memory_path_no_path_exists(self, handlers, mock_memory_db):
        """Test when no path exists between memories."""
        # Setup mock to return empty results
        mock_memory_db.get_related_memories.return_value = []

        # Execute
        result = await handlers.handle_find_memory_path({
            "from_memory_id": "mem-1",
            "to_memory_id": "mem-999",
            "max_depth": 5,
        })

        # Verify
        assert result.isError is None or not result.isError
        content_text = result.content[0].text
        assert "No path found" in content_text

    async def test_find_memory_path_with_relationship_type_filter(
        self, handlers, mock_memory_db, sample_memory_2, sample_relationship
    ):
        """Test finding path with relationship type filtering."""
        # Setup
        mock_memory_db.get_related_memories.return_value = [
            (sample_memory_2, sample_relationship)
        ]

        # Execute with relationship type filter
        result = await handlers.handle_find_memory_path({
            "from_memory_id": "mem-1",
            "to_memory_id": "mem-2",
            "max_depth": 5,
            "relationship_types": ["SOLVES"],
        })

        # Verify
        assert result.isError is None or not result.isError
        # Verify relationship types were converted to enums
        call_args = mock_memory_db.get_related_memories.call_args
        assert call_args[1]["relationship_types"] is not None

    async def test_find_memory_path_default_max_depth(
        self, handlers, mock_memory_db
    ):
        """Test that default max_depth is used when not provided."""
        mock_memory_db.get_related_memories.return_value = []

        result = await handlers.handle_find_memory_path({
            "from_memory_id": "mem-1",
            "to_memory_id": "mem-2",
        })

        # Verify default max_depth=5 was used in keyword args
        call_args = mock_memory_db.get_related_memories.call_args
        assert call_args.kwargs["max_depth"] == 5

    async def test_find_memory_path_error_handling(self, handlers, mock_memory_db):
        """Test error handling when database query fails."""
        # Setup mock to raise exception
        mock_memory_db.get_related_memories.side_effect = Exception("Database error")

        # Execute
        result = await handlers.handle_find_memory_path({
            "from_memory_id": "mem-1",
            "to_memory_id": "mem-2",
        })

        # Verify error response
        assert result.isError is True
        assert "Error finding path" in result.content[0].text


class TestAnalyzeMemoryClusters:
    """Tests for analyze_memory_clusters handler."""

    async def test_analyze_memory_clusters_success(self, handlers, mock_memory_db):
        """Test basic cluster analysis."""
        # Setup mock statistics
        mock_memory_db.get_memory_statistics.return_value = {
            "total_memories": 100,
            "total_relationships": 250,
            "memory_by_type": {"problem": 30, "solution": 40, "task": 30},
        }

        # Execute
        result = await handlers.handle_analyze_memory_clusters({
            "min_cluster_size": 3,
            "min_density": 0.3,
        })

        # Verify
        assert result.isError is None or not result.isError
        content_text = result.content[0].text
        cluster_info = json.loads(content_text)
        assert cluster_info["analysis_type"] == "cluster_detection"
        assert cluster_info["total_memories"] == 100
        assert cluster_info["total_relationships"] == 250

    async def test_analyze_memory_clusters_default_params(
        self, handlers, mock_memory_db
    ):
        """Test cluster analysis with default parameters."""
        mock_memory_db.get_memory_statistics.return_value = {
            "total_memories": 50,
            "total_relationships": 75,
        }

        # Execute without explicit parameters
        result = await handlers.handle_analyze_memory_clusters({})

        # Verify
        assert result.isError is None or not result.isError
        content_text = result.content[0].text
        cluster_info = json.loads(content_text)
        assert "total_memories" in cluster_info

    async def test_analyze_memory_clusters_empty_database(
        self, handlers, mock_memory_db
    ):
        """Test cluster analysis on empty database."""
        mock_memory_db.get_memory_statistics.return_value = {
            "total_memories": 0,
            "total_relationships": 0,
        }

        result = await handlers.handle_analyze_memory_clusters({})

        assert result.isError is None or not result.isError
        content_text = result.content[0].text
        cluster_info = json.loads(content_text)
        assert cluster_info["total_memories"] == 0

    async def test_analyze_memory_clusters_error_handling(
        self, handlers, mock_memory_db
    ):
        """Test error handling when statistics query fails."""
        mock_memory_db.get_memory_statistics.side_effect = Exception("Stats error")

        result = await handlers.handle_analyze_memory_clusters({})

        assert result.isError is True
        assert "Error analyzing clusters" in result.content[0].text


class TestFindBridgeMemories:
    """Tests for find_bridge_memories handler."""

    async def test_find_bridge_memories_success(self, handlers, mock_memory_db):
        """Test finding bridge memories."""
        mock_memory_db.get_memory_statistics.return_value = {
            "total_memories": 100,
            "total_relationships": 150,
        }

        result = await handlers.handle_find_bridge_memories({})

        assert result.isError is None or not result.isError
        content_text = result.content[0].text
        bridge_info = json.loads(content_text)
        assert bridge_info["analysis_type"] == "bridge_detection"
        assert bridge_info["total_memories"] == 100

    async def test_find_bridge_memories_no_memories(self, handlers, mock_memory_db):
        """Test bridge detection with no memories."""
        mock_memory_db.get_memory_statistics.return_value = {
            "total_memories": 0,
        }

        result = await handlers.handle_find_bridge_memories({})

        assert result.isError is None or not result.isError
        content_text = result.content[0].text
        bridge_info = json.loads(content_text)
        assert bridge_info["total_memories"] == 0

    async def test_find_bridge_memories_error_handling(
        self, handlers, mock_memory_db
    ):
        """Test error handling."""
        mock_memory_db.get_memory_statistics.side_effect = Exception("DB error")

        result = await handlers.handle_find_bridge_memories({})

        assert result.isError is True
        assert "Error finding bridges" in result.content[0].text


class TestSuggestRelationshipType:
    """Tests for suggest_relationship_type handler."""

    async def test_suggest_relationship_type_success(
        self, handlers, mock_memory_db, sample_memory_1, sample_memory_2
    ):
        """Test relationship type suggestion."""
        # Setup mocks
        mock_memory_db.get_memory.side_effect = [sample_memory_1, sample_memory_2]

        result = await handlers.handle_suggest_relationship_type({
            "from_memory_id": "mem-1",
            "to_memory_id": "mem-2",
        })

        # Verify
        assert result.isError is None or not result.isError
        content_text = result.content[0].text
        suggestion = json.loads(content_text)
        assert "from_memory" in suggestion
        assert "to_memory" in suggestion
        assert "suggestions" in suggestion
        assert suggestion["from_memory"]["id"] == "mem-1"
        assert suggestion["to_memory"]["id"] == "mem-2"

    async def test_suggest_relationship_type_from_memory_not_found(
        self, handlers, mock_memory_db, sample_memory_2
    ):
        """Test when source memory doesn't exist."""
        mock_memory_db.get_memory.side_effect = [None, sample_memory_2]

        result = await handlers.handle_suggest_relationship_type({
            "from_memory_id": "invalid",
            "to_memory_id": "mem-2",
        })

        assert result.isError is True
        assert "not found" in result.content[0].text

    async def test_suggest_relationship_type_to_memory_not_found(
        self, handlers, mock_memory_db, sample_memory_1
    ):
        """Test when target memory doesn't exist."""
        mock_memory_db.get_memory.side_effect = [sample_memory_1, None]

        result = await handlers.handle_suggest_relationship_type({
            "from_memory_id": "mem-1",
            "to_memory_id": "invalid",
        })

        assert result.isError is True
        assert "not found" in result.content[0].text

    async def test_suggest_relationship_type_error_handling(
        self, handlers, mock_memory_db
    ):
        """Test error handling."""
        mock_memory_db.get_memory.side_effect = Exception("DB error")

        result = await handlers.handle_suggest_relationship_type({
            "from_memory_id": "mem-1",
            "to_memory_id": "mem-2",
        })

        assert result.isError is True
        assert "Error" in result.content[0].text


class TestReinforceRelationship:
    """Tests for reinforce_relationship handler."""

    async def test_reinforce_relationship_success(
        self, handlers, mock_memory_db, sample_memory_2, sample_relationship
    ):
        """Test reinforcing an existing relationship."""
        # Setup mocks
        mock_memory_db.get_related_memories.return_value = [
            (sample_memory_2, sample_relationship)
        ]
        mock_memory_db.update_relationship_properties = AsyncMock()

        result = await handlers.handle_reinforce_relationship({
            "from_memory_id": "mem-1",
            "to_memory_id": "mem-2",
            "success": True,
        })

        # Verify
        assert result.isError is None or not result.isError
        content_text = result.content[0].text
        reinforcement = json.loads(content_text)
        assert reinforcement["from_memory_id"] == "mem-1"
        assert reinforcement["to_memory_id"] == "mem-2"
        assert reinforcement["success"] is True
        assert "updated_properties" in reinforcement
        mock_memory_db.update_relationship_properties.assert_called_once()

    async def test_reinforce_relationship_with_failure(
        self, handlers, mock_memory_db, sample_memory_2, sample_relationship
    ):
        """Test reinforcing relationship with failure outcome."""
        mock_memory_db.get_related_memories.return_value = [
            (sample_memory_2, sample_relationship)
        ]
        mock_memory_db.update_relationship_properties = AsyncMock()

        result = await handlers.handle_reinforce_relationship({
            "from_memory_id": "mem-1",
            "to_memory_id": "mem-2",
            "success": False,
        })

        assert result.isError is None or not result.isError
        content_text = result.content[0].text
        reinforcement = json.loads(content_text)
        assert reinforcement["success"] is False

    async def test_reinforce_relationship_not_found(
        self, handlers, mock_memory_db
    ):
        """Test reinforcing non-existent relationship."""
        mock_memory_db.get_related_memories.return_value = []

        result = await handlers.handle_reinforce_relationship({
            "from_memory_id": "mem-1",
            "to_memory_id": "mem-999",
        })

        assert result.isError is True
        assert "No relationship found" in result.content[0].text

    async def test_reinforce_relationship_default_success(
        self, handlers, mock_memory_db, sample_memory_2, sample_relationship
    ):
        """Test that success defaults to True."""
        mock_memory_db.get_related_memories.return_value = [
            (sample_memory_2, sample_relationship)
        ]
        mock_memory_db.update_relationship_properties = AsyncMock()

        result = await handlers.handle_reinforce_relationship({
            "from_memory_id": "mem-1",
            "to_memory_id": "mem-2",
        })

        # Default should be success=True
        content_text = result.content[0].text
        reinforcement = json.loads(content_text)
        assert reinforcement["success"] is True

    async def test_reinforce_relationship_error_handling(
        self, handlers, mock_memory_db
    ):
        """Test error handling."""
        mock_memory_db.get_related_memories.side_effect = Exception("DB error")

        result = await handlers.handle_reinforce_relationship({
            "from_memory_id": "mem-1",
            "to_memory_id": "mem-2",
        })

        assert result.isError is True
        assert "Error" in result.content[0].text


class TestGetRelationshipTypesByCategory:
    """Tests for get_relationship_types_by_category handler."""

    async def test_get_relationship_types_by_category_causal(
        self, handlers, mock_memory_db
    ):
        """Test getting causal relationship types."""
        result = await handlers.handle_get_relationship_types_by_category({
            "category": "causal"
        })

        assert result.isError is None or not result.isError
        content_text = result.content[0].text
        types_info = json.loads(content_text)
        assert types_info["category"] == "causal"
        assert "relationship_types" in types_info
        assert types_info["count"] > 0

    async def test_get_relationship_types_by_category_solution(
        self, handlers, mock_memory_db
    ):
        """Test getting solution relationship types."""
        result = await handlers.handle_get_relationship_types_by_category({
            "category": "solution"
        })

        assert result.isError is None or not result.isError
        content_text = result.content[0].text
        types_info = json.loads(content_text)
        assert types_info["category"] == "solution"
        assert types_info["count"] > 0

    async def test_get_relationship_types_includes_metadata(
        self, handlers, mock_memory_db
    ):
        """Test that relationship types include metadata."""
        result = await handlers.handle_get_relationship_types_by_category({
            "category": "causal"
        })

        content_text = result.content[0].text
        types_info = json.loads(content_text)
        # Check that each type has required fields
        for rel_type in types_info["relationship_types"]:
            assert "type" in rel_type
            assert "description" in rel_type
            assert "default_strength" in rel_type
            assert "bidirectional" in rel_type

    async def test_get_relationship_types_error_handling(
        self, handlers, mock_memory_db
    ):
        """Test error handling with invalid category."""
        result = await handlers.handle_get_relationship_types_by_category({
            "category": "invalid_category"
        })

        assert result.isError is True
        assert "Error" in result.content[0].text


class TestAnalyzeGraphMetrics:
    """Tests for analyze_graph_metrics handler."""

    async def test_analyze_graph_metrics_success(self, handlers, mock_memory_db):
        """Test comprehensive graph metrics."""
        mock_memory_db.get_memory_statistics.return_value = {
            "total_memories": 100,
            "total_relationships": 250,
            "memory_by_type": {"problem": 30, "solution": 40},
        }

        result = await handlers.handle_analyze_graph_metrics({})

        assert result.isError is None or not result.isError
        content_text = result.content[0].text
        metrics = json.loads(content_text)
        assert "database_statistics" in metrics
        assert "relationship_system" in metrics
        assert metrics["database_statistics"]["total_memories"] == 100
        assert metrics["relationship_system"]["total_relationship_types"] == 35

    async def test_analyze_graph_metrics_includes_categories(
        self, handlers, mock_memory_db
    ):
        """Test that metrics include relationship categories."""
        mock_memory_db.get_memory_statistics.return_value = {
            "total_memories": 50,
        }

        result = await handlers.handle_analyze_graph_metrics({})

        content_text = result.content[0].text
        metrics = json.loads(content_text)
        categories = metrics["relationship_system"]["categories"]
        assert len(categories) > 0
        # Verify category structure
        for cat in categories:
            assert "name" in cat
            assert "types_count" in cat

    async def test_analyze_graph_metrics_empty_graph(self, handlers, mock_memory_db):
        """Test metrics on empty graph."""
        mock_memory_db.get_memory_statistics.return_value = {
            "total_memories": 0,
            "total_relationships": 0,
        }

        result = await handlers.handle_analyze_graph_metrics({})

        assert result.isError is None or not result.isError
        content_text = result.content[0].text
        metrics = json.loads(content_text)
        assert metrics["database_statistics"]["total_memories"] == 0

    async def test_analyze_graph_metrics_error_handling(
        self, handlers, mock_memory_db
    ):
        """Test error handling."""
        mock_memory_db.get_memory_statistics.side_effect = Exception("DB error")

        result = await handlers.handle_analyze_graph_metrics({})

        assert result.isError is True
        assert "Error" in result.content[0].text
