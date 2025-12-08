# MemoryGraph v0.11.2 Announcement Drafts

> Ready-to-post announcements for v0.11.2 release with SDK

---

## Reddit: r/ClaudeAI

**Title**: I built a Python SDK for MemoryGraph - now works with LlamaIndex, LangChain, CrewAI, and AutoGen

**Content**:
```
I've been working on MemoryGraph, a graph-based memory server for Claude Code, and just released v0.11.2 with a major new feature: **a Python SDK** that works with popular AI agent frameworks.

## What's New

**memorygraphsdk** - Native integrations for:
- 🦙 **LlamaIndex** - MemoryGraphChatMemory, MemoryGraphRetriever for RAG
- 🦜 **LangChain** - MemoryGraphMemory with session support
- 👥 **CrewAI** - Persistent memory for multi-agent crews
- 🤖 **AutoGen** - Conversation history that persists

## Quick Start

```bash
pip install memorygraphsdk[all]
```

```python
from memorygraphsdk import MemoryGraphClient

client = MemoryGraphClient(api_key="your_key")
memory = client.create_memory(
    type="solution",
    title="Fixed Redis timeout",
    content="Used exponential backoff",
    tags=["redis", "fix"]
)
```

## Why Graph Memory?

Unlike vector-based memory that just stores embeddings, MemoryGraph captures *relationships* between memories:
- What solution fixed which problem?
- What decisions led to what outcomes?
- What patterns appear across projects?

## Links
- SDK: https://pypi.org/project/memorygraphsdk/
- MCP Server: https://pypi.org/project/memorygraphMCP/
- GitHub: https://github.com/gregorydickson/memory-graph
- Docs: https://memorygraph.dev

Happy to answer questions!
```

---

## Reddit: r/LangChain

**Title**: MemoryGraph SDK - Graph-based persistent memory for LangChain (captures relationships, not just embeddings)

**Content**:
```
Just released **memorygraphsdk** with native LangChain integration.

## Why Graph Memory vs Vector Memory?

Vector stores are great for similarity search, but they don't capture *how* information connects. MemoryGraph stores memories as a graph, so you can:

- Find what solution fixed a similar problem
- Track what decisions led to outcomes
- Discover patterns across conversations

## LangChain Integration

```python
from memorygraphsdk.integrations.langchain import MemoryGraphMemory
from langchain.chains import ConversationChain

memory = MemoryGraphMemory(api_key="your_key")
chain = ConversationChain(memory=memory, llm=llm)

# Memories persist across sessions and devices
# Relationships between memories are tracked automatically
```

## Install

```bash
pip install memorygraphsdk[langchain]
```

## Links
- PyPI: https://pypi.org/project/memorygraphsdk/
- Docs: https://github.com/gregorydickson/memory-graph/blob/main/sdk/docs/langchain.md
- Full SDK docs: https://memorygraph.dev/docs/sdk

Feedback welcome!
```

---

## Reddit: r/LocalLLaMA

**Title**: MemoryGraph - Graph-based memory for AI agents (works with LlamaIndex, LangChain, local or cloud)

**Content**:
```
Released v0.11.2 of MemoryGraph with a Python SDK for agent frameworks.

## What It Does

Persistent, graph-based memory for AI agents. Instead of just storing text/embeddings, it captures relationships:
- Solution A **SOLVES** Problem B
- Decision X **LEADS_TO** Outcome Y
- Pattern M **APPLIES_TO** Project N

## Local-First

- Default: SQLite (zero config, no external dependencies)
- Optional: Neo4j, FalkorDB for scale
- Cloud option: Sync across devices via memorygraph.dev

## Framework Support

```bash
pip install memorygraphsdk[llamaindex]  # LlamaIndex
pip install memorygraphsdk[langchain]   # LangChain
pip install memorygraphsdk[all]         # Everything
```

## For Claude Code Users

Also works as an MCP server:
```bash
pip install memorygraphMCP
memorygraph  # Starts server with SQLite
```

## Links
- GitHub: https://github.com/gregorydickson/memory-graph
- SDK: https://pypi.org/project/memorygraphsdk/
- MCP: https://pypi.org/project/memorygraphMCP/

1,200+ tests, Apache 2.0 license.
```

---

## Twitter/X Thread

