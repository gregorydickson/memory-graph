"""
Tests for structured context-based relationship queries.

This module tests the ability to query relationships based on
their extracted context structure (scope, conditions, evidence, etc.).
"""

import json
import pytest
from memorygraph.sqlite_database import SQLiteMemoryDatabase
from memorygraph.backends.sqlite_fallback import SQLiteFallbackBackend
from memorygraph.models import (
    Memory,
    MemoryType,
    RelationshipType,
    RelationshipProperties,
    MemoryContext,
)
from memorygraph.utils.context_extractor import extract_context_structure


@pytest.fixture
async def db():
    """Create an in-memory SQLite database for testing."""
    backend = SQLiteFallbackBackend(":memory:")
    await backend.connect()
    await backend.initialize_schema()
    database = SQLiteMemoryDatabase(backend)
    await database.initialize_schema()
    yield database
    await backend.disconnect()


@pytest.fixture
async def sample_memories(db):
    """Create sample memories for testing."""
    memories = []

    # Create test memories
    mem1 = Memory(
        type=MemoryType.SOLUTION,
        title="Auth Implementation",
        content="Implemented authentication system",
        tags=["auth", "security"],
        context=MemoryContext(project_path="/test/project"),
    )
    mem1.id = await db.store_memory(mem1)
    memories.append(mem1)

    mem2 = Memory(
        type=MemoryType.PROBLEM,
        title="Memory Leak",
        content="Memory leak in worker threads",
        tags=["performance", "bug"],
        context=MemoryContext(project_path="/test/project"),
    )
    mem2.id = await db.store_memory(mem2)
    memories.append(mem2)

    mem3 = Memory(
        type=MemoryType.SOLUTION,
        title="Rate Limiting",
        content="Implemented rate limiting",
        tags=["api", "security"],
        context=MemoryContext(project_path="/test/project"),
    )
    mem3.id = await db.store_memory(mem3)
    memories.append(mem3)

    mem4 = Memory(
        type=MemoryType.CODE_PATTERN,
        title="Caching Pattern",
        content="Redis caching pattern",
        tags=["caching", "performance"],
        context=MemoryContext(project_path="/test/project"),
    )
    mem4.id = await db.store_memory(mem4)
    memories.append(mem4)

    return memories


class TestScopeFiltering:
    """Test filtering relationships by scope field."""

    @pytest.mark.asyncio
    async def test_filter_by_partial_scope(self, db, sample_memories):
        """Find all relationships with partial scope."""
        mem1, mem2, mem3, mem4 = sample_memories

        # Create relationships with different scopes
        rel1_id = await db.create_relationship(
            from_memory_id=mem1.id,
            to_memory_id=mem2.id,
            relationship_type=RelationshipType.SOLVES,
            properties=RelationshipProperties(
                context="partially implements auth module",
                strength=0.8,
            )
        )

        rel2_id = await db.create_relationship(
            from_memory_id=mem3.id,
            to_memory_id=mem4.id,
            relationship_type=RelationshipType.REQUIRES,
            properties=RelationshipProperties(
                context="fully supports rate limiting",
                strength=0.9,
            )
        )

        # Query by scope=partial
        results = await db.search_relationships_by_context(scope="partial")

        # Should find only the partial implementation
        assert len(results) == 1
        assert results[0].id == rel1_id
        assert results[0].type == RelationshipType.SOLVES

    @pytest.mark.asyncio
    async def test_filter_by_full_scope(self, db, sample_memories):
        """Find all relationships with full scope."""
        mem1, mem2, mem3, mem4 = sample_memories

        # Create relationships
        await db.create_relationship(
            from_memory_id=mem1.id,
            to_memory_id=mem2.id,
            relationship_type=RelationshipType.SOLVES,
            properties=RelationshipProperties(
                context="partially implements auth",
                strength=0.8,
            )
        )

        rel2_id = await db.create_relationship(
            from_memory_id=mem3.id,
            to_memory_id=mem4.id,
            relationship_type=RelationshipType.REQUIRES,
            properties=RelationshipProperties(
                context="fully supports caching",
                strength=0.9,
            )
        )

        # Query by scope=full
        results = await db.search_relationships_by_context(scope="full")

        # Should find only the full implementation
        assert len(results) == 1
        assert results[0].id == rel2_id

    @pytest.mark.asyncio
    async def test_filter_by_conditional_scope(self, db, sample_memories):
        """Find all relationships with conditional scope."""
        mem1, mem2, mem3, mem4 = sample_memories

        # Create relationships
        rel1_id = await db.create_relationship(
            from_memory_id=mem1.id,
            to_memory_id=mem2.id,
            relationship_type=RelationshipType.SOLVES,
            properties=RelationshipProperties(
                context="only works in production environment",
                strength=0.7,
            )
        )

        await db.create_relationship(
            from_memory_id=mem3.id,
            to_memory_id=mem4.id,
            relationship_type=RelationshipType.REQUIRES,
            properties=RelationshipProperties(
                context="fully supports all environments",
                strength=0.9,
            )
        )

        # Query by scope=conditional
        results = await db.search_relationships_by_context(scope="conditional")

        # Should find only the conditional relationship
        assert len(results) == 1
        assert results[0].id == rel1_id


