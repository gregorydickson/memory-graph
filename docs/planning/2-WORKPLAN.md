# 2-WORKPLAN: Test Coverage Improvements

**Goal**: Increase test coverage for server.py and Memgraph backend
**Priority**: HIGH - Improves code quality and confidence
**Estimated Tasks**: 35 tasks
**Target Coverage**: server.py 49% → 70%, Memgraph 28% → 70%

---

## Prerequisites

- [ ] 1-WORKPLAN completed (datetime fixes, health check)
- [ ] All existing tests passing

---

## 1. Server.py Test Coverage (49% → >70%)

**Current**: 49% coverage (721/1473 lines)
**Target**: >70% coverage (~1030 lines)
**Gap**: Need ~300 additional lines tested

### 1.1 Analyze Coverage Gaps

- [ ] Run coverage report: `pytest --cov=src/memorygraph/server --cov-report=html`
- [ ] Open `htmlcov/index.html` and review uncovered lines
- [ ] Document which tool handlers have <50% coverage
- [ ] List untested edge cases and error paths

**Output file**: Document findings for reference

### 1.2 Test Tool Handlers - Memory CRUD

Create/expand `/Users/gregorydickson/claude-code-memory/tests/test_server_tools.py`:

**store_memory handler**:
- [ ] Test successful memory storage
- [ ] Test with missing required fields (title, content)
- [ ] Test with invalid memory type
- [ ] Test with empty content
- [ ] Test importance validation (must be 0.0-1.0)
- [ ] Test with maximum field lengths

**get_memory handler**:
- [ ] Test successful retrieval
- [ ] Test with non-existent memory_id
- [ ] Test include_relationships=True
- [ ] Test include_relationships=False

**update_memory handler**:
- [ ] Test successful full update
- [ ] Test partial updates (only title, only tags, etc.)
- [ ] Test with non-existent memory_id
- [ ] Test validation failures on update

**delete_memory handler**:
- [ ] Test successful deletion
- [ ] Test with non-existent memory_id
- [ ] Test cascade deletion of relationships

### 1.3 Test Tool Handlers - Search & Recall

**search_memories handler**:
- [ ] Test basic text query
- [ ] Test with memory_types filter
- [ ] Test with tags filter
- [ ] Test with min_importance filter
- [ ] Test with project_path filter
- [ ] Test with empty results
- [ ] Test search_tolerance modes (strict, normal, fuzzy)
- [ ] Test match_mode (any, all)
- [ ] Test with limit parameter

**recall_memories handler** (convenience wrapper):
- [ ] Test natural language query
- [ ] Test with memory_types filter
- [ ] Test with project_path filter
- [ ] Test with limit parameter
- [ ] Verify uses search_memories internally
- [ ] Verify default tolerance is "normal"

### 1.4 Test Tool Handlers - Relationships

**create_relationship handler**:
- [ ] Test successful relationship creation
- [ ] Test with invalid from_memory_id
- [ ] Test with invalid to_memory_id
- [ ] Test with invalid relationship_type
- [ ] Test strength validation (0.0-1.0)
- [ ] Test confidence validation (0.0-1.0)
- [ ] Test context extraction

**get_related_memories handler**:
- [ ] Test with max_depth=1
- [ ] Test with max_depth=2
- [ ] Test with max_depth=3
- [ ] Test with relationship_types filter
- [ ] Test with no related memories
- [ ] Test bidirectional relationships

### 1.5 Test Tool Handlers - Activity

**get_recent_activity handler**:
- [ ] Test default 7-day window
- [ ] Test custom day ranges (1, 30, 90 days)
- [ ] Test with project filter
- [ ] Test with no recent activity
- [ ] Verify counts by memory type
- [ ] Verify unresolved problems list

### 1.6 Test Error Handling Paths

- [ ] Test invalid tool name
- [ ] Test malformed tool arguments
- [ ] Test backend initialization failure
- [ ] Test database connection errors during tool execution
- [ ] Test transaction rollback scenarios
- [ ] Test timeout scenarios (if implemented)

### 1.7 Test MCP Protocol Integration

