"""
Comprehensive tests for MCP server handlers.

Tests cover:
- MCP tool registration
- Handler validation
- Success and failure cases
- Error handling
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from memorygraph.server import ClaudeMemoryServer
from memorygraph.database import MemoryDatabase, Neo4jConnection
from memorygraph.models import (
    Memory, MemoryType, MemoryContext, Relationship,
    RelationshipType, RelationshipProperties, SearchQuery,
    MemoryNotFoundError, ValidationError
)
from memorygraph.tools import (
    handle_store_memory,
    handle_get_memory,
    handle_search_memories,
    handle_update_memory,
    handle_delete_memory,
    handle_create_relationship,
    handle_get_related_memories,
    handle_get_memory_statistics,
)


@pytest.fixture
async def mock_database():
    """Create a mock MemoryDatabase."""
    db = AsyncMock(spec=MemoryDatabase)
    db.initialize_schema = AsyncMock()
    db.store_memory = AsyncMock()
    db.get_memory = AsyncMock()
    db.search_memories = AsyncMock()
    db.update_memory = AsyncMock()
    db.delete_memory = AsyncMock()
    db.create_relationship = AsyncMock()
    db.get_related_memories = AsyncMock()
    db.get_memory_statistics = AsyncMock()
    return db


@pytest.fixture
async def mcp_server(mock_database):
    """Create MCP server with mocked database."""
    server = ClaudeMemoryServer()
    server.memory_db = mock_database
    return server


@pytest.fixture
def sample_memory_args():
    """Sample arguments for storing a memory."""
    return {
        "type": "solution",
        "title": "Test Solution",
        "content": "This is a test solution",
        "tags": ["python", "testing"],
        "importance": 0.8,
        "confidence": 0.9,
        "context": {
            "project_path": "/test/project",
            "files_involved": ["test.py"],
            "languages": ["python"]
        }
    }


class TestStoreMemory:
    """Test store_memory handler."""

    @pytest.mark.asyncio
    async def test_store_memory_success(self, mcp_server, mock_database, sample_memory_args):
        """Test successful memory storage."""
        memory_id = str(uuid.uuid4())
        mock_database.store_memory.return_value = memory_id

        result = await handle_store_memory(mock_database, sample_memory_args)

        assert result.isError is False
        assert memory_id in str(result.content)
        mock_database.store_memory.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_memory_missing_required_fields(self, mcp_server, mock_database):
        """Test store_memory with missing required fields."""
        args = {"title": "Test"}  # Missing type and content

        result = await handle_store_memory(mock_database, args)

        assert result.isError is True
        assert "error" in str(result.content).lower()

    @pytest.mark.asyncio
    async def test_store_memory_invalid_type(self, mcp_server, mock_database):
        """Test store_memory with invalid memory type."""
        args = {
            "type": "invalid_type",
            "title": "Test",
            "content": "Test content"
        }

        result = await handle_store_memory(mock_database, args)

        assert result.isError is True

    @pytest.mark.asyncio
    async def test_store_memory_default_importance(self, mcp_server, mock_database):
        """Test that default importance (0.5) is applied when not provided."""
        memory_id = str(uuid.uuid4())
        mock_database.store_memory.return_value = memory_id

        args = {
            "type": "solution",
            "title": "Test",
            "content": "Test content"
            # importance not provided
        }
        result = await handle_store_memory(mock_database, args)

        assert result.isError is False
        # Verify the Memory object passed to store_memory has default importance
        call_args = mock_database.store_memory.call_args
        memory_obj = call_args[0][0]
        assert memory_obj.importance == 0.5

    @pytest.mark.asyncio
    async def test_store_memory_default_empty_tags(self, mcp_server, mock_database):
        """Test that default empty tags list is applied when not provided."""
        memory_id = str(uuid.uuid4())
        mock_database.store_memory.return_value = memory_id

        args = {
            "type": "solution",
            "title": "Test",
            "content": "Test content"
            # tags not provided
        }
        result = await handle_store_memory(mock_database, args)

        assert result.isError is False
        call_args = mock_database.store_memory.call_args
        memory_obj = call_args[0][0]
        assert memory_obj.tags == []

    @pytest.mark.asyncio
    async def test_store_memory_with_context(self, mcp_server, mock_database):
        """Test storing memory with context object."""
        memory_id = str(uuid.uuid4())
        mock_database.store_memory.return_value = memory_id

        args = {
            "type": "solution",
            "title": "Test",
            "content": "Test content",
            "context": {
                "project_path": "/my/project",
                "files_involved": ["main.py", "utils.py"],
                "languages": ["python"],
                "frameworks": ["fastapi"]
            }
        }
        result = await handle_store_memory(mock_database, args)

        assert result.isError is False
        call_args = mock_database.store_memory.call_args
        memory_obj = call_args[0][0]
        assert memory_obj.context is not None
        assert memory_obj.context.project_path == "/my/project"
        assert memory_obj.context.files_involved == ["main.py", "utils.py"]

    @pytest.mark.asyncio
    async def test_store_memory_with_summary(self, mcp_server, mock_database):
        """Test storing memory with optional summary field."""
        memory_id = str(uuid.uuid4())
        mock_database.store_memory.return_value = memory_id

        args = {
            "type": "solution",
            "title": "Test",
            "content": "Test content",
            "summary": "Brief summary of the solution"
        }
        result = await handle_store_memory(mock_database, args)

        assert result.isError is False
        call_args = mock_database.store_memory.call_args
        memory_obj = call_args[0][0]
        assert memory_obj.summary == "Brief summary of the solution"

    @pytest.mark.asyncio
    async def test_store_memory_importance_boundary_zero(self, mcp_server, mock_database):
        """Test storing memory with importance = 0.0 (boundary)."""
        memory_id = str(uuid.uuid4())
        mock_database.store_memory.return_value = memory_id

        args = {
            "type": "solution",
            "title": "Test",
            "content": "Test content",
            "importance": 0.0
        }
        result = await handle_store_memory(mock_database, args)

        assert result.isError is False
        call_args = mock_database.store_memory.call_args
        memory_obj = call_args[0][0]
        assert memory_obj.importance == 0.0

    @pytest.mark.asyncio
    async def test_store_memory_importance_boundary_one(self, mcp_server, mock_database):
        """Test storing memory with importance = 1.0 (boundary)."""
        memory_id = str(uuid.uuid4())
        mock_database.store_memory.return_value = memory_id

        args = {
            "type": "solution",
            "title": "Test",
            "content": "Test content",
            "importance": 1.0
        }
        result = await handle_store_memory(mock_database, args)

        assert result.isError is False
        call_args = mock_database.store_memory.call_args
        memory_obj = call_args[0][0]
        assert memory_obj.importance == 1.0

    @pytest.mark.asyncio
    async def test_store_memory_all_memory_types(self, mcp_server, mock_database):
        """Test storing memories with all valid memory types."""
        memory_id = str(uuid.uuid4())
        mock_database.store_memory.return_value = memory_id

        valid_types = [
            "task", "code_pattern", "problem", "solution", "project",
            "technology", "error", "fix", "command", "file_context",
            "workflow", "general"
        ]

        for mem_type in valid_types:
            args = {
                "type": mem_type,
                "title": f"Test {mem_type}",
                "content": "Test content"
            }
            result = await handle_store_memory(mock_database, args)
            assert result.isError is False, f"Valid type '{mem_type}' was rejected"


class TestGetMemory:
    """Test get_memory handler."""

    @pytest.mark.asyncio
    async def test_get_memory_success(self, mcp_server, mock_database):
        """Test successful memory retrieval."""
        memory_id = str(uuid.uuid4())
        mock_memory = Memory(
            id=memory_id,
            type=MemoryType.SOLUTION,
            title="Test Solution",
            content="Test content"
        )
        mock_database.get_memory.return_value = mock_memory

        result = await handle_get_memory(mock_database, {"memory_id": memory_id})

        assert result.isError is False
        assert "Test Solution" in str(result.content)
        assert "Test content" in str(result.content)
        mock_database.get_memory.assert_called_once_with(memory_id, True)

    @pytest.mark.asyncio
    async def test_get_memory_not_found(self, mcp_server, mock_database):
        """Test get_memory when memory doesn't exist."""
        memory_id = str(uuid.uuid4())
        mock_database.get_memory.return_value = None

        result = await handle_get_memory(mock_database, {"memory_id": memory_id})

        assert result.isError is True
        assert "not found" in str(result.content).lower()

    @pytest.mark.asyncio
    async def test_get_memory_missing_id(self, mcp_server, mock_database):
        """Test get_memory without providing ID."""
        result = await handle_get_memory(mock_database, {})

        assert result.isError is True
        assert "missing" in str(result.content).lower()

    @pytest.mark.asyncio
    async def test_get_memory_include_relationships_false(self, mcp_server, mock_database):
        """Test get_memory with include_relationships=False."""
        memory_id = str(uuid.uuid4())
        mock_memory = Memory(
            id=memory_id,
            type=MemoryType.SOLUTION,
            title="Test Solution",
            content="Test content"
        )
        mock_database.get_memory.return_value = mock_memory

        result = await handle_get_memory(mock_database, {
            "memory_id": memory_id,
            "include_relationships": False
        })

        assert result.isError is False
        mock_database.get_memory.assert_called_once_with(memory_id, False)

    @pytest.mark.asyncio
    async def test_get_memory_with_summary(self, mcp_server, mock_database):
        """Test get_memory displays summary when present."""
        memory_id = str(uuid.uuid4())
        mock_memory = Memory(
            id=memory_id,
            type=MemoryType.SOLUTION,
            title="Test Solution",
            content="Test content",
            summary="Brief summary"
        )
        mock_database.get_memory.return_value = mock_memory

        result = await handle_get_memory(mock_database, {"memory_id": memory_id})

        assert result.isError is False
        assert "Brief summary" in str(result.content)
        assert "Summary" in str(result.content)

    @pytest.mark.asyncio
    async def test_get_memory_with_context(self, mcp_server, mock_database):
        """Test get_memory displays context when present."""
        memory_id = str(uuid.uuid4())
        mock_memory = Memory(
            id=memory_id,
            type=MemoryType.SOLUTION,
            title="Test Solution",
            content="Test content",
            context=MemoryContext(
                project_path="/my/project",
                languages=["python"],
                frameworks=["fastapi"],
                git_branch="main"
            )
        )
        mock_database.get_memory.return_value = mock_memory

        result = await handle_get_memory(mock_database, {"memory_id": memory_id})

        assert result.isError is False
        assert "/my/project" in str(result.content)
        assert "python" in str(result.content)
        assert "fastapi" in str(result.content)
        assert "main" in str(result.content)

    @pytest.mark.asyncio
    async def test_get_memory_files_truncation_exactly_three(self, mcp_server, mock_database):
        """Test get_memory shows all files when exactly 3."""
        memory_id = str(uuid.uuid4())
        mock_memory = Memory(
            id=memory_id,
            type=MemoryType.SOLUTION,
            title="Test",
            content="Test content",
            context=MemoryContext(
                files_involved=["file1.py", "file2.py", "file3.py"]
            )
        )
        mock_database.get_memory.return_value = mock_memory

        result = await handle_get_memory(mock_database, {"memory_id": memory_id})

        assert result.isError is False
        assert "file1.py" in str(result.content)
        assert "file2.py" in str(result.content)
        assert "file3.py" in str(result.content)
        assert "more" not in str(result.content).lower()

    @pytest.mark.asyncio
    async def test_get_memory_files_truncation_more_than_three(self, mcp_server, mock_database):
        """Test get_memory truncates files list when more than 3."""
        memory_id = str(uuid.uuid4())
        mock_memory = Memory(
            id=memory_id,
            type=MemoryType.SOLUTION,
            title="Test",
            content="Test content",
            context=MemoryContext(
                files_involved=["file1.py", "file2.py", "file3.py", "file4.py", "file5.py"]
            )
        )
        mock_database.get_memory.return_value = mock_memory

        result = await handle_get_memory(mock_database, {"memory_id": memory_id})

        assert result.isError is False
        assert "file1.py" in str(result.content)
        assert "file2.py" in str(result.content)
        assert "file3.py" in str(result.content)
        assert "+2 more" in str(result.content)

    @pytest.mark.asyncio
    async def test_get_memory_with_tags(self, mcp_server, mock_database):
        """Test get_memory displays tags when present."""
        memory_id = str(uuid.uuid4())
        mock_memory = Memory(
            id=memory_id,
            type=MemoryType.SOLUTION,
            title="Test",
            content="Test content",
            tags=["python", "testing", "api"]
        )
        mock_database.get_memory.return_value = mock_memory

        result = await handle_get_memory(mock_database, {"memory_id": memory_id})

        assert result.isError is False
        assert "python" in str(result.content)
        assert "testing" in str(result.content)
        assert "api" in str(result.content)

    @pytest.mark.asyncio
    async def test_get_memory_no_tags(self, mcp_server, mock_database):
        """Test get_memory displays 'None' when no tags."""
        memory_id = str(uuid.uuid4())
        mock_memory = Memory(
            id=memory_id,
            type=MemoryType.SOLUTION,
            title="Test",
            content="Test content",
            tags=[]
        )
        mock_database.get_memory.return_value = mock_memory

        result = await handle_get_memory(mock_database, {"memory_id": memory_id})

        assert result.isError is False
        assert "Tags: None" in str(result.content)


