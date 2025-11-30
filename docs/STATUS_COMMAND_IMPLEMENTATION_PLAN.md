# MemoryGraph Status Command - Implementation Plan

## Overview
Implement `memorygraph status` command to provide diagnostics and statistics about the memory database.

**Goal**: Enable users to quickly understand database health, memory usage, and system status.

**Priority**: Future Enhancement

---

## Quick Reference

### Command Examples
```bash
memorygraph status                    # Basic overview
memorygraph status --detailed         # Comprehensive stats
memorygraph status --format json      # Machine-readable output
memorygraph status --watch 5          # Live monitoring (refresh every 5s)
```

### Expected Output (Basic)
```
MemoryGraph Status Report
━━━━━━━━━━━━━━━━━━━━━━━━━━

System Information
├─ Version: 0.5.6
├─ Backend: sqlite (connected)
├─ Tool Profile: lite (8 tools)
└─ Database: ~/.memorygraph/memory.db

Storage Statistics
├─ Total Memories: 142
├─ Total Relationships: 87
├─ Database Size: 2.4 MB
└─ Last Updated: 2025-11-30 14:32:15

Memory Distribution
├─ SOLUTION: 45 (31.7%)
├─ CODE_PATTERN: 38 (26.8%)
├─ ERROR: 24 (16.9%)
├─ PROBLEM: 18 (12.7%)
└─ Other: 17 (12.0%)

Health Status
└─ All systems operational ✓
```

---

## Phase 1: Core Infrastructure (MVP)

### 1.1 Create Module Structure
- [ ] Create `src/memorygraph/status/` directory
- [ ] Create `src/memorygraph/status/__init__.py`
- [ ] Create `src/memorygraph/status/models.py` for data classes
- [ ] Create `src/memorygraph/status/collector.py` for data collection
- [ ] Create `src/memorygraph/status/formatter.py` for output formatting

### 1.2 Define Data Models
**File**: `src/memorygraph/status/models.py`

- [ ] Define `StatusData` dataclass with fields:
  - `timestamp: datetime`
  - `version: str`
  - `backend_info: BackendInfo`
  - `config_info: ConfigInfo`
  - `memory_stats: MemoryStats`
  - `relationship_stats: RelationshipStats`
  - `storage_info: StorageInfo`
  - `health_checks: List[HealthCheck]`

- [ ] Define `BackendInfo` dataclass with fields:
  - `type: str` (sqlite|neo4j|memgraph)
  - `connected: bool`
  - `version: Optional[str]`
  - `path_or_uri: str`
  - `features: Dict[str, bool]`

- [ ] Define `MemoryStats` dataclass with fields:
  - `total: int`
  - `by_type: Dict[str, int]`
  - `quality_metrics: Optional[Dict[str, float]]`
  - `temporal_breakdown: Optional[Dict[str, int]]`

- [ ] Define `RelationshipStats` dataclass with fields:
  - `total: int`
  - `by_type: Optional[Dict[str, int]]`
  - `avg_per_memory: Optional[float]`
  - `orphaned_count: Optional[int]`

- [ ] Define `StorageInfo` dataclass with fields:
  - `size_bytes: int`
  - `size_human: str`
  - `path: str`

- [ ] Define `HealthCheck` dataclass with fields:
  - `name: str`
  - `status: str` (pass|fail|warning)
  - `message: Optional[str]`
  - `details: Optional[Dict[str, Any]]`

### 1.3 Implement StatusCollector (SQLite Focus)
**File**: `src/memorygraph/status/collector.py`

- [ ] Create `StatusCollector` class
- [ ] Implement `__init__(self, backend: GraphBackend, config: Config)`
- [ ] Implement `async def collect_backend_info(self) -> BackendInfo`
  - Query backend type from config
  - Test connection with `backend.health_check()`
  - Get SQLite version from database
  - Get database path from config
  - Check FTS5 support
