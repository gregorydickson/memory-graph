# Memory-Graph Code Quality Workplan

**Purpose**: Address code review findings to improve code quality, test coverage, and maintainability.

**Priority**: TDD-first approach - write tests before fixes where applicable.

---

## Phase 1: Critical Deprecation Warnings (2,379 instances)

**Goal**: Replace all `datetime.utcnow()` calls with `datetime.now(datetime.UTC)` to eliminate deprecation warnings.

### 1.1 Identify All Deprecation Instances

- [ ] Run grep to identify all files containing `datetime.utcnow()`
- [ ] Create a comprehensive list of affected files with line numbers
- [ ] Document the pattern: `datetime.utcnow()` → `datetime.now(datetime.UTC)`

### 1.2 Write Tests for Datetime Usage

- [ ] Identify existing tests that may break with datetime changes
- [ ] Add timezone-aware datetime tests in `tests/test_memory.py`
- [ ] Add timezone-aware datetime tests in `tests/test_relationships.py`
- [ ] Ensure all timestamp comparisons handle timezone-aware datetimes

### 1.3 Update Core Memory Module

- [ ] Replace `datetime.utcnow()` in `src/memorygraph/models/memory.py`
- [ ] Replace `datetime.utcnow()` in `src/memorygraph/models/relationship.py`
- [ ] Run unit tests to verify changes
- [ ] Verify no deprecation warnings in core models

### 1.4 Update SQLite Backend

- [ ] Replace `datetime.utcnow()` in `src/memorygraph/backends/sqlite_backend.py`
- [ ] Replace `datetime.utcnow()` in `src/memorygraph/backends/sqlite_fallback.py`
- [ ] Run SQLite backend tests
- [ ] Verify timestamp storage and retrieval works correctly

### 1.5 Update Neo4j Backend

- [ ] Replace `datetime.utcnow()` in `src/memorygraph/backends/neo4j_backend.py`
- [ ] Run Neo4j backend tests (if available)
- [ ] Verify timestamp handling in Cypher queries

### 1.6 Update Memgraph Backend

- [ ] Replace `datetime.utcnow()` in `src/memorygraph/backends/memgraph_backend.py`
- [ ] Run Memgraph backend tests
- [ ] Verify timestamp handling in Cypher queries

### 1.7 Update FalkorDB Backend

- [ ] Replace `datetime.utcnow()` in `src/memorygraph/backends/falkordb_backend.py`
- [ ] Run FalkorDB backend tests
- [ ] Verify timestamp handling in queries

### 1.8 Update Test Files

- [ ] Replace `datetime.utcnow()` in all test files under `tests/`
- [ ] Update test fixtures to use timezone-aware datetimes
- [ ] Run full test suite to verify no regressions

### 1.9 Update Server and Tools

- [ ] Replace `datetime.utcnow()` in `src/memorygraph/server.py`
- [ ] Replace `datetime.utcnow()` in `src/memorygraph/tools/`
- [ ] Run integration tests
- [ ] Verify MCP tool responses handle timezones correctly

### 1.10 Verification

- [ ] Run full test suite with `pytest -v`
- [ ] Verify zero deprecation warnings
- [ ] Run type checker: `mypy src/memorygraph`
- [ ] Document datetime handling pattern in ADR

**Acceptance Criteria**:
- Zero `datetime.utcnow()` calls remaining in codebase
- All tests pass
- No deprecation warnings in test output
- Datetime handling is consistent across all backends

---

## Phase 2: Increase server.py Test Coverage (49% → >70%)

**Goal**: Improve test coverage for `src/memorygraph/server.py` from 49% to >70%.

### 2.1 Analyze Current Coverage

- [ ] Run `pytest --cov=src/memorygraph/server --cov-report=html`
- [ ] Review HTML coverage report to identify untested code paths
- [ ] Document which tool handlers have <50% coverage
- [ ] Create list of edge cases not currently tested

### 2.2 Write Tests for Tool Handlers - Part 1

- [ ] Add tests for `store_memory` tool handler
  - [ ] Test successful memory storage
  - [ ] Test with missing required fields
  - [ ] Test with invalid memory type
  - [ ] Test with empty content
  - [ ] Test importance validation (0.0-1.0)

- [ ] Add tests for `get_memory` tool handler
  - [ ] Test successful memory retrieval
  - [ ] Test with non-existent memory_id
  - [ ] Test with include_relationships=True
  - [ ] Test with include_relationships=False

