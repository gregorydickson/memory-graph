# Smithery HTTP Transport Analysis & Recommendations

**Date:** 2025-11-29
**Version:** 1.0
**Status:** Final Recommendation

---

## Executive Summary

**RECOMMENDATION: DO NOT IMPLEMENT** - Smithery distribution is not critical enough to justify the development and maintenance effort required for HTTP transport support.

**Key Findings:**
- HTTP transport implementation is **technically feasible** with moderate effort (2-3 days)
- MCP Python SDK already provides `StreamableHTTPServerTransport` class
- However, MemoryGraph already has **successful distribution via PyPI** and works perfectly with Claude Code, Cursor, and all stdio-based MCP clients
- Smithery's market position and user base do not warrant this effort at this time
- Risk of breaking existing functionality vs minimal benefit

---

## 1. Technical Feasibility Assessment

### Current State Analysis

**Existing Implementation:**
- **Transport:** stdio via `mcp.server.stdio.stdio_server()` (line 846 in server.py)
- **Entry Point:** `memorygraph` CLI command
- **Distribution:** PyPI package `memorygraphMCP` v0.5.2
- **Architecture:** Clean separation between server logic and transport layer
- **Works With:** Claude Code, Cursor, and all stdio-based MCP clients

**Current Code Structure:**
```python
# src/memorygraph/server.py:837-859
async def main():
    """Main entry point for the MCP server."""
    server = ClaudeMemoryServer()

    try:
        await server.initialize()

        # Currently uses stdio transport
        async with stdio_server() as (read_stream, write_stream):
            await server.server.run(
                read_stream,
                write_stream,
                InitializationOptions(...)
            )
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
    finally:
        await server.cleanup()
```

### MCP Python SDK Capabilities

**Available Transport Modules:**
```python
from mcp.server.sse import SseServerTransport  # Legacy SSE (deprecated)
from mcp.server.streamable_http import StreamableHTTPServerTransport  # Recommended
```

**SDK Support:** ✅ **CONFIRMED**
- MCP Python SDK v1.8.0+ includes `StreamableHTTPServerTransport`
- Official support for HTTP transport via Starlette/FastAPI integration
- CORS middleware built-in
- Session management included

### Smithery Requirements

**Configuration Requirements:**
```yaml
# smithery.yaml
runtime: "container"
build:
  dockerfile: "Dockerfile"
  dockerBuildPath: "."
startCommand:
  type: "http"  # REQUIRED - stdio blocked for hosted deployments
```

**Python Server Requirements:**
1. Listen on `PORT` environment variable (Smithery sets to 8081)
2. Use `mcp.streamable_http_app()` or manual StreamableHTTPServerTransport
3. Add CORS middleware with specific headers: `mcp-session-id`, `mcp-protocol-version`
4. Provide Dockerfile for containerization

**Transport Support Matrix:**
| Language   | STDIO | HTTP | Smithery Support |
|------------|-------|------|------------------|
| TypeScript | ✅    | ✅   | Both supported   |
| Python     | ✅    | ✅   | HTTP only        |

**Important Note:** Smithery is discontinuing STDIO support on **September 7, 2025**.

---

## 2. Architecture Assessment

### Current Server Architecture

**Strengths:**
- Clean separation: `ClaudeMemoryServer` class is transport-agnostic
- All tool handlers are async methods independent of transport
- Database layer (`MemoryDatabase`) has no transport coupling
- Configuration via `Config` class is environment-based

**Transport Coupling Analysis:**
```
server.py (Transport Layer)
    ├─ main() function - STDIO transport initialization ← ONLY COUPLING POINT
    │
    └─ ClaudeMemoryServer class - Transport agnostic ✓
        ├─ __init__() - Register handlers
        ├─ initialize() - Database setup
        ├─ _register_handlers() - MCP protocol handlers
        ├─ _handle_store_memory() - Business logic
        ├─ _handle_get_memory() - Business logic
        └─ ... (all handler methods transport-agnostic)
```

**Verdict:** ✅ **Excellent architecture for multi-transport support**
- Only the `main()` function (23 lines) is transport-specific
- 99% of codebase is reusable

### Integration Patterns

**Option A: Dual Transport (Recommended if implementing)**

