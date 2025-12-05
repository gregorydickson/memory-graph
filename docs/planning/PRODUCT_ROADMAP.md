# memory-graph Product Roadmap

**Document Version**: 3.1
**Last Updated**: December 2025
**Author**: Gregory Dickson
**Status**: Strategic Plan - COMPETITIVE RESPONSE UPDATE

---

## ⚠️ COMPETITIVE LANDSCAPE

**This version incorporates strategic responses to our key competitors in the AI agent memory space.**

### Competitor 1: Byterover Cipher (Direct MCP Competitor)

Cipher is an MCP-based memory layer for coding agents with 3.2K GitHub stars, built-in semantic search, and a commercial cloud product (Byterover.dev). They target the exact same market as memory-graph.

| Aspect | Cipher | memory-graph |
|--------|--------|--------------|
| License | Elastic 2.0 (restrictive) | Apache 2.0 ✅ |
| Language | Node.js | Python ✅ |
| Search | Vector-first (Qdrant, Milvus) | Graph-first + planned hybrid |
| Relationships | Generic edges | 35+ typed relationships ✅ |
| GitHub Stars | 3,200+ | Growing |
| Cloud | Byterover.dev (live) | memorygraph.dev (planned) |

### Competitor 2: Zep/Graphiti (Temporal Knowledge Graph Leader)

Graphiti (by Zep AI, Y Combinator backed) is the state-of-the-art temporal knowledge graph framework with 20K+ GitHub stars. While not coding-specific, they've solved hard problems we can learn from.

| Aspect | Graphiti | memory-graph |
|--------|----------|--------------|
| License | Apache 2.0 | Apache 2.0 ✅ |
| Focus | General AI agents | Coding-specific ✅ |
| Temporal Model | Bi-temporal (advanced) ✅ | Basic → Phase 2 upgrade |
| Search | Hybrid (semantic + BM25 + graph) ✅ | Graph → Phase 2 hybrid |
| Dependencies | Neo4j required | SQLite (lightweight) ✅ |
| Benchmark | 94.8% DMR accuracy (SOTA) | Not yet benchmarked |
| GitHub Stars | 20,000+ | Growing |