- [ ] Add tests for `search_memories` tool handler
  - [ ] Test basic query search
  - [ ] Test with memory_types filter
  - [ ] Test with tags filter
  - [ ] Test with min_importance filter
  - [ ] Test with project_path filter
  - [ ] Test with empty results
  - [ ] Test search_tolerance modes (strict, normal, fuzzy)
  - [ ] Test match_mode (any, all)

### 2.3 Write Tests for Tool Handlers - Part 2

- [ ] Add tests for `update_memory` tool handler
  - [ ] Test successful update
  - [ ] Test partial updates
  - [ ] Test with non-existent memory_id
  - [ ] Test validation on update

- [ ] Add tests for `delete_memory` tool handler
  - [ ] Test successful deletion
  - [ ] Test with non-existent memory_id
  - [ ] Test cascade deletion of relationships

- [ ] Add tests for `create_relationship` tool handler
  - [ ] Test successful relationship creation
  - [ ] Test with invalid memory IDs
  - [ ] Test with invalid relationship type
  - [ ] Test strength/confidence validation
  - [ ] Test context extraction

### 2.4 Write Tests for Tool Handlers - Part 3

- [ ] Add tests for `get_related_memories` tool handler
  - [ ] Test with max_depth=1
  - [ ] Test with max_depth>1
  - [ ] Test with relationship_types filter
  - [ ] Test with no related memories

- [ ] Add tests for `get_recent_activity` tool handler
  - [ ] Test default 7-day window
  - [ ] Test custom day ranges
  - [ ] Test with project filter
  - [ ] Test with no recent activity

- [ ] Add tests for `recall_memories` tool handler
  - [ ] Test natural language queries
  - [ ] Test with memory_types filter
  - [ ] Test with project_path filter
  - [ ] Test with limit parameter

### 2.5 Write Tests for Error Handling

- [ ] Test invalid tool arguments
- [ ] Test backend initialization failures
- [ ] Test database connection errors
- [ ] Test transaction rollback scenarios
- [ ] Test concurrent access scenarios

### 2.6 Write Tests for MCP Protocol

- [ ] Test tool discovery (list_tools)
- [ ] Test tool invocation format
- [ ] Test error response format
- [ ] Test result serialization

### 2.7 Run Coverage Analysis

- [ ] Run full test suite with coverage
- [ ] Verify coverage is >70%
- [ ] Document remaining untested code paths
- [ ] Add coverage badge to README if not present

**Acceptance Criteria**:
- Test coverage for `server.py` is >70%
- All tool handlers have test coverage
- Error handling paths are tested
- Coverage report shows improvement from 49%

---

## Phase 3: Refactor server.py Complexity (1,473 lines)

**Goal**: Extract tool handlers from `server.py` into separate modules for better maintainability.

### 3.1 Design Module Structure

- [ ] Review current `server.py` structure
- [ ] Design new module structure:
  - [ ] `src/memorygraph/tools/memory_tools.py` - CRUD operations
  - [ ] `src/memorygraph/tools/relationship_tools.py` - relationship operations
  - [ ] `src/memorygraph/tools/search_tools.py` - search and recall
  - [ ] `src/memorygraph/tools/activity_tools.py` - activity and stats
- [ ] Document the refactoring plan in an ADR
- [ ] Ensure backwards compatibility

### 3.2 Create Test Infrastructure for New Modules

- [ ] Create `tests/tools/test_memory_tools.py`
- [ ] Create `tests/tools/test_relationship_tools.py`
- [ ] Create `tests/tools/test_search_tools.py`
- [ ] Create `tests/tools/test_activity_tools.py`
- [ ] Set up fixtures for tool testing

### 3.3 Extract Memory CRUD Tools

- [ ] Create `src/memorygraph/tools/memory_tools.py`
- [ ] Extract `store_memory` handler
- [ ] Extract `get_memory` handler
- [ ] Extract `update_memory` handler
- [ ] Extract `delete_memory` handler
- [ ] Write unit tests for each extracted function
- [ ] Run tests to verify extraction

### 3.4 Extract Relationship Tools

- [ ] Create `src/memorygraph/tools/relationship_tools.py`
- [ ] Extract `create_relationship` handler
- [ ] Extract `get_related_memories` handler
- [ ] Write unit tests for each extracted function
- [ ] Run tests to verify extraction

### 3.5 Extract Search Tools

- [ ] Create `src/memorygraph/tools/search_tools.py`
- [ ] Extract `search_memories` handler
- [ ] Extract `recall_memories` handler
- [ ] Write unit tests for each extracted function
- [ ] Run tests to verify extraction

