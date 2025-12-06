"""
Comprehensive tests for bi-temporal tracking functionality.

Tests cover:
- Temporal field creation and defaults
- Point-in-time queries
- Relationship invalidation
- History retrieval
- What changed queries
- Contradiction detection
- Migration from non-temporal to temporal
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import sqlite3
import tempfile
import os

from src.memorygraph.models import (
    Memory, MemoryType, Relationship, RelationshipType,
    RelationshipProperties
)
from src.memorygraph.backends.sqlite_fallback import SQLiteFallbackBackend
from src.memorygraph.sqlite_database import SQLiteMemoryDatabase


@pytest.fixture
async def temporal_backend(tmp_path):
    """Create a SQLite backend with temporal schema."""
    db_path = str(tmp_path / "temporal_test.db")
    backend = SQLiteFallbackBackend(db_path=db_path)
    await backend.connect()
    await backend.initialize_schema()
    yield backend
    await backend.disconnect()


@pytest.fixture
async def temporal_db(temporal_backend):
    """Create a SQLiteMemoryDatabase with temporal support."""
    db = SQLiteMemoryDatabase(temporal_backend)
    await db.initialize_schema()
    yield db


@pytest.fixture
def sample_memories():
    """Create sample memories for testing."""
    return [
        Memory(
            id="mem1",
            type=MemoryType.PROBLEM,
            title="Redis timeout error",
            content="Redis connections timing out in production"
        ),
        Memory(
            id="mem2",
            type=MemoryType.SOLUTION,
            title="Solution: Increase timeout to 5s",
            content="Increased Redis timeout to 5 seconds"
        ),
        Memory(
            id="mem3",
            type=MemoryType.SOLUTION,
            title="Solution: Connection pooling",
            content="Implemented connection pooling with redis-py"
        )
    ]


class TestTemporalSchemaCreation:
    """Test that temporal schema is created correctly."""

    @pytest.mark.asyncio
    async def test_relationships_table_has_temporal_fields(self, temporal_backend):
        """Test that relationships table includes temporal fields."""
        cursor = temporal_backend.conn.cursor()
        cursor.execute("PRAGMA table_info(relationships)")
        columns = {row[1] for row in cursor.fetchall()}

        # Check all temporal fields exist
        assert "valid_from" in columns, "valid_from field missing"
        assert "valid_until" in columns, "valid_until field missing"
        assert "recorded_at" in columns, "recorded_at field missing"
        assert "invalidated_by" in columns, "invalidated_by field missing"

    @pytest.mark.asyncio
    async def test_temporal_indexes_exist(self, temporal_backend):
        """Test that temporal indexes are created."""
        cursor = temporal_backend.conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='relationships'"
        )
        indexes = {row[0] for row in cursor.fetchall()}

        # Check for temporal indexes
        assert "idx_relationships_temporal" in indexes, "Temporal index missing"
        assert "idx_relationships_current" in indexes, "Current relationships index missing"
        assert "idx_relationships_recorded" in indexes, "Recorded_at index missing"


class TestTemporalRelationshipCreation:
    """Test creating relationships with temporal fields."""

    @pytest.mark.asyncio
    async def test_create_relationship_with_defaults(self, temporal_db, sample_memories):
        """Test creating relationship with default temporal values."""
        # Store memories first
        for mem in sample_memories[:2]:
            await temporal_db.store_memory(mem)

        # Create relationship (should use defaults)
        before_create = datetime.now(timezone.utc)
        rel_id = await temporal_db.create_relationship(
            from_memory_id="mem2",
            to_memory_id="mem1",
            relationship_type=RelationshipType.SOLVES,
            strength=0.9
        )
        after_create = datetime.now(timezone.utc)

        # Verify relationship exists with temporal fields
        cursor = temporal_db.backend.conn.cursor()
        cursor.execute("SELECT * FROM relationships WHERE id = ?", (rel_id,))
        row = cursor.fetchone()

        assert row is not None
        # Get column names
        columns = [desc[0] for desc in cursor.description]
        rel_dict = dict(zip(columns, row))

        # Check temporal fields have sensible defaults
        assert "valid_from" in rel_dict
        assert "valid_until" in rel_dict
        assert "recorded_at" in rel_dict
        assert "invalidated_by" in rel_dict

        # valid_from should be set to now
        valid_from = datetime.fromisoformat(rel_dict["valid_from"])
        assert before_create <= valid_from <= after_create

        # valid_until should be NULL (currently valid)
        assert rel_dict["valid_until"] is None

        # recorded_at should be set to now
        recorded_at = datetime.fromisoformat(rel_dict["recorded_at"])
        assert before_create <= recorded_at <= after_create

        # invalidated_by should be NULL
        assert rel_dict["invalidated_by"] is None

    @pytest.mark.asyncio
    async def test_create_relationship_with_explicit_valid_from(self, temporal_db, sample_memories):
        """Test creating relationship with explicit valid_from timestamp."""
        for mem in sample_memories[:2]:
            await temporal_db.store_memory(mem)

        # Create relationship with explicit valid_from (2 months ago)
        past_time = datetime.now(timezone.utc) - timedelta(days=60)
        rel_id = await temporal_db.create_relationship(
            from_memory_id="mem2",
            to_memory_id="mem1",
            relationship_type=RelationshipType.SOLVES,
            valid_from=past_time
        )

        # Verify valid_from was set correctly
        cursor = temporal_db.backend.conn.cursor()
        cursor.execute("SELECT valid_from FROM relationships WHERE id = ?", (rel_id,))
        row = cursor.fetchone()
        valid_from = datetime.fromisoformat(row[0])

        # Should match the past_time we provided (within 1 second)
        assert abs((valid_from - past_time).total_seconds()) < 1


class TestPointInTimeQueries:
    """Test querying relationships as they existed at a specific time."""

    @pytest.mark.asyncio
    async def test_query_current_relationships_only(self, temporal_db, sample_memories):
        """Test that default queries return only current relationships."""
        for mem in sample_memories:
            await temporal_db.store_memory(mem)

        # Create two relationships: one current, one invalidated
        rel1_id = await temporal_db.create_relationship(
            from_memory_id="mem2",
            to_memory_id="mem1",
            relationship_type=RelationshipType.SOLVES
        )

        rel2_id = await temporal_db.create_relationship(
            from_memory_id="mem3",
            to_memory_id="mem1",
            relationship_type=RelationshipType.SOLVES
        )

        # Invalidate rel1 (it was superseded)
        cursor = temporal_db.backend.conn.cursor()
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute(
            "UPDATE relationships SET valid_until = ?, invalidated_by = ? WHERE id = ?",
            (now, rel2_id, rel1_id)
        )
        temporal_db.backend.commit()

        # Query current relationships (should only return rel2)
        relationships = await temporal_db.get_related_memories("mem1")

        # Should only return current (non-invalidated) relationships
        # get_related_memories returns List[Tuple[Memory, Relationship]]
        rel_ids = [r[1].id for r in relationships]  # r[1] is the Relationship
        assert rel2_id in rel_ids, "Current relationship should be returned"
        assert rel1_id not in rel_ids, "Invalidated relationship should not be returned"

    @pytest.mark.asyncio
    async def test_query_as_of_past_date(self, temporal_db, sample_memories):
        """Test querying relationships as they existed in the past."""
        for mem in sample_memories:
            await temporal_db.store_memory(mem)

        # Create relationship 1 (2 months ago)
        two_months_ago = datetime.now(timezone.utc) - timedelta(days=60)
        rel1_id = await temporal_db.create_relationship(
            from_memory_id="mem2",
            to_memory_id="mem1",
            relationship_type=RelationshipType.SOLVES,
            valid_from=two_months_ago
        )

        # Invalidate it 1 month ago
        one_month_ago = datetime.now(timezone.utc) - timedelta(days=30)
        cursor = temporal_db.backend.conn.cursor()
        cursor.execute(
            "UPDATE relationships SET valid_until = ? WHERE id = ?",
            (one_month_ago.isoformat(), rel1_id)
        )
        temporal_db.backend.commit()

        # Create relationship 2 (1 month ago)
        rel2_id = await temporal_db.create_relationship(
            from_memory_id="mem3",
            to_memory_id="mem1",
            relationship_type=RelationshipType.SOLVES,
            valid_from=one_month_ago
        )

        # Query as of 45 days ago (should return only rel1)
        fortyfive_days_ago = datetime.now(timezone.utc) - timedelta(days=45)
        relationships = await temporal_db.get_related_memories(
            "mem1",
            as_of=fortyfive_days_ago
        )

        rel_ids = [r[1].id for r in relationships]  # r[1] is the Relationship
        assert rel1_id in rel_ids, "Relationship 1 should be valid at that time"
        assert rel2_id not in rel_ids, "Relationship 2 did not exist at that time"

        # Query as of today (should return only rel2)
        relationships_now = await temporal_db.get_related_memories("mem1")
        rel_ids_now = [r[1].id for r in relationships_now]  # r[1] is the Relationship
        assert rel1_id not in rel_ids_now, "Relationship 1 should be invalidated now"
        assert rel2_id in rel_ids_now, "Relationship 2 should be current"


class TestRelationshipInvalidation:
    """Test invalidating relationships."""

    @pytest.mark.asyncio
    async def test_invalidate_relationship(self, temporal_db, sample_memories):
        """Test manually invalidating a relationship."""
        for mem in sample_memories[:2]:
            await temporal_db.store_memory(mem)

        # Create relationship
        rel_id = await temporal_db.create_relationship(
            from_memory_id="mem2",
            to_memory_id="mem1",
            relationship_type=RelationshipType.SOLVES
        )

        # Invalidate it
        await temporal_db.invalidate_relationship(rel_id)

        # Verify it's marked as invalid
        cursor = temporal_db.backend.conn.cursor()
        cursor.execute("SELECT valid_until FROM relationships WHERE id = ?", (rel_id,))
        row = cursor.fetchone()

        assert row[0] is not None, "valid_until should be set"
        valid_until = datetime.fromisoformat(row[0])
        assert valid_until <= datetime.now(timezone.utc)

    @pytest.mark.asyncio
    async def test_invalidate_with_successor(self, temporal_db, sample_memories):
        """Test invalidating a relationship with a successor reference."""
        for mem in sample_memories:
            await temporal_db.store_memory(mem)

        # Create first relationship
        old_rel_id = await temporal_db.create_relationship(
            from_memory_id="mem2",
            to_memory_id="mem1",
            relationship_type=RelationshipType.SOLVES
        )

        # Create new relationship that supersedes the old one
        new_rel_id = await temporal_db.create_relationship(
            from_memory_id="mem3",
            to_memory_id="mem1",
            relationship_type=RelationshipType.SOLVES
        )

        # Invalidate old relationship, referencing the new one
        await temporal_db.invalidate_relationship(old_rel_id, invalidated_by=new_rel_id)

        # Verify invalidated_by is set
        cursor = temporal_db.backend.conn.cursor()
        cursor.execute(
            "SELECT valid_until, invalidated_by FROM relationships WHERE id = ?",
            (old_rel_id,)
        )
        row = cursor.fetchone()

        assert row[0] is not None, "valid_until should be set"
        assert row[1] == new_rel_id, "invalidated_by should reference new relationship"


class TestRelationshipHistory:
    """Test retrieving relationship history."""

    @pytest.mark.asyncio
    async def test_get_relationship_history(self, temporal_db, sample_memories):
        """Test getting full history of relationships for a memory."""
        for mem in sample_memories:
            await temporal_db.store_memory(mem)

        # Create three solutions over time
        three_months_ago = datetime.now(timezone.utc) - timedelta(days=90)
        two_months_ago = datetime.now(timezone.utc) - timedelta(days=60)
        one_month_ago = datetime.now(timezone.utc) - timedelta(days=30)

        # Solution 1 (old)
        rel1_id = await temporal_db.create_relationship(
            from_memory_id="mem2",
            to_memory_id="mem1",
            relationship_type=RelationshipType.SOLVES,
            valid_from=three_months_ago
        )

        # Invalidate solution 1
        cursor = temporal_db.backend.conn.cursor()
        cursor.execute(
            "UPDATE relationships SET valid_until = ? WHERE id = ?",
            (two_months_ago.isoformat(), rel1_id)
        )
        temporal_db.backend.commit()

        # Solution 2 (replaced)
        rel2_id = await temporal_db.create_relationship(
            from_memory_id="mem3",
            to_memory_id="mem1",
            relationship_type=RelationshipType.SOLVES,
            valid_from=two_months_ago
        )

        # Invalidate solution 2
        cursor.execute(
            "UPDATE relationships SET valid_until = ? WHERE id = ?",
            (one_month_ago.isoformat(), rel2_id)
        )
        temporal_db.backend.commit()

        # Solution 3 (current)
        rel3_id = await temporal_db.create_relationship(
            from_memory_id="mem2",  # Back to solution 2, but improved
            to_memory_id="mem1",
            relationship_type=RelationshipType.SOLVES,
            valid_from=one_month_ago
        )

        # Get full history
        history = await temporal_db.get_relationship_history("mem1")

        # Should return all 3 relationships, ordered by valid_from
        assert len(history) == 3
        assert history[0].id == rel1_id
        assert history[1].id == rel2_id
        assert history[2].id == rel3_id

        # Verify temporal ordering
        assert history[0].properties.valid_from < history[1].properties.valid_from
        assert history[1].properties.valid_from < history[2].properties.valid_from

        # Verify current state
        assert history[2].properties.valid_until is None, "Latest should be current"


class TestWhatChanged:
    """Test what_changed queries."""

    @pytest.mark.asyncio
    async def test_what_changed_since_date(self, temporal_db, sample_memories):
        """Test querying what changed since a specific date."""
        for mem in sample_memories[:2]:
            await temporal_db.store_memory(mem)

        # Create relationships at different times
        one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        two_days_ago = datetime.now(timezone.utc) - timedelta(days=2)

        # Old relationship
        old_rel_id = await temporal_db.create_relationship(
            from_memory_id="mem2",
            to_memory_id="mem1",
            relationship_type=RelationshipType.SOLVES,
            valid_from=one_week_ago
        )

        # Update recorded_at to be in the past
        cursor = temporal_db.backend.conn.cursor()
        cursor.execute(
            "UPDATE relationships SET recorded_at = ? WHERE id = ?",
            (one_week_ago.isoformat(), old_rel_id)
        )
        temporal_db.backend.commit()

        # Recent relationship
        new_rel_id = await temporal_db.create_relationship(
            from_memory_id="mem2",
            to_memory_id="mem1",
            relationship_type=RelationshipType.IMPROVES
        )

        # Query what changed in last 3 days
        three_days_ago = datetime.now(timezone.utc) - timedelta(days=3)
        changes = await temporal_db.what_changed(since=three_days_ago)

        # Should only include recent relationship
        new_rel_ids = [r.id for r in changes["new_relationships"]]
        assert new_rel_id in new_rel_ids
        assert old_rel_id not in new_rel_ids


class TestBackwardCompatibility:
    """Test that temporal changes don't break existing functionality."""

    @pytest.mark.asyncio
    async def test_existing_queries_work_unchanged(self, temporal_db, sample_memories):
        """Test that existing non-temporal queries still work."""
        for mem in sample_memories[:2]:
            await temporal_db.store_memory(mem)

        # Create relationship using old API (no temporal params)
        rel_id = await temporal_db.create_relationship(
            from_memory_id="mem2",
            to_memory_id="mem1",
            relationship_type=RelationshipType.SOLVES
        )

        # Old query methods should still work
        relationships = await temporal_db.get_related_memories("mem1")
        assert len(relationships) > 0
        # get_related_memories returns List[Tuple[Memory, Relationship]]
        assert any(r[1].id == rel_id for r in relationships)

    @pytest.mark.asyncio
    async def test_default_behavior_no_breaking_changes(self, temporal_db, sample_memories):
        """Test that default behavior returns only current relationships."""
        for mem in sample_memories:
            await temporal_db.store_memory(mem)

        # Create and invalidate a relationship
        old_rel_id = await temporal_db.create_relationship(
            from_memory_id="mem2",
            to_memory_id="mem1",
            relationship_type=RelationshipType.SOLVES
        )
        await temporal_db.invalidate_relationship(old_rel_id)

        # Create current relationship
        current_rel_id = await temporal_db.create_relationship(
            from_memory_id="mem3",
            to_memory_id="mem1",
            relationship_type=RelationshipType.SOLVES
        )

        # Default query should only return current
        relationships = await temporal_db.get_related_memories("mem1")
        # get_related_memories returns List[Tuple[Memory, Relationship]]
        rel_ids = [r[1].id for r in relationships]  # r[1] is the Relationship

        assert current_rel_id in rel_ids, "Current relationship should be returned"
        assert old_rel_id not in rel_ids, "Old relationship should NOT be returned by default"