class TestConditionsFiltering:
    """Test filtering relationships by conditions field."""

    @pytest.mark.asyncio
    async def test_filter_by_single_condition(self, db, sample_memories):
        """Find relationships with specific condition."""
        mem1, mem2, mem3, mem4 = sample_memories

        # Create relationships with different conditions
        rel1_id = await db.create_relationship(
            from_memory_id=mem1.id,
            to_memory_id=mem2.id,
            relationship_type=RelationshipType.SOLVES,
            properties=RelationshipProperties(
                context="works only in production environment",
                strength=0.8,
            )
        )

        await db.create_relationship(
            from_memory_id=mem3.id,
            to_memory_id=mem4.id,
            relationship_type=RelationshipType.REQUIRES,
            properties=RelationshipProperties(
                context="works in development environment",
                strength=0.9,
            )
        )

        # Query for production condition
        results = await db.search_relationships_by_context(
            conditions=["production"]
        )

        # Should find only production relationship
        assert len(results) == 1
        assert results[0].id == rel1_id

    @pytest.mark.asyncio
    async def test_filter_by_multiple_conditions(self, db, sample_memories):
        """Find relationships matching any of multiple conditions."""
        mem1, mem2, mem3, mem4 = sample_memories

        # Create relationships
        rel1_id = await db.create_relationship(
            from_memory_id=mem1.id,
            to_memory_id=mem2.id,
            relationship_type=RelationshipType.SOLVES,
            properties=RelationshipProperties(
                context="only in production environment",
                strength=0.8,
            )
        )

        rel2_id = await db.create_relationship(
            from_memory_id=mem3.id,
            to_memory_id=mem4.id,
            relationship_type=RelationshipType.REQUIRES,
            properties=RelationshipProperties(
                context="requires Redis to be enabled",
                strength=0.9,
            )
        )

        # Query for multiple conditions (OR logic)
        results = await db.search_relationships_by_context(
            conditions=["production", "Redis"]
        )

        # Should find both relationships
        assert len(results) == 2
        result_ids = {r.id for r in results}
        assert rel1_id in result_ids
        assert rel2_id in result_ids