class TestSearchMemories:
    """Test search_memories handler."""

    @pytest.mark.asyncio
    async def test_search_memories_success(self, mcp_server, mock_database):
        """Test successful memory search."""
        mock_memories = [
            Memory(
                id=str(uuid.uuid4()),
                type=MemoryType.SOLUTION,
                title="Test 1",
                content="Content 1"
            ),
            Memory(
                id=str(uuid.uuid4()),
                type=MemoryType.PROBLEM,
                title="Test 2",
                content="Content 2"
            )
        ]
        mock_database.search_memories.return_value = mock_memories

        args = {
            "query": "test",
            "memory_types": ["solution", "problem"],
            "limit": 10
        }
        result = await handle_search_memories(mock_database, args)

        assert result.isError is False
        assert "Test 1" in str(result.content) or "found" in str(result.content).lower()

    @pytest.mark.asyncio
    async def test_search_memories_no_results(self, mcp_server, mock_database):
        """Test search with no results."""
        mock_database.search_memories.return_value = []

        result = await handle_search_memories(mock_database, {"query": "nonexistent"})

        assert result.isError is False
        assert "0" in str(result.content) or "no" in str(result.content).lower()


class TestUpdateMemory:
    """Test update_memory handler."""

    @pytest.mark.asyncio
    async def test_update_memory_success(self, mcp_server, mock_database):
        """Test successful memory update."""
        memory_id = str(uuid.uuid4())
        existing_memory = Memory(
            id=memory_id,
            type=MemoryType.SOLUTION,
            title="Original Title",
            content="Original content"
        )
        mock_database.get_memory.return_value = existing_memory
        mock_database.update_memory.return_value = True

        args = {
            "memory_id": memory_id,
            "title": "Updated Title",
            "content": "Updated content"
        }
        result = await handle_update_memory(mock_database, args)

        assert result.isError is False
        assert "updated" in str(result.content).lower()

    @pytest.mark.asyncio
    async def test_update_memory_not_found(self, mcp_server, mock_database):
        """Test update when memory doesn't exist."""
        memory_id = str(uuid.uuid4())
        mock_database.get_memory.return_value = None

        args = {
            "memory_id": memory_id,
            "title": "Updated Title"
        }
        result = await handle_update_memory(mock_database, args)

        assert result.isError is True
        assert "not found" in str(result.content).lower()

    @pytest.mark.asyncio
    async def test_update_memory_missing_id(self, mcp_server, mock_database):
        """Test update_memory without providing memory_id."""
        args = {"title": "Updated Title"}

        result = await handle_update_memory(mock_database, args)

        assert result.isError is True
        assert "missing" in str(result.content).lower()

    @pytest.mark.asyncio
    async def test_update_memory_partial_title_only(self, mcp_server, mock_database):
        """Test updating only the title field."""
        memory_id = str(uuid.uuid4())
        existing_memory = Memory(
            id=memory_id,
            type=MemoryType.SOLUTION,
            title="Original Title",
            content="Original content",
            tags=["original"],
            importance=0.5
        )
        mock_database.get_memory.return_value = existing_memory
        mock_database.update_memory.return_value = True

        args = {
            "memory_id": memory_id,
            "title": "New Title Only"
        }
        result = await handle_update_memory(mock_database, args)

        assert result.isError is False
        # Verify only title was changed
        call_args = mock_database.update_memory.call_args
        updated_memory = call_args[0][0]
        assert updated_memory.title == "New Title Only"
        assert updated_memory.content == "Original content"  # unchanged
        assert updated_memory.tags == ["original"]  # unchanged

    @pytest.mark.asyncio
    async def test_update_memory_partial_tags_only(self, mcp_server, mock_database):
        """Test updating only the tags field."""
        memory_id = str(uuid.uuid4())
        existing_memory = Memory(
            id=memory_id,
            type=MemoryType.SOLUTION,
            title="Original Title",
            content="Original content",
            tags=["old_tag"],
            importance=0.5
        )
        mock_database.get_memory.return_value = existing_memory
        mock_database.update_memory.return_value = True

        args = {
            "memory_id": memory_id,
            "tags": ["new_tag1", "new_tag2"]
        }
        result = await handle_update_memory(mock_database, args)

        assert result.isError is False
        call_args = mock_database.update_memory.call_args
        updated_memory = call_args[0][0]
        assert updated_memory.tags == ["new_tag1", "new_tag2"]
        assert updated_memory.title == "Original Title"  # unchanged

    @pytest.mark.asyncio
    async def test_update_memory_partial_importance_only(self, mcp_server, mock_database):
        """Test updating only the importance field."""
        memory_id = str(uuid.uuid4())
        existing_memory = Memory(
            id=memory_id,
            type=MemoryType.SOLUTION,
            title="Original Title",
            content="Original content",
            importance=0.5
        )
        mock_database.get_memory.return_value = existing_memory
        mock_database.update_memory.return_value = True

        args = {
            "memory_id": memory_id,
            "importance": 0.9
        }
        result = await handle_update_memory(mock_database, args)

        assert result.isError is False
        call_args = mock_database.update_memory.call_args
        updated_memory = call_args[0][0]
        assert updated_memory.importance == 0.9
        assert updated_memory.title == "Original Title"  # unchanged

    @pytest.mark.asyncio
    async def test_update_memory_partial_summary_only(self, mcp_server, mock_database):
        """Test updating only the summary field."""
        memory_id = str(uuid.uuid4())
        existing_memory = Memory(
            id=memory_id,
            type=MemoryType.SOLUTION,
            title="Original Title",
            content="Original content",
            summary=None
        )
        mock_database.get_memory.return_value = existing_memory
        mock_database.update_memory.return_value = True

        args = {
            "memory_id": memory_id,
            "summary": "New summary"
        }
        result = await handle_update_memory(mock_database, args)

        assert result.isError is False
        call_args = mock_database.update_memory.call_args
        updated_memory = call_args[0][0]
        assert updated_memory.summary == "New summary"

    @pytest.mark.asyncio
    async def test_update_memory_database_failure(self, mcp_server, mock_database):
        """Test when database update returns False."""
        memory_id = str(uuid.uuid4())
        existing_memory = Memory(
            id=memory_id,
            type=MemoryType.SOLUTION,
            title="Original Title",
            content="Original content"
        )
        mock_database.get_memory.return_value = existing_memory
        mock_database.update_memory.return_value = False  # DB update failed

        args = {
            "memory_id": memory_id,
            "title": "New Title"
        }
        result = await handle_update_memory(mock_database, args)

        assert result.isError is True
        assert "failed" in str(result.content).lower()


