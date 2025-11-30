# Smithery HTTP Transport - Decision Summary

**Date:** 2025-11-29
**Status:** ❌ **NOT RECOMMENDED**
**Review Date:** 2025-03-01

---

## TL;DR

**DO NOT implement HTTP transport for Smithery at this time.**

- **Effort:** 2.5 days development + ongoing maintenance
- **Benefit:** Unknown/minimal (no evidence of demand)
- **Current State:** PyPI distribution works perfectly for all primary use cases
- **Risk:** Adding complexity for uncertain ROI

---

## Quick Facts

### Technical Feasibility
✅ **FEASIBLE** - MCP Python SDK has `StreamableHTTPServerTransport`
✅ **LOW RISK** - Architecture is transport-agnostic
✅ **CLEAN PATTERN** - Can add without breaking stdio

### Business Case
❌ **NO EVIDENCE OF DEMAND** - Zero user requests
❌ **UNKNOWN USER BASE** - Smithery adoption unclear
❌ **EXISTING SOLUTION WORKS** - PyPI + stdio perfect for Claude Code

---

## Why Not?

1. **PyPI Distribution is Sufficient**
   - Works with Claude Code (primary target)
   - Works with Cursor
   - Easy install: `uvx memorygraphMCP`

2. **Unknown ROI**
   - No data on potential Smithery users
   - No requests for Smithery deployment
   - 2.5 days better spent on features

3. **Maintenance Burden**
   - Two transport code paths
   - Double testing effort
   - More dependencies
   - Ongoing support complexity

---

## When to Revisit

Revisit this decision IF:

- [ ] **5+ users** explicitly request Smithery deployment
- [ ] **Evidence** that competitors gain adoption via Smithery
- [ ] **Client request** for HTTP transport integration
- [ ] **Other use case** for HTTP transport emerges
- [ ] Smithery ecosystem shows significant growth

---

## If You Need to Implement

See full analysis: [`SMITHERY_HTTP_TRANSPORT_ANALYSIS.md`](./SMITHERY_HTTP_TRANSPORT_ANALYSIS.md)

**Recommended Approach:** Dual Transport (Option A)
- Add `main_http()` function alongside existing `main_stdio()`
- Use native MCP SDK `StreamableHTTPServerTransport`
- Create separate CLI entry point: `memorygraph-http`
- Effort: ~20 hours (2.5 days)
- Risk: Medium (isolated changes)

**Code Pattern:**
```python
from mcp.server.streamable_http import StreamableHTTPServerTransport
import uvicorn

async def main_http(port: int = 8081):
    server = ClaudeMemoryServer()
    await server.initialize()

    transport = StreamableHTTPServerTransport()
    # ... configure Starlette app with CORS

    uvicorn.run(app, host="0.0.0.0", port=port)
```

---

## Current Status

| Distribution | Status | Priority |
|-------------|--------|----------|
| PyPI | ✅ Active | High |
| GitHub Releases | ✅ Active | Medium |
| Direct Install (uvx) | ✅ Active | High |
| Smithery | ❌ Blocked by stdio | Low |

---

## Architecture Notes

**Transport Coupling:** Minimal ✅
- Only `main()` function uses stdio (23 lines)
- `ClaudeMemoryServer` class is 100% transport-agnostic
- Easy to add HTTP transport without refactoring

**If Implementing:**
- Add `uvicorn>=0.27.0`, `starlette>=0.36.0` to dependencies
- Create `transports/http.py` module
- Update `smithery.yaml` to `type: http`
- Provide Dockerfile listening on PORT env var

---

## Full Analysis

For complete technical assessment, effort estimation, and implementation plan:

📄 **[SMITHERY_HTTP_TRANSPORT_ANALYSIS.md](./SMITHERY_HTTP_TRANSPORT_ANALYSIS.md)**

Sections include:
1. Technical Feasibility Assessment
2. Architecture Assessment
3. Implementation Effort Estimation
4. Alternative Approaches Comparison
5. Trade-offs Analysis
6. Final Recommendation
7. Implementation Plan (if decision changes)
8. References & ADR

---

**Next Review:** 2025-03-01
**Owner:** Architecture/Product
**Related Docs:**
- [Full Analysis](./SMITHERY_HTTP_TRANSPORT_ANALYSIS.md)
- [Current Implementation](../src/memorygraph/server.py)
- [CLI Entry Point](../src/memorygraph/cli.py)
