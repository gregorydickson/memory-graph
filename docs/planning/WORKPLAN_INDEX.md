# MemoryGraph Workplan Index

**Last Updated**: 2025-12-02
**Purpose**: Central index for all workplans organized by priority and dependency

---

## Overview

Workplans are numbered and organized for sequential execution by coding agents. Each workplan is designed to be:
- **Readable in one session** (~130-500 lines)
- **Self-contained** with clear prerequisites
- **Actionable** with markdown checkboxes
- **File-specific** with absolute paths where relevant

---

## Workplan Structure

### Marketing & Distribution

**[0-WORKPLAN-MARKETING.md](0-WORKPLAN-MARKETING.md)** - Marketing & Distribution (180 lines)
- Submit to official MCP servers repo
- Submit to awesome-mcp-servers lists
- Reddit/Twitter/HN launch announcements
- Community monitoring and engagement
- **Priority**: HIGH (can run parallel with development)
- **Prerequisites**: None
- **Tasks**: 25+

### Critical Path (Must Complete First)

**[1-WORKPLAN.md](1-WORKPLAN.md)** - Critical Fixes (128 lines)
- Fix datetime.utcnow() deprecation (2,379 instances)
- Implement health check (TODO in cli.py:293)
- **Priority**: CRITICAL
- **Prerequisites**: None
- **Estimated Time**: 1-2 days
- **Tasks**: 12

### High Priority (Quality & Testing)

**[2-WORKPLAN.md](2-WORKPLAN.md)** - Test Coverage Improvements (238 lines)
- Increase server.py coverage: 49% → 70%
- Increase Memgraph backend coverage: 28% → 70%
- **Priority**: HIGH
- **Prerequisites**: 1-WORKPLAN completed
- **Estimated Time**: 2-3 days
- **Tasks**: 35

**[3-WORKPLAN.md](3-WORKPLAN.md)** - Code Quality Improvements (296 lines)
- Standardize error handling with decorators
- Add missing type hints (especially sqlite_fallback.py)
- Standardize docstrings to Google style
- **Priority**: MEDIUM
- **Prerequisites**: 1-WORKPLAN completed
- **Estimated Time**: 3-4 days
- **Tasks**: 30

### Medium Priority (Refactoring)

**[4-WORKPLAN.md](4-WORKPLAN.md)** - Refactoring server.py (406 lines)
- Extract tool handlers into separate modules
- Reduce server.py: 1,473 lines → <500 lines
- Improve code organization and maintainability
- **Priority**: MEDIUM
- **Prerequisites**: 1-WORKPLAN, 2-WORKPLAN progress, 3-WORKPLAN progress
- **Estimated Time**: 2-3 days
- **Tasks**: 20

### Low Priority (New Features)

**[5-WORKPLAN.md](5-WORKPLAN.md)** - New Features (387 lines)
- Implement result pagination (offset/limit)
- Implement cycle detection for relationships
- **Priority**: LOW
- **Prerequisites**: 1-3 completed
- **Estimated Time**: 3-4 days
- **Tasks**: 22

### Future (Strategic Features)

**[6-WORKPLAN.md](6-WORKPLAN.md)** - Multi-Tenancy Phase 1 (496 lines)
- Implement schema enhancement for multi-tenant support
- Add optional tenant_id, team_id, visibility fields
- Maintain 100% backward compatibility
- **Priority**: FUTURE
- **Prerequisites**: 1-4 completed, ADR 009 approved
- **Reference**: [ADR 009](adr/009-multi-tenant-team-memory-sharing.md)
- **Estimated Time**: 4-5 days
- **Tasks**: 25

---

## Execution Recommendations

### For Coding Agents

**Sequential Execution**:
1. Start with 1-WORKPLAN (critical)
2. Proceed to 2-WORKPLAN (tests)
3. Work on 3-WORKPLAN (quality)
4. Execute 4-WORKPLAN (refactoring)
5. Consider 5-WORKPLAN (features) if needed
6. Defer 6-WORKPLAN until multi-tenancy is prioritized

