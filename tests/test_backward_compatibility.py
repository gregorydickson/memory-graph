"""
Tests for backward compatibility with existing single-tenant deployments.

This module ensures that existing single-tenant deployments continue to work
unchanged when multi-tenancy code is added, and that all existing features
work without requiring tenant_id or other multi-tenant fields.
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest import mock

from memorygraph.backends.sqlite_fallback import SQLiteFallbackBackend
from memorygraph.sqlite_database import SQLiteMemoryDatabase
from memorygraph.models import (
    Memory, MemoryType, MemoryContext, Relationship, RelationshipType, SearchQuery
)
from memorygraph.config import Config


class TestSingleTenantModeUnchanged:
    """Test that existing single-tenant deployments work unchanged."""

    @pytest.fixture
    async def backend(self):
        """Create backend in single-tenant mode (default)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "single_tenant.db")

            # Ensure single-tenant mode (default)
            with mock.patch.dict(os.environ, {"MEMORY_MULTI_TENANT_MODE": "false"}):
                from importlib import reload
                import memorygraph.config
                reload(memorygraph.config)

                backend = SQLiteFallbackBackend(db_path=db_path)
                await backend.connect()
                await backend.initialize_schema()

                # Wrap backend with database layer
                db = SQLiteMemoryDatabase(backend)
                await db.initialize_schema()

                yield db

                await backend.disconnect()

    async def test_create_memory_without_tenant_id(self, backend):
        """Test creating memory without tenant_id works (backward compatible)."""
        db = backend
        memory = Memory(
            type=MemoryType.TASK,
            title="Legacy Task",
            content="Task created without tenant_id",
            context=MemoryContext(
                project_path="/my/project",
                session_id="session123"
            )
        )

        memory_id = await db.store_memory(memory)
        created = await db.get_memory(memory_id)

        assert created.id is not None
        assert created.title == "Legacy Task"
        assert created.context.tenant_id is None
        assert created.context.project_path == "/my/project"
        assert created.context.visibility == "project"  # default

    async def test_search_without_tenant_filtering(self, backend):
        """Test that search works without tenant filtering."""
        db = backend
        # Create multiple memories without tenant_id
        memories = [
            Memory(
                type=MemoryType.SOLUTION,
                title=f"Solution {i}",
                content=f"Solution content {i}",
                context=MemoryContext(project_path="/project")
            )
            for i in range(5)
        ]

        for memory in memories:
            await db.store_memory(memory)

        # Search should find all memories
        search_query = SearchQuery(query="Solution", limit=50)
        results = await db.search_memories(search_query)

        assert len(results) >= 5
        for result in results:
            assert result.context.tenant_id is None

    async def test_project_path_filtering_still_works(self, backend):
        """Test that project_path filtering continues to work."""
        db = backend
        # Create memories in different projects
        project_a_memory = Memory(
            type=MemoryType.CODE_PATTERN,
            title="Pattern A",
            content="Pattern for project A",
            context=MemoryContext(project_path="/project/a")
        )

        project_b_memory = Memory(
            type=MemoryType.CODE_PATTERN,
            title="Pattern B",
            content="Pattern for project B",
            context=MemoryContext(project_path="/project/b")
        )

        await db.store_memory(project_a_memory)
        await db.store_memory(project_b_memory)

        # Search with project_path filter
        search_query = SearchQuery(query="Pattern", limit=50)
        results = await db.search_memories(search_query)

        # At minimum, both should be found
        assert len(results) >= 2

        # Verify project paths are preserved
        project_paths = {r.context.project_path for r in results if r.context}
        assert "/project/a" in project_paths
        assert "/project/b" in project_paths

    async def test_update_memory_without_tenant_fields(self, backend):
        """Test updating memory without tenant fields."""
        db = backend
        # Create memory
        memory = Memory(
            type=MemoryType.TASK,
            title="Original Title",
            content="Original content"
        )

        memory_id = await db.store_memory(memory)
        created = await db.get_memory(memory_id)

        # Update without tenant fields
        created.title = "Updated Title"
        created.content = "Updated content"

        success = await db.update_memory(created)
        assert success is True

        # Get updated memory
        updated = await db.get_memory(memory_id)
        assert updated.title == "Updated Title"
        assert updated.content == "Updated content"
        assert updated.context.tenant_id is None if updated.context else True

    async def test_delete_memory_without_tenant_id(self, backend):
        """Test deleting memory without tenant_id."""
        db = backend
        memory = Memory(
            type=MemoryType.PROBLEM,
            title="Problem to Delete",
            content="This will be deleted"
        )

        memory_id = await db.store_memory(memory)

        # Delete should work
        success = await db.delete_memory(memory_id)
        assert success is True

        # Verify deletion
        retrieved = await db.get_memory(memory_id)
        assert retrieved is None

    async def test_create_relationship_without_tenant_context(self, backend):
        """Test creating relationships between memories without tenant context."""
        db = backend
        # Create two memories
        problem = Memory(
            type=MemoryType.PROBLEM,
            title="API Timeout",
            content="API calls timing out"
        )

        solution = Memory(
            type=MemoryType.SOLUTION,
            title="Increase Timeout",
            content="Set timeout to 30 seconds"
        )

        problem_id = await db.store_memory(problem)
        solution_id = await db.store_memory(solution)

        # Create relationship
        from memorygraph.models import RelationshipProperties
        relationship_id = await db.create_relationship(
            from_memory_id=solution_id,
            to_memory_id=problem_id,
            relationship_type=RelationshipType.SOLVES,
            properties=RelationshipProperties(strength=0.9)
        )

        assert relationship_id is not None
        assert isinstance(relationship_id, str)

    async def test_get_related_memories_without_tenant_filtering(self, backend):
        """Test getting related memories without tenant filtering."""
        db = backend
        # Create memories and relationships
        task = Memory(
            type=MemoryType.TASK,
            title="Main Task",
            content="Main task content"
        )

        subtask = Memory(
            type=MemoryType.TASK,
            title="Subtask",
            content="Subtask content"
        )

        task_id = await db.store_memory(task)
        subtask_id = await db.store_memory(subtask)

        # Create relationship
        from memorygraph.models import RelationshipProperties
        await db.create_relationship(
            from_memory_id=task_id,
            to_memory_id=subtask_id,
            relationship_type=RelationshipType.DEPENDS_ON,
            properties=RelationshipProperties(strength=0.8)
        )

        # Get related memories
        related = await db.get_related_memories(task_id)

        assert len(related) > 0
        # related is List[Tuple[Memory, Relationship]]
        assert any(memory.id == subtask_id for memory, rel in related)

    async def test_all_memory_types_work_without_tenant_id(self, backend):
        """Test that all memory types work without tenant_id."""
        db = backend
        memory_types = [
            MemoryType.TASK,
            MemoryType.CODE_PATTERN,
            MemoryType.PROBLEM,
            MemoryType.SOLUTION,
            MemoryType.PROJECT,
            MemoryType.TECHNOLOGY,
            MemoryType.ERROR,
            MemoryType.FIX,
            MemoryType.COMMAND,
            MemoryType.FILE_CONTEXT,
            MemoryType.WORKFLOW,
            MemoryType.GENERAL
        ]

        for mem_type in memory_types:
            memory = Memory(
                type=mem_type,
                title=f"Test {mem_type.value}",
                content=f"Content for {mem_type.value}"
            )

            memory_id = await db.store_memory(memory)
            created = await db.get_memory(memory_id)
            assert created.id is not None
            assert created.type == mem_type

    async def test_version_field_defaults_correctly(self, backend):
        """Test that version field defaults to 1 in single-tenant mode."""
        db = backend
        memory = Memory(
            type=MemoryType.TASK,
            title="Versioned Task",
            content="Task content"
        )

        memory_id = await db.store_memory(memory)
        created = await db.get_memory(memory_id)

        assert created.version == 1

    async def test_search_by_tags_without_tenant_id(self, backend):
        """Test searching by tags without tenant_id."""
        db = backend
        memory = Memory(
            type=MemoryType.CODE_PATTERN,
            title="Python Pattern",
            content="Pattern content",
            tags=["python", "async", "pattern"]
        )

        await db.store_memory(memory)

        # Search by tag (implementation specific)
        search_query = SearchQuery(query="python", limit=50)
        results = await db.search_memories(search_query)

        assert len(results) > 0

    async def test_search_by_importance_without_tenant_id(self, backend):
        """Test searching by importance without tenant_id."""
        db = backend
        high_importance = Memory(
            type=MemoryType.SOLUTION,
            title="Critical Solution",
            content="Very important solution",
            importance=0.9
        )

        low_importance = Memory(
            type=MemoryType.GENERAL,
            title="Minor Note",
            content="Low priority note",
            importance=0.2
        )

        await db.store_memory(high_importance)
        await db.store_memory(low_importance)

        # Both should be searchable
        search_query = SearchQuery(query="solution", limit=50)
        results = await db.search_memories(search_query)
        assert len(results) > 0