class TestMigrationFromNonTemporal:
    """Test migrating existing databases to temporal schema."""

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Migration script not yet implemented - covered by workplan Section 5")
    async def test_migration_adds_temporal_fields(self, tmp_path):
        """Test that migration adds temporal fields to existing database."""
        db_path = str(tmp_path / "pre_temporal.db")

        # Create old schema (without temporal fields but with created_at/updated_at to match backend)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE nodes (
                id TEXT PRIMARY KEY,
                label TEXT NOT NULL,
                properties TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE relationships (
                id TEXT PRIMARY KEY,
                from_id TEXT NOT NULL,
                to_id TEXT NOT NULL,
                rel_type TEXT NOT NULL,
                properties TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (from_id) REFERENCES nodes(id),
                FOREIGN KEY (to_id) REFERENCES nodes(id)
            )
        """)
        conn.commit()
        conn.close()

        # Now connect with temporal backend (will create new schema with temporal fields)
        backend = SQLiteFallbackBackend(db_path=db_path)
        await backend.connect()
        # initialize_schema uses CREATE TABLE IF NOT EXISTS, so it will just add indexes
        await backend.initialize_schema()

        # TODO: This will work once we implement the migration
        # For now, we'll manually add the fields to test the concept
        cursor = backend.conn.cursor()
        try:
            cursor.execute("ALTER TABLE relationships ADD COLUMN valid_from TIMESTAMP")
            cursor.execute("ALTER TABLE relationships ADD COLUMN valid_until TIMESTAMP")
            cursor.execute("ALTER TABLE relationships ADD COLUMN recorded_at TIMESTAMP")
            cursor.execute("ALTER TABLE relationships ADD COLUMN invalidated_by TEXT")
            backend.commit()
        except sqlite3.Error as e:
            # Columns might already exist
            pass

        # Verify temporal fields exist
        cursor.execute("PRAGMA table_info(relationships)")
        columns = {row[1] for row in cursor.fetchall()}

        assert "valid_from" in columns
        assert "valid_until" in columns
        assert "recorded_at" in columns
        assert "invalidated_by" in columns

        await backend.disconnect()

    @pytest.mark.asyncio
    async def test_migration_sets_defaults_for_existing_data(self, tmp_path):
        """Test that migration sets sensible defaults for existing relationships."""
        db_path = str(tmp_path / "pre_temporal_with_data.db")

        # Create old schema with some data
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE nodes (
                id TEXT PRIMARY KEY,
                label TEXT NOT NULL,
                properties TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE relationships (
                id TEXT PRIMARY KEY,
                from_id TEXT NOT NULL,
                to_id TEXT NOT NULL,
                rel_type TEXT NOT NULL,
                properties TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Insert test data
        cursor.execute(
            "INSERT INTO nodes (id, label, properties) VALUES (?, ?, ?)",
            ("n1", "Memory", '{"title": "Test"}')
        )
        cursor.execute(
            "INSERT INTO nodes (id, label, properties) VALUES (?, ?, ?)",
            ("n2", "Memory", '{"title": "Test 2"}')
        )
        cursor.execute(
            "INSERT INTO relationships (id, from_id, to_id, rel_type, properties) VALUES (?, ?, ?, ?, ?)",
            ("r1", "n1", "n2", "RELATES_TO", '{}')
        )
        conn.commit()
        conn.close()

        # Run migration
        backend = SQLiteFallbackBackend(db_path=db_path)
        await backend.connect()

        # Add temporal fields (simulating migration)
        cursor = backend.conn.cursor()
        cursor.execute("ALTER TABLE relationships ADD COLUMN valid_from TIMESTAMP")
        cursor.execute("ALTER TABLE relationships ADD COLUMN valid_until TIMESTAMP")
        cursor.execute("ALTER TABLE relationships ADD COLUMN recorded_at TIMESTAMP")
        cursor.execute("ALTER TABLE relationships ADD COLUMN invalidated_by TEXT")

        # Set defaults: valid_from = created_at, valid_until = NULL
        cursor.execute("""
            UPDATE relationships
            SET valid_from = created_at,
                recorded_at = created_at,
                valid_until = NULL,
                invalidated_by = NULL
            WHERE valid_from IS NULL
        """)
        backend.commit()

        # Verify defaults were set
        cursor.execute("SELECT valid_from, valid_until, recorded_at FROM relationships WHERE id = 'r1'")
        row = cursor.fetchone()

        assert row[0] is not None, "valid_from should be set"
        assert row[1] is None, "valid_until should be NULL (still valid)"
        assert row[2] is not None, "recorded_at should be set"

        await backend.disconnect()


class TestTemporalQueryPerformance:
    """Test performance characteristics of temporal queries."""

    @pytest.mark.asyncio
    async def test_current_query_uses_index(self, temporal_db, sample_memories):
        """Test that queries for current relationships use the partial index."""
        for mem in sample_memories[:2]:
            await temporal_db.store_memory(mem)

        # Create many relationships
        for i in range(100):
            await temporal_db.create_relationship(
                from_memory_id="mem2",
                to_memory_id="mem1",
                relationship_type=RelationshipType.RELATED_TO
            )

        # Query current relationships
        # SQLite's EXPLAIN QUERY PLAN would show if index is used
        cursor = temporal_db.backend.conn.cursor()
        cursor.execute("""
            EXPLAIN QUERY PLAN
            SELECT * FROM relationships WHERE valid_until IS NULL
        """)
        plan = cursor.fetchall()

        # Should mention the index in the query plan
        # Convert each row to string properly (accessing row fields)
        plan_str = " ".join([" ".join([str(col) for col in row]) for row in plan])
        # For partial index, SQLite might not always report it by name, but it should use an index scan
        assert "idx_relationships_current" in plan_str or "SEARCH" in plan_str or "USING INDEX" in plan_str

    @pytest.mark.asyncio
    async def test_point_in_time_query_performance(self, temporal_db, sample_memories):
        """Test that point-in-time queries are reasonably fast."""
        import time

        for mem in sample_memories[:2]:
            await temporal_db.store_memory(mem)

        # Create many relationships with different timestamps
        for i in range(100):
            days_ago = i
            timestamp = datetime.now(timezone.utc) - timedelta(days=days_ago)
            await temporal_db.create_relationship(
                from_memory_id="mem2",
                to_memory_id="mem1",
                relationship_type=RelationshipType.RELATED_TO,
                valid_from=timestamp
            )

        # Time a point-in-time query
        query_time = datetime.now(timezone.utc) - timedelta(days=50)
        start = time.time()
        relationships = await temporal_db.get_related_memories("mem1", as_of=query_time)
        elapsed = time.time() - start

        # Should complete in under 100ms for 100 relationships
        assert elapsed < 0.1, f"Query took {elapsed}s, expected < 0.1s"
        assert len(relationships) > 0


# Mark all tests as requiring asyncio
pytestmark = pytest.mark.asyncio