**Parallel Execution**:
- **0-WORKPLAN-MARKETING**: Can run in parallel with ALL development work
- 2-WORKPLAN and 3-WORKPLAN can be worked on in parallel (after 1-WORKPLAN)
- 4-WORKPLAN requires some progress on 2 and 3
- 5-WORKPLAN requires 1-3 completed
- 6-WORKPLAN requires 1-4 completed

### Dependency Graph

```
0-WORKPLAN-MARKETING (parallel track)
        │
        ├────────────────────────────────────────────────────┐
        │                                                    │
1-WORKPLAN (Critical Fixes)                                  │
    ↓                                                        │
    ├─→ 2-WORKPLAN (Test Coverage)                          │
    │       ↓                                                │
    ├─→ 3-WORKPLAN (Code Quality)                           │
    │       ↓                                                │
    └─────→ 4-WORKPLAN (Refactoring)                        │
                ↓                                            │
            5-WORKPLAN (New Features) ←─────────────────────┘
                ↓                    (marketing drives feedback)
            6-WORKPLAN (Multi-Tenancy)
```

---

## Metrics Summary

### Total Work Estimated
- **Total Tasks**: 170+ tasks across 7 workplans
- **Total Lines**: 2,100+ lines of workplan documentation

### Priority Breakdown
- Marketing (parallel): 25+ tasks (0-WORKPLAN-MARKETING)
- Critical: 12 tasks (1-WORKPLAN)
- High: 65 tasks (2-WORKPLAN, 3-WORKPLAN)
- Medium: 20 tasks (4-WORKPLAN)
- Low: 22 tasks (5-WORKPLAN)
- Future: 25 tasks (6-WORKPLAN)

### Coverage Targets
- **Before**: server.py 49%, Memgraph 28%
- **After**: server.py >70%, Memgraph >70%
- **Overall**: Maintain/improve 85% coverage

### Code Reduction
- **Before**: server.py 1,473 lines
- **After**: server.py <500 lines
- **Extraction**: 4 new tool modules

---

## Strategic Context

### Product Roadmap Alignment

These workplans align with [PRODUCT_ROADMAP.md](planning/PRODUCT_ROADMAP.md):
- **Phase 1-2** (Current): Focus on quality and testing (1-4 workplans)
- **Phase 3-4** (Future): Cloud sync and multi-tenancy (6-WORKPLAN)

### Architecture Decision Records

Relevant ADRs:
- [ADR 009](adr/009-multi-tenant-team-memory-sharing.md): Multi-Tenant Team Memory Sharing (referenced in 6-WORKPLAN)
- Future ADRs will be created for:
  - Server refactoring approach (4-WORKPLAN)
  - Pagination design (5-WORKPLAN)
  - Cycle detection strategy (5-WORKPLAN)

---

## Archived Workplans

Old workplans moved to `/docs/archive/`:
- `WORKPLAN_2025-12-02.md` (75KB, comprehensive original)
- `2-WORKPLAN_CODE_QUALITY_2025-12-02.md` (21KB, code review findings)

These are superseded by the new numbered workplans above.

---

## Usage Notes

### For Project Managers
- Use this index to understand scope and priorities
- Track progress by checking completion of workplans
- Adjust priority based on business needs

### For Developers
- Start with 1-WORKPLAN before others
- Update checkboxes as you complete tasks
- Run full test suite between workplans
- Create feature branches for major refactoring (4-WORKPLAN)

### For Contributors
- Refer to individual workplans for detailed task lists
- All file paths are absolute for clarity
- Tests should be written before implementation (TDD approach)
- Each workplan has clear acceptance criteria

---

## Questions?

- **Not sure where to start?** Begin with 1-WORKPLAN.md
- **Need strategic context?** Review [PRODUCT_ROADMAP.md](planning/PRODUCT_ROADMAP.md)
- **Want to understand multi-tenancy?** Read [ADR 009](adr/009-multi-tenant-team-memory-sharing.md)
- **Looking for completed work?** Check `/docs/archive/`

---

**Last Updated**: 2025-12-02
**Maintainer**: Gregory Dickson
**Status**: Active - ready for execution