### 3.6 Extract Activity Tools

- [ ] Create `src/memorygraph/tools/activity_tools.py`
- [ ] Extract `get_recent_activity` handler
- [ ] Write unit tests for extracted function
- [ ] Run tests to verify extraction

### 3.7 Update server.py

- [ ] Import new tool modules in `server.py`
- [ ] Update tool registration to use extracted handlers
- [ ] Remove extracted code from `server.py`
- [ ] Verify `server.py` line count reduced significantly
- [ ] Run full integration tests

### 3.8 Update Documentation

- [ ] Update architecture documentation
- [ ] Document new module structure
- [ ] Update contribution guidelines if needed
- [ ] Add docstrings to all extracted functions

**Acceptance Criteria**:
- `server.py` reduced to <500 lines
- Tool handlers extracted to separate modules
- All tests pass after refactoring
- No breaking changes to MCP API
- Code complexity metrics improved

---

## Phase 4: Implement Health Check (TODO in cli.py:293)

**Goal**: Implement the health check functionality noted as TODO.

### 4.1 Write Health Check Tests

- [ ] Create `tests/test_health_check.py`
- [ ] Write test for successful health check
- [ ] Write test for backend connection failure
- [ ] Write test for database unavailable
- [ ] Write test for health check timeout
- [ ] Write test for health check output format

### 4.2 Implement Health Check

- [ ] Review TODO at `src/memorygraph/cli.py:293`
- [ ] Design health check functionality:
  - [ ] Check backend initialization
  - [ ] Check database connectivity
  - [ ] Check basic query execution
  - [ ] Report backend type and version
- [ ] Implement health check function
- [ ] Add CLI command for health check
- [ ] Run tests to verify implementation

### 4.3 Add Health Check to MCP Server

- [ ] Add health check MCP tool if appropriate
- [ ] Document health check usage
- [ ] Add health check to CI/CD pipeline

**Acceptance Criteria**:
- TODO removed from `cli.py:293`
- Health check function implemented and tested
- Health check reports backend status
- Tests verify all health check scenarios

---

## Phase 5: Inconsistent Error Handling

**Goal**: Standardize error handling with decorators for common patterns.

### 5.1 Analyze Current Error Handling

- [ ] Review error handling patterns across codebase
- [ ] Document inconsistencies:
  - [ ] Different exception types for similar errors
  - [ ] Inconsistent error messages
  - [ ] Missing error context
- [ ] Identify common error handling patterns

### 5.2 Design Error Handling Decorator

- [ ] Create design for error handling decorator
- [ ] Define standard exception hierarchy:
  - [ ] `MemoryGraphError` (base)
  - [ ] `ValidationError`
  - [ ] `NotFoundError`
  - [ ] `BackendError`
  - [ ] `ConfigurationError`
- [ ] Design decorator interface
- [ ] Document error handling strategy in ADR

### 5.3 Implement Error Handling Decorator

- [ ] Create `src/memorygraph/utils/error_handling.py`
- [ ] Implement exception classes
- [ ] Implement `@handle_errors` decorator
- [ ] Write unit tests for decorator
- [ ] Write tests for each exception type

### 5.4 Apply Error Decorator to Backends

- [ ] Apply decorator to SQLite backend methods
- [ ] Apply decorator to Neo4j backend methods
- [ ] Apply decorator to Memgraph backend methods
- [ ] Apply decorator to FalkorDB backend methods
- [ ] Run backend tests to verify

### 5.5 Apply Error Decorator to Tools

- [ ] Apply decorator to tool handlers
- [ ] Update error responses in MCP format
- [ ] Ensure error context is preserved
- [ ] Run integration tests

### 5.6 Update Error Documentation

- [ ] Document exception hierarchy
- [ ] Add error handling examples
- [ ] Update troubleshooting guide
- [ ] Add error codes if appropriate

**Acceptance Criteria**:
- Consistent error handling across codebase
- Standard exception hierarchy
- Error decorator reduces boilerplate
- All errors include helpful context
- Tests verify error handling

---

## Phase 6: Add Missing Type Hints

**Goal**: Add type hints to functions missing them, particularly in `sqlite_fallback.py`.

### 6.1 Audit Type Hint Coverage

- [ ] Run `mypy --strict src/memorygraph`
- [ ] Document files with type hint violations
- [ ] Identify specific functions missing type hints
- [ ] Prioritize by module importance

### 6.2 Add Type Hints to sqlite_fallback.py