- [ ] Implement `async def collect_memory_stats(self, detailed: bool = False) -> MemoryStats`
  - Query total memory count: `SELECT COUNT(*) FROM memories`
  - Query memories by type: `SELECT type, COUNT(*) FROM memories GROUP BY type`
  - If detailed: query quality metrics (avg importance, confidence, effectiveness)
  - If detailed: query temporal breakdown (created today/week/month)
- [ ] Implement `async def collect_relationship_stats(self, detailed: bool = False) -> RelationshipStats`
  - Query total relationship count: `SELECT COUNT(*) FROM relationships`
  - Calculate avg relationships per memory
  - If detailed: query by type
  - If detailed: find orphaned memories (memories with no relationships)
- [ ] Implement `async def collect_storage_info(self) -> StorageInfo`
  - Get database file path from backend
  - Get file size using `os.path.getsize()`
  - Convert to human-readable format (KB/MB/GB)
- [ ] Implement `async def collect(self, detailed: bool = False) -> StatusData`
  - Call all collection methods
  - Combine into StatusData object
  - Set timestamp to current time
  - Get version from `memorygraph.__version__`

### 1.4 Implement StatusFormatter (Text Output)
**File**: `src/memorygraph/status/formatter.py`

- [ ] Create `StatusFormatter` class
- [ ] Implement `def format_text(self, status: StatusData, detailed: bool = False) -> str`
  - Format header with box drawing characters
  - Format System Information section
  - Format Storage Statistics section
  - Format Memory Distribution section with percentages
  - Format Health Status section
  - If detailed: add Backend-Specific Metrics section
  - If detailed: add Memory Quality Metrics section
  - If detailed: add Relationship Analysis section
  - If detailed: add Temporal Statistics section
- [ ] Implement helper `def _format_size(self, size_bytes: int) -> str`
  - Convert bytes to KB/MB/GB with 1 decimal place
- [ ] Implement helper `def _format_percentage(self, count: int, total: int) -> str`
  - Calculate percentage with 1 decimal place
  - Return formatted string like "45 (31.7%)"

### 1.5 Add Status Subcommand to CLI
**File**: `src/memorygraph/cli.py`

- [ ] Import status modules at top of file:
  ```python
  from memorygraph.status.collector import StatusCollector
  from memorygraph.status.formatter import StatusFormatter
  ```
- [ ] Create `async def run_status_command(args)` function:
  - Initialize backend based on config
  - Create StatusCollector instance
  - Collect status data with `detailed=args.detailed`
  - Create StatusFormatter instance
  - Format and print output
  - Handle exceptions gracefully
- [ ] Update `main()` function to support subcommands:
  - Change argument parser to use subparsers
  - Add `status` subcommand parser
  - Add `--detailed` / `-d` flag (action='store_true')
  - Add `--format` option (choices=['text', 'json'], default='text')
  - Route to `run_status_command()` if command is 'status'
  - Keep existing behavior if no subcommand (start server)
- [ ] Update help text to show status subcommand

### 1.6 Testing
**File**: `tests/status/test_collector.py`

- [ ] Create test file and directory structure
- [ ] Test `test_collector_basic_sqlite()`:
  - Create in-memory SQLite database with test data
  - Instantiate StatusCollector
  - Call collect()
  - Assert StatusData fields are populated correctly
- [ ] Test `test_collector_empty_database()`:
  - Create empty database
  - Verify all counts are 0
  - Verify no errors occur
- [ ] Test `test_collector_memory_stats()`:
  - Insert 10 memories of different types
  - Verify total count is 10
  - Verify by_type counts are correct
- [ ] Test `test_collector_relationship_stats()`:
  - Insert memories and relationships
  - Verify total relationship count
  - Verify avg_per_memory calculation

**File**: `tests/status/test_formatter.py`

- [ ] Test `test_formatter_text_basic()`:
  - Create mock StatusData
  - Call format_text()
  - Verify output contains expected sections
  - Verify numbers are formatted correctly
- [ ] Test `test_formatter_percentages()`:
  - Verify percentage calculations
  - Verify formatting matches expected pattern
