"""
Comprehensive tests for SQLiteMemoryDatabase.

This module tests the SQLite-specific implementation of MemoryDatabase that uses
SQL queries instead of Cypher. These are INTEGRATION tests that use a real SQLite
backend, not mocks.

Tests cover:
- Database initialization with SQLite backend
- Schema creation (tables, indexes)
- Memory CRUD operations (Create, Read, Update, Delete)
- Search operations with various filters
- Relationship creation and retrieval
- Statistics gathering
- Error handling
"""

import pytest
import uuid
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path

from memorygraph.sqlite_database import SQLiteMemoryDatabase
from memorygraph.backends.sqlite_fallback import SQLiteFallbackBackend
from memorygraph.models import (
    Memory, MemoryType, MemoryContext, Relationship,
    RelationshipType, RelationshipProperties, SearchQuery,
    ValidationError, DatabaseConnectionError
)


@pytest.fixture
async def temp_db_path():
    """Create a temporary database path for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_memory.db")
        yield db_path


@pytest.fixture
async def sqlite_backend(temp_db_path):
    """Create a connected SQLite backend for testing."""
    backend = SQLiteFallbackBackend(db_path=temp_db_path)
    await backend.connect()
    await backend.initialize_schema()
    yield backend
    await backend.disconnect()


@pytest.fixture
async def sqlite_db(sqlite_backend):
    """Create a SQLiteMemoryDatabase instance for testing."""
    db = SQLiteMemoryDatabase(sqlite_backend)
    await db.initialize_schema()
    return db


@pytest.fixture
def sample_memory():
    """Create a sample memory for testing."""
    return Memory(
        type=MemoryType.SOLUTION,
        title="Test Solution",
        content="This is a test solution for a problem",
        tags=["python", "testing"],
        importance=0.8,
        confidence=0.9,
        context=MemoryContext(
            project_path="/test/project",
            files_involved=["test.py"],
            languages=["python"],
            technologies=["pytest"]
        )
    )


@pytest.fixture
def sample_memory_minimal():
    """Create a minimal memory for testing."""
    return Memory(
        type=MemoryType.GENERAL,
        title="Minimal Memory",
        content="Simple content"
    )


class TestSQLiteMemoryDatabaseInitialization:
    """Test SQLiteMemoryDatabase initialization and schema creation."""

    @pytest.mark.asyncio
    async def test_database_initialization(self, temp_db_path):
        """Test that database can be initialized with SQLite backend."""
        backend = SQLiteFallbackBackend(db_path=temp_db_path)
        await backend.connect()

        db = SQLiteMemoryDatabase(backend)
        assert db.backend == backend

        await backend.disconnect()

    @pytest.mark.asyncio
    async def test_schema_initialization_creates_tables(self, sqlite_backend):
        """Test that schema initialization creates necessary tables."""
        db = SQLiteMemoryDatabase(sqlite_backend)
        await db.initialize_schema()

        # Verify tables exist
        result = sqlite_backend.execute_sync(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        table_names = [row['name'] for row in result]

        assert 'nodes' in table_names
        assert 'relationships' in table_names

    @pytest.mark.asyncio
    async def test_schema_initialization_creates_indexes(self, sqlite_backend):
        """Test that schema initialization creates indexes."""
        db = SQLiteMemoryDatabase(sqlite_backend)
        await db.initialize_schema()

        # Verify indexes exist
        result = sqlite_backend.execute_sync(
            "SELECT name FROM sqlite_master WHERE type='index'"
        )
        index_names = [row['name'] for row in result]

        assert any('nodes_label' in name or 'idx_nodes_label' in name for name in index_names)


class TestSQLiteMemoryDatabaseCRUD:
    """Test Create, Read, Update, Delete operations."""

    @pytest.mark.asyncio
    async def test_store_memory_basic(self, sqlite_db, sample_memory):
        """Test storing a basic memory."""
        memory_id = await sqlite_db.store_memory(sample_memory)

        assert memory_id is not None
        assert isinstance(memory_id, str)
        # Verify ID was set on the memory object
        assert sample_memory.id == memory_id

    @pytest.mark.asyncio
    async def test_store_memory_generates_id(self, sqlite_db):
        """Test that storing a memory without ID generates one."""
        memory = Memory(
            type=MemoryType.TASK,
            title="Test Task",
            content="Do something"
        )

        assert memory.id is None
        memory_id = await sqlite_db.store_memory(memory)

        assert memory_id is not None
        assert memory.id == memory_id

    @pytest.mark.asyncio
    async def test_store_memory_with_context(self, sqlite_db, sample_memory):
        """Test storing a memory with full context information."""
        memory_id = await sqlite_db.store_memory(sample_memory)

        # Retrieve and verify context was stored
        retrieved = await sqlite_db.get_memory(memory_id)

        assert retrieved is not None
        assert retrieved.context is not None
        assert retrieved.context.project_path == "/test/project"
        assert retrieved.context.files_involved == ["test.py"]
        assert retrieved.context.languages == ["python"]

    @pytest.mark.asyncio
    async def test_get_memory_exists(self, sqlite_db, sample_memory):
        """Test retrieving an existing memory."""
        memory_id = await sqlite_db.store_memory(sample_memory)

        retrieved = await sqlite_db.get_memory(memory_id)

        assert retrieved is not None
        assert retrieved.id == memory_id
        assert retrieved.type == sample_memory.type
        assert retrieved.title == sample_memory.title
        assert retrieved.content == sample_memory.content
        assert retrieved.tags == sample_memory.tags
        assert retrieved.importance == sample_memory.importance

    @pytest.mark.asyncio
    async def test_get_memory_not_exists(self, sqlite_db):
        """Test retrieving a non-existent memory returns None."""
        fake_id = str(uuid.uuid4())
        retrieved = await sqlite_db.get_memory(fake_id)

        assert retrieved is None

    @pytest.mark.asyncio
    async def test_update_memory(self, sqlite_db, sample_memory):
        """Test updating an existing memory."""
        # Store original
        memory_id = await sqlite_db.store_memory(sample_memory)

        # Update fields
        sample_memory.title = "Updated Title"
        sample_memory.content = "Updated content"
        sample_memory.importance = 0.95

        success = await sqlite_db.update_memory(sample_memory)
        assert success is True

        # Verify updates
        retrieved = await sqlite_db.get_memory(memory_id)
        assert retrieved.title == "Updated Title"
        assert retrieved.content == "Updated content"
        assert retrieved.importance == 0.95

    @pytest.mark.asyncio
    async def test_update_memory_without_id_fails(self, sqlite_db):
        """Test that updating a memory without ID raises ValidationError."""
        memory = Memory(
            type=MemoryType.GENERAL,
            title="No ID",
            content="Content"
        )

        with pytest.raises(ValidationError):
            await sqlite_db.update_memory(memory)

    @pytest.mark.asyncio
    async def test_update_nonexistent_memory_returns_false(self, sqlite_db):
        """Test that updating a non-existent memory returns False."""
        memory = Memory(
            id=str(uuid.uuid4()),
            type=MemoryType.GENERAL,
            title="Doesn't Exist",
            content="Content"
        )

        success = await sqlite_db.update_memory(memory)
        assert success is False

    @pytest.mark.asyncio
    async def test_delete_memory(self, sqlite_db, sample_memory):
        """Test deleting a memory."""
        memory_id = await sqlite_db.store_memory(sample_memory)

        # Verify it exists
        assert await sqlite_db.get_memory(memory_id) is not None

        # Delete it
        success = await sqlite_db.delete_memory(memory_id)
        assert success is True

        # Verify it's gone
        assert await sqlite_db.get_memory(memory_id) is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_memory_returns_false(self, sqlite_db):
        """Test that deleting a non-existent memory returns False."""
        fake_id = str(uuid.uuid4())
        success = await sqlite_db.delete_memory(fake_id)

        assert success is False


class TestSQLiteMemoryDatabaseSearch:
    """Test search functionality with various filters."""

    @pytest.mark.asyncio
    async def test_search_all_memories(self, sqlite_db):
        """Test searching for all memories."""
        # Store multiple memories
        for i in range(3):
            memory = Memory(
                type=MemoryType.GENERAL,
                title=f"Memory {i}",
                content=f"Content {i}"
            )
            await sqlite_db.store_memory(memory)

        query = SearchQuery()
        results = await sqlite_db.search_memories(query)

        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_search_by_text_query(self, sqlite_db):
        """Test searching by text content."""
        # Store memories with specific content
        await sqlite_db.store_memory(Memory(
            type=MemoryType.SOLUTION,
            title="Python Solution",
            content="Use pytest for testing"
        ))
        await sqlite_db.store_memory(Memory(
            type=MemoryType.PROBLEM,
            title="JavaScript Problem",
            content="Need to fix webpack config"
        ))

        query = SearchQuery(query="pytest")
        results = await sqlite_db.search_memories(query)

        assert len(results) == 1
        assert "pytest" in results[0].content.lower()

    @pytest.mark.asyncio
    async def test_search_by_memory_type(self, sqlite_db):
        """Test searching by memory type."""
        await sqlite_db.store_memory(Memory(
            type=MemoryType.SOLUTION,
            title="Solution 1",
            content="Content"
        ))
        await sqlite_db.store_memory(Memory(
            type=MemoryType.PROBLEM,
            title="Problem 1",
            content="Content"
        ))
        await sqlite_db.store_memory(Memory(
            type=MemoryType.SOLUTION,
            title="Solution 2",
            content="Content"
        ))

        query = SearchQuery(memory_types=[MemoryType.SOLUTION])
        results = await sqlite_db.search_memories(query)

        assert len(results) == 2
        assert all(m.type == MemoryType.SOLUTION for m in results)

    @pytest.mark.asyncio
    async def test_search_by_tags(self, sqlite_db):
        """Test searching by tags."""
        await sqlite_db.store_memory(Memory(
            type=MemoryType.CODE_PATTERN,
            title="Pattern 1",
            content="Content",
            tags=["python", "async"]
        ))
        await sqlite_db.store_memory(Memory(
            type=MemoryType.CODE_PATTERN,
            title="Pattern 2",
            content="Content",
            tags=["javascript", "react"]
        ))

        query = SearchQuery(tags=["python"])
        results = await sqlite_db.search_memories(query)

        assert len(results) == 1
        assert "python" in results[0].tags

    @pytest.mark.asyncio
    async def test_search_by_project_path(self, sqlite_db):
        """Test searching by project path."""
        await sqlite_db.store_memory(Memory(
            type=MemoryType.FILE_CONTEXT,
            title="File 1",
            content="Content",
            context=MemoryContext(project_path="/project/a")
        ))
        await sqlite_db.store_memory(Memory(
            type=MemoryType.FILE_CONTEXT,
            title="File 2",
            content="Content",
            context=MemoryContext(project_path="/project/b")
        ))

        query = SearchQuery(project_path="/project/a")
        results = await sqlite_db.search_memories(query)

        assert len(results) == 1
        assert results[0].context.project_path == "/project/a"

    @pytest.mark.asyncio
    async def test_search_by_min_importance(self, sqlite_db):
        """Test searching by minimum importance."""
        await sqlite_db.store_memory(Memory(
            type=MemoryType.GENERAL,
            title="Low importance",
            content="Content",
            importance=0.3
        ))
        await sqlite_db.store_memory(Memory(
            type=MemoryType.GENERAL,
            title="High importance",
            content="Content",
            importance=0.9
        ))

        query = SearchQuery(min_importance=0.7)
        results = await sqlite_db.search_memories(query)

        assert len(results) == 1
        assert results[0].importance >= 0.7

    @pytest.mark.asyncio
    async def test_search_limit(self, sqlite_db):
        """Test search result limit."""
        # Store 10 memories
        for i in range(10):
            await sqlite_db.store_memory(Memory(
                type=MemoryType.GENERAL,
                title=f"Memory {i}",
                content="Content"
            ))

        query = SearchQuery(limit=5)
        results = await sqlite_db.search_memories(query)

        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_search_combined_filters(self, sqlite_db):
        """Test searching with multiple filters combined."""
        await sqlite_db.store_memory(Memory(
            type=MemoryType.SOLUTION,
            title="Python Testing",
            content="Use pytest",
            tags=["python", "testing"],
            importance=0.9
        ))
        await sqlite_db.store_memory(Memory(
            type=MemoryType.SOLUTION,
            title="Python Async",
            content="Use asyncio",
            tags=["python", "async"],
            importance=0.5
        ))

        query = SearchQuery(
            memory_types=[MemoryType.SOLUTION],
            tags=["python"],
            min_importance=0.7
        )
        results = await sqlite_db.search_memories(query)

        assert len(results) == 1
        assert results[0].title == "Python Testing"


class TestSQLiteMemoryDatabaseRelationships:
    """Test relationship operations."""

    @pytest.mark.asyncio
    async def test_create_relationship(self, sqlite_db):
        """Test creating a relationship between two memories."""
        # Create two memories
        memory1 = Memory(
            type=MemoryType.PROBLEM,
            title="Problem",
            content="A problem"
        )
        memory2 = Memory(
            type=MemoryType.SOLUTION,
            title="Solution",
            content="The solution"
        )

        id1 = await sqlite_db.store_memory(memory1)
        id2 = await sqlite_db.store_memory(memory2)

        # Create relationship
        props = RelationshipProperties(strength=0.9, confidence=0.85)
        rel_id = await sqlite_db.create_relationship(
            id1, id2, RelationshipType.SOLVES, props
        )

        assert rel_id is not None
        assert isinstance(rel_id, str)

    @pytest.mark.asyncio
    async def test_create_relationship_with_default_properties(self, sqlite_db):
        """Test creating a relationship with default properties."""
        memory1 = Memory(type=MemoryType.TASK, title="Task 1", content="Content")
        memory2 = Memory(type=MemoryType.TASK, title="Task 2", content="Content")

        id1 = await sqlite_db.store_memory(memory1)
        id2 = await sqlite_db.store_memory(memory2)

        rel_id = await sqlite_db.create_relationship(
            id1, id2, RelationshipType.DEPENDS_ON
        )

        assert rel_id is not None

    @pytest.mark.asyncio
    async def test_get_related_memories(self, sqlite_db):
        """Test retrieving related memories."""
        # Create a network of related memories
        problem = Memory(type=MemoryType.PROBLEM, title="Problem", content="Content")
        solution1 = Memory(type=MemoryType.SOLUTION, title="Solution 1", content="Content")
        solution2 = Memory(type=MemoryType.SOLUTION, title="Solution 2", content="Content")

        problem_id = await sqlite_db.store_memory(problem)
        sol1_id = await sqlite_db.store_memory(solution1)
        sol2_id = await sqlite_db.store_memory(solution2)

        # Create relationships
        await sqlite_db.create_relationship(
            sol1_id, problem_id, RelationshipType.SOLVES
        )
        await sqlite_db.create_relationship(
            sol2_id, problem_id, RelationshipType.SOLVES
        )

        # Get related memories for the problem
        related = await sqlite_db.get_related_memories(problem_id)

        assert len(related) == 2
        # Verify structure: list of (Memory, Relationship) tuples
        assert all(isinstance(item, tuple) and len(item) == 2 for item in related)
        assert all(isinstance(item[0], Memory) for item in related)
        assert all(isinstance(item[1], Relationship) for item in related)

    @pytest.mark.asyncio
    async def test_get_related_memories_filtered_by_type(self, sqlite_db):
        """Test retrieving related memories filtered by relationship type."""
        memory = Memory(type=MemoryType.GENERAL, title="Main", content="Content")
        related1 = Memory(type=MemoryType.GENERAL, title="Related 1", content="Content")
        related2 = Memory(type=MemoryType.GENERAL, title="Related 2", content="Content")

        main_id = await sqlite_db.store_memory(memory)
        rel1_id = await sqlite_db.store_memory(related1)
        rel2_id = await sqlite_db.store_memory(related2)

        await sqlite_db.create_relationship(
            main_id, rel1_id, RelationshipType.SIMILAR_TO
        )
        await sqlite_db.create_relationship(
            main_id, rel2_id, RelationshipType.CONTRADICTS
        )

        # Get only SIMILAR_TO relationships
        related = await sqlite_db.get_related_memories(
            main_id,
            relationship_types=[RelationshipType.SIMILAR_TO]
        )

        assert len(related) == 1
        assert related[0][1].type == RelationshipType.SIMILAR_TO

    @pytest.mark.asyncio
    async def test_delete_memory_cascades_relationships(self, sqlite_db):
        """Test that deleting a memory also deletes its relationships."""
        memory1 = Memory(type=MemoryType.GENERAL, title="Memory 1", content="Content")
        memory2 = Memory(type=MemoryType.GENERAL, title="Memory 2", content="Content")

        id1 = await sqlite_db.store_memory(memory1)
        id2 = await sqlite_db.store_memory(memory2)

        await sqlite_db.create_relationship(
            id1, id2, RelationshipType.RELATED_TO
        )

        # Delete memory1
        await sqlite_db.delete_memory(id1)

        # Verify memory2 has no relationships
        related = await sqlite_db.get_related_memories(id2)
        assert len(related) == 0


class TestSQLiteMemoryDatabaseStatistics:
    """Test statistics gathering."""

    @pytest.mark.asyncio
    async def test_get_memory_statistics(self, sqlite_db):
        """Test retrieving database statistics."""
        # Store various memories
        await sqlite_db.store_memory(Memory(
            type=MemoryType.SOLUTION,
            title="Solution 1",
            content="Content",
            importance=0.8
        ))
        await sqlite_db.store_memory(Memory(
            type=MemoryType.PROBLEM,
            title="Problem 1",
            content="Content",
            importance=0.6
        ))

        stats = await sqlite_db.get_memory_statistics()

        assert stats is not None
        assert 'total_memories' in stats
        assert stats['total_memories']['count'] == 2

        assert 'memories_by_type' in stats
        assert 'avg_importance' in stats

    @pytest.mark.asyncio
    async def test_statistics_empty_database(self, sqlite_db):
        """Test statistics on empty database."""
        stats = await sqlite_db.get_memory_statistics()

        assert stats['total_memories']['count'] == 0
        assert stats['total_relationships']['count'] == 0


class TestSQLiteMemoryDatabaseEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_store_memory_with_special_characters(self, sqlite_db):
        """Test storing memory with special characters."""
        memory = Memory(
            type=MemoryType.GENERAL,
            title="Memory with 'quotes' and \"double quotes\"",
            content="Content with <html> tags and $special chars"
        )

        memory_id = await sqlite_db.store_memory(memory)
        retrieved = await sqlite_db.get_memory(memory_id)

        assert retrieved.title == memory.title
        assert retrieved.content == memory.content

    @pytest.mark.asyncio
    async def test_store_memory_with_empty_tags(self, sqlite_db):
        """Test storing memory with empty tag list."""
        memory = Memory(
            type=MemoryType.GENERAL,
            title="No tags",
            content="Content",
            tags=[]
        )

        memory_id = await sqlite_db.store_memory(memory)
        retrieved = await sqlite_db.get_memory(memory_id)

        assert retrieved.tags == []

    @pytest.mark.asyncio
    async def test_store_memory_with_complex_context(self, sqlite_db):
        """Test storing memory with complex nested context."""
        memory = Memory(
            type=MemoryType.FILE_CONTEXT,
            title="Complex context",
            content="Content",
            context=MemoryContext(
                project_path="/complex/path",
                files_involved=["file1.py", "file2.py", "file3.py"],
                languages=["python", "javascript"],
                frameworks=["fastapi", "react"],
                technologies=["docker", "postgres"],
                additional_metadata={
                    "nested": {"key": "value"},
                    "list": [1, 2, 3],
                    "string": "test"
                }
            )
        )

        memory_id = await sqlite_db.store_memory(memory)
        retrieved = await sqlite_db.get_memory(memory_id)

        assert retrieved.context.files_involved == ["file1.py", "file2.py", "file3.py"]
        assert retrieved.context.additional_metadata["nested"]["key"] == "value"

    @pytest.mark.asyncio
    async def test_search_returns_ordered_results(self, sqlite_db):
        """Test that search results are ordered by importance then created_at."""
        # Store memories with different importance levels
        await sqlite_db.store_memory(Memory(
            type=MemoryType.GENERAL,
            title="Low",
            content="Content",
            importance=0.3
        ))
        await sqlite_db.store_memory(Memory(
            type=MemoryType.GENERAL,
            title="High",
            content="Content",
            importance=0.9
        ))
        await sqlite_db.store_memory(Memory(
            type=MemoryType.GENERAL,
            title="Medium",
            content="Content",
            importance=0.6
        ))

        query = SearchQuery()
        results = await sqlite_db.search_memories(query)

        # Results should be ordered by importance descending
        assert results[0].importance >= results[1].importance >= results[2].importance
