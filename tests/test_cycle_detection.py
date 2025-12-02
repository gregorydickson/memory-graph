"""
Tests for cycle detection in relationship graphs.

Tests cover:
- Simple cycles (A → B → A)
- Multi-node cycles (A → B → C → A)
- Self-loops (A → A)
- No cycles (linear chains, trees)
- Different relationship types
- Performance with large graphs
"""

import pytest
from datetime import datetime, UTC

from src.memorygraph.sqlite_database import SQLiteMemoryDatabase
from src.memorygraph.backends.sqlite_fallback import SQLiteFallbackBackend
from src.memorygraph.models import (
    Memory, MemoryType, RelationshipType, RelationshipProperties, ValidationError
)
from src.memorygraph.utils.graph_algorithms import has_cycle


class TestCycleDetectionAlgorithm:
    """Test the cycle detection algorithm directly."""

    @pytest.fixture
    async def memory_db(self, tmp_path):
        """Create a test database."""
        db_path = str(tmp_path / "test_cycles.db")
        backend = SQLiteFallbackBackend(db_path=db_path)
        await backend.connect()
        await backend.initialize_schema()
        db = SQLiteMemoryDatabase(backend)
        await db.initialize_schema()
        yield db
        await backend.disconnect()

    @pytest.mark.asyncio
    async def test_no_cycle_empty_graph(self, memory_db):
        """Test that empty graph has no cycles."""
        # Create two unconnected memories
        mem1_id = await memory_db.store_memory(Memory(
            type=MemoryType.GENERAL,
            title="Memory 1",
            content="First memory"
        ))
        mem2_id = await memory_db.store_memory(Memory(
            type=MemoryType.GENERAL,
            title="Memory 2",
            content="Second memory"
        ))

        # No relationship exists, so no cycle
        result = await has_cycle(
            memory_db,
            mem1_id,
            mem2_id,
            RelationshipType.SOLVES
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_simple_cycle_two_nodes(self, memory_db):
        """Test detection of simple cycle: A → B → A."""
        # Create two memories
        mem_a_id = await memory_db.store_memory(Memory(
            type=MemoryType.PROBLEM,
            title="Problem A",
            content="First problem"
        ))
        mem_b_id = await memory_db.store_memory(Memory(
            type=MemoryType.SOLUTION,
            title="Solution B",
            content="First solution"
        ))

        # Create relationship A → B
        await memory_db.create_relationship(
            mem_a_id,
            mem_b_id,
            RelationshipType.SOLVES
        )

        # Check if B → A would create a cycle (it should)
        result = await has_cycle(
            memory_db,
            mem_b_id,
            mem_a_id,
            RelationshipType.SOLVES
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_three_node_cycle(self, memory_db):
        """Test detection of 3-node cycle: A → B → C → A."""
        # Create three memories
        mem_a_id = await memory_db.store_memory(Memory(
            type=MemoryType.GENERAL,
            title="Node A",
            content="First node"
        ))
        mem_b_id = await memory_db.store_memory(Memory(
            type=MemoryType.GENERAL,
            title="Node B",
            content="Second node"
        ))
        mem_c_id = await memory_db.store_memory(Memory(
            type=MemoryType.GENERAL,
            title="Node C",
            content="Third node"
        ))

        # Create relationships A → B → C
        await memory_db.create_relationship(
            mem_a_id,
            mem_b_id,
            RelationshipType.LEADS_TO
        )
        await memory_db.create_relationship(
            mem_b_id,
            mem_c_id,
            RelationshipType.LEADS_TO
        )

        # Check if C → A would create a cycle (it should)
        result = await has_cycle(
            memory_db,
            mem_c_id,
            mem_a_id,
            RelationshipType.LEADS_TO
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_four_node_cycle(self, memory_db):
        """Test detection of 4-node cycle: A → B → C → D → A."""
        # Create four memories
        memories = []
        for i, letter in enumerate(['A', 'B', 'C', 'D']):
            mem_id = await memory_db.store_memory(Memory(
                type=MemoryType.GENERAL,
                title=f"Node {letter}",
                content=f"Node {i+1}"
            ))
            memories.append(mem_id)

        # Create chain A → B → C → D
        for i in range(3):
            await memory_db.create_relationship(
                memories[i],
                memories[i+1],
                RelationshipType.FOLLOWS
            )

        # Check if D → A would create a cycle (it should)
        result = await has_cycle(
            memory_db,
            memories[3],  # D
            memories[0],  # A
            RelationshipType.FOLLOWS
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_self_loop(self, memory_db):
        """Test detection of self-loop: A → A."""
        mem_id = await memory_db.store_memory(Memory(
            type=MemoryType.GENERAL,
            title="Self-referencing",
            content="Points to itself"
        ))

        # Check if A → A would create a cycle (it should)
        result = await has_cycle(
            memory_db,
            mem_id,
            mem_id,
            RelationshipType.RELATED_TO
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_no_cycle_linear_chain(self, memory_db):
        """Test no cycle in linear chain: A → B → C → D."""
        # Create four memories
        memories = []
        for i in range(4):
            mem_id = await memory_db.store_memory(Memory(
                type=MemoryType.GENERAL,
                title=f"Step {i+1}",
                content=f"Content {i+1}"
            ))
            memories.append(mem_id)

        # Create chain A → B → C
        for i in range(3):
            await memory_db.create_relationship(
                memories[i],
                memories[i+1],
                RelationshipType.FOLLOWS
            )

        # Check if C → D would create a cycle (it shouldn't)
        result = await has_cycle(
            memory_db,
            memories[2],  # C
            memories[3],  # D
            RelationshipType.FOLLOWS
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_no_cycle_tree_structure(self, memory_db):
        """Test no cycle in tree structure: A → B, A → C, B → D."""
        # Create root and children
        root_id = await memory_db.store_memory(Memory(
            type=MemoryType.GENERAL,
            title="Root",
            content="Root node"
        ))
        child_b_id = await memory_db.store_memory(Memory(
            type=MemoryType.GENERAL,
            title="Child B",
            content="Left child"
        ))
        child_c_id = await memory_db.store_memory(Memory(
            type=MemoryType.GENERAL,
            title="Child C",
            content="Right child"
        ))
        child_d_id = await memory_db.store_memory(Memory(
            type=MemoryType.GENERAL,
            title="Child D",
            content="Grandchild"
        ))

        # Create tree: root → B, root → C, B → D
        await memory_db.create_relationship(
            root_id,
            child_b_id,
            RelationshipType.LEADS_TO
        )
        await memory_db.create_relationship(
            root_id,
            child_c_id,
            RelationshipType.LEADS_TO
        )
        await memory_db.create_relationship(
            child_b_id,
            child_d_id,
            RelationshipType.LEADS_TO
        )

        # Check if C → D would create a cycle (it shouldn't)
        result = await has_cycle(
            memory_db,
            child_c_id,
            child_d_id,
            RelationshipType.LEADS_TO
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_different_relationship_types_no_cycle(self, memory_db):
        """Test that cycles are only detected within same relationship type."""
        # Create two memories
        mem_a_id = await memory_db.store_memory(Memory(
            type=MemoryType.PROBLEM,
            title="Problem",
            content="A problem"
        ))
        mem_b_id = await memory_db.store_memory(Memory(
            type=MemoryType.SOLUTION,
            title="Solution",
            content="A solution"
        ))

        # Create relationship A -SOLVES-> B
        await memory_db.create_relationship(
            mem_a_id,
            mem_b_id,
            RelationshipType.SOLVES
        )

        # Check if B -RELATED_TO-> A creates a cycle in RELATED_TO type
        # (it shouldn't, because SOLVES and RELATED_TO are different types)
        result = await has_cycle(
            memory_db,
            mem_b_id,
            mem_a_id,
            RelationshipType.RELATED_TO
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_cycle_with_max_depth(self, memory_db):
        """Test cycle detection respects max_depth parameter."""
        # Create a long chain
        memories = []
        for i in range(10):
            mem_id = await memory_db.store_memory(Memory(
                type=MemoryType.GENERAL,
                title=f"Node {i}",
                content=f"Content {i}"
            ))
            memories.append(mem_id)

        # Create chain 0 → 1 → 2 → ... → 9
        for i in range(9):
            await memory_db.create_relationship(
                memories[i],
                memories[i+1],
                RelationshipType.FOLLOWS
            )

        # Check if 9 → 0 would create a cycle with limited depth
        # With max_depth=5, we can't traverse a chain of 10 nodes
        # So we won't detect the cycle (false negative due to depth limit)
        result = await has_cycle(
            memory_db,
            memories[9],
            memories[0],
            RelationshipType.FOLLOWS,
            max_depth=5
        )
        # Cannot detect cycle due to depth limit
        assert result is False

        # But with sufficient depth, we should detect it
        result_full = await has_cycle(
            memory_db,
            memories[9],
            memories[0],
            RelationshipType.FOLLOWS,
            max_depth=15  # Sufficient for 10-node chain
        )
        assert result_full is True

    @pytest.mark.asyncio
    async def test_cycle_detection_performance(self, memory_db):
        """Test cycle detection performance with moderately large graph."""
        import time

        # Create 100 memories in a chain
        memories = []
        for i in range(100):
            mem_id = await memory_db.store_memory(Memory(
                type=MemoryType.GENERAL,
                title=f"Node {i}",
                content=f"Content {i}"
            ))
            memories.append(mem_id)

        # Create chain
        for i in range(99):
            await memory_db.create_relationship(
                memories[i],
                memories[i+1],
                RelationshipType.FOLLOWS
            )

        # Measure cycle detection time
        start = time.time()
        result = await has_cycle(
            memory_db,
            memories[99],
            memories[0],
            RelationshipType.FOLLOWS
        )
        elapsed = time.time() - start

        assert result is True
        assert elapsed < 0.5  # Should complete in less than 500ms


class TestCycleDetectionIntegration:
    """Test cycle detection integrated with database operations."""

    @pytest.fixture
    async def memory_db(self, tmp_path):
        """Create a test database."""
        db_path = str(tmp_path / "test_cycles_integration.db")
        backend = SQLiteFallbackBackend(db_path=db_path)
        await backend.connect()
        await backend.initialize_schema()
        db = SQLiteMemoryDatabase(backend)
        await db.initialize_schema()
        yield db
        await backend.disconnect()

    @pytest.mark.asyncio
    async def test_create_relationship_prevents_cycle(self, memory_db):
        """Test that create_relationship prevents cycles when configured."""
        # Create two memories
        mem_a_id = await memory_db.store_memory(Memory(
            type=MemoryType.GENERAL,
            title="Node A",
            content="First"
        ))
        mem_b_id = await memory_db.store_memory(Memory(
            type=MemoryType.GENERAL,
            title="Node B",
            content="Second"
        ))

        # Create A → B
        await memory_db.create_relationship(
            mem_a_id,
            mem_b_id,
            RelationshipType.FOLLOWS
        )

        # Try to create B → A (should raise ValidationError if cycle detection enabled)
        # Note: This test assumes cycle detection will be integrated
        # For now, it documents the expected behavior
        # TODO: Uncomment when cycle detection is integrated
        # with pytest.raises(ValidationError, match="cycle"):
        #     await memory_db.create_relationship(
        #         mem_b_id,
        #         mem_a_id,
        #         RelationshipType.FOLLOWS
        #     )

    @pytest.mark.asyncio
    async def test_cycle_detection_error_message(self, memory_db):
        """Test that cycle detection provides helpful error messages."""
        # This test documents expected error message format
        # TODO: Implement when cycle detection is integrated

        mem_a_id = await memory_db.store_memory(Memory(
            type=MemoryType.GENERAL,
            title="A",
            content="First"
        ))
        mem_b_id = await memory_db.store_memory(Memory(
            type=MemoryType.GENERAL,
            title="B",
            content="Second"
        ))

        await memory_db.create_relationship(
            mem_a_id,
            mem_b_id,
            RelationshipType.SOLVES
        )

        # Expected error message format:
        # "Cannot create relationship {from_id} → {to_id}: "
        # "Would create a cycle in the {relationship_type} relationship graph"