- [ ] Test `test_formatter_file_size()`:
  - Test bytes → KB/MB/GB conversion
  - Verify decimal places

**File**: `tests/status/test_status_command.py`

- [ ] Test `test_status_command_execution()`:
  - Run status command end-to-end
  - Verify output is generated
  - Verify no errors

### 1.7 Documentation
- [ ] Update `README.md` with status command example
- [ ] Add status command section to usage documentation
- [ ] Document available flags and options

---

## Phase 2: Multi-Backend Support

### 2.1 Backend Abstraction
**File**: `src/memorygraph/status/collector.py`

- [ ] Refactor `collect_backend_info()` to detect backend type
- [ ] Create `_collect_sqlite_info()` private method
- [ ] Create `_collect_neo4j_info()` private method
- [ ] Create `_collect_memgraph_info()` private method
- [ ] Route to appropriate method based on backend type

### 2.2 Neo4j Support
- [ ] Implement Neo4j version detection: `CALL dbms.components()`
- [ ] Implement Neo4j metrics collection:
  - Node count: `MATCH (n:Memory) RETURN count(n)`
  - Relationship count: `MATCH ()-[r]->() RETURN count(r)`
  - Index list: `SHOW INDEXES`
  - Constraint list: `SHOW CONSTRAINTS`
- [ ] Handle Neo4j-specific errors and connection issues
- [ ] Add Neo4j backend info to formatted output

### 2.3 Memgraph Support
- [ ] Implement Memgraph version detection
- [ ] Implement Memgraph metrics collection:
  - Node and relationship counts
  - Storage mode detection
  - Query cache statistics (if available)
- [ ] Handle Memgraph-specific errors
- [ ] Add Memgraph backend info to formatted output

### 2.4 Safe Read-Only Connections
**File**: `src/memorygraph/status/collector.py`

- [ ] Implement `_create_readonly_backend()` method:
  - For SQLite: use `mode=ro` or `immutable=1` URI parameter
  - For Neo4j: create separate driver with READ access mode
  - For Memgraph: create separate driver with READ access mode
- [ ] Handle database lock gracefully (SQLite)
- [ ] Ensure connections are properly closed

### 2.5 Testing Multi-Backend
- [ ] Test Neo4j status collection with test database
- [ ] Test Memgraph status collection with test database
- [ ] Test backend detection logic
- [ ] Test graceful handling of connection failures

---

## Phase 3: Enhanced Features

### 3.1 JSON Output Format
**File**: `src/memorygraph/status/formatter.py`

- [ ] Implement `def format_json(self, status: StatusData) -> str`
  - Convert StatusData to dictionary
  - Handle datetime serialization
  - Use `json.dumps()` with `indent=2`
  - Ensure valid JSON structure
- [ ] Update CLI to support `--format json` flag
- [ ] Route to JSON formatter when format is 'json'

### 3.2 Detailed Mode Enhancements
**File**: `src/memorygraph/status/collector.py`

- [ ] Implement quality metrics calculation:
  - `SELECT AVG(importance), AVG(confidence), AVG(effectiveness) FROM memories`
  - Count memories with low confidence (<0.5)
- [ ] Implement temporal breakdown:
  - Count memories created today
  - Count memories created this week
  - Count memories created this month
  - Find oldest memory date
- [ ] Implement relationship analysis:
  - Group relationships by type
  - Find top 5 most connected memories
  - Identify orphaned memories (no relationships)
- [ ] Implement storage details:
  - Find 5 largest memories by content size
  - Calculate additional storage metrics

**File**: `src/memorygraph/status/formatter.py`

- [ ] Add detailed sections to text formatter:
  - Memory Quality Metrics section
  - Relationship Analysis section
  - Temporal Statistics section
  - Most Connected Memories section
- [ ] Ensure detailed data is included in JSON output

### 3.3 Health Checks
**File**: `src/memorygraph/status/health_checks.py`

