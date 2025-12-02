"""
Tests for pagination functionality.

Tests cover:
- Basic pagination with limit and offset
- Pagination metadata (total_count, has_more, next_offset)
- Edge cases (empty results, beyond last page)
- Pagination with search filters
"""

import pytest
from datetime import datetime, UTC

from src.memorygraph.sqlite_database import SQLiteMemoryDatabase
from src.memorygraph.backends.sqlite_fallback import SQLiteFallbackBackend
from src.memorygraph.models import (
    Memory, MemoryType, SearchQuery, PaginatedResult
)


class TestPaginationBasics:
    """Test basic pagination functionality."""

    @pytest.mark.asyncio
    async def test_pagination_model_validation(self):
        """Test PaginatedResult model validates correctly."""
        result = PaginatedResult(
            results=[],
            total_count=100,
            limit=50,
            offset=0,
            has_more=True,
            next_offset=50
        )

        assert result.total_count == 100
        assert result.limit == 50
        assert result.offset == 0
        assert result.has_more is True
        assert result.next_offset == 50

    @pytest.mark.asyncio
    async def test_pagination_model_last_page(self):
        """Test PaginatedResult for last page."""
        result = PaginatedResult(
            results=[],
            total_count=75,
            limit=50,
            offset=50,
            has_more=False,
            next_offset=None
        )

        assert result.has_more is False
        assert result.next_offset is None

    @pytest.mark.asyncio
    async def test_search_query_limit_validation(self):
        """Test SearchQuery validates limit parameter."""
        # Valid limits
        query1 = SearchQuery(limit=1)
        assert query1.limit == 1

        query2 = SearchQuery(limit=1000)
        assert query2.limit == 1000

        query3 = SearchQuery()  # Default
        assert query3.limit == 50

        # Invalid limits should raise ValidationError
        with pytest.raises(Exception):  # Pydantic ValidationError
            SearchQuery(limit=0)

        with pytest.raises(Exception):
            SearchQuery(limit=1001)

        with pytest.raises(Exception):
            SearchQuery(limit=-1)

    @pytest.mark.asyncio
    async def test_search_query_offset_validation(self):
        """Test SearchQuery validates offset parameter."""
        # Valid offsets
        query1 = SearchQuery(offset=0)
        assert query1.offset == 0

        query2 = SearchQuery(offset=1000)
        assert query2.offset == 1000

        query3 = SearchQuery()  # Default
        assert query3.offset == 0

        # Invalid offset should raise ValidationError
        with pytest.raises(Exception):
            SearchQuery(offset=-1)