```python
# src/memorygraph/server.py

async def main_stdio():
    """STDIO transport entry point (existing)."""
    server = ClaudeMemoryServer()
    await server.initialize()

    async with stdio_server() as (read_stream, write_stream):
        await server.server.run(read_stream, write_stream, ...)

    await server.cleanup()


async def main_http(port: int = 8081):
    """HTTP transport entry point (new)."""
    from mcp.server.streamable_http import StreamableHTTPServerTransport
    from starlette.middleware.cors import CORSMiddleware
    from starlette.applications import Starlette
    from starlette.routing import Route, Mount
    import uvicorn

    server = ClaudeMemoryServer()
    await server.initialize()

    transport = StreamableHTTPServerTransport()

    async def handle_messages(request):
        async with transport.connect(request.scope, request.receive, request._send) as streams:
            await server.server.run(streams[0], streams[1], ...)

    app = Starlette(routes=[
        Route("/messages", endpoint=handle_messages, methods=["GET", "POST"])
    ])

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["mcp-session-id", "mcp-protocol-version"],
        max_age=86400,
    )

    uvicorn.run(app, host="0.0.0.0", port=port)
```

**CLI Entry Points:**
```python
# pyproject.toml
[project.scripts]
memorygraph = "memorygraph.cli:main"              # STDIO (existing)
memorygraph-http = "memorygraph.cli:main_http"    # HTTP (new)
```

**Option B: FastMCP Wrapper (Simpler but less control)**

```python
# Alternative using FastMCP helpers
from mcp.server.fastmcp import FastMCP
import uvicorn

def main_http():
    mcp = FastMCP("claude-memory")

    # Register all tools programmatically
    # ... (convert existing handlers to FastMCP decorators)

    app = mcp.streamable_http_app()

    # Add CORS
    app.add_middleware(...)

    port = int(os.environ.get("PORT", 8081))
    uvicorn.run(app, host="0.0.0.0", port=port)
```

**Trade-off:** FastMCP is simpler but requires refactoring existing handler architecture.

---

## 3. Implementation Effort Estimation

### Option A: Dual Transport (Native MCP SDK)

**Development Tasks:**
1. Create `main_http()` function in server.py (4 hours)
2. Add HTTP CLI entry point in cli.py (2 hours)
3. Create Dockerfile for Smithery deployment (3 hours)
4. Update smithery.yaml configuration (1 hour)
5. Add `uvicorn` and `starlette` dependencies (1 hour)
6. Testing both transports (6 hours)
7. Documentation updates (3 hours)

**Total Effort:** 20 hours (~2.5 days)

**Risk Level:** Medium
- Need to ensure both transports work correctly
- Potential for subtle bugs in session management
- CORS configuration can be tricky

### Option B: FastMCP Wrapper

**Development Tasks:**
1. Refactor handlers to FastMCP decorators (8 hours)
2. Implement HTTP server with FastMCP (4 hours)
3. Create Dockerfile (3 hours)
4. Update smithery.yaml (1 hour)
5. Testing (6 hours)
6. Documentation (3 hours)

**Total Effort:** 25 hours (~3 days)

**Risk Level:** Medium-High
- Requires architectural refactoring
- May break existing stdio functionality
- Less familiar pattern for the codebase

### Option C: Wrapper Service (Bridge Pattern)

**Development Tasks:**
1. Create separate HTTP wrapper service (6 hours)
2. Implement stdio <-> HTTP bridge (8 hours)
3. Docker compose setup (4 hours)
4. Testing (6 hours)
5. Documentation (3 hours)

**Total Effort:** 27 hours (~3.5 days)

**Risk Level:** High
- Additional complexity layer
- Performance overhead
- More moving parts to maintain

**RECOMMENDATION:** If implementing, use **Option A: Dual Transport**
- Cleanest separation
- Preserves existing stdio functionality
- Leverages MCP SDK properly
- Minimal risk to existing users

---

## 4. Alternative Approaches Comparison

### Approach Matrix