class TestDeleteMemory:
    """Test delete_memory handler."""

    @pytest.mark.asyncio
    async def test_delete_memory_success(self, mcp_server, mock_database):
        """Test successful memory deletion."""
        memory_id = str(uuid.uuid4())
        mock_database.delete_memory.return_value = True

        result = await handle_delete_memory(mock_database, {"memory_id": memory_id})

        assert result.isError is False
        assert "deleted" in str(result.content).lower()

    @pytest.mark.asyncio
    async def test_delete_memory_not_found(self, mcp_server, mock_database):
        """Test delete when memory doesn't exist."""
        memory_id = str(uuid.uuid4())
        mock_database.delete_memory.return_value = False

        result = await handle_delete_memory(mock_database, {"memory_id": memory_id})

        assert result.isError is True


class TestCreateRelationship:
    """Test create_relationship handler."""

    @pytest.mark.asyncio
    async def test_create_relationship_success(self, mcp_server, mock_database):
        """Test successful relationship creation."""
        from_id = str(uuid.uuid4())
        to_id = str(uuid.uuid4())
        relationship_id = str(uuid.uuid4())

        # create_relationship returns an ID string, not a Relationship object
        mock_database.create_relationship.return_value = relationship_id

        args = {
            "from_memory_id": from_id,
            "to_memory_id": to_id,
            "relationship_type": "SOLVES",
            "strength": 0.9
        }
        result = await handle_create_relationship(mock_database, args)

        assert result.isError is False
        assert "relationship" in str(result.content).lower()
        assert relationship_id in str(result.content)

    @pytest.mark.asyncio
    async def test_create_relationship_missing_ids(self, mcp_server):
        """Test create_relationship with missing IDs."""
        args = {"relationship_type": "SOLVES"}

        result = await handle_create_relationship(mock_database, args)

        assert result.isError is True

    @pytest.mark.asyncio
    async def test_create_relationship_invalid_type(self, mcp_server, mock_database):
        """Test create_relationship with invalid relationship type.

        This verifies server-side validation catches invalid types even though
        the MCP schema no longer includes the enum constraint (for token efficiency).
        """
        from_id = str(uuid.uuid4())
        to_id = str(uuid.uuid4())

        args = {
            "from_memory_id": from_id,
            "to_memory_id": to_id,
            "relationship_type": "INVALID_TYPE_FOOBAR",
            "strength": 0.9
        }
        result = await handle_create_relationship(mock_database, args)

        assert result.isError is True
        assert "invalid" in str(result.content).lower() or "not a valid" in str(result.content).lower()

    @pytest.mark.asyncio
    async def test_create_relationship_all_valid_types(self, mcp_server, mock_database):
        """Test that all RelationshipType enum values are accepted.

        Ensures the server-side validation accepts all 35 relationship types.
        """
        from_id = str(uuid.uuid4())
        to_id = str(uuid.uuid4())
        relationship_id = str(uuid.uuid4())
        mock_database.create_relationship.return_value = relationship_id

        # Test ALL actual RelationshipType enum values (35 total)
        valid_types = [
            # Causal (5)
            "CAUSES", "TRIGGERS", "LEADS_TO", "PREVENTS", "BREAKS",
            # Solution (5)
            "SOLVES", "ADDRESSES", "ALTERNATIVE_TO", "IMPROVES", "REPLACES",
            # Context (5)
            "OCCURS_IN", "APPLIES_TO", "WORKS_WITH", "REQUIRES", "USED_IN",
            # Learning (5)
            "BUILDS_ON", "CONTRADICTS", "CONFIRMS", "GENERALIZES", "SPECIALIZES",
            # Similarity (5)
            "SIMILAR_TO", "VARIANT_OF", "RELATED_TO", "ANALOGY_TO", "OPPOSITE_OF",
            # Workflow (5)
            "FOLLOWS", "DEPENDS_ON", "ENABLES", "BLOCKS", "PARALLEL_TO",
            # Quality (5)
            "EFFECTIVE_FOR", "INEFFECTIVE_FOR", "PREFERRED_OVER", "DEPRECATED_BY", "VALIDATED_BY"
        ]

        # Verify we're testing all 35 types
        assert len(valid_types) == 35, f"Expected 35 types, got {len(valid_types)}"

        for rel_type in valid_types:
            args = {
                "from_memory_id": from_id,
                "to_memory_id": to_id,
                "relationship_type": rel_type,
            }
            result = await handle_create_relationship(mock_database, args)
            assert result.isError is False, f"Valid type '{rel_type}' was incorrectly rejected"

    @pytest.mark.asyncio
    async def test_create_relationship_case_sensitive(self, mcp_server, mock_database):
        """Test that relationship types are case-sensitive.

        RelationshipType enum uses uppercase values, so lowercase should fail.
        """
        from_id = str(uuid.uuid4())
        to_id = str(uuid.uuid4())

        # Lowercase should fail - enum values are uppercase
        args = {
            "from_memory_id": from_id,
            "to_memory_id": to_id,
            "relationship_type": "solves",  # lowercase
        }
        result = await handle_create_relationship(mock_database, args)

        assert result.isError is True

    @pytest.mark.asyncio
    async def test_create_relationship_default_strength(self, mcp_server, mock_database):
        """Test that default strength (0.5) is applied when not provided."""
        from_id = str(uuid.uuid4())
        to_id = str(uuid.uuid4())
        relationship_id = str(uuid.uuid4())
        mock_database.create_relationship.return_value = relationship_id

        args = {
            "from_memory_id": from_id,
            "to_memory_id": to_id,
            "relationship_type": "SOLVES"
            # strength not provided
        }
        result = await handle_create_relationship(mock_database, args)

        assert result.isError is False
        call_args = mock_database.create_relationship.call_args
        properties = call_args.kwargs["properties"]
        assert properties.strength == 0.5

    @pytest.mark.asyncio
    async def test_create_relationship_default_confidence(self, mcp_server, mock_database):
        """Test that default confidence (0.8) is applied when not provided."""
        from_id = str(uuid.uuid4())
        to_id = str(uuid.uuid4())
        relationship_id = str(uuid.uuid4())
        mock_database.create_relationship.return_value = relationship_id

        args = {
            "from_memory_id": from_id,
            "to_memory_id": to_id,
            "relationship_type": "SOLVES"
            # confidence not provided
        }
        result = await handle_create_relationship(mock_database, args)

        assert result.isError is False
        call_args = mock_database.create_relationship.call_args
        properties = call_args.kwargs["properties"]
        assert properties.confidence == 0.8

    @pytest.mark.asyncio
    async def test_create_relationship_custom_strength_confidence(self, mcp_server, mock_database):
        """Test providing custom strength and confidence values."""
        from_id = str(uuid.uuid4())
        to_id = str(uuid.uuid4())
        relationship_id = str(uuid.uuid4())
        mock_database.create_relationship.return_value = relationship_id

        args = {
            "from_memory_id": from_id,
            "to_memory_id": to_id,
            "relationship_type": "SOLVES",
            "strength": 0.95,
            "confidence": 0.99
        }
        result = await handle_create_relationship(mock_database, args)

        assert result.isError is False
        call_args = mock_database.create_relationship.call_args
        properties = call_args.kwargs["properties"]
        assert properties.strength == 0.95
        assert properties.confidence == 0.99

    @pytest.mark.asyncio
    async def test_create_relationship_with_context_string(self, mcp_server, mock_database):
        """Test creating relationship with context description."""
        from_id = str(uuid.uuid4())
        to_id = str(uuid.uuid4())
        relationship_id = str(uuid.uuid4())
        mock_database.create_relationship.return_value = relationship_id

        args = {
            "from_memory_id": from_id,
            "to_memory_id": to_id,
            "relationship_type": "CAUSES",
            "context": "Config error caused timeout in production"
        }
        result = await handle_create_relationship(mock_database, args)

        assert result.isError is False
        # Context should be extracted and stored
        call_args = mock_database.create_relationship.call_args
        properties = call_args.kwargs["properties"]
        assert properties.context is not None

    @pytest.mark.asyncio
    async def test_create_relationship_strength_boundary_zero(self, mcp_server, mock_database):
        """Test creating relationship with strength = 0.0 (boundary)."""
        from_id = str(uuid.uuid4())
        to_id = str(uuid.uuid4())
        relationship_id = str(uuid.uuid4())
        mock_database.create_relationship.return_value = relationship_id

        args = {
            "from_memory_id": from_id,
            "to_memory_id": to_id,
            "relationship_type": "RELATED_TO",
            "strength": 0.0
        }
        result = await handle_create_relationship(mock_database, args)

        assert result.isError is False
        call_args = mock_database.create_relationship.call_args
        properties = call_args.kwargs["properties"]
        assert properties.strength == 0.0

    @pytest.mark.asyncio
    async def test_create_relationship_strength_boundary_one(self, mcp_server, mock_database):
        """Test creating relationship with strength = 1.0 (boundary)."""
        from_id = str(uuid.uuid4())
        to_id = str(uuid.uuid4())
        relationship_id = str(uuid.uuid4())
        mock_database.create_relationship.return_value = relationship_id

        args = {
            "from_memory_id": from_id,
            "to_memory_id": to_id,
            "relationship_type": "SOLVES",
            "strength": 1.0
        }
        result = await handle_create_relationship(mock_database, args)

        assert result.isError is False
        call_args = mock_database.create_relationship.call_args
        properties = call_args.kwargs["properties"]
        assert properties.strength == 1.0


