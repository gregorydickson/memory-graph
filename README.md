# Claude Code Memory Server

[![PyPI](https://img.shields.io/badge/pip-install-blue)](https://pypi.org/project/claude-code-memory/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Zero Config](https://img.shields.io/badge/setup-zero--config-green)](docs/DEPLOYMENT.md)
[![3 Backends](https://img.shields.io/badge/backends-SQLite%20%7C%20Neo4j%20%7C%20Memgraph-purple)](docs/FULL_MODE.md)

A graph-based Model Context Protocol (MCP) server that gives Claude Code persistent memory. Store development patterns, track relationships, and retrieve contextual knowledge across sessions and projects.

## Quick Start (30 seconds)

```bash
# Install
pip install claude-code-memory

# Run
claude-memory
```

That's it! Memory is stored in `~/.claude-memory/memory.db`. Zero configuration needed.

### Claude Code Integration

Add to your `.claude/mcp.json`:

```json
{
  "mcpServers": {
    "claude-memory": {
      "command": "claude-memory"
    }
  }
}
```

Start using it immediately:
- "Store this pattern for later"
- "What similar problems have we solved?"
- "Remember this approach works well for authentication"

See [CLAUDE_CODE_SETUP.md](docs/CLAUDE_CODE_SETUP.md) for detailed integration guide.

---

## Choose Your Mode

Start simple, upgrade when needed:

| Feature | Lite (Default) | Standard | Full |
|---------|----------------|----------|------|
| **Memory Storage** | ✅ | ✅ | ✅ |
| **Relationships** | ✅ Basic | ✅ Basic | ✅ Advanced |
| **Pattern Recognition** | ❌ | ✅ | ✅ |
| **Session Briefings** | ❌ | ✅ | ✅ |
| **Graph Analytics** | ❌ | ❌ | ✅ |
| **Project Integration** | ❌ | ❌ | ✅ |
| **Workflow Automation** | ❌ | ❌ | ✅ |
| **Backend** | SQLite | SQLite | SQLite/Neo4j/Memgraph |
| **Tools Available** | 8 | 15 | 44 |
| **Setup Time** | 30 sec | 30 sec | 5 min |

```bash
# Default (lite mode)
claude-memory

# Standard mode (pattern recognition)
claude-memory --profile standard

# Full power (all 44 tools)
claude-memory --profile full --backend neo4j
```

---

## Features

### Core Memory Operations (All Modes)
- **Store & Retrieve** - Persistent memory across sessions
- **Smart Search** - Find memories by content, context, or relationships
- **Relationship Tracking** - Link related concepts, solutions, and patterns
- **Project Context** - Organize memories by project and technology

### Intelligence Features (Standard & Full)
- **Pattern Recognition** - Automatically identify reusable patterns
- **Solution Suggestions** - Find similar solutions from past work
- **Context Awareness** - Smart context retrieval with token limiting
- **Session Briefings** - Get AI-generated summaries of your work

### Advanced Analytics (Full Mode Only)
- **Graph Analytics** - Cluster analysis, bridging nodes, path finding
- **Workflow Automation** - Track and optimize development workflows
- **Project Integration** - Codebase scanning and pattern detection
- **Proactive Suggestions** - AI-powered recommendations and issue detection

See [TOOL_PROFILES.md](docs/TOOL_PROFILES.md) for complete tool list.

---

## Why Claude Code Memory?

### The Problem
Claude Code has no memory between sessions. Every conversation starts fresh. You repeat yourself. Patterns get lost. Context disappears.

### The Solution
This MCP server gives Claude persistent memory:
- "What authentication approach did we use last time?"
- "Find all memories about database migrations"
- "What patterns work best for this codebase?"
- "How did we solve this error before?"

### The Approach
**Three-tier complexity model:**

1. **Start Zero-Config** (Lite) - SQLite backend, 8 core tools, works immediately
2. **Upgrade to Intelligence** (Standard) - Same backend, add pattern recognition
3. **Go Full Power** (Full) - Switch to Neo4j/Memgraph, unlock all 44 tools

You choose how much complexity you need.

---

## Installation

### Option 1: pip (Recommended)

```bash
# Basic installation (SQLite, lite mode)
pip install claude-code-memory

# With intelligence features (standard mode)
pip install "claude-code-memory[intelligence]"

# Full power with Neo4j
pip install "claude-code-memory[neo4j,intelligence]"
```

### Option 2: Docker

```bash
# SQLite mode (default)
docker compose up -d

# Neo4j mode (full power)
docker compose -f docker-compose.neo4j.yml up -d
```

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed installation options.

---

## Usage Examples

### Basic Memory Storage

```json
{
  "tool": "store_memory",
  "content": "Use bcrypt for password hashing in this project",
  "memory_type": "CodePattern",
  "project": "my-app",
  "tags": ["security", "authentication"]
}
```

### Find Related Memories

```json
{
  "tool": "search_memories",
  "query": "authentication",
  "memory_type": "CodePattern",
  "limit": 5
}
```

### Create Relationships

```json
{
  "tool": "create_relationship",
  "from_memory_id": "mem_123",
  "to_memory_id": "mem_456",
  "relationship_type": "SOLVES"
}
```

### Pattern Recognition (Standard/Full)

```json
{
  "tool": "find_similar_solutions",
  "problem_description": "need to validate user input",
  "limit": 3
}
```

See examples in [docs/examples/](docs/examples/) for more use cases.

---

## Architecture

### Memory Types
- **Task** - Development tasks and execution patterns
- **CodePattern** - Reusable code solutions and architectural decisions
- **Problem** - Issues encountered and their context
- **Solution** - How problems were resolved and effectiveness
- **Project** - Codebase context and project-specific knowledge
- **Technology** - Framework, language, and tool-specific knowledge

### Relationship Categories (7 types, 35+ relationships)
1. **Causal** - `CAUSES`, `TRIGGERS`, `LEADS_TO`, `PREVENTS`, `BREAKS`
2. **Solution** - `SOLVES`, `ADDRESSES`, `ALTERNATIVE_TO`, `IMPROVES`, `REPLACES`
3. **Context** - `OCCURS_IN`, `APPLIES_TO`, `WORKS_WITH`, `REQUIRES`, `USED_IN`
4. **Learning** - `BUILDS_ON`, `CONTRADICTS`, `CONFIRMS`, `GENERALIZES`, `SPECIALIZES`
5. **Similarity** - `SIMILAR_TO`, `VARIANT_OF`, `RELATED_TO`, `ANALOGY_TO`, `OPPOSITE_OF`
6. **Workflow** - `FOLLOWS`, `DEPENDS_ON`, `ENABLES`, `BLOCKS`, `PARALLEL_TO`
7. **Quality** - `EFFECTIVE_FOR`, `INEFFECTIVE_FOR`, `PREFERRED_OVER`, `DEPRECATED_BY`, `VALIDATED_BY`

See [schema.md](docs/schema.md) for complete data model.

---

## Backends

### SQLite (Default)
- **Use for**: Getting started, personal projects, <10k memories
- **Pros**: Zero config, no dependencies, portable, fast for most use cases
- **Cons**: Graph queries slower at scale, no concurrent writes
- **Backend**: `--backend sqlite` (default)

### Neo4j
- **Use for**: Production, team use, complex graph analytics
- **Pros**: Industry-standard graph DB, rich query language, excellent tooling
- **Cons**: Requires setup, resource intensive
- **Backend**: `--backend neo4j`

### Memgraph
- **Use for**: High-performance analytics, real-time queries
- **Pros**: Fastest graph analytics, in-memory processing, compatible with Neo4j
- **Cons**: Requires setup, less mature ecosystem
- **Backend**: `--backend memgraph`

See [FULL_MODE.md](docs/FULL_MODE.md) for backend setup guides.

---

## Configuration

### Environment Variables

```bash
# Backend selection
export MEMORY_BACKEND=sqlite          # sqlite (default) | neo4j | memgraph

# Tool profile
export MEMORY_TOOL_PROFILE=lite       # lite (default) | standard | full

# SQLite configuration (default backend)
export MEMORY_SQLITE_PATH=~/.claude-memory/memory.db

# Neo4j configuration (if using neo4j backend)
export MEMORY_NEO4J_URI=bolt://localhost:7687
export MEMORY_NEO4J_USER=neo4j
export MEMORY_NEO4J_PASSWORD=your-password

# Memgraph configuration (if using memgraph backend)
export MEMORY_MEMGRAPH_URI=bolt://localhost:7687
export MEMORY_MEMGRAPH_USER=memgraph
export MEMORY_MEMGRAPH_PASSWORD=your-password

# Logging
export MEMORY_LOG_LEVEL=INFO          # DEBUG | INFO | WARNING | ERROR
```

### CLI Options

```bash
# Show help
claude-memory --help

# Show current configuration
claude-memory --show-config

# Show version
claude-memory --version

# Run with custom settings
claude-memory --backend neo4j --profile full --log-level DEBUG
```

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for complete configuration reference.

---

## Development

### Project Structure
```
claude-code-memory/
├── src/claude_memory/          # Main source code
│   ├── server.py               # MCP server (44 tools)
│   ├── backends/               # SQLite, Neo4j, Memgraph
│   ├── tools/                  # Tool implementations
│   ├── models.py               # Data models
│   └── cli.py                  # Command-line interface
├── tests/                      # 409 tests, 93% coverage
├── docs/                       # Documentation
└── pyproject.toml             # Package configuration
```

### Development Setup

```bash
# Clone repository
git clone https://github.com/gregorydickson/claude-code-memory.git
cd claude-code-memory

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v --cov=claude_memory

# Type checking
mypy src/

# Format code
black src/ tests/
ruff --fix src/ tests/
```

### Test Suite

```bash
# All tests
pytest

# With coverage
pytest --cov=claude_memory --cov-report=html

# Specific backend
pytest tests/backends/test_sqlite_backend.py

# Integration tests
pytest tests/integration/
```

**Current Status**: 401/409 tests passing, 93% coverage

---

## Upgrading

### From Lite to Standard
No changes needed - just add the flag:
```bash
claude-memory --profile standard
```

### From SQLite to Neo4j
1. Export SQLite data: `claude-memory --export backup.json`
2. Set up Neo4j (see [FULL_MODE.md](docs/FULL_MODE.md))
3. Import data: `claude-memory --backend neo4j --import backup.json`
4. Update MCP config to use `--backend neo4j`

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed migration guide.

---

## Troubleshooting

### Common Issues

**Server won't start**
```bash
# Check configuration
claude-memory --show-config

# Verify database connection
claude-memory --health
```

**SQLite database locked**
```bash
# Check for running processes
ps aux | grep claude-memory

# Remove lock file (if safe)
rm ~/.claude-memory/memory.db-lock
```

**Neo4j connection refused**
```bash
# Verify Neo4j is running
docker ps | grep neo4j

# Check credentials
claude-memory --backend neo4j --show-config
```

See [DEPLOYMENT.md](docs/DEPLOYMENT.md#troubleshooting) for more solutions.

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Workflow
1. Check [GitHub Issues](https://github.com/gregorydickson/claude-code-memory/issues)
2. Fork the repository and create a feature branch
3. Make changes following our coding standards (Black, Ruff, mypy)
4. Add tests for new functionality (maintain 90%+ coverage)
5. Submit a pull request with clear description

---

## Roadmap

### v1.0 (Current) ✅
- ✅ SQLite default backend
- ✅ Three-tier complexity (lite/standard/full)
- ✅ 44 MCP tools
- ✅ CLI with `claude-memory` command
- ✅ PyPI publication
- ✅ Docker support

### v1.1 (Planned)
- Web visualization dashboard
- Enhanced embedding support
- PostgreSQL backend (pg_graph)
- Advanced analytics UI
- Workflow automation templates

### v2.0 (Future)
- Multi-user support
- Team memory sharing
- Cloud-hosted options
- Advanced AI features

---

## Performance

### Benchmarks (SQLite)
- **1,000 memories**: <50ms query time
- **10,000 memories**: <100ms query time
- **100,000 memories**: <500ms query time
- **Relationship traversal**: <100ms for 3-hop queries

### Benchmarks (Neo4j)
- **10x faster** graph traversals at scale
- **100x faster** complex analytics queries
- Handles millions of memories efficiently

See [FULL_MODE.md](docs/FULL_MODE.md#performance) for detailed benchmarks.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Support

- [Documentation](docs/) - Guides, references, examples
- [GitHub Issues](https://github.com/gregorydickson/claude-code-memory/issues) - Bug reports and feature requests
- [GitHub Discussions](https://github.com/gregorydickson/claude-code-memory/discussions) - Questions and community support

---

## Acknowledgments

- [Model Context Protocol](https://github.com/modelcontextprotocol) - Protocol specification
- [Neo4j](https://neo4j.com/) - Graph database platform
- [Memgraph](https://memgraph.com/) - High-performance graph platform
- [Claude Code](https://claude.ai/code) - AI-powered development environment

---

**Made with ❤️ for the Claude Code community**

*Start simple. Upgrade when needed. Never lose context again.*