class TestNoPerformanceDegradation:
    """Test that single-tenant mode has no performance degradation."""

    @pytest.fixture
    async def backend(self):
        """Create backend in single-tenant mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "perf_test.db")

            with mock.patch.dict(os.environ, {"MEMORY_MULTI_TENANT_MODE": "false"}):
                from importlib import reload
                import memorygraph.config
                reload(memorygraph.config)

                backend = SQLiteFallbackBackend(db_path=db_path)
                await backend.connect()
                await backend.initialize_schema()

                # Wrap backend with database layer
                db = SQLiteMemoryDatabase(backend)
                await db.initialize_schema()

                yield db

                await backend.disconnect()

    async def test_batch_create_performance(self, backend):
        """Test batch creation performance in single-tenant mode."""
        db = backend
        memories = [
            Memory(
                type=MemoryType.TASK,
                title=f"Task {i}",
                content=f"Content {i}",
                context=MemoryContext(project_path="/project")
            )
            for i in range(100)
        ]

        # Should complete in reasonable time (no specific timing assertion,
        # just ensure it completes without hanging)
        for memory in memories:
            memory_id = await db.store_memory(memory)
            assert memory_id is not None

        # Verify all created
        search_query = SearchQuery(query="Task", limit=150)
        results = await db.search_memories(search_query)
        assert len(results) >= 100

    async def test_search_performance_without_tenant_filtering(self, backend):
        """Test search performance without tenant filtering."""
        db = backend
        # Create memories
        for i in range(50):
            memory = Memory(
                type=MemoryType.SOLUTION,
                title=f"Solution {i}",
                content=f"Solution content for test case {i}"
            )
            await db.store_memory(memory)

        # Search should be fast
        search_query = SearchQuery(query="Solution", limit=100)
        results = await db.search_memories(search_query)

        assert len(results) >= 50


class TestExistingToolHandlers:
    """Test that all existing tool handlers work in single-tenant mode."""

    @pytest.fixture
    async def backend(self):
        """Create backend in single-tenant mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "tools_test.db")

            with mock.patch.dict(os.environ, {"MEMORY_MULTI_TENANT_MODE": "false"}):
                from importlib import reload
                import memorygraph.config
                reload(memorygraph.config)

                backend = SQLiteFallbackBackend(db_path=db_path)
                await backend.connect()
                await backend.initialize_schema()

                # Wrap backend with database layer
                db = SQLiteMemoryDatabase(backend)
                await db.initialize_schema()

                yield db

                await backend.disconnect()

    async def test_store_memory_handler_pattern(self, backend):
        """Test typical store_memory tool handler pattern."""
        db = backend
        # Simulate tool handler creating a memory
        memory_data = {
            "type": "solution",
            "title": "API Rate Limiting",
            "content": "Implemented token bucket algorithm",
            "tags": ["api", "rate-limiting"],
            "importance": 0.8,
            "context": {
                "project_path": "/apps/backend",
                "files_involved": ["api.py", "middleware.py"]
            }
        }

        memory = Memory(
            type=MemoryType(memory_data["type"]),
            title=memory_data["title"],
            content=memory_data["content"],
            tags=memory_data["tags"],
            importance=memory_data["importance"],
            context=MemoryContext(**memory_data["context"])
        )

        memory_id = await db.store_memory(memory)
        created = await db.get_memory(memory_id)

        assert created.id is not None
        assert created.title == "API Rate Limiting"

    async def test_search_memories_handler_pattern(self, backend):
        """Test typical search_memories tool handler pattern."""
        db = backend
        # Create test data
        memory = Memory(
            type=MemoryType.PROBLEM,
            title="Database Connection Pool Exhausted",
            content="Connection pool hits max connections",
            tags=["database", "performance"]
        )

        await db.store_memory(memory)

        # Simulate search tool handler
        search_query = SearchQuery(query="database connection", limit=50)
        results = await db.search_memories(search_query)

        assert len(results) > 0
        assert any("connection" in r.content.lower() for r in results)

    async def test_get_memory_handler_pattern(self, backend):
        """Test typical get_memory tool handler pattern."""
        db = backend
        # Create memory
        memory = Memory(
            type=MemoryType.FIX,
            title="Fix for Memory Leak",
            content="Close connections properly"
        )

        memory_id = await db.store_memory(memory)

        # Simulate get_memory tool handler
        retrieved = await db.get_memory(memory_id)

        assert retrieved is not None
        assert retrieved.id == memory_id
        assert retrieved.title == "Fix for Memory Leak"

    async def test_update_memory_handler_pattern(self, backend):
        """Test typical update_memory tool handler pattern."""
        db = backend
        # Create memory
        memory = Memory(
            type=MemoryType.WORKFLOW,
            title="Deployment Workflow",
            content="Original workflow"
        )

        memory_id = await db.store_memory(memory)
        created = await db.get_memory(memory_id)

        # Simulate update tool handler
        created.content = "Updated workflow with rollback steps"
        created.importance = 0.9

        success = await db.update_memory(created)
        assert success is True

        # Get updated memory
        updated = await db.get_memory(memory_id)
        assert updated.content == "Updated workflow with rollback steps"
        assert updated.importance == 0.9

    async def test_create_relationship_handler_pattern(self, backend):
        """Test typical create_relationship tool handler pattern."""
        db = backend
        # Create memories
        error = Memory(
            type=MemoryType.ERROR,
            title="NullPointerException",
            content="Null reference error"
        )

        fix = Memory(
            type=MemoryType.FIX,
            title="Add Null Check",
            content="Added null safety checks"
        )

        error_id = await db.store_memory(error)
        fix_id = await db.store_memory(fix)

        # Simulate create_relationship tool handler
        from memorygraph.models import RelationshipProperties
        relationship_id = await db.create_relationship(
            from_memory_id=fix_id,
            to_memory_id=error_id,
            relationship_type=RelationshipType.ADDRESSES,
            properties=RelationshipProperties(
                strength=0.95,
                context="Fix addresses the null pointer error"
            )
        )

        assert relationship_id is not None
        assert isinstance(relationship_id, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
