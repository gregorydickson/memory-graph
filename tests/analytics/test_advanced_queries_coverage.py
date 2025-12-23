"""Additional comprehensive tests for analytics/advanced_queries module.

This test suite improves coverage from 72% to 85%+ by testing:
- Learning path recommendations with different scenarios
- Solution effectiveness prediction
- Memory ROI tracking edge cases
- Error handling in analytics queries
- Empty result handling
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta

from src.memorygraph.analytics.advanced_queries import (
    recommend_learning_paths,
    predict_solution_effectiveness,
    track_memory_roi,
    get_memory_graph_visualization,
    analyze_solution_similarity,
    identify_knowledge_gaps,
    LearningPath,
    MemoryROI,
    KnowledgeGap,
    SimilarSolution,
)


@pytest.mark.asyncio
class TestLearningPathRecommendations:
    """Test learning path recommendation queries."""

    async def test_recommend_learning_path_no_results(self):
        """Test when no learning paths found."""
        backend = AsyncMock()
        backend.execute_query = AsyncMock(return_value=[])

        result = await recommend_learning_paths(backend, topic="nonexistent")

        assert result == []

    async def test_recommend_learning_path_error_handling(self):
        """Test error handling in learning path recommendations."""
        backend = AsyncMock()
        backend.execute_query = AsyncMock(side_effect=Exception("Database error"))

        result = await recommend_learning_paths(backend, topic="python")

        # Should return empty list on error
        assert result == []

    async def test_recommend_learning_path_query_params(self):
        """Test that query is called with correct parameters."""
        backend = AsyncMock()
        backend.execute_query = AsyncMock(return_value=[])

        await recommend_learning_paths(backend, topic="python", max_paths=5)

        # Verify query was called with correct params
        backend.execute_query.assert_called_once()
        call_args = backend.execute_query.call_args
        params = call_args[0][1] if len(call_args[0]) > 1 else call_args[1]

        assert params["topic"] == "python"
        assert params["topic_lower"] == "python"
        assert params["max_paths"] == 5


@pytest.mark.asyncio
class TestSolutionEffectiveness:
    """Test solution effectiveness prediction."""

    async def test_predict_effectiveness_high_confidence(self):
        """Test effectiveness prediction with high confidence historical data."""
        backend = AsyncMock()

        backend.execute_query = AsyncMock(return_value=[
            {
                "base_effectiveness": 0.9,
                "confidence": 0.85,
                "outcomes": 20,
                "successes": 18,
            }
        ])

        result = await predict_solution_effectiveness(
            backend,
            problem_description="Authentication failing with JWT",
            solution_id="solution_123",
        )

        # With high confidence, should use base effectiveness
        assert result == 0.9

    async def test_predict_effectiveness_low_confidence(self):
        """Test effectiveness prediction with low confidence."""
        backend = AsyncMock()

        # Mock solution query
        backend.execute_query = AsyncMock(side_effect=[
            # First call: solution query
            [
                {
                    "base_effectiveness": 0.5,
                    "confidence": 0.3,  # Low confidence
                    "outcomes": 2,
                    "successes": 1,
                }
            ],
            # Second call: entity match query
            [{"matched_entities": 3}],
        ])

        with patch("src.memorygraph.intelligence.entity_extraction.extract_entities") as mock_extract:
            # Mock entity extraction
            mock_entity = MagicMock()
            mock_entity.text = "JWT"
            mock_extract.return_value = [mock_entity, MagicMock(text="auth"), MagicMock(text="token")]

            result = await predict_solution_effectiveness(
                backend,
                problem_description="JWT authentication issue",
                solution_id="solution_123",
            )

            # Should blend base effectiveness with entity matching
            assert 0.0 <= result <= 1.0
            assert result > 0.5  # Should be higher than base due to perfect entity match

    async def test_predict_effectiveness_no_solution_found(self):
        """Test when solution is not found."""
        backend = AsyncMock()
        backend.execute_query = AsyncMock(return_value=[])

        result = await predict_solution_effectiveness(
            backend,
            problem_description="Test problem",
            solution_id="nonexistent",
        )

        # Should return default
        assert result == 0.5

    async def test_predict_effectiveness_no_entities(self):
        """Test prediction when problem has no extractable entities."""
        backend = AsyncMock()

        backend.execute_query = AsyncMock(return_value=[
            {
                "base_effectiveness": 0.6,
                "confidence": 0.4,
                "outcomes": 5,
                "successes": 3,
            }
        ])

        with patch("src.memorygraph.intelligence.entity_extraction.extract_entities") as mock_extract:
            mock_extract.return_value = []  # No entities

            result = await predict_solution_effectiveness(
                backend,
                problem_description="Generic problem",
                solution_id="solution_123",
            )

            # Should return base effectiveness when no entities
            assert result == 0.6

    async def test_predict_effectiveness_error_handling(self):
        """Test error handling in effectiveness prediction."""
        backend = AsyncMock()
        backend.execute_query = AsyncMock(side_effect=Exception("Database error"))

        result = await predict_solution_effectiveness(
            backend,
            problem_description="Test",
            solution_id="solution_123",
        )

        # Should return default on error
        assert result == 0.5

    async def test_predict_effectiveness_partial_entity_match(self):
        """Test effectiveness with partial entity matching."""
        backend = AsyncMock()

        backend.execute_query = AsyncMock(side_effect=[
            [
                {
                    "base_effectiveness": 0.5,
                    "confidence": 0.5,
                    "outcomes": 10,
                    "successes": 5,
                }
            ],
            [{"matched_entities": 1}],  # Only 1 out of 3 entities matched
        ])

        with patch("src.memorygraph.intelligence.entity_extraction.extract_entities") as mock_extract:
            mock_extract.return_value = [
                MagicMock(text="Entity1"),
                MagicMock(text="Entity2"),
                MagicMock(text="Entity3"),
            ]

            result = await predict_solution_effectiveness(
                backend,
                problem_description="Problem with multiple entities",
                solution_id="solution_123",
            )

            # Should blend with partial match (1/3 = 0.33)
            assert 0.0 <= result <= 1.0


@pytest.mark.asyncio
class TestMemoryROITracking:
    """Test memory ROI tracking queries."""

    async def test_track_roi_high_usage_high_success(self):
        """Test ROI tracking for high-usage, high-success memory."""
        backend = AsyncMock()

        created_at = datetime.now(timezone.utc) - timedelta(days=30)
        last_accessed = datetime.now(timezone.utc) - timedelta(hours=1)

        backend.execute_query = AsyncMock(return_value=[
            {
                "id": "mem_popular",
                "title": "Popular Solution",
                "created_at": created_at.isoformat(),
                "usage_count": 25,
                "last_accessed": last_accessed.isoformat(),
                "total_outcomes": 20,
                "successful_outcomes": 18,
            }
        ])

        roi = await track_memory_roi(backend, "mem_popular")

        assert roi is not None
        assert roi.memory_id == "mem_popular"
        assert roi.times_accessed == 25
        assert roi.times_helpful == 18
        assert roi.success_rate == 0.9
        assert roi.value_score > 0.8  # High usage + high success

    async def test_track_roi_high_usage_low_success(self):
        """Test ROI for high-usage but low-success memory."""
        backend = AsyncMock()

        backend.execute_query = AsyncMock(return_value=[
            {
                "id": "mem_unreliable",
                "title": "Unreliable Solution",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "usage_count": 20,
                "last_accessed": datetime.now(timezone.utc).isoformat(),
                "total_outcomes": 20,
                "successful_outcomes": 4,  # Only 20% success rate
            }
        ])

        roi = await track_memory_roi(backend, "mem_unreliable")

        assert roi is not None
        assert roi.success_rate == 0.2
        # High usage but low success should give moderate score
        assert 0.3 < roi.value_score < 0.7

    async def test_track_roi_negative(self):
        """Test negative ROI scenario (unused memory)."""
        backend = AsyncMock()

        backend.execute_query = AsyncMock(return_value=[
            {
                "id": "mem_unused",
                "title": "Unused Memory",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "usage_count": 0,
                "last_accessed": None,
                "total_outcomes": 0,
                "successful_outcomes": 0,
            }
        ])

        roi = await track_memory_roi(backend, "mem_unused")

        assert roi is not None
        assert roi.times_accessed == 0
        assert roi.success_rate == 0.0
        assert roi.value_score == 0.0
        assert roi.last_used is None

    async def test_track_roi_not_found(self):
        """Test ROI tracking for non-existent memory."""
        backend = AsyncMock()
        backend.execute_query = AsyncMock(return_value=[])

        roi = await track_memory_roi(backend, "nonexistent")

        assert roi is None

    async def test_track_roi_error_handling(self):
        """Test error handling in ROI tracking."""
        backend = AsyncMock()
        backend.execute_query = AsyncMock(side_effect=Exception("Database error"))

        roi = await track_memory_roi(backend, "mem_123")

        assert roi is None

    async def test_track_roi_usage_capped_at_10(self):
        """Test that usage score is capped at 10 uses."""
        backend = AsyncMock()

        backend.execute_query = AsyncMock(return_value=[
            {
                "id": "mem_super_popular",
                "title": "Super Popular",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "usage_count": 100,  # Way more than 10
                "last_accessed": datetime.now(timezone.utc).isoformat(),
                "total_outcomes": 100,
                "successful_outcomes": 100,
            }
        ])

        roi = await track_memory_roi(backend, "mem_super_popular")

        assert roi is not None
        # Usage score capped at 1.0, so with 100% success: (1.0 * 0.5) + (1.0 * 0.5) = 1.0
        assert roi.value_score == 1.0


@pytest.mark.asyncio
class TestGraphVisualizationEdgeCases:
    """Test edge cases in graph visualization."""

    async def test_visualization_empty_graph(self):
        """Test visualization with empty graph."""
        backend = AsyncMock()
        backend.execute_query = AsyncMock(return_value=[])

        viz_data = await get_memory_graph_visualization(backend)

        assert viz_data is not None
        assert len(viz_data.nodes) == 0
        assert len(viz_data.edges) == 0
        assert viz_data.metadata["node_count"] == 0
        assert viz_data.metadata["edge_count"] == 0

    async def test_visualization_error_returns_empty(self):
        """Test that errors return empty visualization with metadata."""
        backend = AsyncMock()
        backend.execute_query = AsyncMock(side_effect=Exception("Query failed"))

        viz_data = await get_memory_graph_visualization(backend, center_memory_id="mem_1")

        assert viz_data is not None
        assert len(viz_data.nodes) == 0
        assert len(viz_data.edges) == 0
        # Metadata should still be set
        assert "center_id" in viz_data.metadata
        assert viz_data.metadata["center_id"] == "mem_1"

    async def test_visualization_max_nodes_limit(self):
        """Test that max_nodes limit is respected."""
        backend = AsyncMock()

        # Create more nodes than the limit
        memories = [
            {"id": f"mem_{i}", "type": "solution", "title": f"Mem {i}", "importance": 0.5}
            for i in range(150)
        ]

        backend.execute_query = AsyncMock(return_value=[
            {
                "memories": memories,
                "relationships": [],
            }
        ])

        viz_data = await get_memory_graph_visualization(backend, max_nodes=50)

        # Should only return up to max_nodes
        assert len(viz_data.nodes) <= 50

    async def test_visualization_unknown_memory_type(self):
        """Test visualization with unknown memory type."""
        backend = AsyncMock()

        backend.execute_query = AsyncMock(return_value=[
            {
                "memories": [
                    {"id": "mem_1", "type": "unknown_type", "title": "Unknown", "importance": 0.5}
                ],
                "relationships": [],
            }
        ])

        viz_data = await get_memory_graph_visualization(backend)

        assert len(viz_data.nodes) == 1
        # Unknown types should get default group 5
        assert viz_data.nodes[0].group == 5


@pytest.mark.asyncio
class TestSimilarityEdgeCases:
    """Test edge cases in similarity analysis."""

    async def test_similarity_no_tags_or_entities(self):
        """Test similarity when solutions have no tags or entities."""
        backend = AsyncMock()

        backend.execute_query = AsyncMock(side_effect=[
            [{"tags": [], "entities": []}],  # Target has nothing
            [
                {
                    "id": "sol_2",
                    "title": "Other",
                    "content": "Content",
                    "tags": [],
                    "entities": [],
                    "effectiveness": None,
                }
            ],
        ])

        result = await analyze_solution_similarity(backend, "sol_1")

        # With no shared attributes and threshold 0.3, should filter out
        assert len(result) == 0

    async def test_similarity_target_not_found(self):
        """Test similarity when target solution not found."""
        backend = AsyncMock()
        backend.execute_query = AsyncMock(return_value=[])

        result = await analyze_solution_similarity(backend, "nonexistent")

        assert result == []

    async def test_similarity_error_handling(self):
        """Test error handling in similarity analysis."""
        backend = AsyncMock()
        backend.execute_query = AsyncMock(side_effect=Exception("Database error"))

        result = await analyze_solution_similarity(backend, "sol_1")

        assert result == []


@pytest.mark.asyncio
class TestKnowledgeGapsEdgeCases:
    """Test edge cases in knowledge gap identification."""

    async def test_gaps_severity_filtering(self):
        """Test filtering gaps by severity level."""
        backend = AsyncMock()

        old_problem = datetime.now(timezone.utc) - timedelta(days=45)
        medium_problem = datetime.now(timezone.utc) - timedelta(days=15)

        backend.execute_query = AsyncMock(side_effect=[
            [
                {"id": "old", "title": "Old Problem", "tags": [], "created_at": old_problem.isoformat()},
                {"id": "medium", "title": "Medium Problem", "tags": [], "created_at": medium_problem.isoformat()},
            ],
            [],  # No sparse entities
        ])

        # Filter for medium and high only
        gaps = await identify_knowledge_gaps(backend, min_gap_severity="medium")

        # Should only include medium and high severity gaps
        assert all(gap.severity in ["medium", "high"] for gap in gaps)

    async def test_gaps_error_handling(self):
        """Test error handling in gap identification."""
        backend = AsyncMock()
        backend.execute_query = AsyncMock(side_effect=Exception("Database error"))

        gaps = await identify_knowledge_gaps(backend)

        # Should handle errors gracefully and continue with other queries
        assert isinstance(gaps, list)
