# ADR 007: Claude Code Integration Architecture

**Status**: Accepted

**Date**: 2025-11-28

**Context**: Phase 6 - Claude Code Integration

---

## Context

With Phase 5's intelligence layer complete, we needed deep integration with Claude Code development workflows. The goal was to automatically capture development context, analyze projects, and track workflows without requiring manual intervention from users.

## Decision

We implemented a three-pillar integration architecture:

### 1. Context Capture Layer (`integration/context_capture.py`)

**Captures development activities automatically:**

- **Task Context**: Task descriptions, goals, files involved
- **Command Execution**: Commands run, outputs, errors, success status
- **Error Pattern Analysis**: Recurring errors, attempted solutions, what worked
- **Solution Effectiveness**: Track which solutions solve which problems

**Security-First Design:**
- Automatic sanitization of sensitive data (API keys, passwords, tokens, emails)
- Pattern-based redaction before storage
- No credentials leak into memories

**Data Model:**
```python
TaskContext(description, goals, files_involved)
CommandExecution(command, output, error, success)
ErrorPattern(error_type, error_message, frequency, solutions_tried)
```

### 2. Project Analysis Layer (`integration/project_analysis.py`)

**Provides project-aware intelligence:**

- **Project Detection**: Identifies projects from config files (pyproject.toml, package.json, etc.)
- **Codebase Analysis**: File counts, languages, frameworks, structure
- **File Change Tracking**: Git integration to track modifications
- **Code Pattern Identification**: Recognizes API endpoints, class definitions, async patterns

**Technology Detection:**
- Supports Python, TypeScript, JavaScript, Rust, Go, Java, Ruby, PHP
- Framework detection (React, Vue, FastAPI, Flask, Django, etc.)
- Special handling for TypeScript projects (not marked as mixed with JavaScript)

**Data Model:**
```python
ProjectInfo(name, path, project_type, git_remote, technologies)
CodebaseInfo(total_files, file_types, languages, frameworks)
FileChange(file_path, change_type, lines_added, lines_removed)
Pattern(pattern_type, description, examples, frequency, confidence)
```

### 3. Workflow Tracking Layer (`integration/workflow_tracking.py`)

**Tracks and optimizes development workflows:**

- **Workflow Action Tracking**: Records actions in sessions with duration and success
- **Workflow Suggestions**: Identifies successful patterns from history
- **Workflow Optimization**: Detects slow actions, repeated failures, inefficiencies
- **Session State Management**: Enables session continuity and next-step suggestions

**Intelligence Features:**
- Pattern recognition from successful workflows
- Bottleneck identification (slow actions >30s)
- Error pattern detection (repeated failures)
- Back-and-forth inefficiency detection
- Productivity recommendations (long sessions)

**Data Model:**
```python
WorkflowAction(session_id, action_type, action_data, success, duration)
WorkflowSuggestion(workflow_name, steps, success_rate, relevance_score)
Recommendation(recommendation_type, title, description, impact, evidence)
SessionState(session_id, current_task, open_problems, next_steps)
```

### 4. MCP Integration (`integration_tools.py`)

**11 New MCP Tools:**

1. `capture_task` - Capture task context
2. `capture_command` - Capture command execution
3. `track_error_solution` - Track solution effectiveness
4. `detect_project` - Detect project information
5. `analyze_project` - Analyze codebase
6. `track_file_changes` - Track git changes
7. `identify_patterns` - Identify code patterns
8. `track_workflow` - Track workflow actions
9. `suggest_workflow` - Get workflow suggestions
10. `optimize_workflow` - Get optimization recommendations
11. `get_session_state` - Get current session state

## Alternatives Considered

### 1. Manual Context Capture
**Rejected**: Too much friction for users, would rarely be used.

### 2. File-System Monitoring
**Rejected**: Privacy concerns, high overhead, difficult to implement cross-platform.

### 3. Claude Code Direct Integration
**Deferred**: Would require changes to Claude Code itself, current approach works via MCP.

### 4. Separate Database for Integration Data
**Rejected**: Unified graph enables powerful relationships between regular memories and integration data.

## Consequences

### Positive

1. **Automatic Memory Creation**: Development context captured without user effort
2. **Project Intelligence**: Context-aware suggestions based on project type
3. **Pattern Learning**: System learns from successful workflows
4. **Privacy Protected**: Sensitive data sanitized before storage
5. **Backend Agnostic**: Works with all three backends (Neo4j, Memgraph, SQLite)
6. **93% Test Coverage**: Comprehensive testing ensures reliability

### Negative

1. **Git Dependency**: Some features require git (handled gracefully)
2. **Subprocess Calls**: File change tracking uses subprocess (timeout protected)
3. **Pattern Detection Limitations**: Code pattern recognition is regex-based (good enough for common cases)

### Neutral

1. **Additional Memory Types**: Introduced task, observation, file_change, error_pattern, workflow_action, code_pattern types
2. **Entity Types**: Added 'session', 'file', 'project' entity types
3. **Relationships**: Uses existing relationship types (PART_OF, INVOLVES, EXECUTED_IN, EXHIBITS, SOLVES, IN_SESSION, FOLLOWS, FOUND_IN)

## Implementation Details

### Storage Strategy

All integration data stored as standard Memory nodes with specific types:
- Enables querying integration data alongside regular memories
- Leverages existing relationship system
- Maintains graph traversal capabilities

### Security Patterns

Sanitization regex patterns:
```python
r"(?i)(api[_-]?key|token|password|secret|auth)[=:\s]+['\"]?[\w\-\.]+['\"]?"
r"(?i)bearer\s+[\w\-\.]+"  # Bearer tokens
r"-----BEGIN (RSA |EC )?PRIVATE KEY-----"  # Private keys
r"(?:https?://)?[\w\-]+:[\w\-]+@"  # URLs with credentials
r"\b[\w\-\.]+@[\w\-\.]+\.(com|net|org|io|dev)\b"  # Emails
```

### Backend Compatibility

All features tested and working with:
- ✅ Neo4j (full graph capabilities)
- ✅ Memgraph (full graph capabilities)
- ✅ SQLite (NetworkX-based graph traversal)

## Metrics

- **Lines of Code**: 429 (integration module)
- **Test Coverage**: 93% (exceeds 80% target)
- **Test Count**: 75 integration tests (all passing)
- **Total Tests**: 346 (271 existing + 75 new)
- **Pass Rate**: 100%

## Related ADRs

- ADR 001: Neo4j Over PostgreSQL (graph foundation)
- ADR 003: Async Database Layer (async operations)
- ADR 005: Multi-Backend Support (backend abstraction)
- ADR 006: Intelligence Layer Architecture (entity extraction, patterns)

## Notes

This completes Phase 6 of the enhancement plan. The integration layer provides the foundation for Phase 7 (Proactive Features) by automatically capturing the context needed for intelligent suggestions.

The privacy-first approach ensures users can trust the system with their development workflow data.

## Future Enhancements

Potential improvements for future phases:

1. **Semantic Code Analysis**: Use AST parsing instead of regex for deeper pattern recognition
2. **IDE Integration**: Direct integration with VS Code, IntelliJ, etc.
3. **Team Workflow Sharing**: Optional sharing of successful workflows across team
4. **Performance Profiling**: Automatic detection of performance bottlenecks in code
5. **Test Coverage Integration**: Link test results to code changes