class TestGetRelatedMemories:
    """Test get_related_memories handler."""

    @pytest.mark.asyncio
    async def test_get_related_memories_success(self, mcp_server, mock_database):
        """Test successful retrieval of related memories."""
        memory_id = str(uuid.uuid4())
        related_memory = Memory(
            id=str(uuid.uuid4()),
            type=MemoryType.PROBLEM,
            title="Related Problem",
            content="Problem content"
        )
        related_relationship = Relationship(
            from_memory_id=memory_id,
            to_memory_id=related_memory.id,
            type=RelationshipType.SOLVES,
            properties=RelationshipProperties(strength=0.9)
        )
        # get_related_memories returns list of tuples: [(Memory, Relationship), ...]
        mock_related = [(related_memory, related_relationship)]
        mock_database.get_related_memories.return_value = mock_related

        args = {
            "memory_id": memory_id,
            "relationship_types": ["SOLVES"],
            "max_depth": 2
        }
        result = await handle_get_related_memories(mock_database, args)

        assert result.isError is False
        assert "Related Problem" in str(result.content)

    @pytest.mark.asyncio
    async def test_get_related_memories_no_relations(self, mcp_server, mock_database):
        """Test get_related_memories with no relations found."""
        memory_id = str(uuid.uuid4())
        mock_database.get_related_memories.return_value = []

        result = await handle_get_related_memories(mock_database, {"memory_id": memory_id})

        assert result.isError is False

    @pytest.mark.asyncio
    async def test_get_related_memories_invalid_type_filter(self, mcp_server, mock_database):
        """Test get_related_memories with invalid relationship type in filter.

        This verifies server-side validation catches invalid types even though
        the MCP schema no longer includes the enum constraint (for token efficiency).
        """
        memory_id = str(uuid.uuid4())

        args = {
            "memory_id": memory_id,
            "relationship_types": ["INVALID_TYPE_FOOBAR"],
            "max_depth": 2
        }
        result = await handle_get_related_memories(mock_database, args)

        assert result.isError is True
        assert "invalid" in str(result.content).lower() or "not a valid" in str(result.content).lower()

    @pytest.mark.asyncio
    async def test_get_related_memories_multiple_valid_types(self, mcp_server, mock_database):
        """Test get_related_memories with multiple valid relationship types."""
        memory_id = str(uuid.uuid4())
        mock_database.get_related_memories.return_value = []

        args = {
            "memory_id": memory_id,
            "relationship_types": ["SOLVES", "CAUSES", "RELATED_TO"],
            "max_depth": 2
        }
        result = await handle_get_related_memories(mock_database, args)

        # Should not error - all types are valid
        assert result.isError is False
        # Verify the database was called with the correct RelationshipType enums
        mock_database.get_related_memories.assert_called_once()
        call_args = mock_database.get_related_memories.call_args
        assert call_args.kwargs["relationship_types"] == [
            RelationshipType.SOLVES,
            RelationshipType.CAUSES,
            RelationshipType.RELATED_TO
        ]

    @pytest.mark.asyncio
    async def test_get_related_memories_mixed_valid_invalid_types(self, mcp_server, mock_database):
        """Test get_related_memories with mix of valid and invalid types.

        Even one invalid type should cause the request to fail.
        """
        memory_id = str(uuid.uuid4())

        args = {
            "memory_id": memory_id,
            "relationship_types": ["SOLVES", "INVALID_TYPE", "CAUSES"],
            "max_depth": 2
        }
        result = await handle_get_related_memories(mock_database, args)

        assert result.isError is True

    @pytest.mark.asyncio
    async def test_get_related_memories_default_max_depth(self, mcp_server, mock_database):
        """Test that default max_depth (2) is applied when not provided."""
        memory_id = str(uuid.uuid4())
        mock_database.get_related_memories.return_value = []

        args = {
            "memory_id": memory_id
            # max_depth not provided
        }
        result = await handle_get_related_memories(mock_database, args)

        assert result.isError is False
        call_args = mock_database.get_related_memories.call_args
        assert call_args.kwargs["max_depth"] == 2

    @pytest.mark.asyncio
    async def test_get_related_memories_without_type_filter(self, mcp_server, mock_database):
        """Test get_related_memories without relationship_types filter (returns all types)."""
        memory_id = str(uuid.uuid4())
        mock_database.get_related_memories.return_value = []

        args = {
            "memory_id": memory_id
            # relationship_types not provided
        }
        result = await handle_get_related_memories(mock_database, args)

        assert result.isError is False
        call_args = mock_database.get_related_memories.call_args
        assert call_args.kwargs["relationship_types"] is None

    @pytest.mark.asyncio
    async def test_get_related_memories_max_depth_boundary(self, mcp_server, mock_database):
        """Test get_related_memories with max_depth at boundaries."""
        memory_id = str(uuid.uuid4())
        mock_database.get_related_memories.return_value = []

        # Test max_depth = 1 (minimum)
        args = {"memory_id": memory_id, "max_depth": 1}
        result = await handle_get_related_memories(mock_database, args)
        assert result.isError is False

        # Test max_depth = 5 (maximum allowed)
        args = {"memory_id": memory_id, "max_depth": 5}
        result = await handle_get_related_memories(mock_database, args)
        assert result.isError is False

    @pytest.mark.asyncio
    async def test_get_related_memories_missing_memory_id(self, mcp_server, mock_database):
        """Test get_related_memories without providing memory_id."""
        args = {"max_depth": 2}  # missing memory_id

        result = await handle_get_related_memories(mock_database, args)

        assert result.isError is True
        assert "missing" in str(result.content).lower()


