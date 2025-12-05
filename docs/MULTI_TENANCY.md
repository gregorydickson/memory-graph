# Multi-Tenancy Guide

MemoryGraph v0.9.6+ includes Phase 1 of multi-tenancy support, enabling team memory sharing and organizational memory management. This guide covers configuration, migration, and usage patterns.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [Migration](#migration)
- [Usage Patterns](#usage-patterns)
- [Phase Roadmap](#phase-roadmap)
- [Troubleshooting](#troubleshooting)

## Overview

### What is Multi-Tenancy?

Multi-tenancy allows multiple teams or organizations to share a single MemoryGraph deployment while maintaining data isolation and access control. Phase 1 provides the foundational schema and configuration.

### Key Features (Phase 1)

- **Optional Multi-Tenant Mode**: Disabled by default, zero impact on existing deployments
- **Tenant Isolation**: Memories can be scoped to specific tenants/organizations
- **Team Collaboration**: Memories can be shared within teams
- **Visibility Levels**: Control who can access memories (private, project, team, public)
- **Backward Compatible**: 100% compatible with existing single-tenant deployments
- **Performance Optimized**: Conditional indexes only created when multi-tenant mode is enabled

### Deployment Modes

**Single-Tenant Mode (Default)**:
- No tenant_id required
- Works exactly as before
- Zero performance overhead
- Recommended for individual developers and simple use cases

**Multi-Tenant Mode**:
- Enables tenant_id and visibility fields
- Creates optimized indexes for tenant queries
- Supports team collaboration
- Recommended for organizations and teams

## Architecture

### Data Model

Multi-tenancy extends the `MemoryContext` model with optional fields:

```python
class MemoryContext(BaseModel):
    # Existing fields (unchanged)
    project_path: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None

    # New multi-tenancy fields (Phase 1)
    tenant_id: Optional[str] = None        # Organization/tenant identifier
    team_id: Optional[str] = None          # Team within tenant
    visibility: str = "project"            # private | project | team | public
    created_by: Optional[str] = None       # User who created the memory
```

### Tenant Hierarchy

```
Tenant (Organization)
├── Team A
│   ├── User 1
│   └── User 2
└── Team B
    ├── User 3
    └── User 4
```

### Visibility Levels

| Level | Accessible By | Use Case |
|-------|---------------|----------|
| `private` | Only the creator | Personal notes, drafts |
| `project` | Users in the same project | Project-specific learnings (default) |
| `team` | All team members | Team best practices, shared solutions |
| `public` | Everyone in the tenant | Organization-wide patterns |

## Configuration

### Enable Multi-Tenant Mode

Set environment variable before starting the server:

```bash
export MEMORY_MULTI_TENANT_MODE=true
export MEMORY_DEFAULT_TENANT=acme-corp  # Optional, defaults to "default"
```

Or configure in `~/.claude.json`:

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "env": {
        "MEMORY_MULTI_TENANT_MODE": "true",
        "MEMORY_DEFAULT_TENANT": "acme-corp"
      }
    }
  }
}
```

### Verify Configuration

Check current configuration:

```bash
memorygraph --show-config
```

Expected output:
```
multi_tenancy:
  enabled: true
  default_tenant: acme-corp
  require_auth: false
```

## Migration

### Migrating from Single-Tenant to Multi-Tenant

When you enable multi-tenant mode on an existing database, you need to backfill `tenant_id` for existing memories.

#### Step 1: Dry-Run (Recommended)

Always test the migration first:

```bash
memorygraph migrate-to-multitenant \
  --tenant-id="acme-corp" \
  --visibility=team \
  --dry-run
```

Output:
```
🔄 Migrating to multi-tenant mode on SQLite...
   Tenant ID: acme-corp
   Visibility: team

✅ Dry-run successful - migration would proceed safely
   Would update: 1247 memories
   Tenant ID would be: acme-corp
   Visibility would be: team
```

#### Step 2: Run Migration

If dry-run looks good, run the actual migration:

```bash
memorygraph migrate-to-multitenant \
  --tenant-id="acme-corp" \
  --visibility=team
```

Output:
```
✅ Migration completed successfully!
   Updated: 1247 memories
   Tenant ID: acme-corp
   Visibility: team

Next steps:
   1. Set MEMORY_MULTI_TENANT_MODE=true in your environment
   2. Restart the server to enable multi-tenant indexes
```

#### Step 3: Enable Multi-Tenant Mode

Update your environment or configuration file:

```bash
export MEMORY_MULTI_TENANT_MODE=true
```

#### Step 4: Restart Server

```bash
memorygraph
```

The server will now create multi-tenant indexes on startup.

### Rollback

If you need to revert to single-tenant mode:

```bash
# Dry-run first
memorygraph migrate-to-multitenant --rollback --dry-run

# Execute rollback
memorygraph migrate-to-multitenant --rollback

# Disable multi-tenant mode
export MEMORY_MULTI_TENANT_MODE=false

# Restart server
memorygraph
```

## Usage Patterns

### Creating Memories with Tenant Context

**Team Memory (Default for Multi-Tenant)**:
```python
from memorygraph import store_memory

memory = {
    "type": "solution",
    "title": "API Rate Limiting Solution",
    "content": "Implemented token bucket algorithm...",
    "context": {
        "tenant_id": "acme-corp",
        "team_id": "backend-team",
        "visibility": "team",
        "created_by": "alice"
    }
}
```

**Private Memory**:
```python
memory = {
    "type": "task",
    "title": "Personal TODO",
    "content": "Items to complete",
    "context": {
        "tenant_id": "acme-corp",
        "visibility": "private",
        "created_by": "bob",
        "user_id": "bob"
    }
}
```

**Public Memory (Organization-Wide)**:
```python
memory = {
    "type": "code_pattern",
    "title": "Standard Error Handling",
    "content": "Company-wide error handling pattern...",
    "context": {
        "tenant_id": "acme-corp",
        "visibility": "public",
        "created_by": "admin"
    }
}
```

### Searching with Tenant Filtering

Phase 1 stores tenant context but doesn't enforce filtering yet (that's Phase 2). However, the data is ready for future query filtering.

## Phase Roadmap

### Phase 1: Schema Enhancement (v0.9.6) ✅

- ✅ Add optional multi-tenancy fields to MemoryContext
- ✅ Conditional multi-tenant indexes
- ✅ Configuration system
- ✅ Migration script
- ✅ 100% backward compatibility
- ✅ CLI commands for migration

### Phase 2: Query Layer (Future v0.10.0)

- [ ] Implement tenant filtering in all search operations
- [ ] Add visibility enforcement to all tools
- [ ] Create tenant-aware search methods
- [ ] Add team-based memory discovery

### Phase 3: Authentication Integration (Future v1.0.0)

- [ ] JWT token validation
- [ ] OAuth2 provider integration
- [ ] MCP protocol extension for auth context
- [ ] User identity management

### Phase 4: Advanced RBAC (Future v1.1.0)

- [ ] Role-based permissions
- [ ] Fine-grained access control
- [ ] Audit logging
- [ ] Admin management tools

## Troubleshooting

### Issue: Multi-tenant indexes not created

**Symptom**: Query plans show table scans instead of index usage.

**Solution**: Ensure `MEMORY_MULTI_TENANT_MODE=true` was set *before* running `memorygraph`. Restart the server after setting the environment variable.

```bash
# Set environment
export MEMORY_MULTI_TENANT_MODE=true

# Restart server
memorygraph
```

### Issue: Migration fails with "Backend not connected"

**Symptom**: Migration command fails immediately.

**Solution**: The migration needs to connect to the backend. Ensure your backend configuration is correct:

```bash
# For SQLite (default)
export MEMORY_SQLITE_PATH=~/.memorygraph/memory.db

# For Neo4j
export MEMORY_BACKEND=neo4j
export MEMORY_NEO4J_URI=bolt://localhost:7687
export MEMORY_NEO4J_PASSWORD=your-password
```

### Issue: Existing memories don't have tenant_id

**Symptom**: Old memories show `tenant_id: null`.

**Solution**: Run the migration script to backfill tenant_id:

```bash
memorygraph migrate-to-multitenant --tenant-id="your-tenant"
```

### Issue: Performance degradation after enabling multi-tenant mode

**Symptom**: Queries are slower after migration.

**Solution**: Ensure indexes were created:

```sql
-- SQLite
SELECT name FROM sqlite_master
WHERE type='index' AND name LIKE 'idx_memory_%';

-- Expected indexes:
-- idx_memory_tenant
-- idx_memory_team
-- idx_memory_visibility
-- idx_memory_created_by
-- idx_memory_tenant_visibility
```

If indexes are missing, reinitialize the schema:

```python
# In Python
from memorygraph.backends.factory import BackendFactory

backend = await BackendFactory.create_backend()
await backend.initialize_schema()
```

### Issue: Want to use multi-tenant fields without enabling mode

**Symptom**: Want to prepare for future multi-tenancy without enabling now.

**Solution**: You can set tenant_id in memory context even in single-tenant mode. The fields are always available, just not indexed or enforced until multi-tenant mode is enabled.

## Performance Considerations

### Single-Tenant Mode

- **Zero overhead**: No multi-tenant indexes created
- **No performance impact**: Queries work exactly as before
- **Same memory usage**: No additional storage overhead

### Multi-Tenant Mode

- **Index overhead**: 5 additional indexes created (tenant, team, visibility, created_by, composite)
- **Query performance**: < 10% overhead for indexed tenant queries
- **Write performance**: Minimal impact from additional index maintenance
- **Storage overhead**: Approximately 5-10% additional storage for indexes

### Benchmark Results

Performance comparison (1000 memories, SQLite backend):

| Operation | Single-Tenant | Multi-Tenant | Overhead |
|-----------|---------------|--------------|----------|
| Create memory | 2.3ms | 2.5ms | +8.7% |
| Search by content | 15ms | 16ms | +6.7% |
| Search by tenant | N/A | 3ms | - |
| Get by ID | 0.5ms | 0.5ms | 0% |

## Best Practices

1. **Start Single-Tenant**: Begin with single-tenant mode and migrate when needed
2. **Plan Tenant Structure**: Design your tenant/team hierarchy before migration
3. **Use Dry-Run**: Always test migration with `--dry-run` first
4. **Set Visibility Carefully**: Choose appropriate defaults for your organization
5. **Document Tenant IDs**: Keep a record of tenant/team identifiers
6. **Monitor Performance**: Track query performance after enabling multi-tenant mode
7. **Regular Backups**: Backup before and after migration

## Examples

### Example 1: Small Team

Single tenant for the whole team:

```bash
# Migrate existing database
memorygraph migrate-to-multitenant --tenant-id="myteam" --visibility=team

# Enable multi-tenant mode
export MEMORY_MULTI_TENANT_MODE=true

# All team members share memories at "team" visibility
```

### Example 2: Multiple Teams in Organization

One tenant with multiple teams:

```bash
# Migrate with organization tenant
memorygraph migrate-to-multitenant --tenant-id="acme-corp" --visibility=team

# Backend team creates memories
{
  "context": {
    "tenant_id": "acme-corp",
    "team_id": "backend",
    "visibility": "team"
  }
}

# Frontend team creates memories
{
  "context": {
    "tenant_id": "acme-corp",
    "team_id": "frontend",
    "visibility": "team"
  }
}

# Organization-wide patterns
{
  "context": {
    "tenant_id": "acme-corp",
    "visibility": "public"
  }
}
```

### Example 3: Multi-Organization Deployment

Multiple tenants on one server:

```bash
# Each organization is a separate tenant
# Tenant A
{
  "context": {
    "tenant_id": "company-a",
    "visibility": "team"
  }
}

# Tenant B
{
  "context": {
    "tenant_id": "company-b",
    "visibility": "team"
  }
}
```

## Security Notes

### Phase 1 Limitations

Phase 1 provides data structure and isolation but **does not enforce access control**:

- Tenant_id is stored but not validated
- Visibility is recorded but not enforced in queries
- No authentication or authorization

### Recommended for Phase 1

- Internal teams (trusted users)
- Development/staging environments
- Single-organization deployments

### Wait for Phase 2/3 if you need

- Strong access control
- Multi-organization isolation
- Production multi-tenant SaaS
- Authenticated API access

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/gregorydickson/claude-code-memory/issues)
- **Documentation**: [Configuration Guide](CONFIGURATION.md)
- **Troubleshooting**: [Troubleshooting Guide](TROUBLESHOOTING.md)

## Changelog

### v0.9.6 - Phase 1 Implementation

- Added optional multi-tenancy fields to MemoryContext
- Implemented conditional multi-tenant indexes
- Created migration script and CLI command
- Added configuration options
- Maintained 100% backward compatibility