```
🚀 Just released MemoryGraph v0.11.2 with a Python SDK!

Now works with @llaboratory @LangChainAI CrewAI and AutoGen.

Graph-based memory that captures *relationships* - not just embeddings.

🧵 Thread:

---

1/ The problem with vector memory:

It's great for similarity search, but loses context.

"What solution fixed similar problems before?"
"What decisions led to this?"

Graph memory tracks these connections.

---

2/ memorygraphsdk integrations:

🦙 LlamaIndex - MemoryGraphChatMemory, MemoryGraphRetriever
🦜 LangChain - MemoryGraphMemory with sessions
👥 CrewAI - Multi-agent persistent memory
🤖 AutoGen - Conversation history

pip install memorygraphsdk[all]

---

3/ Quick example:

```python
from memorygraphsdk import MemoryGraphClient

client = MemoryGraphClient(api_key="...")
client.create_memory(
    type="solution",
    title="Fixed Redis timeout",
    tags=["redis"]
)
```

Memories persist. Relationships tracked automatically.

---

4/ Also works as MCP server for @AnthropicAI Claude Code:

pip install memorygraphMCP
memorygraph

Zero-config SQLite. Or connect to Neo4j, FalkorDB, or our cloud.

---

5/ Links:

📦 SDK: https://pypi.org/project/memorygraphsdk/
📦 MCP: https://pypi.org/project/memorygraphMCP/
🐙 GitHub: https://github.com/gregorydickson/memory-graph
📚 Docs: https://memorygraph.dev

1,200+ tests. Apache 2.0. Feedback welcome!

#MCP #ClaudeCode #AIAgents #LangChain #LlamaIndex
```

---

## Hacker News: Show HN

**Title**: Show HN: MemoryGraph – Graph-based memory for AI agents (LlamaIndex, LangChain, MCP)

**Content**:
```
Hi HN,

I built MemoryGraph, a graph-based memory system for AI agents. Just released v0.11.2 with a Python SDK.

## The Problem

Most AI memory solutions use vector stores - great for similarity search, but they don't capture how information connects. When you ask "what solved similar problems?", you get semantically similar text, not actual solutions that worked.

## The Solution

MemoryGraph stores memories as a graph with typed relationships:
- Solution A SOLVES Problem B
- Decision X LEADS_TO Outcome Y
- Error M TRIGGERS Fix N

This enables queries like:
- "What have I tried for this type of problem?"
- "What decisions led to this architecture?"
- "What patterns work across my projects?"

## What's New in v0.11

Python SDK (`memorygraphsdk`) with native integrations:
- LlamaIndex: Chat memory + RAG retriever
- LangChain: BaseMemory implementation
- CrewAI: Multi-agent memory
- AutoGen: Conversation history

Plus cloud backend for multi-device sync.

## Technical Details

- Graph storage: SQLite (default), Neo4j, FalkorDB
- 1,200+ tests
- MCP server for Claude Code
- Apache 2.0 license

## Links

- GitHub: https://github.com/gregorydickson/memory-graph
- SDK: https://pypi.org/project/memorygraphsdk/
- MCP Server: https://pypi.org/project/memorygraphMCP/

Would love feedback on the approach. The graph-vs-vector debate is interesting - happy to discuss tradeoffs.
```

---

## Framework-Specific Posts

### LlamaIndex Discord/Forums

```
**MemoryGraph SDK - Graph-based memory for LlamaIndex**

Just released native LlamaIndex integration for MemoryGraph:

**MemoryGraphChatMemory** - Persistent chat memory backed by a graph database
**MemoryGraphRetriever** - RAG retriever that understands relationships

Unlike vector retrieval, graph memory captures *how* memories connect:
- What solutions fixed which problems
- What patterns apply to which contexts
- What decisions led to outcomes

Install:
```bash
pip install memorygraphsdk[llamaindex]
```

Usage:
```python
from memorygraphsdk.integrations.llamaindex import MemoryGraphChatMemory
from llama_index.core.chat_engine import SimpleChatEngine

memory = MemoryGraphChatMemory(api_key="your_key")
chat_engine = SimpleChatEngine.from_defaults(memory=memory)
```

Full docs: https://github.com/gregorydickson/memory-graph/blob/main/sdk/docs/llamaindex.md
```

---

## Notes

- Best posting times: Tuesday-Thursday, 9am-12pm EST
- Engage with comments within first 2 hours
- Cross-post to framework-specific communities after main posts
- Monitor for questions and feedback