- [ ] Test list_tools returns all tool schemas
- [ ] Test tool schema validation
- [ ] Test error response format matches MCP spec
- [ ] Test result serialization
- [ ] Test JSON encoding of complex types (datetime, relationships)

### 1.8 Verify Coverage Target

- [ ] Run coverage: `pytest --cov=src/memorygraph/server --cov-report=term-missing`
- [ ] Verify coverage >70%
- [ ] Document any remaining gaps <70%
- [ ] Add coverage badge to README if appropriate

---

## 2. Memgraph Backend Test Coverage (28% → >70%)

**Current**: 28% coverage
**Target**: >70% coverage
**Approach**: Add integration tests (unit tests exist)

### 2.1 Set Up Memgraph Test Infrastructure

- [ ] Verify Memgraph Docker setup in CI
- [ ] Create test fixtures in `/Users/gregorydickson/claude-code-memory/tests/backends/test_memgraph_integration.py`
- [ ] Set up test database initialization
- [ ] Add cleanup after tests

### 2.2 Integration Tests - CRUD Operations

- [ ] Test create memory in Memgraph
- [ ] Test retrieve memory by ID
- [ ] Test update memory (full and partial)
- [ ] Test delete memory
- [ ] Test bulk memory operations (create 100 memories)

### 2.3 Integration Tests - Search Operations

- [ ] Test basic text search
- [ ] Test search with memory_types filter
- [ ] Test search with tags filter
- [ ] Test search with importance filter
- [ ] Test search with project_path filter
- [ ] Test full-text search performance
- [ ] Test search_tolerance modes
- [ ] Test large result sets (>1000 results)

### 2.4 Integration Tests - Relationship Operations

- [ ] Test create relationship
- [ ] Test get related memories (depth=1)
- [ ] Test get related memories (depth=2)
- [ ] Test get related memories (depth=3)
- [ ] Test relationship queries with type filters
- [ ] Test delete memory with relationships (cascade)
- [ ] Test bidirectional relationship traversal

### 2.5 Integration Tests - Edge Cases

- [ ] Test concurrent memory creation (10 parallel clients)
- [ ] Test concurrent memory updates (optimistic locking)
- [ ] Test transaction handling
- [ ] Test connection pool exhaustion
- [ ] Test query timeout
- [ ] Test large content (>1MB per memory)

### 2.6 Performance Benchmarks

Create `/Users/gregorydickson/claude-code-memory/tests/benchmarks/test_memgraph_performance.py`:

- [ ] Benchmark insert throughput (memories/second)
- [ ] Benchmark search query latency (p50, p95, p99)
- [ ] Benchmark relationship traversal (depth 1-5)
- [ ] Compare with SQLite backend
- [ ] Document results in performance report

### 2.7 Verify Coverage Target

- [ ] Run Memgraph tests: `pytest tests/backends/test_memgraph_integration.py -v`
- [ ] Run coverage: `pytest --cov=src/memorygraph/backends/memgraph_backend --cov-report=term-missing`
- [ ] Verify coverage >70%
- [ ] Document any gaps

---

## Acceptance Criteria

### Server.py Coverage
- [ ] Coverage increased from 49% to >70%
- [ ] All tool handlers tested
- [ ] Error handling paths covered
- [ ] MCP protocol integration tested
- [ ] At least 50 new test cases added

### Memgraph Backend Coverage
- [ ] Coverage increased from 28% to >70%
- [ ] Integration tests run successfully in CI
- [ ] All CRUD operations tested
- [ ] Search and relationship operations tested
- [ ] Edge cases covered
- [ ] Performance benchmarks documented

### Overall
- [ ] Full test suite passes (910+ tests)
- [ ] No regressions in other modules
- [ ] Coverage report shows improvement
- [ ] Documentation updated with coverage metrics

---

## Notes

- TDD approach: Write tests before fixing bugs found during testing
- Integration tests require running Memgraph instance (Docker)
- Performance benchmarks are informational, not blocking
- Focus on common code paths first, edge cases second
- Estimated time: 2-3 days