- [ ] Add type hints to all functions
- [ ] Add return type annotations
- [ ] Add parameter type annotations
- [ ] Run `mypy` to verify
- [ ] Fix any type errors discovered

### 6.3 Add Type Hints to Other Modules

- [ ] Review and add type hints to `src/memorygraph/models/`
- [ ] Review and add type hints to `src/memorygraph/backends/`
- [ ] Review and add type hints to `src/memorygraph/tools/`
- [ ] Review and add type hints to `src/memorygraph/utils/`

### 6.4 Configure Stricter Type Checking

- [ ] Update `pyproject.toml` with stricter mypy settings
- [ ] Enable `disallow_untyped_defs`
- [ ] Enable `disallow_any_unimported`
- [ ] Run CI with strict type checking
- [ ] Document type checking requirements

**Acceptance Criteria**:
- All functions have type hints
- `mypy --strict` passes
- CI enforces type checking
- Type hints improve IDE support

---

## Phase 7: Improve Memgraph Backend Test Coverage (28% → >70%)

**Goal**: Increase test coverage for Memgraph backend with integration tests.

### 7.1 Set Up Memgraph Test Infrastructure

- [ ] Review current Memgraph test setup
- [ ] Ensure Memgraph Docker container available for tests
- [ ] Create test fixtures for Memgraph backend
- [ ] Set up test database initialization
- [ ] Add Memgraph tests to CI pipeline

### 7.2 Write Memgraph Integration Tests - CRUD

- [ ] Test memory creation in Memgraph
- [ ] Test memory retrieval by ID
- [ ] Test memory updates
- [ ] Test memory deletion
- [ ] Test bulk memory operations

### 7.3 Write Memgraph Integration Tests - Search

- [ ] Test basic text search
- [ ] Test search with filters
- [ ] Test full-text search capabilities
- [ ] Test search performance with large datasets
- [ ] Test search_tolerance modes

### 7.4 Write Memgraph Integration Tests - Relationships

- [ ] Test relationship creation
- [ ] Test relationship traversal
- [ ] Test multi-hop relationships (max_depth)
- [ ] Test relationship deletion
- [ ] Test relationship queries with filters

### 7.5 Write Memgraph Integration Tests - Edge Cases

- [ ] Test concurrent access
- [ ] Test transaction handling
- [ ] Test error recovery
- [ ] Test connection pooling
- [ ] Test large result sets

### 7.6 Performance Testing

- [ ] Add performance benchmarks for Memgraph backend
- [ ] Compare with SQLite backend performance
- [ ] Document performance characteristics
- [ ] Add performance regression tests

**Acceptance Criteria**:
- Memgraph backend test coverage >70%
- Integration tests run in CI
- Edge cases covered
- Performance benchmarks documented

---

## Phase 8: Result Pagination

**Goal**: Add pagination support for large query results.

### 8.1 Design Pagination API

- [ ] Design pagination parameters (offset, limit)
- [ ] Design pagination response format (total_count, has_more)
- [ ] Consider cursor-based pagination for relationships
- [ ] Document pagination design in ADR

### 8.2 Write Pagination Tests

- [ ] Create test dataset with >100 memories
- [ ] Test pagination with various page sizes
- [ ] Test edge cases (first page, last page, beyond last)
- [ ] Test pagination with filters
- [ ] Test pagination stability with concurrent updates

### 8.3 Implement Pagination in Backends

- [ ] Add pagination to SQLite backend
- [ ] Add pagination to Neo4j backend
- [ ] Add pagination to Memgraph backend
- [ ] Add pagination to FalkorDB backend
- [ ] Ensure consistent pagination behavior

### 8.4 Update Tool Handlers

- [ ] Add pagination parameters to `search_memories`
- [ ] Add pagination parameters to `get_related_memories`
- [ ] Add pagination parameters to `get_recent_activity`
- [ ] Update tool descriptions with pagination params
- [ ] Update response format with pagination metadata

### 8.5 Update Documentation

- [ ] Document pagination usage
- [ ] Add pagination examples
- [ ] Document best practices for pagination
- [ ] Update API documentation

**Acceptance Criteria**:
- Pagination works across all backends
- Tests verify pagination correctness
- Tool handlers support pagination
- Documentation includes pagination examples

---

## Phase 9: Cycle Detection in Relationships

**Goal**: Add cycle detection to prevent circular relationship graphs.

### 9.1 Design Cycle Detection

- [ ] Research cycle detection algorithms (DFS, Union-Find)
- [ ] Design cycle detection strategy
- [ ] Consider performance implications
- [ ] Decide: prevent cycles or warn about them?
- [ ] Document design in ADR