| Approach | Dev Effort | Risk | Maintenance | Pros | Cons |
|----------|-----------|------|-------------|------|------|
| **Option A: Dual Transport** | 2.5 days | Medium | Low | Clean, SDK-native, both transports work | Need to maintain two entry points |
| **Option B: FastMCP Wrapper** | 3 days | Medium-High | Medium | Simpler HTTP code | Requires refactoring, may break stdio |
| **Option C: Bridge Service** | 3.5 days | High | High | Isolates concerns | Complex, performance overhead |
| **Option D: Wait/Skip** | 0 days | None | None | No effort, no risk | No Smithery distribution |

### Distribution Channels Comparison

| Channel | Status | Users | Effort to Maintain |
|---------|--------|-------|-------------------|
| **PyPI** | ✅ Active | High (Claude Code, Cursor, etc.) | Low |
| **GitHub Releases** | ✅ Active | Medium | Low |
| **Direct Install** | ✅ Active | High | None |
| **Smithery** | ❌ Blocked | Unknown (low estimate) | High |

---

## 5. Trade-offs Analysis

### Option A: Implement Dual Transport

**Pros:**
- ✅ Enables Smithery distribution
- ✅ Future-proof for HTTP-based clients
- ✅ Demonstrates technical capability
- ✅ Clean architecture using MCP SDK
- ✅ Both transports supported

**Cons:**
- ❌ 2.5 days development effort
- ❌ Increased maintenance burden (two code paths)
- ❌ Testing complexity (need to test both transports)
- ❌ Additional dependencies (uvicorn, starlette)
- ❌ Larger Docker images
- ❌ Need to document both usage patterns
- ❌ Smithery user base is unknown/potentially small

### Option D: Wait/Skip Smithery

**Pros:**
- ✅ Zero development effort
- ✅ No maintenance burden increase
- ✅ No risk to existing functionality
- ✅ PyPI distribution already successful
- ✅ Focus on core features instead
- ✅ Can revisit if Smithery becomes critical

**Cons:**
- ❌ No presence on Smithery marketplace
- ❌ Miss potential discoverability
- ❌ Can't serve Smithery users (if any)

---

## 6. Final Recommendation

### Recommendation: **DO NOT IMPLEMENT HTTP TRANSPORT AT THIS TIME**

**Rationale:**

1. **Existing Distribution is Sufficient**
   - PyPI package works perfectly with Claude Code (primary use case)
   - Cursor support via stdio
   - Direct installation via `uvx memorygraphMCP`
   - GitHub releases for version tracking

2. **Unknown ROI**
   - Smithery user base is unknown
   - No data on potential users blocked by stdio requirement
   - 2.5 days effort could be spent on features that benefit all users
   - Maintenance burden ongoing for uncertain benefit

3. **Alternative Path Available**
   - Users can run MemoryGraph locally via stdio (which is better anyway)
   - Smithery discontinuing STDIO in Sept 2025, but that's 9 months away
   - Can revisit decision if Smithery becomes critical
   - If user demand emerges, then implement

4. **Technical Debt Consideration**
   - Adding HTTP transport is ~800-1000 LOC
   - Two code paths to maintain
   - Testing burden doubles
   - Documentation overhead increases
   - All for uncertain benefit

5. **Focus on Core Value**
   - Better to improve memory features
   - Enhance intelligence tools
   - Improve SQLite backend performance
   - Add features all users benefit from

### When to Revisit This Decision

**Revisit IF:**
- [ ] 5+ users request Smithery deployment specifically
- [ ] Smithery user base grows significantly (evidence of traction)
- [ ] Competitor MCP servers gain adoption via Smithery
- [ ] HTTP transport becomes useful for other use cases
- [ ] Client requests HTTP transport for their integration

**Until Then:**
- ✅ Focus on PyPI distribution (working perfectly)
- ✅ Improve core memory features
- ✅ Enhance documentation for stdio usage
- ✅ Monitor Smithery ecosystem growth

---

## 7. Implementation Plan (If Decision Changes)

### Phase 1: Preparation (Day 1)
- [ ] Add `uvicorn>=0.27.0` and `starlette>=0.36.0` to dependencies
- [ ] Create `src/memorygraph/transports/` module
- [ ] Move stdio logic to `transports/stdio.py`
- [ ] Create `transports/http.py` for HTTP transport

### Phase 2: HTTP Transport (Day 2)
- [ ] Implement `StreamableHTTPServerTransport` integration
- [ ] Add CORS middleware configuration
- [ ] Create `main_http()` entry point
- [ ] Add `memorygraph-http` CLI command
- [ ] Create Dockerfile with multi-stage build

