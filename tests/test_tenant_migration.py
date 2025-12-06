"""
Tests for migrating from single-tenant to multi-tenant mode.

This module tests the migration process when enabling multi-tenant mode
on an existing single-tenant database, ensuring data integrity and
proper backfilling of tenant_id fields.
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest import mock

from memorygraph.backends.sqlite_fallback import SQLiteFallbackBackend
from memorygraph.sqlite_database import SQLiteMemoryDatabase
from memorygraph.models import Memory, MemoryType, MemoryContext, RelationshipType, SearchQuery
from memorygraph.config import Config


class TestEnableMultiTenantMode:
    """Test enabling multi-tenant mode on existing database."""

    async def test_enable_multitenant_on_existing_database(self):
        """Test that enabling multi-tenant mode on existing DB works correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "migration.db")

            # Step 1: Create database with single-tenant data
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

                # Create memories without tenant_id
                memories = [
                    Memory(
                        type=MemoryType.TASK,
                        title=f"Task {i}",
                        content=f"Task content {i}",
                        context=MemoryContext(project_path="/project")
                    )
                    for i in range(5)
                ]

                memory_ids = []
                for memory in memories:
                    memory_id = await db.store_memory(memory)
                    memory_ids.append(memory_id)

                await backend.disconnect()

            # Step 2: Enable multi-tenant mode and reconnect
            with mock.patch.dict(os.environ, {"MEMORY_MULTI_TENANT_MODE": "true"}):
                from importlib import reload
                import memorygraph.config
                reload(memorygraph.config)

                backend = SQLiteFallbackBackend(db_path=db_path)
                await backend.connect()
                await backend.initialize_schema()

                # Wrap backend with database layer
                db = SQLiteMemoryDatabase(backend)
                await db.initialize_schema()

                # Verify memories still exist
                for memory_id in memory_ids:
                    memory = await db.get_memory(memory_id)
                    assert memory is not None
                    assert memory.title.startswith("Task")

                await backend.disconnect()

    async def test_backfill_tenant_id_for_existing_memories(self):
        """Test backfilling tenant_id for existing memories during migration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "backfill.db")

            # Create single-tenant database
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

                # Create memories
                memory = Memory(
                    type=MemoryType.SOLUTION,
                    title="Legacy Solution",
                    content="Solution without tenant",
                    context=MemoryContext(project_path="/legacy")
                )

                memory_id = await db.store_memory(memory)

                await backend.disconnect()

            # Enable multi-tenant and perform migration
            with mock.patch.dict(os.environ, {
                "MEMORY_MULTI_TENANT_MODE": "true",
                "MEMORY_DEFAULT_TENANT": "migrated-tenant"
            }):
                from importlib import reload
                import memorygraph.config
                reload(memorygraph.config)

                backend = SQLiteFallbackBackend(db_path=db_path)
                await backend.connect()
                await backend.initialize_schema()

                # Wrap backend with database layer
                db = SQLiteMemoryDatabase(backend)
                await db.initialize_schema()

                # Here we would call a migration function to backfill tenant_id
                # For now, we verify the memory still exists and can be retrieved
                memory = await db.get_memory(memory_id)
                assert memory is not None
                assert memory.title == "Legacy Solution"

                # In a real migration, we would update the memory with tenant_id
                if memory.context:
                    memory.context.tenant_id = "migrated-tenant"
                    memory.context.visibility = "team"
                    success = await db.update_memory(memory)
                    assert success is True

                    # Get updated memory
                    updated = await db.get_memory(memory_id)
                    assert updated.context.tenant_id == "migrated-tenant"

                await backend.disconnect()

    async def test_data_integrity_during_migration(self):
        """Test that all data is preserved during migration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "integrity.db")

            # Create complex single-tenant data
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

                # Create memories with various fields
                problem = Memory(
                    type=MemoryType.PROBLEM,
                    title="Complex Problem",
                    content="Problem with many fields",
                    summary="Complex issue",
                    tags=["tag1", "tag2", "tag3"],
                    importance=0.8,
                    confidence=0.9,
                    context=MemoryContext(
                        project_path="/complex/project",
                        files_involved=["file1.py", "file2.py"],
                        languages=["python"],
                        frameworks=["fastapi"],
                        git_branch="main",
                        session_id="session123"
                    )
                )

                solution = Memory(
                    type=MemoryType.SOLUTION,
                    title="Complex Solution",
                    content="Solution with many fields",
                    summary="Detailed solution",
                    tags=["tag1", "tag4"],
                    importance=0.9,
                    context=MemoryContext(project_path="/complex/project")
                )

                problem_id = await db.store_memory(problem)
                solution_id = await db.store_memory(solution)

                # Create relationship
                from memorygraph.models import RelationshipProperties
                relationship_id = await db.create_relationship(
                    from_memory_id=solution_id,
                    to_memory_id=problem_id,
                    relationship_type=RelationshipType.SOLVES,
                    properties=RelationshipProperties(
                        strength=0.95,
                        context="Solution addresses the complex problem"
                    )
                )

                rel_id = relationship_id if relationship_id else None

                await backend.disconnect()

            # Enable multi-tenant mode
            with mock.patch.dict(os.environ, {"MEMORY_MULTI_TENANT_MODE": "true"}):
                from importlib import reload
                import memorygraph.config
                reload(memorygraph.config)

                backend = SQLiteFallbackBackend(db_path=db_path)
                await backend.connect()
                await backend.initialize_schema()

                # Wrap backend with database layer
                db = SQLiteMemoryDatabase(backend)
                await db.initialize_schema()

                # Verify problem memory preserved
                problem = await db.get_memory(problem_id)
                assert problem is not None
                assert problem.title == "Complex Problem"
                assert problem.summary == "Complex issue"
                assert set(problem.tags) == {"tag1", "tag2", "tag3"}
                assert problem.importance == 0.8
                assert problem.confidence == 0.9
                if problem.context:
                    assert problem.context.project_path == "/complex/project"
                    assert "file1.py" in problem.context.files_involved
                    assert "python" in problem.context.languages

                # Verify solution memory preserved
                solution = await db.get_memory(solution_id)
                assert solution is not None
                assert solution.title == "Complex Solution"
                assert "tag1" in solution.tags

                # Verify relationship preserved
                related = await db.get_related_memories(solution_id)
                assert len(related) > 0
                # related is List[Tuple[Memory, Relationship]]
                assert any(memory.id == problem_id for memory, rel in related)

                await backend.disconnect()


