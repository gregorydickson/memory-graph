"""
Graph algorithm utilities for MemoryGraph.

This module provides graph algorithms for cycle detection, path finding,
and other graph operations on memory relationships.
"""

import logging
from typing import Set, Optional
from ..models import RelationshipType

logger = logging.getLogger(__name__)


async def has_cycle(
    memory_db,
    from_memory_id: str,
    to_memory_id: str,
    relationship_type: RelationshipType,
    max_depth: int = 100
) -> bool:
    """
    Check if adding a relationship would create a cycle in the graph.

    Uses depth-first search (DFS) to traverse from to_memory_id and check
    if from_memory_id is reachable. If it is, then adding the edge
    from_memory_id → to_memory_id would create a cycle.

    Args:
        memory_db: Database instance to query relationships
        from_memory_id: Source memory ID for the proposed relationship
        to_memory_id: Target memory ID for the proposed relationship
        relationship_type: Type of relationship to check for cycles
        max_depth: Maximum traversal depth (prevents infinite loops)

    Returns:
        True if adding the relationship would create a cycle, False otherwise

    Examples:
        # Check if B → A would create a cycle when A → B exists
        >>> await has_cycle(db, "B", "A", RelationshipType.FOLLOWS)
        True

        # Check if C → D creates cycle in linear chain A → B → C
        >>> await has_cycle(db, "C", "D", RelationshipType.FOLLOWS)
        False
    """
    # Self-loops always create cycles
    if from_memory_id == to_memory_id:
        logger.debug(f"Cycle detected: self-loop {from_memory_id} → {from_memory_id}")
        return True

    # Use DFS to check if from_memory_id is reachable from to_memory_id
    visited: Set[str] = set()

    async def dfs(current_id: str, depth: int = 0) -> bool:
        """
        Depth-first search to find if target is reachable from current node.

        Args:
            current_id: Current memory ID in traversal
            depth: Current depth in the traversal

        Returns:
            True if from_memory_id is reachable from current_id
        """
        # Depth limit reached
        if depth > max_depth:
            logger.warning(f"Cycle detection depth limit ({max_depth}) reached")
            return False

        # Already visited this node
        if current_id in visited:
            return False

        # Found the target - cycle would be created
        if current_id == from_memory_id:
            logger.debug(
                f"Cycle detected: {from_memory_id} is reachable from {to_memory_id} "
                f"via {relationship_type.value} relationships"
            )
            return True

        # Mark as visited
        visited.add(current_id)

        try:
            # Get all outgoing relationships of the specified type from current node
            relationships = await memory_db.get_related_memories(
                current_id,
                relationship_types=[relationship_type],
                max_depth=1  # Only immediate neighbors
            )

            # Traverse each neighbor
            for related in relationships:
                # Determine if related memory is a target (outgoing edge from current)
                # get_related_memories returns both incoming and outgoing relationships
                # We only want to follow outgoing edges for cycle detection

                # Get the actual relationship to determine direction
                rels = await _get_outgoing_relationships(
                    memory_db,
                    current_id,
                    relationship_type
                )

                for target_id in rels:
                    if await dfs(target_id, depth + 1):
                        return True

            return False

        except Exception as e:
            logger.error(f"Error during cycle detection DFS: {e}")
            return False

    # Start DFS from to_memory_id
    result = await dfs(to_memory_id)

    if result:
        logger.info(
            f"Cycle would be created: {from_memory_id} → {to_memory_id} "
            f"(type: {relationship_type.value})"
        )
    else:
        logger.debug(
            f"No cycle: {from_memory_id} → {to_memory_id} "
            f"(type: {relationship_type.value})"
        )

    return result


async def _get_outgoing_relationships(
    memory_db,
    from_memory_id: str,
    relationship_type: RelationshipType
) -> list[str]:
    """
    Get target memory IDs for all outgoing relationships of a specific type.

    Args:
        memory_db: Database instance
        from_memory_id: Source memory ID
        relationship_type: Type of relationships to find

    Returns:
        List of target memory IDs
    """
    try:
        # Query depends on database backend
        # For SQLite backend, query the relationships table directly
        if hasattr(memory_db, 'backend'):
            query = """
                SELECT to_id FROM relationships
                WHERE from_id = ? AND rel_type = ?
            """
            result = memory_db.backend.execute_sync(
                query,
                (from_memory_id, relationship_type.value)
            )
            return [row['to_id'] for row in result]
        else:
            # For Neo4j/other backends, use Cypher query
            query = f"""
                MATCH (m:Memory {{id: $from_id}})-[r:{relationship_type.value}]->(target:Memory)
                RETURN target.id as to_id
            """
            result = await memory_db.connection.execute_read_query(
                query,
                {"from_id": from_memory_id}
            )
            return [row['to_id'] for row in result]
    except Exception as e:
        logger.error(f"Error getting outgoing relationships: {e}")
        return []


async def find_all_cycles(
    memory_db,
    relationship_type: Optional[RelationshipType] = None
) -> list[list[str]]:
    """
    Find all cycles in the memory graph.

    Args:
        memory_db: Database instance
        relationship_type: Optional relationship type to filter by

    Returns:
        List of cycles, where each cycle is a list of memory IDs

    Note:
        This is an expensive operation on large graphs.
        Use sparingly or implement as a background task.
    """
    # TODO: Implement for cycle visualization/reporting
    # This would be useful for a CLI command to detect existing cycles
    raise NotImplementedError("find_all_cycles not yet implemented")