**Key Graphiti innovations to study and adopt:**
- **Bi-temporal tracking**: Track both when a fact was true AND when we learned it
- **Hybrid search**: Combine semantic embeddings, BM25 keyword search, and graph traversal
- **Edge invalidation**: Mark outdated facts as invalid (don't delete), preserving history
- **Episode-based ingestion**: Structure memories as discrete episodes with provenance

### Key Competitive Gaps to Close

| Gap | Competitors Have | We Need | Priority | Phase |
|-----|-----------------|---------|----------|-------|
| Semantic Search | Cipher: vectors, Graphiti: hybrid | Add embedding support | 🔴 CRITICAL | 2 |
| Temporal Model | Graphiti: bi-temporal | Implement bi-temporal tracking | 🔴 HIGH | 2 |
| Cloud Product | Cipher: Byterover.dev, Zep: managed | memorygraph.dev | 🔴 CRITICAL | 3 |
| GitHub Stars | Cipher: 3.2K, Graphiti: 20K | Accelerate marketing | 🔴 HIGH | 1 |
| Benchmarks | Graphiti: DMR 94.8% | Run DMR benchmark | 🟡 MEDIUM | 2 |

### Key Advantages to Leverage

| Advantage | Details | Marketing Action |
|-----------|---------|-----------------|
| **Apache 2.0 License** | True open source vs. Cipher's Elastic 2.0 | Blog post, prominent badge |
| **Typed Relationships** | 35+ semantic types vs. generic edges | Comparison demos |
| **Coding-Specific Types** | 8 entity types designed for dev workflows | Feature comparison |
| **Python Native** | AI/ML ecosystem majority | Target Python devs |
| **Lightweight** | SQLite default vs. Neo4j required | Performance benchmarks |
| **Test Coverage** | 93% (409 tests) | Quality messaging |

---

## Executive Summary

memory-graph is a lightweight memory server for AI coding agents. It helps coding assistants like Claude Code remember what worked, avoid past mistakes, and maintain context across sessions.

### Vision Statement

> **"Never re-explain your project to your AI again."**

### Revised Competitive Positioning

```
                    MCP Memory for Coding Agents
                    
     Vector-First                    Graph-First
     (Similarity)                   (Relationships)
           │                            │
    ┌──────┴──────┐              ┌──────┴──────┐
    │   Cipher    │              │ memory-graph│
    │ (Byterover) │              │             │
    ├─────────────┤              ├─────────────┤
    │ • 3.2K stars│              │ • Apache 2.0│
    │ • Vectors   │              │ • 35+ types │
    │ • Node.js   │              │ • Python    │
    │ • Elastic   │              │ • 93% tests │
    └─────────────┘              └─────────────┘
    
              Graphiti (Zep)
           ┌─────────────────┐
           │ • 20K stars     │
           │ • Bi-temporal   │
           │ • Hybrid search │
           │ • Neo4j required│
           │ • General focus │
           └─────────────────┘
```

**Our Position**: "Memory that understands code relationships, not just similarity"

---

## REVISED PHASE STRUCTURE

### Phase 0: Competitive Response Sprint ⚡ NEW
**Timeline**: Weeks 1-2 (IMMEDIATE)
**Goal**: Close critical gaps, establish differentiation

### Phase 1: Launch & Community (Updated)
**Timeline**: Weeks 3-5
**Goal**: Establish presence, outpace Cipher in adoption velocity

### Phase 2: Search & Temporal Model (ELEVATED PRIORITY)
**Timeline**: Weeks 6-9
**Goal**: Close semantic search gap, implement bi-temporal tracking (learn from Graphiti)

### Phase 3: Cloud Launch (ACCELERATED)
**Timeline**: Weeks 10-14
**Goal**: Launch memorygraph.dev before Byterover gains more ground

### Phase 4: Team Features
**Timeline**: Weeks 15-20
**Goal**: Match Cipher's workspace memory, add unique value

### Phase 5: Scale & Enterprise
**Timeline**: Weeks 21-28
**Goal**: Enterprise readiness, sustainable growth

---

## Phase 0: Competitive Response Sprint ⚡
**Timeline**: Weeks 1-2 (START IMMEDIATELY)
**Goal**: Close critical gaps, establish clear differentiation

### 0.1 License Differentiation Campaign

| Task | Priority | Status |
|------|----------|--------|
| Add prominent "Apache 2.0" badge to README | 🔴 CRITICAL | ⬜ TODO |
| Blog post: "Why memory-graph is True Open Source" | 🔴 CRITICAL | ⬜ TODO |
| Comparison page: memory-graph vs Cipher licensing | 🔴 CRITICAL | ⬜ TODO |
| Update all marketing to highlight Apache 2.0 | 🔴 HIGH | ⬜ TODO |

**Key Message**: "Cipher uses Elastic License 2.0 which restricts competitive use. memory-graph is Apache 2.0 - use it however you want, forever."

### 0.2 Typed Relationships Showcase

| Task | Priority | Status |
|------|----------|--------|
| Create visual diagram: "35+ relationship types" | 🔴 CRITICAL | ⬜ TODO |
| Demo video: "How relationships enable smarter recall" | 🔴 HIGH | ⬜ TODO |
| Blog post: "Why Graph Relationships Beat Vector Similarity" | 🔴 HIGH | ⬜ TODO |
| Add relationship examples to README | 🔴 HIGH | ⬜ TODO |

**Example Showcase**:
```
Cipher: "Found 5 documents similar to 'timeout'"

memory-graph: "Found TimeoutError which was SOLVED by RetryWithBackoff,
              which DEPENDS_ON ExponentialBackoff, which is USED_IN 
              PaymentService and AuthService"
```

### 0.3 Competitive Comparison Page

| Task | Priority | Status |
|------|----------|--------|
| Create docs/COMPARISON.md | 🔴 CRITICAL | ⬜ TODO |
| Feature matrix: memory-graph vs Cipher vs Graphiti | 🔴 CRITICAL | ⬜ TODO |
| Honest assessment (acknowledge their strengths) | 🔴 HIGH | ⬜ TODO |
| Migration guide from Cipher | 🟡 MEDIUM | ⬜ TODO |

### 0.4 Smithery Marketplace Listing

Cipher is listed on Smithery. We need to be there too.

| Task | Priority | Status |
|------|----------|--------|
| Create Smithery listing | 🔴 CRITICAL | ⬜ TODO |
| Optimize listing description | 🔴 HIGH | ⬜ TODO |
| Add installation via Smithery to README | 🔴 HIGH | ⬜ TODO |

### 0.5 SDK Foundation (Pre-work for SDK Expansion)

Begin laying groundwork for SDK that will differentiate us from Cipher's MCP-only approach.

| Task | Priority | Status |
|------|----------|--------|
| Design SDK API surface | 🔴 HIGH | ⬜ TODO |
| Create memorygraphsdk package stub | 🟡 MEDIUM | ⬜ TODO |
| Document SDK roadmap publicly | 🟡 MEDIUM | ⬜ TODO |

### Phase 0 Success Metrics
- [ ] Apache 2.0 prominently displayed everywhere
- [ ] Comparison page live (including Graphiti)
- [ ] Smithery listing active
- [ ] 2+ blog posts published (license, relationships)
- [ ] SDK roadmap announced

---

## Phase 1: Launch & Community (UPDATED)
**Timeline**: Weeks 3-5
**Goal**: Establish presence, outpace Cipher adoption velocity

### 1.1 Aggressive Messaging Update

| Before | After |
|--------|-------|
| "Lightweight memory server" | "The Python-native memory for AI coding agents" |
| "Graph-based architecture" | "Memory that understands code relationships" |
| Generic value props | Direct Cipher comparison points |

**New README Structure**:
```
1. Hero: "Never re-explain your project" + Apache 2.0 badge
2. "Why memory-graph over alternatives?" (vs Cipher, basic-memory)
3. 30-second install
4. GIF demo
5. "What makes us different" (typed relationships, Python, license)
6. Getting started
```

### 1.2 Visual Demo (Anti-Cipher)

| Task | Priority | Status |
|------|----------|--------|
| Demo showing relationship traversal (Cipher can't do this) | 🔴 CRITICAL | ⬜ TODO |
| Side-by-side: vector search vs graph query | 🔴 HIGH | ⬜ TODO |
| "Problem → Solution" chain demo | 🔴 HIGH | ⬜ TODO |

**Demo Script** (60 seconds):
```
1. "Let's find what solved our timeout issues"
2. memory-graph returns: TimeoutError SOLVED_BY RetryWithBackoff
3. "What else uses this pattern?"
4. Graph traversal shows: Used in 3 services
5. "What caused the original error?"
6. Shows: APIRateLimiting CAUSES TimeoutError
7. End: "Relationships reveal context. Vectors just find similarity."
```

### 1.3 Launch Campaign (Cipher-Aware)

| Task | Priority | Status |
|------|----------|--------|
| HN post emphasizing Apache 2.0 + typed relationships | 🔴 CRITICAL | ⬜ TODO |
| Reddit post with Cipher comparison (respectful) | 🔴 HIGH | ⬜ TODO |
| LinkedIn targeting Python AI/ML developers | 🔴 HIGH | ⬜ TODO |
| Twitter thread: "Why we chose Apache 2.0" | 🔴 HIGH | ⬜ TODO |

**Updated HN Post**:
```
Title: Show HN: memory-graph – Apache 2.0 memory for Claude Code with typed relationships

Comment:
I built memory-graph because AI coding assistants forget everything between sessions.

What makes it different:
- 35+ typed relationships (SOLVES, CAUSES, DEPENDS_ON) - not just vector similarity
- Apache 2.0 license - truly open, no restrictions
- Python-native - fits the AI/ML ecosystem
- 93% test coverage - production quality

When you ask "what solved the timeout issue?", memory-graph doesn't just find 
similar documents. It traces: TimeoutError → SOLVED_BY → RetryWithBackoff → 
USED_IN → PaymentService.

Install:
  pip install memorygraphMCP
  claude mcp add memorygraph

Local SQLite, works offline, your data stays private.

https://github.com/gregorydickson/memory-graph

There's another tool in this space (Cipher) with more stars, but it uses 
Elastic License and is Node.js only. We chose Apache 2.0 and Python deliberately.
```

### 1.4 Community Building (Outpace Cipher)

| Task | Priority | Status |
|------|----------|--------|
| Discord server with active engagement | 🔴 CRITICAL | ⬜ TODO |
| Weekly "office hours" in Discord | 🔴 HIGH | ⬜ TODO |
| Showcase channel for user implementations | 🔴 HIGH | ⬜ TODO |
| Contribution guide for community PRs | 🟡 MEDIUM | ⬜ TODO |

### Phase 1 Success Metrics
- [ ] 200+ GitHub stars (vs Cipher's 3.2K - start closing gap)
- [ ] 100+ Discord members
- [ ] 2,000+ PyPI downloads
- [ ] HN post 100+ points
- [ ] 5+ mentions comparing us favorably to Cipher
- [ ] Smithery listing with 50+ installs

---

## Phase 2: Search & Temporal Model (ELEVATED PRIORITY)
**Timeline**: Weeks 6-9
**Goal**: Close semantic search gap with Cipher, implement bi-temporal tracking (learn from Graphiti)

### Critical Gap Analysis

Cipher's semantic search is a real advantage. Graphiti's temporal model is state-of-the-art (94.8% DMR accuracy). We need to close both gaps while maintaining our lightweight advantage.

### 2.1 Study Graphiti Architecture

Before implementing, study how Graphiti solved these problems.

| Task | Priority | Status |
|------|----------|--------|
| Read Graphiti paper: "Zep: A Temporal Knowledge Graph Architecture" | 🔴 CRITICAL | ⬜ TODO |
| Review Graphiti source code (Apache 2.0, can learn from it) | 🔴 CRITICAL | ⬜ TODO |
| Document key patterns: bi-temporal model, hybrid search, edge invalidation | 🔴 HIGH | ⬜ TODO |
| Identify what we can adopt vs. what's overkill for our use case | 🔴 HIGH | ⬜ TODO |
| Write internal technical spec based on learnings | 🔴 HIGH | ⬜ TODO |

**Key Graphiti concepts to understand:**
- **Bi-temporal model**: `t_valid` (when fact was true) vs. `t_invalid` (when superseded)
- **Episode-based ingestion**: Each memory is tied to a discrete episode with provenance
- **Edge invalidation**: Contradicting facts invalidate old edges, don't delete them
- **Hybrid retrieval**: Semantic + BM25 + graph traversal without LLM calls at query time

### 2.2 Implement Bi-Temporal Tracking

Adopt Graphiti's temporal model for our schema.

| Task | Priority | Status |
|------|----------|--------|
| Design bi-temporal schema for memory-graph | 🔴 CRITICAL | ⬜ TODO |
| Add `valid_from` timestamp to relationships | 🔴 CRITICAL | ⬜ TODO |
| Add `valid_until` timestamp to relationships (NULL = still valid) | 🔴 CRITICAL | ⬜ TODO |
| Add `recorded_at` timestamp (when we learned the fact) | 🔴 CRITICAL | ⬜ TODO |
| Implement edge invalidation (mark old facts invalid on contradiction) | 🔴 HIGH | ⬜ TODO |
| Add point-in-time query support ("what did we know on date X?") | 🟡 MEDIUM | ⬜ TODO |
| Migration script for existing databases | 🔴 HIGH | ⬜ TODO |

**Bi-Temporal Schema Design:**
```sql
-- Current: relationships table
CREATE TABLE relationships (
    id TEXT PRIMARY KEY,
    from_entity_id TEXT,
    to_entity_id TEXT,
    relationship_type TEXT,
    created_at TIMESTAMP,
    -- ... existing fields
);

-- New: bi-temporal relationships table
CREATE TABLE relationships (
    id TEXT PRIMARY KEY,
    from_entity_id TEXT,
    to_entity_id TEXT,
    relationship_type TEXT,
    
    -- Bi-temporal fields (inspired by Graphiti)
    valid_from TIMESTAMP NOT NULL,      -- When the fact became true
    valid_until TIMESTAMP,              -- When the fact stopped being true (NULL = still valid)
    recorded_at TIMESTAMP NOT NULL,     -- When we learned this fact
    invalidated_by TEXT,                -- ID of relationship that superseded this one
    
    -- Existing fields
    created_at TIMESTAMP,
    -- ...
);

-- Index for temporal queries
CREATE INDEX idx_relationships_temporal ON relationships(valid_from, valid_until);
```

**Use Cases Enabled:**
- "What solutions were we using before we switched to Redis?"
- "Show me how our understanding evolved over time"
- "What did we know about this problem last month?"

### 2.3 Embedding Support (Core)

| Task | Priority | Status |
|------|----------|--------|
| Add optional sentence-transformers dependency | 🔴 CRITICAL | ⬜ TODO |
| Implement embedding generation for entities | 🔴 CRITICAL | ⬜ TODO |
| Implement embedding generation for observations | 🔴 CRITICAL | ⬜ TODO |
| SQLite vector storage (sqlite-vec extension) | 🔴 CRITICAL | ⬜ TODO |
| Cosine similarity search | 🔴 CRITICAL | ⬜ TODO |

**Implementation**:
```python
# Optional embedding support
class EmbeddingProvider:
    def __init__(self, model: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model)
    
    def embed(self, texts: List[str]) -> np.ndarray:
        return self.model.encode(texts, normalize_embeddings=True)
```

### 2.4 Hybrid Search (Our Differentiator)

Combine vectors WITH graph relationships (like Graphiti, but coding-specific).

| Task | Priority | Status |
|------|----------|--------|
| Implement hybrid search algorithm | 🔴 CRITICAL | ⬜ TODO |
| Semantic results enriched with relationships | 🔴 CRITICAL | ⬜ TODO |
| Add BM25 keyword search component | 🔴 HIGH | ⬜ TODO |
| Configurable semantic vs. graph weighting | 🔴 HIGH | ⬜ TODO |
| "Why this result?" explanations | 🟡 MEDIUM | ⬜ TODO |
| No LLM calls during retrieval (like Graphiti) | 🔴 HIGH | ⬜ TODO |

**Hybrid Search Flow**:
```
User: "timeout issues"
         │
         ▼
┌─────────────────────────────────────────┐
│         HYBRID SEARCH ENGINE            │
│    (Inspired by Graphiti approach)      │
├─────────────────┬───────────────────────┤
│  Vector Search  │   Graph Enrichment    │
│  + BM25 Keyword │   (our advantage)     │
├─────────────────┼───────────────────────┤
│ TimeoutError    │ SOLVED_BY RetryBackoff│
│ ConnectionError │ CAUSED_BY RateLimit   │
│ APITimeout      │ USED_IN PaymentService│
└─────────────────┴───────────────────────┘
         │
         ▼
Result: "TimeoutError (semantic match) was SOLVED_BY 
        RetryWithBackoff, which DEPENDS_ON ExponentialBackoff"
        
        + Temporal context: "This solution has been valid since 2024-01-15"
```

### 2.5 Search UX Improvements

| Task | Priority | Status |
|------|----------|--------|
| Natural language query support | 🔴 HIGH | ⬜ TODO |
| Auto-suggest completions | 🟡 MEDIUM | ⬜ TODO |
| Search history | 🟡 MEDIUM | ⬜ TODO |
| Saved searches | 🟢 LOW | ⬜ TODO |

### 2.6 Marketing: "Vectors + Relationships + Time"

| Task | Priority | Status |
|------|----------|--------|
| Blog: "Why Hybrid Search Beats Pure Vectors" | 🔴 HIGH | ⬜ TODO |
| Blog: "Temporal Memory: Know What Changed and When" | 🔴 HIGH | ⬜ TODO |
| Demo video: hybrid search in action | 🔴 HIGH | ⬜ TODO |
| Update comparison page with search + temporal capabilities | 🔴 HIGH | ⬜ TODO |

### Phase 2 Success Metrics
- [ ] Bi-temporal schema implemented and documented
- [ ] Semantic search functional and documented
- [ ] Hybrid search demo video published
- [ ] <100ms p95 latency for hybrid queries
- [ ] Point-in-time queries working
- [ ] User feedback: "search is as good or better than Cipher"
- [ ] 500+ GitHub stars

---

## Phase 3: Cloud Launch (ACCELERATED)
**Timeline**: Weeks 10-14
**Goal**: Launch memorygraph.dev before Byterover consolidates market

### Urgency Note

Byterover.dev is already live. Every week we delay, they gain more users and market mindshare. We must launch a competitive cloud offering ASAP.

### 3.1 Cloud Infrastructure (From Existing Workplan)

Reference: Cloud platform workplan document

| Task | Priority | Status |
|------|----------|--------|
| GCP project setup (memorygraph-prod) | 🔴 CRITICAL | ⬜ TODO |
| Cloud SQL PostgreSQL instance | 🔴 CRITICAL | ⬜ TODO |
| FalkorDB Cloud cluster | 🔴 CRITICAL | ⬜ TODO |
| Auth API (FastAPI on Cloud Run) | 🔴 CRITICAL | ⬜ TODO |
| Graph API (FastAPI on Cloud Run) | 🔴 CRITICAL | ⬜ TODO |

### 3.2 Competitive Pricing

Match or beat Byterover's pricing (if known). Our target:

| Tier | Price | vs. Competitor |
|------|-------|----------------|
| Free | $0 | Match Cipher free tier |
| Pro | $8/month | Competitive |
| Team | $12/user/month | Competitive |

### 3.3 Landing Page (memorygraph.dev)

| Task | Priority | Status |
|------|----------|--------|
| Domain registration | 🔴 CRITICAL | ⬜ TODO |
| Landing page with comparison section | 🔴 CRITICAL | ⬜ TODO |
| "Why Choose memory-graph" (vs alternatives) | 🔴 HIGH | ⬜ TODO |
| Pricing page | 🔴 HIGH | ⬜ TODO |

**Landing Page Must Include**:
1. Apache 2.0 badge prominently displayed
2. "35+ typed relationships" highlight
3. "Bi-temporal tracking" as advanced feature
4. Side-by-side comparison with "other tools"
5. Python-native messaging
6. Clear pricing vs. alternatives

### 3.4 SDK Launch (Differentiation from Cipher)

Cipher is MCP-only. Our SDK expands to LangChain, CrewAI, etc.

| Task | Priority | Status |
|------|----------|--------|
| memorygraphsdk core package | 🔴 HIGH | ⬜ TODO |
| LangChain integration | 🔴 HIGH | ⬜ TODO |
| CrewAI integration | 🔴 HIGH | ⬜ TODO |
| Publish to PyPI | 🔴 HIGH | ⬜ TODO |

**Key Message**: "memory-graph works everywhere - MCP, LangChain, CrewAI, and more. Not locked into one protocol."

### Phase 3 Success Metrics
- [ ] memorygraph.dev live
- [ ] 50+ Pro subscribers
- [ ] SDK published with 2+ framework integrations
- [ ] $400+ MRR
- [ ] 1,000+ GitHub stars
- [ ] Feature parity with Byterover cloud (core features)

---

## Phase 4: Team Features
**Timeline**: Weeks 15-20
**Goal**: Match Cipher's workspace memory, add unique value

### 4.1 Match Cipher's Workspace Memory

Cipher has "workspace memory" for teams. We need parity.

| Task | Priority | Status |
|------|----------|--------|
| Shared team memory namespace | 🔴 CRITICAL | ⬜ TODO |
| Team member management | 🔴 HIGH | ⬜ TODO |
| Personal vs. team memory toggle | 🔴 HIGH | ⬜ TODO |
| Team-wide search | 🔴 HIGH | ⬜ TODO |

### 4.2 Beat Cipher with Better Attribution

Cipher has basic team sharing. We can add:

| Task | Priority | Status |
|------|----------|--------|
| Knowledge attribution (who discovered what) | 🔴 HIGH | ⬜ TODO |
| Team activity feed | 🟡 MEDIUM | ⬜ TODO |
| "Trending solutions" in team | 🟡 MEDIUM | ⬜ TODO |
| Expertise mapping (who knows what) | 🟢 LOW | ⬜ TODO |

### 4.3 RBAC (Match Cipher)

| Task | Priority | Status |
|------|----------|--------|
| Role-based permissions | 🔴 HIGH | ⬜ TODO |
| Admin controls | 🔴 HIGH | ⬜ TODO |
| Audit logging | 🟡 MEDIUM | ⬜ TODO |

### Phase 4 Success Metrics
- [ ] Team tier launched
- [ ] 10+ team subscriptions
- [ ] Feature parity with Cipher workspace memory
- [ ] $1,500+ MRR
- [ ] 2,000+ GitHub stars

---

## Phase 5: Scale & Enterprise
**Timeline**: Weeks 21-28
**Goal**: Enterprise readiness, sustainable market position

### 5.1 Enterprise Features (Beat Cipher to Enterprise)

Cipher's Elastic License may deter some enterprises. Opportunity!

| Task | Priority | Status |
|------|----------|--------|
| SSO (SAML/OIDC) | 🔴 HIGH | ⬜ TODO |
| Self-hosted deployment option | 🔴 HIGH | ⬜ TODO |
| Audit logging | 🔴 HIGH | ⬜ TODO |
| SOC 2 Type I | 🟡 MEDIUM | ⬜ TODO |

### 5.2 Expand SDK Ecosystem

| Task | Priority | Status |
|------|----------|--------|
| AutoGen integration | 🔴 HIGH | ⬜ TODO |
| LlamaIndex integration | 🔴 HIGH | ⬜ TODO |
| OpenAI Agents SDK integration | 🟡 MEDIUM | ⬜ TODO |
| JavaScript/TypeScript SDK | 🟡 MEDIUM | ⬜ TODO |

### 5.3 Advanced Temporal Features

Build on Phase 2 bi-temporal foundation.

| Task | Priority | Status |
|------|----------|--------|
| Time-travel queries in UI | 🟡 MEDIUM | ⬜ TODO |
| Knowledge evolution visualization | 🟡 MEDIUM | ⬜ TODO |
| Automated fact decay/expiration | 🟢 LOW | ⬜ TODO |

### Phase 5 Success Metrics
- [ ] 3+ enterprise customers
- [ ] $5,000+ MRR
- [ ] 3,000+ GitHub stars (closing gap with Cipher)
- [ ] SDK used by 500+ developers
- [ ] 1+ enterprise case study

---

## Competitive Overtake Strategy

### GitHub Stars Gap Analysis

| Timeline | Cipher (projected) | Graphiti (projected) | memory-graph (target) |
|----------|-------------------|---------------------|----------------------|
| Now | 3,200 | 20,000 | ~100 |
| 3 months | 4,000 | 22,000 | 500 |
| 6 months | 5,000 | 25,000 | 1,500 |
| 12 months | 7,000 | 30,000 | 4,000 |
| 18 months | 9,000 | 35,000 | 8,000 |

**Strategy**: We won't beat Graphiti on stars (they're general-purpose with massive reach). We can beat Cipher by being better for coding-specific use cases. Key differentiators:

1. **License** - Apache 2.0 wins for enterprises (vs Cipher's Elastic)
2. **Ecosystem** - SDK + framework integrations (Cipher is MCP-only)
3. **Relationships** - 35+ typed relationships (our unique technical advantage)
4. **Python** - AI/ML ecosystem alignment
5. **Temporal** - Bi-temporal tracking (learning from Graphiti, but lightweight)
6. **Coding-specific** - Purpose-built vs general-purpose (vs Graphiti)

### Win Scenarios

**Scenario 1: Enterprise Wins**
- Cipher's Elastic License blocks enterprise adoption
- memory-graph's Apache 2.0 wins enterprise deals
- 3-5 enterprise customers = $10K+ MRR

**Scenario 2: SDK Ecosystem Wins**
- Cipher stays MCP-only
- memory-graph SDK captures LangChain/CrewAI users
- Framework integrations drive adoption

**Scenario 3: Relationship Quality Wins**
- Users realize vectors aren't enough
- Typed relationships prove more useful
- Word of mouth: "memory-graph actually understands my code"

**Scenario 4: Coding-Specific Focus Wins**
- Graphiti is general-purpose, we're coding-specific
- Developers prefer purpose-built tools
- "memory-graph is made for developers, by developers"

**Scenario 5: Community Wins**
- More responsive, engaged community
- Better documentation
- More tutorials and examples
- Users feel heard and supported

---

## Immediate Action Items

### This Week (Phase 0)
- [ ] Add Apache 2.0 badge to README
- [ ] Create COMPARISON.md with Cipher + Graphiti feature matrix
- [ ] Submit Smithery marketplace listing
- [ ] Draft "Why Apache 2.0" blog post
- [ ] Create relationship visualization diagram

### Next Week
- [ ] Publish comparison blog post
- [ ] Update all marketing materials with competitive messaging
- [ ] Begin Graphiti architecture study (read paper, review code)
- [ ] Set up competitive monitoring (track Cipher and Graphiti releases)

### This Month
- [ ] Complete Phase 0 competitive response
- [ ] Launch revised marketing campaign
- [ ] Complete Graphiti technical study document
- [ ] Begin Phase 2 bi-temporal schema design
- [ ] Publish SDK roadmap

---

## Risk Assessment Update

### Competitive Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Cipher gains more market share | High | High | Accelerate cloud launch, emphasize differentiation |
| Cipher adds typed relationships | Medium | High | Move fast, build ecosystem moat |
| Cipher switches to permissive license | Low | Medium | Focus on technical differentiation |
| Cipher raises funding | Medium | High | Bootstrap efficiently, focus on profitability |
| Graphiti adds coding-specific features | Low | Medium | Stay focused on dev workflow, move faster |

### Mitigation Priorities
1. **Speed**: Launch cloud ASAP
2. **Differentiation**: Typed relationships + SDK ecosystem + bi-temporal
3. **License**: Apache 2.0 messaging everywhere
4. **Community**: Build stronger, more engaged community
5. **Learn**: Study Graphiti's proven patterns, adopt what makes sense

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Dec 2025 | Gregory Dickson | Initial roadmap |
| 2.0 | Dec 2025 | Gregory Dickson | Value-focused refactor |
| 2.1 | Dec 2025 | Gregory Dickson | Semantic search strategy |
| 3.0 | Dec 2025 | Gregory Dickson | **COMPETITIVE RESPONSE**: Added Phase 0 for Byterover Cipher response |
| 3.1 | Dec 2025 | Gregory Dickson | **GRAPHITI ANALYSIS**: Added Zep/Graphiti as competitor, added bi-temporal tracking to Phase 2, renamed Phase 2 to "Search & Temporal Model", added Graphiti architecture study tasks |

---

*This roadmap is a living document updated based on competitive dynamics, user feedback, and market conditions.*