class TestPaginationWithDatabase:
    """Test pagination with actual database operations."""

    @pytest.fixture
    async def memory_db(self, tmp_path):
        """Create a test database with sample memories."""
        db_path = str(tmp_path / "test_pagination.db")
        backend = SQLiteFallbackBackend(db_path=db_path)
        await backend.connect()
        await backend.initialize_schema()
        db = SQLiteMemoryDatabase(backend)
        await db.initialize_schema()
        yield db
        await backend.disconnect()

    @pytest.fixture
    async def populated_db(self, memory_db):
        """Populate database with 200 test memories."""
        memories = []
        for i in range(200):
            memory = Memory(
                type=MemoryType.GENERAL,
                title=f"Test Memory {i+1}",
                content=f"This is test memory number {i+1} for pagination testing",
                tags=[f"tag{i % 10}"],  # 10 different tags, cycling
                importance=0.5 + (i % 10) * 0.05  # Vary importance
            )
            created = await memory_db.store_memory(memory)
            memories.append(created)

        return memory_db, memories

    @pytest.mark.asyncio
    async def test_first_page_pagination(self, populated_db):
        """Test retrieving first page of results."""
        db, all_memories = populated_db

        query = SearchQuery(limit=50, offset=0)
        result = await db.search_memories_paginated(query)

        assert isinstance(result, PaginatedResult)
        assert len(result.results) == 50
        assert result.total_count == 200
        assert result.limit == 50
        assert result.offset == 0
        assert result.has_more is True
        assert result.next_offset == 50

    @pytest.mark.asyncio
    async def test_middle_page_pagination(self, populated_db):
        """Test retrieving middle page of results."""
        db, all_memories = populated_db

        query = SearchQuery(limit=50, offset=50)
        result = await db.search_memories_paginated(query)

        assert len(result.results) == 50
        assert result.total_count == 200
        assert result.offset == 50
        assert result.has_more is True
        assert result.next_offset == 100

    @pytest.mark.asyncio
    async def test_last_page_pagination(self, populated_db):
        """Test retrieving last page of results."""
        db, all_memories = populated_db

        query = SearchQuery(limit=50, offset=150)
        result = await db.search_memories_paginated(query)

        assert len(result.results) == 50
        assert result.total_count == 200
        assert result.offset == 150
        assert result.has_more is False
        assert result.next_offset is None

    @pytest.mark.asyncio
    async def test_partial_last_page(self, populated_db):
        """Test last page with fewer results than limit."""
        db, all_memories = populated_db

        query = SearchQuery(limit=60, offset=180)
        result = await db.search_memories_paginated(query)

        assert len(result.results) == 20  # Only 20 left
        assert result.total_count == 200
        assert result.offset == 180
        assert result.has_more is False
        assert result.next_offset is None

    @pytest.mark.asyncio
    async def test_beyond_last_page(self, populated_db):
        """Test offset beyond last page returns empty results."""
        db, all_memories = populated_db

        query = SearchQuery(limit=50, offset=300)
        result = await db.search_memories_paginated(query)

        assert len(result.results) == 0
        assert result.total_count == 200
        assert result.offset == 300
        assert result.has_more is False
        assert result.next_offset is None

    @pytest.mark.asyncio
    async def test_small_page_size(self, populated_db):
        """Test pagination with small page size."""
        db, all_memories = populated_db

        query = SearchQuery(limit=10, offset=0)
        result = await db.search_memories_paginated(query)

        assert len(result.results) == 10
        assert result.total_count == 200
        assert result.has_more is True
        assert result.next_offset == 10

    @pytest.mark.asyncio
    async def test_large_page_size(self, populated_db):
        """Test pagination with large page size."""
        db, all_memories = populated_db

        query = SearchQuery(limit=500, offset=0)
        result = await db.search_memories_paginated(query)

        # Should return all 200 even though limit is 500
        assert len(result.results) == 200
        assert result.total_count == 200
        assert result.has_more is False
        assert result.next_offset is None

    @pytest.mark.asyncio
    async def test_pagination_with_filters(self, populated_db):
        """Test pagination works correctly with search filters."""
        db, all_memories = populated_db

        # Filter by tag - should match 20 memories (tag0 appears every 10th item)
        query = SearchQuery(
            tags=["tag0"],
            limit=10,
            offset=0
        )
        result = await db.search_memories_paginated(query)

        assert len(result.results) == 10
        assert result.total_count == 20  # Only 20 with tag0
        assert result.has_more is True
        assert result.next_offset == 10

        # Get second page
        query2 = SearchQuery(
            tags=["tag0"],
            limit=10,
            offset=10
        )
        result2 = await db.search_memories_paginated(query2)

        assert len(result2.results) == 10
        assert result2.total_count == 20
        assert result2.has_more is False
        assert result2.next_offset is None

    @pytest.mark.asyncio
    async def test_pagination_with_importance_filter(self, populated_db):
        """Test pagination with importance threshold."""
        db, all_memories = populated_db

        query = SearchQuery(
            min_importance=0.7,
            limit=20,
            offset=0
        )
        result = await db.search_memories_paginated(query)

        # Verify all results meet importance threshold
        assert all(m.importance >= 0.7 for m in result.results)
        assert result.total_count > 0

    @pytest.mark.asyncio
    async def test_pagination_empty_results(self, memory_db):
        """Test pagination with no matching results."""
        query = SearchQuery(
            tags=["nonexistent"],
            limit=50,
            offset=0
        )
        result = await memory_db.search_memories_paginated(query)

        assert len(result.results) == 0
        assert result.total_count == 0
        assert result.has_more is False
        assert result.next_offset is None

    @pytest.mark.asyncio
    async def test_pagination_consistency(self, populated_db):
        """Test that paginated results are consistent across pages."""
        db, all_memories = populated_db

        # Get all memories in one query for comparison
        query_all = SearchQuery(limit=1000, offset=0)
        all_result = await db.search_memories_paginated(query_all)

        # Get same memories across multiple pages
        page1 = await db.search_memories_paginated(SearchQuery(limit=50, offset=0))
        page2 = await db.search_memories_paginated(SearchQuery(limit=50, offset=50))
        page3 = await db.search_memories_paginated(SearchQuery(limit=50, offset=100))
        page4 = await db.search_memories_paginated(SearchQuery(limit=50, offset=150))

        # Combine paginated results
        combined = page1.results + page2.results + page3.results + page4.results

        # Should have same IDs (order may differ depending on backend)
        all_ids = {m.id for m in all_result.results}
        combined_ids = {m.id for m in combined}

        assert all_ids == combined_ids
        assert len(combined) == 200


class TestPaginationEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    async def memory_db(self, tmp_path):
        """Create a test database."""
        db_path = str(tmp_path / "test_edge.db")
        backend = SQLiteFallbackBackend(db_path=db_path)
        await backend.connect()
        await backend.initialize_schema()
        db = SQLiteMemoryDatabase(backend)
        await db.initialize_schema()
        yield db
        await backend.disconnect()

    @pytest.mark.asyncio
    async def test_pagination_single_result(self, memory_db):
        """Test pagination with exactly one result."""
        memory = Memory(
            type=MemoryType.GENERAL,
            title="Single Memory",
            content="Only one memory"
        )
        await memory_db.store_memory(memory)

        query = SearchQuery(limit=50, offset=0)
        result = await memory_db.search_memories_paginated(query)

        assert len(result.results) == 1
        assert result.total_count == 1
        assert result.has_more is False
        assert result.next_offset is None

    @pytest.mark.asyncio
    async def test_pagination_exact_page_size(self, memory_db):
        """Test when total results exactly match page size."""
        # Create exactly 50 memories
        for i in range(50):
            memory = Memory(
                type=MemoryType.GENERAL,
                title=f"Memory {i}",
                content=f"Content {i}"
            )
            await memory_db.store_memory(memory)

        query = SearchQuery(limit=50, offset=0)
        result = await memory_db.search_memories_paginated(query)

        assert len(result.results) == 50
        assert result.total_count == 50
        assert result.has_more is False
        assert result.next_offset is None

    @pytest.mark.asyncio
    async def test_pagination_one_more_than_page(self, memory_db):
        """Test when total is exactly one more than page size."""
        # Create 51 memories
        for i in range(51):
            memory = Memory(
                type=MemoryType.GENERAL,
                title=f"Memory {i}",
                content=f"Content {i}"
            )
            await memory_db.store_memory(memory)

        query = SearchQuery(limit=50, offset=0)
        result = await memory_db.search_memories_paginated(query)

        assert len(result.results) == 50
        assert result.total_count == 51
        assert result.has_more is True
        assert result.next_offset == 50