class TestEvidenceFiltering:
    """Test filtering relationships by evidence field."""

    @pytest.mark.asyncio
    async def test_filter_by_has_evidence(self, db, sample_memories):
        """Find relationships that have evidence."""
        mem1, mem2, mem3, mem4 = sample_memories

        # Create relationships
        rel1_id = await db.create_relationship(
            from_memory_id=mem1.id,
            to_memory_id=mem2.id,
            relationship_type=RelationshipType.SOLVES,
            properties=RelationshipProperties(
                context="verified by integration tests",
                strength=0.9,
            )
        )

        await db.create_relationship(
            from_memory_id=mem3.id,
            to_memory_id=mem4.id,
            relationship_type=RelationshipType.REQUIRES,
            properties=RelationshipProperties(
                context="not tested yet",
                strength=0.5,
            )
        )

        # Query for relationships with evidence
        results = await db.search_relationships_by_context(has_evidence=True)

        # Should find only the verified relationship
        assert len(results) == 1
        assert results[0].id == rel1_id

    @pytest.mark.asyncio
    async def test_filter_by_no_evidence(self, db, sample_memories):
        """Find relationships without evidence."""
        mem1, mem2, mem3, mem4 = sample_memories

        # Create relationships
        await db.create_relationship(
            from_memory_id=mem1.id,
            to_memory_id=mem2.id,
            relationship_type=RelationshipType.SOLVES,
            properties=RelationshipProperties(
                context="verified by tests",
                strength=0.9,
            )
        )

        rel2_id = await db.create_relationship(
            from_memory_id=mem3.id,
            to_memory_id=mem4.id,
            relationship_type=RelationshipType.REQUIRES,
            properties=RelationshipProperties(
                context="needs validation",
                strength=0.5,
            )
        )

        # Query for relationships without evidence
        results = await db.search_relationships_by_context(has_evidence=False)

        # Should find only the unverified relationship
        assert len(results) == 1
        assert results[0].id == rel2_id

    @pytest.mark.asyncio
    async def test_filter_by_specific_evidence(self, db, sample_memories):
        """Find relationships with specific evidence type."""
        mem1, mem2, mem3, mem4 = sample_memories

        # Create relationships
        rel1_id = await db.create_relationship(
            from_memory_id=mem1.id,
            to_memory_id=mem2.id,
            relationship_type=RelationshipType.SOLVES,
            properties=RelationshipProperties(
                context="verified by integration tests",
                strength=0.9,
            )
        )

        await db.create_relationship(
            from_memory_id=mem3.id,
            to_memory_id=mem4.id,
            relationship_type=RelationshipType.REQUIRES,
            properties=RelationshipProperties(
                context="tested by unit tests",
                strength=0.8,
            )
        )

        # Query for specific evidence type
        results = await db.search_relationships_by_context(
            evidence=["integration tests"]
        )

        # Should find only the integration test relationship
        assert len(results) == 1
        assert results[0].id == rel1_id


class TestComponentsFiltering:
    """Test filtering relationships by components field."""

    @pytest.mark.asyncio
    async def test_filter_by_single_component(self, db, sample_memories):
        """Find relationships mentioning specific component."""
        mem1, mem2, mem3, mem4 = sample_memories

        # Create relationships
        rel1_id = await db.create_relationship(
            from_memory_id=mem1.id,
            to_memory_id=mem2.id,
            relationship_type=RelationshipType.SOLVES,
            properties=RelationshipProperties(
                context="implements auth module",
                strength=0.8,
            )
        )

        await db.create_relationship(
            from_memory_id=mem3.id,
            to_memory_id=mem4.id,
            relationship_type=RelationshipType.REQUIRES,
            properties=RelationshipProperties(
                context="implements caching layer",
                strength=0.9,
            )
        )

        # Query for auth component
        results = await db.search_relationships_by_context(
            components=["auth"]
        )

        # Should find only the auth relationship
        assert len(results) == 1
        assert results[0].id == rel1_id

    @pytest.mark.asyncio
    async def test_filter_by_multiple_components(self, db, sample_memories):
        """Find relationships mentioning any of multiple components."""
        mem1, mem2, mem3, mem4 = sample_memories

        # Create relationships
        rel1_id = await db.create_relationship(
            from_memory_id=mem1.id,
            to_memory_id=mem2.id,
            relationship_type=RelationshipType.SOLVES,
            properties=RelationshipProperties(
                context="implements auth module",
                strength=0.8,
            )
        )

        rel2_id = await db.create_relationship(
            from_memory_id=mem3.id,
            to_memory_id=mem4.id,
            relationship_type=RelationshipType.REQUIRES,
            properties=RelationshipProperties(
                context="uses Redis service",
                strength=0.9,
            )
        )

        # Query for multiple components (OR logic)
        results = await db.search_relationships_by_context(
            components=["auth", "Redis"]
        )

        # Should find both relationships
        assert len(results) == 2
        result_ids = {r.id for r in results}
        assert rel1_id in result_ids
        assert rel2_id in result_ids


