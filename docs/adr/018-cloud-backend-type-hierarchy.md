# ADR-018: CloudBackend Type Hierarchy Refactoring

## Status
Accepted

## Context
The original `CloudBackend` class inherited from `GraphBackend` but did not implement the `execute_query()` method for Cypher queries. This was a Liskov Substitution Principle (LSP) violation - code expecting a `GraphBackend` could fail when given a `CloudBackend`.

The CloudBackend uses REST API calls to communicate with the MemoryGraph Cloud service, while GraphBackend implementations use Cypher queries directly against graph databases.

## Decision
1. **Rename** `CloudBackend` to `CloudRESTAdapter` to accurately reflect its nature as a REST API adapter
2. **Add** `is_cypher_capable()` method to all backends to allow runtime capability detection
3. **Create** `MemoryOperations` Protocol to define the common interface all backends support
4. **Maintain** backwards compatibility via `CloudBackend = CloudRESTAdapter` alias
5. **Keep** GraphBackend inheritance for now to avoid breaking changes

## Consequences

### Positive
- Clear naming indicates REST vs Cypher backends
- Runtime capability detection via `is_cypher_capable()`
- Type-safe Protocol for common operations
- Backwards compatible with existing code

### Negative
- Deprecation alias adds slight complexity
- Full LSP compliance would require removing inheritance (future work)

## Implementation
- `src/memorygraph/protocols.py` - MemoryOperations Protocol
- `src/memorygraph/backends/cloud_backend.py` - Renamed class
- `src/memorygraph/backends/base.py` - Added is_cypher_capable()
- All backends implement is_cypher_capable() returning True/False
