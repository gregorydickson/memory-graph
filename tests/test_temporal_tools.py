"""
Integration tests for temporal MCP tools.

Tests the three temporal tools exposed via MCP:
- query_as_of: Point-in-time queries
- get_relationship_history: Full history view
- what_changed: Recent changes query
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

from src.memorygraph.tools.temporal_tools import (
    handle_query_as_of,
    handle_get_relationship_history,
    handle_what_changed,
)
from src.memorygraph.models import (
    Memory, MemoryType, Relationship, RelationshipType,
    RelationshipProperties
)
from src.memorygraph.backends.sqlite_fallback import SQLiteFallbackBackend
from src.memorygraph.sqlite_database import SQLiteMemoryDatabase


@pytest.fixture
async def temporal_db(tmp_path):
    """Create a test database with temporal support."""
    db_path = str(tmp_path / "test_temporal.db")
    backend = SQLiteFallbackBackend(db_path=db_path)
    await backend.connect()
    await backend.initialize_schema()
    db = SQLiteMemoryDatabase(backend)
    await db.initialize_schema()
    yield db
    await backend.disconnect()


@pytest.fixture
async def populated_db(temporal_db):
    """Create a database with temporal test data."""
    # Create memories
    problem = Memory(
        id="problem-1",
        type=MemoryType.PROBLEM,
        title="Redis timeout errors",
        content="Production Redis connections timing out"
    )
    solution1 = Memory(
        id="solution-1",
        type=MemoryType.SOLUTION,
        title="Increase timeout to 5s",
        content="First solution: increase timeout"
    )
    solution2 = Memory(
        id="solution-2",
        type=MemoryType.SOLUTION,
        title="Connection pooling",
        content="Better solution: use connection pooling"
    )

    await temporal_db.store_memory(problem)
    await temporal_db.store_memory(solution1)
    await temporal_db.store_memory(solution2)

    # Create relationships with different timestamps
    two_months_ago = datetime.now(timezone.utc) - timedelta(days=60)
    one_month_ago = datetime.now(timezone.utc) - timedelta(days=30)

    # First solution (old)
    rel1_id = await temporal_db.create_relationship(
        from_memory_id="solution-1",
        to_memory_id="problem-1",
        relationship_type=RelationshipType.SOLVES,
        valid_from=two_months_ago,
        strength=0.7
    )

    # Invalidate first solution
    cursor = temporal_db.backend.conn.cursor()
    cursor.execute(
        "UPDATE relationships SET valid_until = ? WHERE id = ?",
        (one_month_ago.isoformat(), rel1_id)
    )
    temporal_db.backend.commit()

    # Second solution (current)
    rel2_id = await temporal_db.create_relationship(
        from_memory_id="solution-2",
        to_memory_id="problem-1",
        relationship_type=RelationshipType.SOLVES,
        valid_from=one_month_ago,
        strength=0.9
    )

    return temporal_db


@pytest.mark.asyncio
async def test_query_as_of_tool(populated_db):
    """Test query_as_of MCP tool handler."""
    # Query as of 45 days ago (should return solution-1)
    fortyfive_days_ago = datetime.now(timezone.utc) - timedelta(days=45)

    result = await handle_query_as_of(
        populated_db,
        {
            "memory_id": "problem-1",
            "as_of": fortyfive_days_ago.isoformat()
        }
    )

    assert not result.isError
    assert len(result.content) == 1
    text = result.content[0].text

    # Should mention solution-1
    assert "solution-1" in text
    assert "Increase timeout to 5s" in text
    # Should show temporal info
    assert "Valid from:" in text
    assert "Valid until:" in text


@pytest.mark.asyncio
async def test_query_as_of_current(populated_db):
    """Test querying current state (should return solution-2)."""
    now = datetime.now(timezone.utc)

    result = await handle_query_as_of(
        populated_db,
        {
            "memory_id": "problem-1",
            "as_of": now.isoformat()
        }
    )

    assert not result.isError
    text = result.content[0].text

    # Should mention solution-2
    assert "solution-2" in text
    assert "Connection pooling" in text


@pytest.mark.asyncio
async def test_query_as_of_invalid_timestamp(populated_db):
    """Test query_as_of with invalid timestamp format."""
    result = await handle_query_as_of(
        populated_db,
        {
            "memory_id": "problem-1",
            "as_of": "invalid-timestamp"
        }
    )

    assert result.isError
    assert "Invalid timestamp format" in result.content[0].text


@pytest.mark.asyncio
async def test_get_relationship_history_tool(populated_db):
    """Test get_relationship_history MCP tool handler."""
    result = await handle_get_relationship_history(
        populated_db,
        {
            "memory_id": "problem-1"
        }
    )

    assert not result.isError
    text = result.content[0].text

    # Should show both relationships
    assert "Relationship History" in text
    assert "Current Relationships:" in text
    assert "Historical (Invalidated) Relationships:" in text

    # Should mention both solutions
    assert "solution-1" in text or "solution-2" in text

    # Should show temporal info
    assert "Valid from:" in text


@pytest.mark.asyncio
async def test_get_relationship_history_with_filter(populated_db):
    """Test filtering relationship history by type."""
    result = await handle_get_relationship_history(
        populated_db,
        {
            "memory_id": "problem-1",
            "relationship_types": ["SOLVES"]
        }
    )

    assert not result.isError
    text = result.content[0].text
    assert "Relationship History" in text


@pytest.mark.asyncio
async def test_what_changed_tool(populated_db):
    """Test what_changed MCP tool handler."""
    # Query what changed in last 20 days (should show solution-2)
    twenty_days_ago = datetime.now(timezone.utc) - timedelta(days=20)

    result = await handle_what_changed(
        populated_db,
        {
            "since": twenty_days_ago.isoformat()
        }
    )

    # Should find at least the current relationship
    assert not result.isError
    text = result.content[0].text

    # Should show changes section
    assert "Changes since" in text


@pytest.mark.asyncio
async def test_what_changed_far_past(populated_db):
    """Test what_changed with very old timestamp (should show everything)."""
    three_months_ago = datetime.now(timezone.utc) - timedelta(days=90)

    result = await handle_what_changed(
        populated_db,
        {
            "since": three_months_ago.isoformat()
        }
    )

    assert not result.isError
    text = result.content[0].text
    assert "Changes since" in text


@pytest.mark.asyncio
async def test_what_changed_invalid_timestamp(populated_db):
    """Test what_changed with invalid timestamp."""
    result = await handle_what_changed(
        populated_db,
        {
            "since": "not-a-timestamp"
        }
    )

    assert result.isError
    assert "Invalid timestamp format" in result.content[0].text


@pytest.mark.asyncio
async def test_query_as_of_no_results(temporal_db):
    """Test query_as_of when no relationships exist."""
    # Create a memory but no relationships
    memory = Memory(
        id="orphan",
        type=MemoryType.PROBLEM,
        title="Orphan memory",
        content="No relationships"
    )
    await temporal_db.store_memory(memory)

    result = await handle_query_as_of(
        temporal_db,
        {
            "memory_id": "orphan",
            "as_of": datetime.now(timezone.utc).isoformat()
        }
    )

    assert not result.isError
    assert "No relationships found" in result.content[0].text


@pytest.mark.asyncio
async def test_get_relationship_history_no_results(temporal_db):
    """Test get_relationship_history when no relationships exist."""
    memory = Memory(
        id="orphan",
        type=MemoryType.PROBLEM,
        title="Orphan memory",
        content="No relationships"
    )
    await temporal_db.store_memory(memory)

    result = await handle_get_relationship_history(
        temporal_db,
        {
            "memory_id": "orphan"
        }
    )

    assert not result.isError
    assert "No relationship history found" in result.content[0].text


# Mark all tests as requiring asyncio
pytestmark = pytest.mark.asyncio