class TestCombinedFilters:
    """Test combining multiple filter criteria."""

    @pytest.mark.asyncio
    async def test_scope_and_conditions(self, db, sample_memories):
        """Filter by both scope and conditions (AND logic)."""
        mem1, mem2, mem3, mem4 = sample_memories

        # Create relationships
        rel1_id = await db.create_relationship(
            from_memory_id=mem1.id,
            to_memory_id=mem2.id,
            relationship_type=RelationshipType.SOLVES,
            properties=RelationshipProperties(
                context="partially implements auth, only in production",
                strength=0.7,
            )
        )

        await db.create_relationship(
            from_memory_id=mem3.id,
            to_memory_id=mem4.id,
            relationship_type=RelationshipType.REQUIRES,
            properties=RelationshipProperties(
                context="partially implements caching, only in development",
                strength=0.6,
            )
        )

        await db.create_relationship(
            from_memory_id=mem1.id,
            to_memory_id=mem3.id,
            relationship_type=RelationshipType.RELATED_TO,
            properties=RelationshipProperties(
                context="fully supports authentication in production",
                strength=0.9,
            )
        )

        # Query for partial scope AND production condition
        results = await db.search_relationships_by_context(
            scope="partial",
            conditions=["production"]
        )

        # Should find only the relationship matching both criteria
        assert len(results) == 1
        assert results[0].id == rel1_id

    @pytest.mark.asyncio
    async def test_scope_and_evidence(self, db, sample_memories):
        """Filter by scope and evidence presence."""
        mem1, mem2, mem3, mem4 = sample_memories

        # Create relationships
        rel1_id = await db.create_relationship(
            from_memory_id=mem1.id,
            to_memory_id=mem2.id,
            relationship_type=RelationshipType.SOLVES,
            properties=RelationshipProperties(
                context="partially implements auth, verified by tests",
                strength=0.8,
            )
        )

        await db.create_relationship(
            from_memory_id=mem3.id,
            to_memory_id=mem4.id,
            relationship_type=RelationshipType.REQUIRES,
            properties=RelationshipProperties(
                context="partially implements caching",
                strength=0.7,
            )
        )

        # Query for partial scope AND has evidence
        results = await db.search_relationships_by_context(
            scope="partial",
            has_evidence=True
        )

        # Should find only the verified partial implementation
        assert len(results) == 1
        assert results[0].id == rel1_id

    @pytest.mark.asyncio
    async def test_components_and_conditions(self, db, sample_memories):
        """Filter by components and conditions."""
        mem1, mem2, mem3, mem4 = sample_memories

        # Create relationships
        rel1_id = await db.create_relationship(
            from_memory_id=mem1.id,
            to_memory_id=mem2.id,
            relationship_type=RelationshipType.SOLVES,
            properties=RelationshipProperties(
                context="implements auth module only in production",
                strength=0.8,
            )
        )

        await db.create_relationship(
            from_memory_id=mem3.id,
            to_memory_id=mem4.id,
            relationship_type=RelationshipType.REQUIRES,
            properties=RelationshipProperties(
                context="implements auth module in development",
                strength=0.7,
            )
        )

        # Query for auth component AND production condition
        results = await db.search_relationships_by_context(
            components=["auth"],
            conditions=["production"]
        )

        # Should find only production auth relationship
        assert len(results) == 1
        assert results[0].id == rel1_id


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_filter_with_no_matches(self, db, sample_memories):
        """Query that returns no results."""
        mem1, mem2 = sample_memories[:2]

        # Create a relationship
        await db.create_relationship(
            from_memory_id=mem1.id,
            to_memory_id=mem2.id,
            relationship_type=RelationshipType.SOLVES,
            properties=RelationshipProperties(
                context="implements auth",
                strength=0.8,
            )
        )

        # Query for non-existent scope
        results = await db.search_relationships_by_context(
            scope="nonexistent"
        )

        # Should return empty list
        assert results == []

    @pytest.mark.asyncio
    async def test_filter_legacy_text_context(self, db, sample_memories):
        """Handle legacy free-text context gracefully."""
        mem1, mem2 = sample_memories[:2]

        # Create relationship with plain text context
        rel_id = await db.create_relationship(
            from_memory_id=mem1.id,
            to_memory_id=mem2.id,
            relationship_type=RelationshipType.SOLVES,
            properties=RelationshipProperties(
                context="partially implements auth",  # Will be extracted
                strength=0.8,
            )
        )

        # Should still be able to filter by extracted scope
        results = await db.search_relationships_by_context(scope="partial")

        assert len(results) == 1
        assert results[0].id == rel_id

    @pytest.mark.asyncio
    async def test_filter_null_context(self, db, sample_memories):
        """Handle relationships with null context."""
        mem1, mem2 = sample_memories[:2]

        # Create relationship without context
        await db.create_relationship(
            from_memory_id=mem1.id,
            to_memory_id=mem2.id,
            relationship_type=RelationshipType.SOLVES,
            properties=RelationshipProperties(
                context=None,
                strength=0.8,
            )
        )

        # Query should not crash, just return no results
        results = await db.search_relationships_by_context(scope="partial")

        assert results == []

    @pytest.mark.asyncio
    async def test_filter_with_limit(self, db, sample_memories):
        """Respect limit parameter."""
        mem1, mem2, mem3, mem4 = sample_memories

        # Create multiple relationships with same scope
        rel1_id = await db.create_relationship(
            from_memory_id=mem1.id,
            to_memory_id=mem2.id,
            relationship_type=RelationshipType.SOLVES,
            properties=RelationshipProperties(
                context="partially implements feature A",
                strength=0.8,
            )
        )

        rel2_id = await db.create_relationship(
            from_memory_id=mem3.id,
            to_memory_id=mem4.id,
            relationship_type=RelationshipType.SOLVES,
            properties=RelationshipProperties(
                context="partially implements feature B",
                strength=0.9,
            )
        )

        rel3_id = await db.create_relationship(
            from_memory_id=mem1.id,
            to_memory_id=mem4.id,
            relationship_type=RelationshipType.SOLVES,
            properties=RelationshipProperties(
                context="partially implements feature C",
                strength=0.7,
            )
        )

        # Query with limit=2
        results = await db.search_relationships_by_context(
            scope="partial",
            limit=2
        )

        # Should return only 2 results
        assert len(results) == 2
        # Should return highest strength first (rel2, rel1)
        assert results[0].properties.strength >= results[1].properties.strength

    @pytest.mark.asyncio
    async def test_filter_empty_criteria(self, db, sample_memories):
        """Handle query with no filter criteria."""
        mem1, mem2 = sample_memories[:2]

        # Create a relationship
        rel_id = await db.create_relationship(
            from_memory_id=mem1.id,
            to_memory_id=mem2.id,
            relationship_type=RelationshipType.SOLVES,
            properties=RelationshipProperties(
                context="implements auth",
                strength=0.8,
            )
        )

        # Query with no filters should return all relationships
        results = await db.search_relationships_by_context()

        assert len(results) == 1
        assert results[0].id == rel_id