- [ ] Create `HealthChecker` class
- [ ] Implement `async def check_database_connection(self, backend) -> HealthCheck`
  - Test backend.health_check()
  - Return HealthCheck with result
- [ ] Implement `async def check_schema_integrity(self, backend) -> HealthCheck`
  - Verify required tables exist (memories, relationships)
  - Verify indexes exist
  - Return HealthCheck with result
- [ ] Implement `async def check_backend_features(self, backend) -> HealthCheck`
  - Check FTS5 for SQLite
  - Check required Neo4j/Memgraph features
  - Return HealthCheck with result
- [ ] Implement `async def run_all_checks(self, backend) -> List[HealthCheck]`
  - Run all health checks
  - Collect results
  - Return list of HealthCheck objects
- [ ] Integrate health checks into StatusCollector

### 3.4 Watch Mode
**File**: `src/memorygraph/cli.py`

- [ ] Add `--watch` / `-w` argument (type=int, metavar='SECONDS')
- [ ] Implement `async def watch_status(args, interval: int)`:
  - Loop until Ctrl+C
  - Clear terminal using ANSI escape codes (`\033[2J\033[H`)
  - Collect and display status
  - Sleep for interval seconds
  - Track previous values to show deltas (↑↓)
- [ ] Handle KeyboardInterrupt gracefully
- [ ] Route to watch_status if --watch is specified

### 3.5 Connection Check Flag
- [ ] Add `--check-connections` flag to CLI
- [ ] When flag is set, run extended connection tests
- [ ] Display detailed connection information
- [ ] Test all configured backends, not just active one

---

## Phase 4: Polish & Production Ready

### 4.1 Error Handling
**File**: `src/memorygraph/status/exceptions.py`

- [ ] Create custom exceptions:
  - `StatusError` (base class)
  - `DatabaseLockedError` (SQLite locked)
  - `ConnectionFailedError` (backend unreachable)
  - `BackendNotSupportedError` (unknown backend)
- [ ] Implement error handling in collector
- [ ] Implement error handling in CLI command
- [ ] Provide helpful error messages with recovery suggestions

### 4.2 Performance Optimization
- [ ] Add query timeouts for long-running queries
- [ ] Use COUNT queries instead of fetching all records
- [ ] Add pagination for detailed listings
- [ ] Implement caching for expensive calculations
- [ ] Profile performance with large databases (10k+ memories)

### 4.3 Documentation
- [ ] Create `docs/STATUS_COMMAND.md` with:
  - Overview and purpose
  - Command syntax and options
  - Output interpretation guide
  - Examples for common scenarios
  - Troubleshooting guide
- [ ] Update main README with status command section
- [ ] Add docstrings to all status module classes and methods
- [ ] Create man page or detailed help text

### 4.4 Integration Tests
**File**: `tests/integration/test_status_integration.py`

- [ ] Test status with populated SQLite database
- [ ] Test status while MCP server is running (concurrent access)
- [ ] Test status with Neo4j backend
- [ ] Test status with Memgraph backend
- [ ] Test all output formats (text, JSON)
- [ ] Test watch mode (limited duration)
- [ ] Test error scenarios (locked database, connection failure)

### 4.5 Edge Cases
- [ ] Handle database with 0 memories gracefully
- [ ] Handle database with millions of memories efficiently
- [ ] Handle corrupted or invalid memory data
- [ ] Handle database file missing (not yet created)
- [ ] Handle permissions issues (read-only filesystem)

---

## Phase 5: Future Enhancements (Optional)

### 5.1 Historical Tracking
**File**: `src/memorygraph/status/history.py`

- [ ] Create `StatusHistory` class
- [ ] Implement `async def save_snapshot(self, status: StatusData)`
  - Save status to history file (~/.memorygraph/status_history.json)
  - Keep last 30 days of snapshots
  - Rotate old snapshots
- [ ] Implement `async def get_trend(self, metric: str, days: int) -> List[float]`
  - Load history file
  - Extract metric values over time
  - Return list for plotting/analysis