### 9.2 Write Cycle Detection Tests

- [ ] Test simple cycle (A→B→A)
- [ ] Test complex cycle (A→B→C→A)
- [ ] Test no cycle cases
- [ ] Test cycle detection performance
- [ ] Test cycle detection with different relationship types

### 9.3 Implement Cycle Detection

- [ ] Create `src/memorygraph/utils/graph_algorithms.py`
- [ ] Implement cycle detection function
- [ ] Add unit tests for cycle detection
- [ ] Optimize for performance

### 9.4 Integrate Cycle Detection

- [ ] Add cycle check to `create_relationship` in backends
- [ ] Add configuration option to enable/disable cycle detection
- [ ] Return helpful error message when cycle detected
- [ ] Add cycle detection to tool handlers

### 9.5 Documentation and Configuration

- [ ] Document cycle detection behavior
- [ ] Add configuration examples
- [ ] Update troubleshooting guide
- [ ] Consider adding cycle visualization tool

**Acceptance Criteria**:
- Cycle detection prevents circular relationships
- Performance impact is minimal
- Configuration allows enabling/disabling
- Error messages are helpful

---

## Phase 10: Standardize Docstring Style

**Goal**: Choose and apply consistent docstring style (Google vs NumPy).

### 10.1 Audit Current Docstrings

- [ ] Run docstring linter on codebase
- [ ] Count Google-style vs NumPy-style docstrings
- [ ] Document which modules use which style
- [ ] Choose standard style (recommend: Google)

### 10.2 Configure Docstring Tooling

- [ ] Add `pydocstyle` to dev dependencies
- [ ] Configure style in `pyproject.toml`
- [ ] Add docstring linting to pre-commit hooks
- [ ] Add docstring linting to CI

### 10.3 Convert Docstrings - Core Modules

- [ ] Convert docstrings in `src/memorygraph/models/`
- [ ] Convert docstrings in `src/memorygraph/backends/`
- [ ] Run docstring linter to verify
- [ ] Run tests to ensure no breakage

### 10.4 Convert Docstrings - Tools and Utils

- [ ] Convert docstrings in `src/memorygraph/tools/`
- [ ] Convert docstrings in `src/memorygraph/utils/`
- [ ] Convert docstrings in `src/memorygraph/server.py`
- [ ] Convert docstrings in `src/memorygraph/cli.py`

### 10.5 Update Documentation

- [ ] Document docstring style in CONTRIBUTING.md
- [ ] Add docstring examples
- [ ] Update documentation generation if needed
- [ ] Generate API documentation from docstrings

**Acceptance Criteria**:
- All docstrings follow chosen style (Google)
- Docstring linter passes
- CI enforces docstring style
- Documentation is clear and consistent

---

## Completion Checklist

### Final Verification

- [ ] All phases completed
- [ ] Full test suite passes: `pytest -v`
- [ ] Test coverage >80%: `pytest --cov=src/memorygraph --cov-report=term-missing`
- [ ] Type checking passes: `mypy src/memorygraph`
- [ ] Linting passes: `ruff check src/memorygraph`
- [ ] No deprecation warnings
- [ ] Integration tests pass
- [ ] Documentation updated

### Code Quality Metrics

- [ ] server.py reduced from 1,473 lines to <500 lines
- [ ] server.py coverage increased from 49% to >70%
- [ ] Memgraph backend coverage increased from 28% to >70%
- [ ] Zero `datetime.utcnow()` calls
- [ ] All functions have type hints
- [ ] All docstrings follow Google style

### Documentation Updates

- [ ] Update CHANGELOG.md with all changes
- [ ] Update README.md if needed
- [ ] Add new ADRs for significant decisions
- [ ] Update API documentation
- [ ] Update troubleshooting guide
- [ ] Update examples if needed

### Release Preparation

- [ ] Bump version number in `pyproject.toml`
- [ ] Update `__version__` in `__init__.py`
- [ ] Tag release in git
- [ ] Update release notes
- [ ] Build and test package: `python -m build`
- [ ] Test installation: `pip install dist/*.whl`

---

## Notes

- This workplan follows TDD principles: tests before implementation
- Each phase is designed to be independently testable
- Phases can be worked on in parallel after Phase 1 (datetime fixes)
- Priority order: 1 (critical) → 2-4 (high) → 5-7 (medium) → 8-10 (low)
- All file paths are absolute and reference the current project structure
- Checkboxes should be updated as tasks complete to track progress
