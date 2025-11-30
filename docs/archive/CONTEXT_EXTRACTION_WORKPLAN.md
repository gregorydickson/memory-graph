# Context Extraction Workplan

> **STATUS**: Phase 1 COMPLETE (November 30, 2025)
> **CONSOLIDATED**: Active tasks moved to `/docs/WORKPLAN.md`
> **ARCHIVE**: See `/docs/archive/CONTEXT_EXTRACTION_PHASE1_COMPLETION.md` for detailed completion report


## Phase 2: Structured Query Support (Future Enhancement)

**Prerequisites**: Phase 1 complete ✅
**Status**: Deferred - moved to main workplan

### 2.1 Add Structured Context Filtering

- [ ] Add new methods to `MemoryDatabase` class:
  ```python
  async def search_relationships_by_context(
      self,
      scope: Optional[str] = None,
      conditions: Optional[List[str]] = None,
      components: Optional[List[str]] = None,
      temporal: Optional[str] = None
  ) -> List[Relationship]:
      """Search relationships by structured context fields."""
  ```

- [ ] Implementation approach:
  - Parse all relationship contexts from JSON
  - Filter in-memory (SQLite) or use JSON queries (Memgraph/Neo4j)
  - Return matching relationships

### 2.2 Add MCP Tool for Context Search

- [ ] Add new tool to server: `search_relationships_by_context`
  - Schema defines filters: scope, conditions, components, etc.
  - Calls new database method
  - Returns formatted results

### 2.3 Testing - Structured Queries

- [ ] Test filtering by each structure field:
  - Find all "partial" scope relationships
  - Find relationships with specific conditions
  - Find relationships mentioning specific components

- [ ] Test complex combined queries:
  - Scope=partial AND condition=production
  - Component=auth AND temporal=v2.0+

### 2.4 Documentation - Query Features

- [ ] Add examples of structured context queries
- [ ] Document query syntax and capabilities

---

## Token Analysis and Verification

### Baseline Measurement

- [ ] Measure current token usage for relationships:
  - Average context length in tokens
  - Total relationship storage in sample database
  - Document baseline metrics

### Post-Phase-1 Measurement

- [ ] Measure token usage with JSON structure:
  - Average structured context size
  - Compare to baseline (+8-13 tokens expected)
  - Measure retrieval efficiency (with/without "text" field)

### Performance Impact

- [ ] Benchmark context extraction performance:
  - Pattern extraction speed (should be <1ms)
  - LLM extraction speed (if enabled, ~100-500ms)
  - No noticeable impact on relationship creation

---

## Rollout Checklist

### Pre-Deployment

- [ ] All Phase 1 tests passing
- [ ] Backward compatibility verified
- [ ] Documentation complete and accurate
- [ ] Token trade-off clearly communicated

### Deployment

- [ ] Deploy to dev/test environment
- [ ] Monitor for errors or regressions
- [ ] Verify existing relationships still load correctly
- [ ] Test new relationships with various context formats

### Post-Deployment

- [ ] Gather user feedback on extracted structure accuracy
- [ ] Monitor token usage increase (~8-13 tokens per context)
- [ ] Iterate on extraction patterns based on real usage
- [ ] Evaluate if Phase 2 (Structured Query Support) is needed based on usage patterns

---

## Success Criteria

**Phase 1 (Core Feature)**: ✅ COMPLETE
- [x] Pattern extraction works for 80%+ of common cases
- [x] Zero schema changes (uses existing `context` field)
- [x] 100% backward compatible with existing contexts
- [x] All tests passing (74 new tests + 615 existing tests)
- [x] Documentation accurate and clear about trade-offs
- [x] Implementation complete with full test coverage
- [x] Integration with server complete
- [x] Demo script created and verified
- [x] No LLM dependencies - keeps tool lightweight

**Phase 2 (Future Enhancement)**:
- [ ] Structured context queries working
- [ ] Useful filtering by scope, conditions, etc.
- [ ] Performance remains acceptable with large datasets

---

## Risk Mitigation

**Risk**: Pattern extraction accuracy too low
- **Mitigation**: Start with conservative patterns, iterate based on real usage
- **Fallback**: Always preserve original text, users can read it if structure is wrong

**Risk**: Token increase causes issues
- **Mitigation**: Make structure extraction optional via config flag
- **Fallback**: Allow disabling auto-extraction, store plain text only

**Risk**: Breaking changes to existing code
- **Mitigation**: Comprehensive backward compatibility testing
- **Fallback**: `parse_context()` handles both old and new formats transparently

---

## Notes for Coding Agent

**Implementation Order**:
1. Start with `context_extractor.py` utility module (1.1)
2. Add tests BEFORE integrating with server (1.4)
3. Only update server after extraction logic is proven (1.2)
4. Phase 2 (Structured Query Support) is FUTURE work - defer until Phase 1 proves valuable

**Key Files Modified** (Phase 1 - COMPLETE):
- NEW: `/Users/gregorydickson/claude-code-memory/src/memorygraph/utils/__init__.py`
- NEW: `/Users/gregorydickson/claude-code-memory/src/memorygraph/utils/context_extractor.py`
- NEW: `/Users/gregorydickson/claude-code-memory/tests/test_context_extraction.py`
- MODIFY: `/Users/gregorydickson/claude-code-memory/src/memorygraph/server.py` (line ~725)
- MODIFY: `/Users/gregorydickson/claude-code-memory/README.md` (documentation)

**No Changes Needed**:
- `/Users/gregorydickson/claude-code-memory/src/memorygraph/models.py` (keep `context: Optional[str]`)
- `/Users/gregorydickson/claude-code-memory/src/memorygraph/config.py` (no LLM flags needed)
- Database schema (no migrations)
- Existing relationship storage logic (backward compatible)

**Testing Strategy**:
- Unit tests first (pattern extraction)
- Integration tests second (server workflow)
- Manual testing last (real database)

**Success Indicator**:
When done, user can write natural language context and system automatically extracts structure using lightweight pattern matching, with zero training or schema changes, and all existing relationships still work.