class TestGetMemoryStatistics:
    """Test get_memory_statistics handler."""

    @pytest.mark.asyncio
    async def test_get_memory_statistics_success(self, mcp_server, mock_database):
        """Test successful statistics retrieval."""
        # Match the actual structure returned by get_memory_statistics
        mock_stats = {
            "total_memories": {"count": 100},
            "total_relationships": {"count": 250},
            "memories_by_type": {"solution": 50, "problem": 30},
            "avg_importance": {"avg_importance": 0.75},
            "avg_confidence": {"avg_confidence": 0.85}
        }
        mock_database.get_memory_statistics.return_value = mock_stats

        result = await handle_get_memory_statistics(mock_database, {})

        assert result.isError is False
        assert "100" in str(result.content) or "total" in str(result.content).lower()


class TestErrorHandling:
    """Test error handling across handlers."""

    @pytest.mark.asyncio
    async def test_database_error_handling(self, mcp_server, mock_database):
        """Test handling of database errors."""
        from memorygraph.models import DatabaseConnectionError

        mock_database.store_memory.side_effect = DatabaseConnectionError("DB connection failed")

        args = {
            "memory_type": "solution",
            "title": "Test",
            "content": "Test content"
        }
        result = await handle_store_memory(mock_database, args)

        assert result.isError is True
        assert "error" in str(result.content).lower()

    @pytest.mark.asyncio
    async def test_validation_error_handling(self, mcp_server, mock_database):
        """Test handling of validation errors."""
        mock_database.store_memory.side_effect = ValidationError("Invalid data")

        args = {
            "memory_type": "solution",
            "title": "Test",
            "content": "Test content"
        }
        result = await handle_store_memory(mock_database, args)

        assert result.isError is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
