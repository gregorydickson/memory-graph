# Awesome MCP Servers PR Submissions

## 1. appcypher/awesome-mcp-servers (Primary - 7k+ stars)

**URL**: https://github.com/appcypher/awesome-mcp-servers

**Section**: 🗄️ Databases (or propose new 🧠 Memory section)

### PR Title
```
Add MemoryGraph - Graph-based memory server with SDK
```

### Entry to Add (in Databases section)
```markdown
- <img src="https://cdn.simpleicons.org/graphql" height="14"/> [MemoryGraph](https://github.com/gregorydickson/memory-graph) - Graph-based persistent memory with relationship tracking. Supports SQLite, Neo4j, FalkorDB, and cloud sync. Includes Python SDK for LlamaIndex, LangChain, CrewAI, AutoGen.
```

### PR Description
```markdown
## Add MemoryGraph to Databases section

### Server Description
MemoryGraph is a graph-based MCP memory server that captures relationships between memories, not just content. Unlike vector-based memory, it tracks typed relationships (SOLVES, CAUSES, LEADS_TO) to enable queries like "what solved similar problems?"

### Key Features
- **Zero-config**: SQLite default, no external dependencies
- **Graph storage**: Captures relationships between memories
- **Multi-backend**: SQLite, Neo4j, FalkorDB, Cloud
- **Python SDK**: Native integrations for LlamaIndex, LangChain, CrewAI, AutoGen
- **1,200+ tests**: Comprehensive test coverage

### Installation
```bash
pip install memorygraphMCP
memorygraph  # Starts MCP server
```

### Links
- GitHub: https://github.com/gregorydickson/memory-graph
- PyPI (MCP): https://pypi.org/project/memorygraphMCP/
- PyPI (SDK): https://pypi.org/project/memorygraphsdk/
- License: Apache 2.0
```

---

## 2. wong2/awesome-mcp-servers

**URL**: https://github.com/wong2/awesome-mcp-servers

**Section**: Add under appropriate category (they have a simpler format)

### PR Title
```
Add MemoryGraph - Graph-based memory server
```

### Entry to Add
```markdown
- **[MemoryGraph](https://github.com/gregorydickson/memory-graph)** - Graph-based persistent memory server with relationship tracking. Supports SQLite, Neo4j, FalkorDB. Includes Python SDK for LlamaIndex, LangChain, CrewAI, AutoGen.
```

### PR Description
```markdown
## Add MemoryGraph

Graph-based MCP memory server that captures relationships between memories.

**Features:**
- Zero-config SQLite default
- Graph-based storage with typed relationships
- Multi-backend: SQLite, Neo4j, FalkorDB, Cloud
- Python SDK for agent frameworks (LlamaIndex, LangChain, CrewAI, AutoGen)
- 1,200+ tests

**Install:** `pip install memorygraphMCP`

**Links:**
- https://github.com/gregorydickson/memory-graph
- https://pypi.org/project/memorygraphMCP/
```

---

## 3. punkpeye/awesome-mcp-servers

**URL**: https://github.com/punkpeye/awesome-mcp-servers

### PR Title
```
Add MemoryGraph - Graph-based memory with SDK
```

### Entry (check their format first)
```markdown
- [MemoryGraph](https://github.com/gregorydickson/memory-graph) - Graph-based persistent memory server with relationship tracking and Python SDK for LlamaIndex, LangChain, CrewAI, AutoGen.
```

---

## 4. Official MCP Servers Repo

**URL**: https://github.com/modelcontextprotocol/servers

**Section**: Community Servers

### PR Title
```
Add MemoryGraph community server
```

### Entry
```markdown
### MemoryGraph
Graph-based persistent memory server with relationship tracking.

- **Repository**: https://github.com/gregorydickson/memory-graph
- **PyPI**: `pip install memorygraphMCP`
- **Features**: SQLite/Neo4j/FalkorDB backends, Python SDK
```

---

## Quick Steps to Submit PRs

### For appcypher/awesome-mcp-servers:

1. Go to https://github.com/appcypher/awesome-mcp-servers
2. Click "Fork" to create your fork
3. Edit README.md in your fork
4. Find the `## 🗄️ Databases` section
5. Add the entry in alphabetical order
6. Create a PR with the title and description above

### For wong2/awesome-mcp-servers:

1. Go to https://github.com/wong2/awesome-mcp-servers
2. Fork the repo
3. Add entry to README.md
4. Create PR

### For modelcontextprotocol/servers:

1. Go to https://github.com/modelcontextprotocol/servers
2. Check their CONTRIBUTING.md for guidelines
3. Fork and add to community servers section
4. Create PR

---

## Tips

- Submit to **appcypher** first (highest visibility)
- Wait 24-48 hours between submissions to avoid spam appearance
- Respond to any feedback within 24 hours
- Be ready to make requested changes quickly