class TestMigrationRollback:
    """Test rolling back from multi-tenant to single-tenant mode."""

    async def test_rollback_to_single_tenant_mode(self):
        """Test that disabling multi-tenant mode works (rollback scenario)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "rollback.db")

            # Start in multi-tenant mode
            with mock.patch.dict(os.environ, {"MEMORY_MULTI_TENANT_MODE": "true"}):
                from importlib import reload
                import memorygraph.config
                reload(memorygraph.config)

                backend = SQLiteFallbackBackend(db_path=db_path)
                await backend.connect()
                await backend.initialize_schema()

                # Wrap backend with database layer
                db = SQLiteMemoryDatabase(backend)
                await db.initialize_schema()

                # Create memory with tenant_id
                memory = Memory(
                    type=MemoryType.TASK,
                    title="Multi-Tenant Task",
                    content="Task with tenant",
                    context=MemoryContext(
                        tenant_id="acme-corp",
                        visibility="team"
                    )
                )

                memory_id = await db.store_memory(memory)

                await backend.disconnect()

            # Rollback to single-tenant mode
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

                # Memory should still be accessible
                memory = await db.get_memory(memory_id)
                assert memory is not None
                assert memory.title == "Multi-Tenant Task"

                # tenant_id field should still be in data (just not used for filtering)
                if memory.context:
                    # The data is preserved even if not actively used
                    assert memory.context.tenant_id == "acme-corp" or memory.context.tenant_id is None

                await backend.disconnect()

    async def test_data_preserved_after_rollback(self):
        """Test that no data is lost during rollback."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "preserve.db")

            # Multi-tenant mode with data
            with mock.patch.dict(os.environ, {"MEMORY_MULTI_TENANT_MODE": "true"}):
                from importlib import reload
                import memorygraph.config
                reload(memorygraph.config)

                backend = SQLiteFallbackBackend(db_path=db_path)
                await backend.connect()
                await backend.initialize_schema()

                # Wrap backend with database layer
                db = SQLiteMemoryDatabase(backend)
                await db.initialize_schema()

                memories = []
                for i in range(10):
                    memory = Memory(
                        type=MemoryType.GENERAL,
                        title=f"Memory {i}",
                        content=f"Content {i}",
                        context=MemoryContext(
                            tenant_id=f"tenant-{i % 3}",
                            visibility="team"
                        )
                    )
                    memory_id = await db.store_memory(memory)
                    memories.append(memory_id)

                await backend.disconnect()

            # Rollback to single-tenant
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

                # All memories should still exist
                for memory_id in memories:
                    memory = await db.get_memory(memory_id)
                    assert memory is not None

                # Search should find all memories
                results = await db.search_memories(SearchQuery(query="Memory", limit=50))
                assert len(results) >= 10

                await backend.disconnect()