### Phase 3: Configuration (Day 2)
- [ ] Update smithery.yaml to use HTTP transport
- [ ] Add PORT environment variable support
- [ ] Create docker-compose.http.yml example
- [ ] Document HTTP deployment

### Phase 4: Testing (Day 3)
- [ ] Test stdio transport (ensure no regression)
- [ ] Test HTTP transport locally
- [ ] Test with MCP Inspector
- [ ] Test Smithery deployment
- [ ] Integration tests for both transports

### Phase 5: Documentation (Day 3)
- [ ] Update README with both transport options
- [ ] Create DEPLOYMENT_HTTP.md guide
- [ ] Update smithery.yaml documentation
- [ ] Add architecture decision record (ADR)

### Phase 6: Release (Day 3)
- [ ] Version bump to 0.6.0
- [ ] Update CHANGELOG.md
- [ ] Create GitHub release
- [ ] Publish to PyPI
- [ ] Test Smithery deployment

---

## 8. References

### MCP Protocol Documentation
- [MCP Transports](https://modelcontextprotocol.io/docs/concepts/transports)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [StreamableHTTP Transport](https://github.com/modelcontextprotocol/python-sdk/blob/main/src/mcp/server/streamable_http.py)

### Smithery Documentation
- [Smithery Build Docs](https://smithery.ai/docs/build)
- [Python Custom Container](https://smithery.ai/docs/cookbooks/python_custom_container)

### Implementation Examples
- [Ragie FastAPI SSE Server](https://www.ragie.ai/blog/building-a-server-sent-events-sse-mcp-server-with-fastapi)
- [Starlette Client-Server Example](https://github.com/pamelafox/python-mcp-starlette-client-server)

### Technical Analysis
- **Current Transport:** stdio (line 846, server.py)
- **Server Class:** ClaudeMemoryServer (transport-agnostic)
- **Dependencies:** mcp>=1.0.0, pydantic>=2.0.0
- **Entry Point:** memorygraph CLI command
- **PyPI Package:** memorygraphMCP v0.5.2

---

## Appendix A: Effort vs Benefit Analysis

### Quantitative Comparison

| Metric | Current (stdio) | With HTTP | Delta |
|--------|----------------|-----------|-------|
| **Development Days** | 0 (done) | 2.5 | +2.5 days |
| **Lines of Code** | ~2500 | ~3500 | +1000 LOC |
| **Dependencies** | 4 core | 6 core | +2 deps |
| **Supported Clients** | stdio-based | stdio + HTTP | +HTTP |
| **Maintenance Burden** | Low | Medium | +Medium |
| **Docker Image Size** | N/A | ~200MB | +200MB |
| **Testing Complexity** | Medium | High | +High |
| **Potential Users** | All MCP clients | +Smithery | Unknown |

### Cost-Benefit Verdict

**COST > BENEFIT** at this time.

**Breakeven Point:** If Smithery brings 10+ active users, the effort becomes justified.

**Current Evidence:** No user requests for Smithery deployment, no data on potential users.

---

## Appendix B: Decision Record

**Architecture Decision Record (ADR)**

**Title:** Defer HTTP Transport Implementation for Smithery
**Date:** 2025-11-29
**Status:** Accepted
**Deciders:** Architecture Review

### Context
Smithery.ai requires HTTP transport for hosted MCP server deployments. MemoryGraph currently uses stdio transport exclusively, which works perfectly with Claude Code, Cursor, and all stdio-based MCP clients.

### Decision
We will NOT implement HTTP transport support at this time.

### Consequences

**Positive:**
- Zero development effort required
- No risk to existing functionality
- No increased maintenance burden
- Team can focus on core features
- PyPI distribution remains primary channel

**Negative:**
- Cannot distribute via Smithery
- Miss potential discoverability on Smithery marketplace
- Cannot serve Smithery-exclusive users (if any exist)

**Mitigation:**
- Monitor for user requests
- Track Smithery ecosystem growth
- Revisit decision quarterly
- Document decision for transparency

### Review Date
**2025-03-01** (quarterly review)

---

**END OF ANALYSIS**
