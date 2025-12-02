# ADR 011: Pagination Design for Memory Search Results

**Status**: Accepted

**Date**: 2025-12-02

**Context**: MemoryGraph needed a way to handle large result sets efficiently. As memory databases grow to hundreds or thousands of entries, returning all results in a single response becomes impractical for performance, memory usage, and user experience.

---

## Decision

Implement **offset-based pagination** for memory search operations with the following design:

### Pagination Model

```python
class PaginatedResult(BaseModel):
    """Paginated result wrapper for memory search operations."""

    results: List[Memory]           # Memories in this page
    total_count: int                # Total matching results
    limit: int                      # Max results per page
    offset: int                     # Results skipped
    has_more: bool                  # More pages available?
    next_offset: Optional[int]      # Offset for next page
```

### Configuration

- **Default limit**: 50 results per page
- **Maximum limit**: 1000 results per page
- **Minimum limit**: 1 result per page
- **Default offset**: 0 (start from beginning)

### API Changes

Updated `SearchQuery` model to include pagination parameters:
- `limit: int = Field(default=50, ge=1, le=1000)`
- `offset: int = Field(default=0, ge=0)`

Search operations now return `PaginatedResult` instead of raw `List[Memory]`.

---

## Rationale

### Why Offset-Based Pagination?

**Considered alternatives**:

1. **Cursor-based pagination** (rejected)
   - Pros: More efficient for large datasets, prevents missing/duplicate results during concurrent modifications
   - Cons: Complex implementation, harder for users to navigate, requires stable sort order
   - Decision: YAGNI - Memory graphs are typically read-heavy with infrequent writes. The complexity isn't justified for this use case.

2. **Load all results** (rejected)
   - Pros: Simplest implementation
   - Cons: Performance degrades with large result sets, excessive memory usage, poor UX
   - Decision: Not scalable as memory databases grow.

3. **Offset-based pagination** (chosen)
   - Pros: Simple to implement, familiar to users, easy to navigate (jump to any page), works well with SQLite LIMIT/OFFSET
   - Cons: Less efficient for very large offsets, potential for missing results during concurrent writes
   - Decision: Best balance of simplicity and functionality for our use case.

### Design Choices

**Default limit of 50**:
- Balances performance and user experience
- Small enough to display in terminal/UI without scrolling
- Large enough to avoid excessive pagination

**Maximum limit of 1000**:
- Prevents abuse and performance issues
- Still allows "show me everything" for most queries
- Can be adjusted if needed based on real-world usage

**Include total_count**:
- Helps users understand result set size
- Enables "Showing 1-50 of 237 results" UX
- Minimal overhead (same query with COUNT)

**Include has_more and next_offset**:
- Simplifies client logic
- Client doesn't need to calculate if more pages exist
- next_offset makes it easy to fetch next page

---

## Consequences

### Positive

1. **Performance**: Large result sets no longer slow down searches
2. **Scalability**: Works efficiently with thousands of memories
3. **User Experience**: Users can navigate large result sets progressively
4. **Backward Compatible**: Existing code works with default limit
5. **Simple Implementation**: Leverages native SQLite LIMIT/OFFSET

### Negative

1. **Breaking Change**: Return type changed from `List[Memory]` to `PaginatedResult`
   - Mitigation: Version bump to v0.9.0 signals breaking change
   - Mitigation: Updated all documentation and examples

2. **Deep Pagination Performance**: Large offset values (e.g., 10,000) can be slow
   - Acceptable: Memory databases rarely exceed thousands of entries
   - Acceptable: Users typically only navigate first few pages

3. **Concurrent Modification Issues**: Results may shift if memories are added/deleted during pagination
   - Acceptable: Memory operations are infrequent compared to searches
   - Future: Could add cursor-based pagination if this becomes a problem

---

## Implementation Notes

### Backend Support

All backends implement pagination consistently:

**SQLite**:
```sql
SELECT * FROM memories
WHERE <conditions>
ORDER BY created_at DESC
LIMIT ? OFFSET ?
```

**Neo4j/Memgraph**:
```cypher
MATCH (m:Memory)
WHERE <conditions>
RETURN m
ORDER BY m.created_at DESC
SKIP $offset LIMIT $limit
```

**FalkorDB/FalkorDBLite**:
```cypher
GRAPH.QUERY memory_graph
"MATCH (m:Memory)
WHERE <conditions>
RETURN m
ORDER BY m.created_at DESC
SKIP {offset} LIMIT {limit}"
```

### Client Usage Example

```python
# First page
result = search_memories(query="authentication", limit=50)
print(f"Found {result.total_count} total results")
print(f"Showing {len(result.results)} results")

# Navigate to next page
if result.has_more:
    next_page = search_memories(
        query="authentication",
        limit=50,
        offset=result.next_offset
    )
```

---

## Alternatives Considered

### Cursor-Based Pagination

**Approach**: Use memory ID or timestamp as cursor instead of numeric offset.

**Pros**:
- More efficient for large datasets
- Stable even with concurrent modifications
- Prevents duplicate/missing results

**Cons**:
- Complex implementation (need stable sort, encode cursor)
- Harder UX (can't jump to page 5, only next/prev)
- Requires index on cursor field
- Not as familiar to users

**Decision**: Rejected for v0.9.0 due to YAGNI. Can revisit if offset-based proves insufficient.

### Keyset Pagination

**Approach**: Use WHERE created_at > $last_seen instead of OFFSET.

**Pros**:
- Constant-time performance regardless of page
- Works well with time-series data

**Cons**:
- Can't jump to arbitrary pages
- Requires client to track last seen value
- Doesn't work well with multiple sort orders

**Decision**: Rejected. Too restrictive for general-purpose memory search.

---

## Related ADRs

- [ADR 003: Async Database Layer](003-async-database-layer.md) - Pagination works within async architecture
- [ADR 010: Server Refactoring](010-server-refactoring.md) - Pagination added as part of v0.9.0 enhancements

---

## References

- [Pagination Best Practices](https://www.citusdata.com/blog/2016/03/30/five-ways-to-paginate/)
- [Offset vs Cursor Pagination](https://jsonapi.org/profiles/ethanresnick/cursor-pagination/)
- SQLite LIMIT/OFFSET documentation
- Neo4j SKIP/LIMIT documentation

---

**Last Updated**: 2025-12-02
**Version**: 1.0
**Review Date**: After v1.0.0 (evaluate if cursor-based needed)