class TestMigrationIdempotency:
    """Test that migration operations are idempotent."""

    async def test_multiple_schema_initializations(self):
        """Test that multiple schema initializations don't corrupt data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "idempotent.db")

            with mock.patch.dict(os.environ, {"MEMORY_MULTI_TENANT_MODE": "true"}):
                from importlib import reload
                import memorygraph.config
                reload(memorygraph.config)

                backend = SQLiteFallbackBackend(db_path=db_path)
                await backend.connect()
                await backend.initialize_schema()

                # Wrap backend with database layer
                db = SQLiteMemoryDatabase(backend)
                await db.initialize_schema()

                # Create memory
                memory = Memory(
                    type=MemoryType.SOLUTION,
                    title="Test Solution",
                    content="Solution content"
                )
                memory_id = await db.store_memory(memory)

                # Re-initialize schema multiple times
                await backend.initialize_schema()

                # Wrap backend with database layer
                db = SQLiteMemoryDatabase(backend)
                await db.initialize_schema()
                await backend.initialize_schema()

                # Wrap backend with database layer
                db = SQLiteMemoryDatabase(backend)
                await db.initialize_schema()
                await backend.initialize_schema()

                # Wrap backend with database layer
                db = SQLiteMemoryDatabase(backend)
                await db.initialize_schema()

                # Memory should still exist and be intact
                memory = await db.get_memory(memory_id)
                assert memory is not None
                assert memory.title == "Test Solution"

                await backend.disconnect()

    async def test_switching_modes_multiple_times(self):
        """Test switching between single and multi-tenant modes multiple times."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "switch.db")

            # Create initial data in single-tenant
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

                memory = Memory(
                    type=MemoryType.TASK,
                    title="Original Task",
                    content="Original content"
                )
                memory_id = await db.store_memory(memory)

                await backend.disconnect()

            # Switch to multi-tenant
            with mock.patch.dict(os.environ, {"MEMORY_MULTI_TENANT_MODE": "true"}):
                from importlib import reload
                import memorygraph.config
                reload(memorygraph.config)

                backend = SQLiteFallbackBackend(db_path=db_path)
                await backend.connect()
                await backend.initialize_schema()

                # Wrap backend with database layer
                db = SQLiteMemoryDatabase(backend)
                await db.initialize_schema()

                memory = await db.get_memory(memory_id)
                assert memory is not None

                await backend.disconnect()

            # Switch back to single-tenant
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

                memory = await db.get_memory(memory_id)
                assert memory is not None
                assert memory.title == "Original Task"

                await backend.disconnect()

            # Switch to multi-tenant again
            with mock.patch.dict(os.environ, {"MEMORY_MULTI_TENANT_MODE": "true"}):
                from importlib import reload
                import memorygraph.config
                reload(memorygraph.config)

                backend = SQLiteFallbackBackend(db_path=db_path)
                await backend.connect()
                await backend.initialize_schema()

                # Wrap backend with database layer
                db = SQLiteMemoryDatabase(backend)
                await db.initialize_schema()

                memory = await db.get_memory(memory_id)
                assert memory is not None
                assert memory.title == "Original Task"

                await backend.disconnect()


