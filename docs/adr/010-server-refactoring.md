# ADR 010: Server.py Refactoring - Tool Handler Extraction

## Status

Accepted and Implemented

## Context

The `server.py` file had grown to 1,502 lines, containing all MCP tool handlers, server initialization, tool registration, and dispatch logic in a single monolithic file. This size made it difficult to:

- Navigate and locate specific tool handler code
- Understand the codebase structure
- Maintain and modify individual handlers
- Add new tools without increasing file complexity
- Review code changes in pull requests

## Decision

We decided to extract tool handlers from `server.py` into a modular `tools/` package structure, organized by functional area:

```
src/memorygraph/tools/
├── __init__.py              # Module exports and public API
├── memory_tools.py          # CRUD operations (store, get, update, delete)
├── relationship_tools.py    # Relationship management (create, get related)
├── search_tools.py          # Search and recall operations
└── activity_tools.py        # Activity summaries and statistics
```

### Handler Signature Pattern

All extracted handlers follow a consistent signature:

```python
async def handle_<tool_name>(
    memory_db: MemoryDatabase,
    arguments: Dict[str, Any]
) -> CallToolResult:
    """
    Handle <tool_name> tool call.

    Args:
        memory_db: Database instance for memory operations
        arguments: Tool arguments from MCP call

    Returns:
        MCP CallToolResult with success or error
    """
```

### Module Organization

- **memory_tools.py**: Basic CRUD operations on memories
- **relationship_tools.py**: Creating and traversing relationships
- **search_tools.py**: Search, recall, and query operations
- **activity_tools.py**: Statistics, recent activity, and context searches

### Server.py Responsibilities (Retained)

- MCP server initialization and configuration
- Tool registration and schema definitions
- Tool dispatch logic (routing calls to handlers)
- Backend initialization and lifecycle management
- Integration with advanced/intelligence/proactive tools

## Consequences

### Positive

1. **Improved Maintainability**: 44% reduction in server.py size (1,502 → 840 lines)
2. **Better Organization**: 987 lines of handler code now in focused modules
3. **Easier Navigation**: Find specific handlers by functional area
4. **Clearer Separation of Concerns**: MCP protocol vs. business logic
5. **Foundation for Growth**: Easy to add new tool modules
6. **No Breaking Changes**: MCP API remains identical
7. **Test Coverage Maintained**: All 1,006 tests pass

### Negative

1. **Additional Indirection**: One extra import layer for handlers
2. **Test Updates Required**: Tests updated to use extracted functions
3. **Slight Increase in Files**: 5 new files vs. 1 large file

### Neutral

1. **Consistent Handler Pattern**: All handlers now follow same signature
2. **Database Passed Explicitly**: Handlers receive database as parameter
3. **Module Exports**: Public API defined in `__init__.py`

## Implementation Details

### Before

```python
class ClaudeMemoryServer:
    async def _handle_store_memory(self, arguments):
        # 50+ lines of implementation

    async def _handle_get_memory(self, arguments):
        # 40+ lines of implementation

    # ... 8 more handlers
```

### After

```python
# In tools/memory_tools.py
async def handle_store_memory(memory_db, arguments):
    # 50+ lines of implementation

# In server.py
from .tools import handle_store_memory

class ClaudeMemoryServer:
    # Handler dispatch
    if name == "store_memory":
        return await handle_store_memory(self.memory_db, arguments)
```

## Metrics

- **Before**: server.py = 1,502 lines
- **After**: server.py = 840 lines (44% reduction)
- **Extracted**: 987 lines across 5 modules
- **Test Results**: 1,006 passed, 20 skipped
- **Files Added**: 5 new modules in tools/
- **Breaking Changes**: None

## References

- 4-WORKPLAN.md: Original refactoring plan
- Commit: ebcfa9b (refactor: extract tool handlers from server.py)
- Related ADRs: None
- Issue: #N/A (internal refactoring)

## Date

2025-12-02
