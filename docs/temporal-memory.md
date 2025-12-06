# Temporal Memory: Tracking Knowledge Evolution

**Version**: 0.10.0
**Status**: Production Ready
**Last Updated**: 2025-12-06

---

## Overview

MemoryGraph's **bi-temporal tracking** enables you to track how knowledge evolves over time by maintaining two independent time dimensions:

1. **Validity Time**: When was this fact true in the real world?
2. **Transaction Time**: When did we learn this fact?

This allows powerful queries like:
- "What solutions were we using when bug X first appeared?"
- "How did our understanding of this problem evolve?"
- "Show me all facts we learned last week"

### Inspiration

This feature is inspired by [Graphiti](https://github.com/getzep/graphiti) (Zep AI), a temporal knowledge graph system that uses bi-temporal tracking for agent memory. We've adapted their proven approach for coding-specific workflows.

---

## Key Concepts

### The Four Temporal Fields

Every relationship in MemoryGraph now has four temporal fields:

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `valid_from` | Timestamp | When the fact became true | Current time |
| `valid_until` | Timestamp | When the fact stopped being true (NULL = still valid) | NULL |
| `recorded_at` | Timestamp | When we learned this fact | Current time |
| `invalidated_by` | String | ID of relationship that superseded this one | NULL |

### Validity Time vs Transaction Time

**Validity Time** (`valid_from`, `valid_until`):
- Represents when the fact was true in the real world
- External reality, not system-dependent
- Example: "SolutionX worked from Jan 2024 to June 2024"

**Transaction Time** (`recorded_at`):
- Represents when we ingested the fact into the system
- System knowledge, not external reality
- Example: "We learned about SolutionX on Feb 2024"

**Why Both?**
- You might learn about a solution in February that actually worked since January
- You might discover in June that a solution stopped working in May
- Separating these dimensions enables accurate time-travel queries

---

## Use Cases

### 1. Solution Evolution Tracking

**Scenario**: A solution that worked initially stops working later.

```python
# January 2024: Record that SolutionX solves ErrorA
await db.create_relationship(
    from_memory_id="solution_x_id",
    to_memory_id="error_a_id",
    relationship_type=RelationshipType.SOLVES,
    valid_from=datetime(2024, 1, 1, tzinfo=timezone.utc)
)

# June 2024: SolutionX stops working, SolutionY is the new solution
# Invalidate the old relationship
await db.invalidate_relationship(
    old_relationship_id,
    invalidated_by=new_relationship_id
)

# Create new relationship
await db.create_relationship(
    from_memory_id="solution_y_id",
    to_memory_id="error_a_id",
    relationship_type=RelationshipType.SOLVES,
    valid_from=datetime(2024, 6, 1, tzinfo=timezone.utc)
)
```

**Query**: "What solution were we using in March 2024?"
```python
march_2024 = datetime(2024, 3, 1, tzinfo=timezone.utc)
relationships = await db.get_related_memories(
    "error_a_id",
    as_of=march_2024
)
# Returns: SolutionX (it was valid at that time)
```

**Query**: "What solution are we using now?"
```python
relationships = await db.get_related_memories("error_a_id")
# Returns: SolutionY (current solution, valid_until is NULL)
```

---

### 2. Point-in-Time Debugging

**Scenario**: A bug appeared on a specific date. You want to know what dependencies were in place at that time.

```python
# Bug first appeared on May 15, 2024
bug_date = datetime(2024, 5, 15, tzinfo=timezone.utc)

# Query dependencies as they existed on that date
dependencies = await db.get_related_memories(
    "service_a_id",
    as_of=bug_date
)

# Returns all DEPENDS_ON relationships that were valid on May 15
```

**Use Case**: Understanding historical context for debugging:
- What libraries were we using when the bug first appeared?
- What configuration was in place?
- What solutions had we tried before?

---

### 3. Knowledge Audit

**Scenario**: You want to catch up on what changed while you were away.

```python
# Show all facts learned in the last 7 days
one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)

changes = await db.what_changed(since=one_week_ago)

print(f"New relationships: {len(changes['new_relationships'])}")
print(f"Invalidated relationships: {len(changes['invalidated_relationships'])}")

# Examine what was learned
for rel in changes['new_relationships']:
    print(f"- Learned: {rel.type} relationship")
    print(f"  Valid from: {rel.properties.valid_from}")
    print(f"  Recorded at: {rel.properties.recorded_at}")
```

**Use Cases**:
- Daily standup: "What did we learn yesterday?"
- Sprint review: "What knowledge evolved this sprint?"
- Onboarding: "What has changed since you joined?"

---

### 4. Understanding When Solutions Stopped Working

**Scenario**: You want to know when a particular approach stopped being effective.

```python
# Get full history of solutions for a problem
history = await db.get_relationship_history("error_a_id")

for rel in history:
    print(f"Solution: {rel.to_memory_id}")
    print(f"  Valid from: {rel.properties.valid_from}")
    print(f"  Valid until: {rel.properties.valid_until or 'current'}")

    if rel.properties.invalidated_by:
        print(f"  Superseded by: {rel.properties.invalidated_by}")
```

**Output**:
```
Solution: solution_x_id
  Valid from: 2024-01-01
  Valid until: 2024-06-01
  Superseded by: rel_456

Solution: solution_y_id
  Valid from: 2024-06-01
  Valid until: current
```

**Insight**: SolutionX worked for 5 months, then SolutionY replaced it.

---

### 5. Dependency Evolution

**Scenario**: Track how your project's dependencies changed over time.

```python
# Project started using LibraryX in January
await db.create_relationship(
    from_memory_id="project_id",
    to_memory_id="library_x_id",
    relationship_type=RelationshipType.DEPENDS_ON,
    valid_from=datetime(2024, 1, 1, tzinfo=timezone.utc)
)

# Migrated to LibraryY in June
# Invalidate old dependency
await db.invalidate_relationship(old_dep_id)

# Add new dependency
await db.create_relationship(
    from_memory_id="project_id",
    to_memory_id="library_y_id",
    relationship_type=RelationshipType.DEPENDS_ON,
    valid_from=datetime(2024, 6, 1, tzinfo=timezone.utc)
)

# Query: What were our dependencies in March?
march_deps = await db.get_related_memories(
    "project_id",
    as_of=datetime(2024, 3, 1, tzinfo=timezone.utc)
)
# Returns: LibraryX

# Query: What are our current dependencies?
current_deps = await db.get_related_memories("project_id")
# Returns: LibraryY
```

---

## MCP Tools for Temporal Queries

MemoryGraph provides three MCP tools optimized for temporal queries:

### 1. `query_as_of` - Point-in-Time Query

**Purpose**: Query relationships as they existed at a specific time.

**Parameters**:
- `memory_id`: Memory to query relationships for
- `as_of`: ISO 8601 timestamp (e.g., "2024-03-01T00:00:00Z")

**Example**:
```json
{
  "memory_id": "error_a_id",
  "as_of": "2024-03-01T00:00:00Z"
}
```

**Returns**:
```json
{
  "relationships": [
    {
      "id": "rel_123",
      "type": "SOLVES",
      "from_memory_id": "solution_x_id",
      "to_memory_id": "error_a_id",
      "properties": {
        "valid_from": "2024-01-01T00:00:00Z",
        "valid_until": "2024-06-01T00:00:00Z"
      }
    }
  ],
  "as_of": "2024-03-01T00:00:00Z"
}
```

**When to Use**:
- Debugging: "What was our setup when the bug first appeared?"
- Compliance: "What access controls were in place on date X?"
- Investigation: "What was our understanding before the incident?"

---

### 2. `get_relationship_history` - Full Evolution Timeline

**Purpose**: Get the complete history of relationships for a memory.

**Parameters**:
- `memory_id`: Memory to get history for

**Example**:
```json
{
  "memory_id": "error_a_id"
}
```

**Returns**:
```json
{
  "timeline": [
    {
      "relationship": {
        "id": "rel_123",
        "type": "SOLVES",
        "from_memory_id": "solution_x_id"
      },
      "valid_from": "2024-01-01T00:00:00Z",
      "valid_until": "2024-06-01T00:00:00Z",
      "invalidated_by": "rel_456"
    },
    {
      "relationship": {
        "id": "rel_456",
        "type": "SOLVES",
        "from_memory_id": "solution_y_id"
      },
      "valid_from": "2024-06-01T00:00:00Z",
      "valid_until": "current",
      "invalidated_by": null
    }
  ]
}
```

**When to Use**:
- Understanding: "How did our approach to this problem evolve?"
- Review: "What solutions have we tried?"
- Patterns: "Are we repeating past mistakes?"

---

### 3. `what_changed` - Recent Changes Query

**Purpose**: Show all relationship changes since a given time.

**Parameters**:
- `since`: ISO 8601 timestamp (e.g., "2024-12-01T00:00:00Z")

**Example**:
```json
{
  "since": "2024-12-01T00:00:00Z"
}
```

**Returns**:
```json
{
  "new_relationships": [
    {
      "id": "rel_789",
      "type": "SOLVES",
      "recorded_at": "2024-12-05T10:30:00Z"
    }
  ],
  "invalidated_relationships": [
    {
      "id": "rel_456",
      "valid_until": "2024-12-05T10:30:00Z",
      "invalidated_by": "rel_789"
    }
  ],
  "period": "2024-12-01T00:00:00Z"
}
```

**When to Use**:
- Catching up: "What happened while I was away?"
- Standup: "What did we learn yesterday?"
- Audit: "Show me all changes this week"

---

## Query Patterns

### Default Behavior: Current Only

**By default, all queries return only current relationships** (where `valid_until IS NULL`).

```python
# Returns only current relationships
relationships = await db.get_related_memories("memory_id")
```

This ensures **zero breaking changes** for existing code.

---

### Point-in-Time Query

Query relationships as they existed at a specific time:

```python
from datetime import datetime, timezone

# Query as of March 1, 2024
past_time = datetime(2024, 3, 1, tzinfo=timezone.utc)
relationships = await db.get_related_memories(
    "memory_id",
    as_of=past_time
)

# Returns relationships where:
# - valid_from <= past_time
# - valid_until > past_time OR valid_until IS NULL
```

**SQL Equivalent**:
```sql
SELECT * FROM relationships
WHERE from_id = :memory_id
  AND valid_from <= :past_time
  AND (valid_until IS NULL OR valid_until > :past_time);
```

---

### Full History Query

Get all relationships for a memory, including invalidated ones:

```python
history = await db.get_relationship_history("memory_id")

# Returns list of relationships sorted by valid_from (chronological)
for rel in history:
    if rel.properties.valid_until:
        print(f"Ended: {rel.properties.valid_until}")
    else:
        print("Current")
```

**SQL Equivalent**:
```sql
SELECT * FROM relationships
WHERE from_id = :memory_id
ORDER BY valid_from ASC;
```

---

### Recent Changes Query

Find what changed since a specific time:

```python
from datetime import datetime, timedelta, timezone

one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)
changes = await db.what_changed(since=one_week_ago)

# Returns dict with:
# - new_relationships: List of relationships created since that time
# - invalidated_relationships: List of relationships invalidated since then
```

**SQL Equivalent**:
```sql
-- New relationships
SELECT * FROM relationships
WHERE recorded_at > :since_time
ORDER BY recorded_at DESC;

-- Invalidated relationships
SELECT * FROM relationships
WHERE valid_until > :since_time AND valid_until IS NOT NULL
ORDER BY valid_until DESC;
```

---

## Best Practices

### 1. Setting `valid_from` Explicitly

**When to set `valid_from`**:
- You know when the fact became true (different from when you learned it)
- Backfilling historical data
- Recording when a solution started working

**Example**:
```python
# Solution started working on January 1, but we're recording it in February
await db.create_relationship(
    from_memory_id="solution_id",
    to_memory_id="problem_id",
    relationship_type=RelationshipType.SOLVES,
    valid_from=datetime(2024, 1, 1, tzinfo=timezone.utc)
)
# recorded_at will be February (when we ran this code)
# valid_from will be January (when the solution actually started working)
```

### 2. Invalidating Relationships

**When to invalidate**:
- A solution stops working
- A dependency is removed
- A fact is superseded by a better fact

**Best Practice**: Always provide `invalidated_by` when creating a replacement:
```python
# Create new relationship
new_rel_id = await db.create_relationship(
    from_memory_id="new_solution_id",
    to_memory_id="problem_id",
    relationship_type=RelationshipType.SOLVES
)

# Invalidate old relationship with reference to new one
await db.invalidate_relationship(
    old_rel_id,
    invalidated_by=new_rel_id
)
```

This creates a chain showing how knowledge evolved.

### 3. Using Defaults

**When to use defaults** (let the system set temporal fields):
- Recording current facts
- You don't know historical timing
- The fact is currently valid

**Example**:
```python
# System will set:
# - valid_from = now
# - valid_until = NULL (currently valid)
# - recorded_at = now
await db.create_relationship(
    from_memory_id="solution_id",
    to_memory_id="problem_id",
    relationship_type=RelationshipType.SOLVES
)
```

### 4. Handling Time Zones

**Always use UTC** for temporal fields:
```python
from datetime import datetime, timezone

# GOOD: Explicit UTC
timestamp = datetime.now(timezone.utc)

# GOOD: Parse with timezone
timestamp = datetime.fromisoformat("2024-01-01T00:00:00Z")

# BAD: Naive datetime (no timezone)
timestamp = datetime.now()  # Avoid this
```

### 5. Performance Considerations

**Indexes optimize temporal queries**:
- `idx_relationships_temporal`: For point-in-time queries
- `idx_relationships_current`: For current-only queries (partial index)
- `idx_relationships_recorded`: For "what changed" queries

**Query Performance Targets**:
- Current state: < 10ms (most common)
- Point-in-time: < 50ms
- Full history: < 100ms

**Tips**:
- Default queries (current only) are fastest
- Point-in-time queries use composite index
- History queries scan all relationships for an entity

---

## Migration Guide

### Migrating Existing Databases

If you have an existing MemoryGraph database, you can migrate to bi-temporal schema:

```python
from memorygraph.migration.scripts import migrate_to_bitemporal
from memorygraph.backends.sqlite_fallback import SQLiteFallbackBackend

# Connect to existing database
backend = SQLiteFallbackBackend(db_path="~/.memorygraph/memory.db")
await backend.connect()

# Run migration
result = await migrate_to_bitemporal(backend)

print(f"Migrated {result['relationships_updated']} relationships")
print(f"Created {result['indexes_created']} indexes")
```

**What the migration does**:
1. Adds four temporal columns to `relationships` table
2. Sets defaults for existing relationships:
   - `valid_from` = `created_at` (assume fact was true when recorded)
   - `valid_until` = NULL (assume still valid)
   - `recorded_at` = `created_at`
   - `invalidated_by` = NULL
3. Creates temporal indexes

**Dry Run First**:
```python
# See what would be changed without making changes
result = await migrate_to_bitemporal(backend, dry_run=True)
print(f"Would update {result['relationships_updated']} relationships")
```

### Rollback (WARNING: Loses Data)

**Rolling back loses all temporal data!** Export first:

```python
from memorygraph.migration.scripts import rollback_from_bitemporal

# Rollback removes temporal fields
result = await rollback_from_bitemporal(backend)

print(f"Removed temporal data from {result['relationships_updated']} relationships")
print(f"Dropped {result['indexes_dropped']} indexes")
```

---

## Examples for Coding Agents

### Example 1: Track API Deprecation

```python
# Old API endpoint works initially
await db.create_relationship(
    from_memory_id="service_a",
    to_memory_id="old_api_endpoint",
    relationship_type=RelationshipType.USES,
    valid_from=datetime(2024, 1, 1, tzinfo=timezone.utc)
)

# API deprecated on June 1, 2024
await db.invalidate_relationship(
    old_api_rel_id,
    valid_until=datetime(2024, 6, 1, tzinfo=timezone.utc)
)

# New API endpoint used from June 1
await db.create_relationship(
    from_memory_id="service_a",
    to_memory_id="new_api_endpoint",
    relationship_type=RelationshipType.USES,
    valid_from=datetime(2024, 6, 1, tzinfo=timezone.utc),
    invalidated_by=old_api_rel_id
)

# Query: What API were we using in March 2024?
march_api = await db.get_related_memories(
    "service_a",
    as_of=datetime(2024, 3, 1, tzinfo=timezone.utc)
)
# Returns: old_api_endpoint
```

### Example 2: Bug Fix Timeline

```python
# Bug discovered
bug_id = await db.store_memory(Memory(
    type=MemoryType.ERROR,
    title="Authentication fails on mobile",
    content="..."
))

# Root cause identified
cause_id = await db.store_memory(Memory(
    type=MemoryType.PROBLEM,
    title="OAuth token expiry too short",
    content="..."
))

# Link bug to cause
await db.create_relationship(
    from_memory_id=cause_id,
    to_memory_id=bug_id,
    relationship_type=RelationshipType.CAUSES,
    valid_from=datetime(2024, 5, 1, tzinfo=timezone.utc)  # When bug started
)

# Solution applied
solution_id = await db.store_memory(Memory(
    type=MemoryType.SOLUTION,
    title="Increase token expiry to 30 days",
    content="..."
))

# Link solution to cause
await db.create_relationship(
    from_memory_id=solution_id,
    to_memory_id=cause_id,
    relationship_type=RelationshipType.SOLVES,
    valid_from=datetime(2024, 5, 15, tzinfo=timezone.utc)  # When fixed
)

# Timeline query
history = await db.get_relationship_history(bug_id)
# Shows: Cause identified, then solved 15 days later
```

### Example 3: Dependency Upgrade

```python
# Track library version changes
old_version = await db.store_memory(Memory(
    type=MemoryType.TECHNOLOGY,
    title="React 17.0.2",
    content="..."
))

new_version = await db.store_memory(Memory(
    type=MemoryType.TECHNOLOGY,
    title="React 18.2.0",
    content="..."
))

# Project used React 17 initially
old_dep_id = await db.create_relationship(
    from_memory_id="project_id",
    to_memory_id=old_version.id,
    relationship_type=RelationshipType.DEPENDS_ON,
    valid_from=datetime(2024, 1, 1, tzinfo=timezone.utc)
)

# Upgraded to React 18 on July 1
await db.invalidate_relationship(old_dep_id)

await db.create_relationship(
    from_memory_id="project_id",
    to_memory_id=new_version.id,
    relationship_type=RelationshipType.DEPENDS_ON,
    valid_from=datetime(2024, 7, 1, tzinfo=timezone.utc),
    invalidated_by=old_dep_id
)

# Query: What version were we using in March?
march_deps = await db.get_related_memories(
    "project_id",
    as_of=datetime(2024, 3, 1, tzinfo=timezone.utc)
)
# Returns: React 17.0.2
```

---

## Technical Details

### Schema (SQLite)

```sql
CREATE TABLE relationships (
    id TEXT PRIMARY KEY,
    from_id TEXT NOT NULL,
    to_id TEXT NOT NULL,
    rel_type TEXT NOT NULL,

    -- Temporal fields
    valid_from TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP,
    recorded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    invalidated_by TEXT,

    -- Other fields
    properties TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (from_id) REFERENCES nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (to_id) REFERENCES nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (invalidated_by) REFERENCES relationships(id) ON DELETE SET NULL
);

-- Indexes
CREATE INDEX idx_relationships_temporal ON relationships(valid_from, valid_until);
CREATE INDEX idx_relationships_current ON relationships(valid_until) WHERE valid_until IS NULL;
CREATE INDEX idx_relationships_recorded ON relationships(recorded_at);
```

### Schema (Neo4j/Memgraph)

```cypher
// Relationships have temporal properties
CREATE (a)-[r:SOLVES {
    valid_from: datetime(),
    valid_until: null,
    recorded_at: datetime(),
    invalidated_by: null,
    strength: 0.8,
    confidence: 0.9
}]->(b)

// Indexes
CREATE INDEX rel_valid_from IF NOT EXISTS FOR ()-[r]-() ON (r.valid_from)
CREATE INDEX rel_valid_until IF NOT EXISTS FOR ()-[r]-() ON (r.valid_until)
CREATE INDEX rel_recorded_at IF NOT EXISTS FOR ()-[r]-() ON (r.recorded_at)
```

---

## Frequently Asked Questions

### Q: Do I need to migrate my existing database?

**A**: No, new databases automatically have the temporal schema. Existing databases work fine without migration but won't have temporal features. Migrate when you need time-travel queries.

### Q: Will migration break my existing queries?

**A**: No, the migration is designed for backward compatibility. Default queries still return only current relationships. You opt-in to temporal features by using `as_of` parameter.

### Q: What happens if I don't set `valid_from`?

**A**: It defaults to the current timestamp. This is fine for current facts. Set it explicitly only when backfilling historical data.

### Q: Can I query by `recorded_at` instead of `valid_from`?

**A**: Yes, use `what_changed(since=timestamp)` to query by when facts were learned.

### Q: How much storage overhead does temporal tracking add?

**A**: Approximately 20% (4 timestamp fields + 1 reference field). For 10,000 relationships, this is ~400KB.

### Q: Can I delete temporal data entirely?

**A**: Yes, use `rollback_from_bitemporal()`, but **this loses all temporal information**. Export first if you might need it later.

### Q: What if I invalidate a relationship by mistake?

**A**: Temporal data is preserved. You can re-create the relationship or manually update `valid_until` back to NULL in the database.

---

## Further Reading

- **ADR-016**: [Bi-Temporal Tracking Architecture Decision](./adr/016-bi-temporal-tracking.md)
- **Workplan 13**: [Bi-Temporal Schema Implementation](./planning/13-WORKPLAN.md)
- **Graphiti Paper**: [Zep: A Temporal Knowledge Graph Architecture](https://arxiv.org/html/2501.13956v1)
- **Neo4j Blog**: [Graphiti: Knowledge Graph Memory for an Agentic World](https://neo4j.com/blog/developer/graphiti-knowledge-graph-memory/)

---

**Questions or Issues?** Open an issue on GitHub or consult the [Troubleshooting Guide](./TROUBLESHOOTING.md).