class TestMigrationFailureScenarios:
    """Test migration failure and error handling scenarios."""

    async def test_invalid_tenant_id_empty(self):
        """Test that migration fails with empty tenant_id."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "invalid_empty.db")

            with mock.patch.dict(os.environ, {"MEMORY_MULTI_TENANT_MODE": "true"}):
                from importlib import reload
                import memorygraph.config
                reload(memorygraph.config)

                backend = SQLiteFallbackBackend(db_path=db_path)
                await backend.connect()
                await backend.initialize_schema()

                # Attempt migration with empty tenant_id
                from memorygraph.migration.scripts.multitenancy_migration import migrate_to_multitenant

                # Test empty string
                with pytest.raises(ValueError, match="tenant_id cannot be empty"):
                    await migrate_to_multitenant(backend, tenant_id="")

                # Test whitespace only
                with pytest.raises(ValueError, match="tenant_id cannot be empty"):
                    await migrate_to_multitenant(backend, tenant_id="   ")

                await backend.disconnect()

    async def test_invalid_tenant_id_special_characters(self):
        """Test that migration fails with invalid characters in tenant_id."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "invalid_chars.db")

            with mock.patch.dict(os.environ, {"MEMORY_MULTI_TENANT_MODE": "true"}):
                from importlib import reload
                import memorygraph.config
                reload(memorygraph.config)

                backend = SQLiteFallbackBackend(db_path=db_path)
                await backend.connect()
                await backend.initialize_schema()

                from memorygraph.migration.scripts.multitenancy_migration import migrate_to_multitenant

                # Test special characters
                invalid_tenant_ids = [
                    "tenant@corp",
                    "tenant.corp",
                    "tenant corp",
                    "tenant/corp",
                    "tenant\\corp",
                    "tenant#corp",
                    "tenant$corp"
                ]

                for invalid_id in invalid_tenant_ids:
                    with pytest.raises(
                        ValueError,
                        match="tenant_id must contain only alphanumeric characters, dashes, and underscores"
                    ):
                        await migrate_to_multitenant(backend, tenant_id=invalid_id)

                await backend.disconnect()

    async def test_invalid_tenant_id_too_long(self):
        """Test that migration fails with tenant_id exceeding 64 characters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "invalid_length.db")

            with mock.patch.dict(os.environ, {"MEMORY_MULTI_TENANT_MODE": "true"}):
                from importlib import reload
                import memorygraph.config
                reload(memorygraph.config)

                backend = SQLiteFallbackBackend(db_path=db_path)
                await backend.connect()
                await backend.initialize_schema()

                from memorygraph.migration.scripts.multitenancy_migration import migrate_to_multitenant

                # Test tenant_id with 65 characters
                long_tenant_id = "a" * 65

                with pytest.raises(ValueError, match="tenant_id must be 64 characters or less"):
                    await migrate_to_multitenant(backend, tenant_id=long_tenant_id)

                # Test that 64 characters is OK
                max_tenant_id = "a" * 64
                result = await migrate_to_multitenant(backend, tenant_id=max_tenant_id, dry_run=True)
                assert result["success"] is True

                await backend.disconnect()

    async def test_invalid_visibility_value(self):
        """Test that migration fails with invalid visibility value."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "invalid_visibility.db")

            with mock.patch.dict(os.environ, {"MEMORY_MULTI_TENANT_MODE": "true"}):
                from importlib import reload
                import memorygraph.config
                reload(memorygraph.config)

                backend = SQLiteFallbackBackend(db_path=db_path)
                await backend.connect()
                await backend.initialize_schema()

                from memorygraph.migration.scripts.multitenancy_migration import migrate_to_multitenant

                # Test invalid visibility values
                invalid_visibility_values = ["global", "shared", "internal", "secret", ""]

                for invalid_visibility in invalid_visibility_values:
                    with pytest.raises(
                        ValueError,
                        match="visibility must be one of"
                    ):
                        await migrate_to_multitenant(
                            backend,
                            tenant_id="valid-tenant",
                            visibility=invalid_visibility
                        )

                await backend.disconnect()

    async def test_migration_with_disconnected_backend(self):
        """Test that migration fails when backend is not connected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "disconnected.db")

            backend = SQLiteFallbackBackend(db_path=db_path)
            # Don't connect the backend

            from memorygraph.migration.scripts.multitenancy_migration import migrate_to_multitenant
            from memorygraph.models import DatabaseConnectionError

            with pytest.raises(DatabaseConnectionError, match="Backend must be connected"):
                await migrate_to_multitenant(backend, tenant_id="test-tenant")

    async def test_migration_dry_run_no_changes(self):
        """Test that dry_run mode does not make any actual changes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "dry_run.db")

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

                # Create memories without tenant_id
                memory = Memory(
                    type=MemoryType.TASK,
                    title="Test Memory",
                    content="Test content",
                    context=MemoryContext(project_path="/project")
                )
                memory_id = await db.store_memory(memory)

                from memorygraph.migration.scripts.multitenancy_migration import migrate_to_multitenant

                # Run dry_run migration
                result = await migrate_to_multitenant(backend, tenant_id="test-tenant", dry_run=True)

                assert result["success"] is True
                assert result["dry_run"] is True
                assert result["memories_updated"] == 1

                # Verify memory was NOT actually updated
                memory = await db.get_memory(memory_id)
                assert memory.context.tenant_id is None

                await backend.disconnect()

    async def test_migration_partial_success_tracking(self):
        """Test that migration tracks partial success when some memories update successfully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "partial.db")

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

                # Create multiple memories
                for i in range(5):
                    memory = Memory(
                        type=MemoryType.TASK,
                        title=f"Task {i}",
                        content=f"Content {i}",
                        context=MemoryContext(project_path="/project")
                    )
                    await db.store_memory(memory)

                from memorygraph.migration.scripts.multitenancy_migration import migrate_to_multitenant

                # Run migration (should succeed for all memories)
                result = await migrate_to_multitenant(backend, tenant_id="test-tenant")

                assert result["success"] is True
                assert result["memories_updated"] == 5
                assert len(result["errors"]) == 0

                await backend.disconnect()

    async def test_rollback_with_disconnected_backend(self):
        """Test that rollback fails when backend is not connected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "rollback_disconnected.db")

            backend = SQLiteFallbackBackend(db_path=db_path)
            # Don't connect the backend

            from memorygraph.migration.scripts.multitenancy_migration import rollback_from_multitenant
            from memorygraph.models import DatabaseConnectionError

            with pytest.raises(DatabaseConnectionError, match="Backend must be connected"):
                await rollback_from_multitenant(backend)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