- [ ] Add `--trend` option to CLI to show historical trends

### 5.2 Alert Thresholds
**File**: `src/memorygraph/status/alerts.py`

- [ ] Define configurable alert thresholds in config:
  ```python
  STATUS_ALERTS = {
      "low_quality_memories_threshold": 10,
      "orphaned_memories_threshold": 20,
      "database_size_warning_mb": 100
  }
  ```
- [ ] Create `AlertChecker` class
- [ ] Implement alert evaluation logic
- [ ] Add warnings to status output when thresholds exceeded
- [ ] Support custom alert rules

### 5.3 Export Formats
**File**: `src/memorygraph/status/exporters/`

- [ ] Create `html.py` for HTML report export
- [ ] Create `csv.py` for CSV export
- [ ] Create `markdown.py` for Markdown report
- [ ] Add `--export` option to CLI with format selection
- [ ] Generate static HTML dashboard with charts

### 5.4 Plugin Architecture
**File**: `src/memorygraph/status/plugins/`

- [ ] Design plugin interface for custom metrics
- [ ] Create example plugin
- [ ] Document plugin development guide
- [ ] Auto-discover and load plugins from directory

---

## Implementation Notes for Coding Agent

### Key Files to Modify
1. `src/memorygraph/cli.py` - Add status subcommand
2. `src/memorygraph/status/` - New module (create all files)
3. `tests/status/` - New test directory (create all files)

### Existing Code to Leverage
- `src/memorygraph/backends/base.py` - Has `health_check()` method
- `src/memorygraph/database.py` - Has `get_memory_statistics()` method
- `src/memorygraph/config.py` - Has `get_config_summary()` method
- `src/memorygraph/__init__.py` - Has `__version__` for version display

### Database Schema Reference
```sql
-- Memories table
CREATE TABLE memories (
    id TEXT PRIMARY KEY,
    type TEXT,
    content TEXT,
    importance REAL,
    confidence REAL,
    effectiveness REAL,
    created_at TIMESTAMP,
    ...
);

-- Relationships table
CREATE TABLE relationships (
    id TEXT PRIMARY KEY,
    source_id TEXT,
    target_id TEXT,
    type TEXT,
    ...
);
```

### Testing Commands
```bash
# After implementing Phase 1
python -m pytest tests/status/ -v

# Manual testing
memorygraph status
memorygraph status --detailed
memorygraph status --format json

# With test database
export MEMORY_SQLITE_PATH=/tmp/test_memory.db
memorygraph status
```

### Dependencies
No new dependencies required. Uses existing:
- `asyncio` - for async operations
- `json` - for JSON output
- `os` - for file operations
- `dataclasses` - for data models
- `datetime` - for timestamps

---

## Success Criteria

- [ ] Basic status command works with SQLite backend
- [ ] Status completes in <2 seconds for 10k memories
- [ ] Works while MCP server is running (no database locks)
- [ ] JSON output is valid and parseable
- [ ] All tests pass (unit + integration)
- [ ] Documentation is complete and accurate
- [ ] Error messages are helpful and actionable

---

## Rollout Plan

1. **MVP Release** (Phase 1): Basic status with SQLite
2. **Multi-Backend Release** (Phase 2): Neo4j and Memgraph support
3. **Enhanced Release** (Phase 3): JSON, detailed mode, health checks, watch mode
4. **Production Release** (Phase 4): Polish, optimization, comprehensive docs
5. **Future Releases** (Phase 5): Advanced features based on user feedback

---

## Related Documentation
- Architecture Design: See full architectural analysis in task context
- Backend API: `src/memorygraph/backends/base.py`
- Database Schema: `src/memorygraph/database.py`
- CLI Structure: `src/memorygraph/cli.py`

---

**Status**: Not Started
**Priority**: Future Enhancement
**Estimated Effort**: 2-3 weeks (phased implementation)
**Dependencies**: None (uses existing infrastructure)
