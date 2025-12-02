# ADR 012: Cycle Detection in Relationship Graphs

**Status**: Accepted

**Date**: 2025-12-02

**Context**: MemoryGraph allows creating directed relationships between memories (e.g., `A DEPENDS_ON B`, `B SOLVES C`). Without cycle detection, it's possible to create circular dependencies that can lead to infinite loops during graph traversal, ambiguous dependency resolution, and logical inconsistencies in the memory graph.

---

## Decision

Implement **cycle detection** using Depth-First Search (DFS) algorithm before creating new relationships, with a configuration option to allow cycles when explicitly needed.

### Implementation

1. **Default Behavior**: Prevent cycles
   - Check for cycles before creating any new relationship
   - Raise `ValidationError` if cycle detected
   - Provide clear error message showing the cycle path

2. **Configuration Option**: `MEMORY_ALLOW_CYCLES`
   - `false` (default): Enforce acyclic graph
   - `true`: Allow cycles (skip detection)

3. **Detection Algorithm**: Depth-First Search (DFS)
   - Traverse from target memory backwards through incoming relationships
   - Check if source memory is reachable from target
   - If reachable, creating the relationship would form a cycle

---

## Rationale

### Why Prevent Cycles by Default?

**Problem scenarios without cycle detection**:

1. **Infinite loops in traversal**:
   ```
   A DEPENDS_ON B DEPENDS_ON C DEPENDS_ON A
   → Traversing dependencies leads to infinite loop
   ```

2. **Ambiguous dependency resolution**:
   ```
   Task A BLOCKS Task B BLOCKS Task C BLOCKS Task A
   → Which task should be resolved first?
   ```

3. **Logical inconsistencies**:
   ```
   Problem X CAUSES Error Y
   Error Y CAUSES Problem X
   → Circular causality doesn't make logical sense
   ```

4. **Graph analysis failures**:
   - Topological sort fails on cyclic graphs
   - Dependency chains become ambiguous
   - Impact analysis becomes unreliable

**Use cases where cycles might be valid**:

1. **Mutual dependencies** (rare but valid):
   ```
   Module A WORKS_WITH Module B (bidirectional)
   → Both modules depend on each other
   ```

2. **Feedback loops** (design pattern):
   ```
   Action TRIGGERS Feedback IMPROVES Action
   → Valid in control systems
   ```

3. **Iterative processes**:
   ```
   V1 IMPROVES V0, V2 IMPROVES V1, ..., V0 DEPRECATED_BY Vn
   → Version cycle after major refactor
   ```

**Decision**: Prevent by default because:
- Most relationships should be acyclic (dependencies, solutions, causality)
- Cycles often indicate modeling errors
- Users can explicitly enable if needed
- Safer default (fail early vs. silent corruption)

---

## Algorithm Choice

### Why DFS?

**Considered alternatives**:

1. **Union-Find** (rejected)
   - Pros: Efficient for undirected graphs
   - Cons: Doesn't work well for directed graphs
   - Decision: Relationships are directed

2. **Topological Sort** (rejected)
   - Pros: Can detect cycles as side effect
   - Cons: Overkill for single relationship check, O(V+E) every time
   - Decision: Too expensive for simple validation

3. **Depth-First Search** (chosen)
   - Pros: Simple, efficient for sparse graphs, O(V+E) worst case but typically much faster
   - Cons: Stack depth limited (not an issue for memory graphs)
   - Decision: Best fit for directed graph cycle detection

### DFS Implementation

```python
def would_create_cycle(self, from_memory_id: str, to_memory_id: str) -> bool:
    """
    Check if creating a relationship would create a cycle.

    Algorithm: DFS from target backwards to check if source is reachable.
    If source is reachable from target, adding edge creates cycle.

    Time Complexity: O(V + E) worst case, typically O(depth) average
    Space Complexity: O(V) for visited set
    """
    if from_memory_id == to_memory_id:
        return True  # Self-loop

    visited = set()
    stack = [to_memory_id]

    while stack:
        current = stack.pop()
        if current == from_memory_id:
            return True  # Cycle detected

        if current in visited:
            continue

        visited.add(current)

        # Add all nodes that current points to
        outgoing = get_outgoing_relationships(current)
        stack.extend(r.to_memory_id for r in outgoing)

    return False  # No cycle
```

**Why this works**:
- If we can reach `from_memory_id` by following relationships starting from `to_memory_id`
- Then adding a relationship from `from_memory_id` to `to_memory_id` would close a loop
- DFS efficiently explores all reachable nodes

---

## Configuration Design

### Environment Variable: `MEMORY_ALLOW_CYCLES`

**Values**:
- `false` (default): Strict acyclic graph
- `true`: Allow cycles (skip detection)

**Configuration in different contexts**:

```bash
# Environment variable
export MEMORY_ALLOW_CYCLES=true

# Claude Code CLI
claude mcp add --scope user memorygraph \
  --env MEMORY_ALLOW_CYCLES=true \
  -- memorygraph

# JSON config
{
  "env": {
    "MEMORY_ALLOW_CYCLES": "true"
  }
}
```

**Why not per-relationship setting?**:
- Complexity: Would require passing flag through all relationship creation paths
- Consistency: Graph either allows cycles or doesn't, mixing is confusing
- YAGNI: Can add fine-grained control later if needed

---

## Consequences

### Positive

1. **Data Integrity**: Prevents logical inconsistencies in memory graph
2. **Reliability**: Traversal operations guaranteed to terminate
3. **Early Error Detection**: Catches modeling errors at creation time
4. **Clear Semantics**: Relationship semantics are unambiguous
5. **Optional**: Can be disabled for valid use cases

### Negative

1. **Performance Overhead**: DFS check on every relationship creation
   - Mitigation: Only runs when cycles disabled (default)
   - Mitigation: DFS is fast for sparse graphs (typical case)
   - Mitigation: Can disable for batch operations if needed

2. **Rejected Valid Cycles**: Some valid patterns might be rejected
   - Mitigation: Configuration option to allow cycles
   - Mitigation: Alternative relationship types (e.g., RELATED_TO vs DEPENDS_ON)
   - Mitigation: Bidirectional flag for symmetric relationships

3. **Learning Curve**: Users need to understand acyclic constraint
   - Mitigation: Clear error messages with cycle path
   - Mitigation: Documentation with examples
   - Mitigation: Suggestions for alternative modeling

---

## Error Handling

### Error Message Design

When cycle detected:

```python
raise ValidationError(
    f"Creating relationship would create a cycle: "
    f"{from_memory_id} -> {to_memory_id} -> ... -> {from_memory_id}. "
    f"Set MEMORY_ALLOW_CYCLES=true to allow cycles."
)
```

**Includes**:
- What went wrong (cycle detected)
- Why it's a problem (implicit)
- How to fix (set environment variable)
- Where the cycle is (memory IDs involved)

### User Recovery Options

1. **Restructure relationships** (recommended):
   - Review the chain to understand why cycle exists
   - Use different relationship type that doesn't imply ordering
   - Break the cycle by removing unnecessary relationships

2. **Enable cycles** (use with caution):
   - Set `MEMORY_ALLOW_CYCLES=true`
   - Understand the implications for traversal
   - Document why cycles are needed

3. **Use bidirectional relationships**:
   - Set `bidirectional=true` instead of creating two relationships
   - Semantically clearer for symmetric relationships

---

## Future Enhancements

### Cycle Detection Improvements (Future)

1. **Cycle Path Reporting**:
   - Show full cycle path in error message
   - Help users understand the cycle structure

2. **Weak Edges**:
   - Mark certain relationship types as "weak" (don't participate in cycle detection)
   - Example: RELATED_TO could be weak, DEPENDS_ON strong

3. **Configurable by Relationship Type**:
   - Allow cycles for some types (SIMILAR_TO) but not others (DEPENDS_ON)
   - More flexible than global setting

4. **Cycle Breaking Suggestions**:
   - Analyze cycle and suggest which edge to remove
   - Use relationship strength/confidence to recommend

---

## Alternatives Considered

### 1. No Cycle Detection (Rejected)

**Approach**: Allow all relationships, handle cycles during traversal.

**Pros**:
- Simpler implementation
- No performance overhead
- Maximum flexibility

**Cons**:
- Silent data corruption
- Traversal algorithms need cycle protection (visited set)
- Harder to debug issues
- Degrades user trust

**Decision**: Too risky. Prevention is better than cure.

### 2. Topological Sort Validation (Rejected)

**Approach**: Maintain topological sort of entire graph.

**Pros**:
- Can validate entire graph consistency
- Useful for dependency resolution

**Cons**:
- O(V+E) complexity on every change
- Requires graph-wide lock
- Overkill for simple validation
- Not applicable to all relationship types

**Decision**: Too expensive for marginal benefit.

### 3. Union-Find for Undirected (Rejected)

**Approach**: Treat as undirected graph, use union-find.

**Pros**:
- Very efficient for undirected graphs
- Simple to implement

**Cons**:
- Loses directional information
- False positives (A->B and B->C not a cycle, but detected as one)
- Doesn't match our use case (directed relationships)

**Decision**: Doesn't fit directed graph model.

---

## Related ADRs

- [ADR 001: Neo4j over Postgres](001-neo4j-over-postgres.md) - Graph database enables efficient cycle detection
- [ADR 011: Pagination Design](011-pagination-design.md) - Both part of v0.9.0 enhancements

---

## References

- [Graph Cycle Detection Algorithms](https://en.wikipedia.org/wiki/Cycle_(graph_theory))
- [DFS for Cycle Detection](https://www.geeksforgeeks.org/detect-cycle-in-a-graph/)
- [Acyclic Dependencies Principle](https://en.wikipedia.org/wiki/Acyclic_dependencies_principle)

---

**Last Updated**: 2025-12-02
**Version**: 1.0
**Review Date**: After v1.0.0 (evaluate need for weak edges or per-type configuration)
