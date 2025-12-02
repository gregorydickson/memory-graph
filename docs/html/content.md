# MemoryGraph - Main Page Content

---

## HEADER

```
memorygraph_                                     Docs | GitHub | Discord
```

---

## HERO SECTION

### Headline (with typing animation)
```
> MEMORY FOR YOUR AI CODING AGENT_
```

### Subheadline
**Never re-explain your project again.**

Claude Code forgets everything between sessions. You explain your architecture, your patterns, what worked, what failed—and next session, it's gone. 

MemoryGraph fixes that.

### Install Block
```
┌────────────────────────────────────────────────────┐
│ $ pip install memorygraphMCP                       │
│ $ claude mcp add memorygraph                       │
│                                                    │
│ ✓ Ready. Your AI now has a memory.                 │
└────────────────────────────────────────────────────┘
```

### CTA Buttons
```
[GET STARTED]     [VIEW ON GITHUB]     [JOIN DISCORD]
```

---

## DEMO SECTION

### Section Header
```
> SEE IT IN ACTION_
```

### Demo Description
*(Placeholder for asciinema GIF/video)*

```
┌─ TERMINAL ──────────────────────────────────────────────────┐
│                                                             │
│  SESSION 1:                                                 │
│  You: "Remember: retry with exponential backoff             │
│        fixed the API timeout issues"                        │
│  Claude: ✓ Stored in memory                                 │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  SESSION 2 (days later):                                    │
│  You: "What fixed the timeout issues we had?"               │
│  Claude: "We fixed the API timeouts using exponential       │
│           backoff retry logic. This solved both the         │
│           connection timeouts and rate limiting issues."    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## PROBLEM/SOLUTION SECTION

### Section Header
```
> THE PROBLEM_
```

### Without Memory (Left Column)
```
┌─ WITHOUT MEMORY ─────────────────────┐
│                                      │
│  SESSION 1:                          │
│  "Let me explain my project          │
│   architecture..."                   │
│                                      │
│  SESSION 2:                          │
│  "Let me explain my project          │
│   architecture..." (again)           │
│                                      │
│  SESSION 3:                          │
│  "Let me explain my project          │
│   architecture..." (seriously?)      │
│                                      │
│  SESSION 47:                         │
│  *quiet sobbing*                     │
│                                      │
└──────────────────────────────────────┘
```

### With MemoryGraph (Right Column)
```
┌─ WITH MEMORYGRAPH ───────────────────┐
│                                      │
│  SESSION 1:                          │
│  "Remember this architecture..."     │
│  ✓ Stored                            │
│                                      │
│  SESSION 2:                          │
│  Claude already knows. You ship.     │
│                                      │
│  SESSION 3:                          │
│  Claude recalls what worked AND      │
│  what failed. You ship faster.       │
│                                      │
│  SESSION 47:                         │
│  Claude knows your project better    │
│  than you remember it yourself.      │
│                                      │
└──────────────────────────────────────┘
```

---

## FEATURES SECTION

### Section Header
```
> FEATURES_
```

### Feature 1: Persistent Memory
```
┌─ PERSISTENT MEMORY ──────────────────────────────────────────┐
│                                                              │
│  Store solutions, patterns, decisions, and learnings that    │
│  survive across sessions. Never lose context to compaction   │
│  again.                                                      │
│                                                              │
│  > "Remember: the auth bug was caused by token expiry"       │
│  > "Remember: we use repository pattern for data access"     │
│  > "Remember: pytest fixtures go in conftest.py"             │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Feature 2: Relationship Tracking
```
┌─ KNOWS WHAT SOLVED WHAT ─────────────────────────────────────┐
│                                                              │
│  Not just notes—connected knowledge. MemoryGraph tracks      │
│  relationships between problems, solutions, and patterns.    │
│                                                              │
│  ┌──────────────┐    SOLVES    ┌──────────────┐              │
│  │ RetryBackoff │ ──────────▶  │ APITimeout   │              │
│  └──────────────┘              └──────────────┘              │
│         │                                                    │
│         │ RELATES_TO                                         │
│         ▼                                                    │
│  ┌──────────────┐                                            │
│  │ RateLimiting │                                            │
│  └──────────────┘                                            │
│                                                              │
│  Ask "what solved the timeout?" and get the actual solution, │
│  not just text that mentions "timeout" somewhere.            │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Feature 3: Zero Config
```
┌─ ZERO CONFIG ────────────────────────────────────────────────┐
│                                                              │
│  Works in 30 seconds. SQLite by default—no database to set   │
│  up, no cloud account to create, no API keys to manage.      │
│                                                              │
│  $ pip install memorygraphMCP                                │
│  $ claude mcp add memorygraph                                │
│  $ # That's it. You're done.                                 │
│                                                              │
│  Your data stays on your machine. Works offline.             │
│  Privacy by default.                                         │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Feature 4: Project Aware
```
┌─ PROJECT AWARE ──────────────────────────────────────────────┐
│                                                              │
│  Organize memories by project. Switch contexts cleanly.      │
│  What you learned on Project A doesn't pollute Project B.    │
│                                                              │
│  > Project: api-service                                      │
│    └── 47 memories (auth, caching, deployment)               │
│                                                              │
│  > Project: data-pipeline                                    │
│    └── 23 memories (ETL patterns, error handling)            │
│                                                              │
│  > Project: personal-site                                    │
│    └── 12 memories (styling, deployment)                     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## HOW IT WORKS SECTION

### Section Header
```
> HOW IT WORKS_
```

### Step 1: Store
```
═══════════════════════════════════════════════════════════════
  STEP 1: STORE
═══════════════════════════════════════════════════════════════

  Just talk naturally. Tell Claude what to remember.

  You: "Remember: exponential backoff fixed the API timeouts.
        Start at 100ms, max 5 retries, 2x multiplier."

                              ↓

  ┌─────────────────────────────────────────────────────────┐
  │  Entity: ExponentialBackoff                             │
  │  Type: Solution                                         │
  │  Observations:                                          │
  │    - Start at 100ms delay                               │
  │    - Maximum 5 retries                                  │
  │    - 2x multiplier between attempts                     │
  │  Relationship: SOLVES → APITimeout                      │
  └─────────────────────────────────────────────────────────┘
```

### Step 2: Recall
```
═══════════════════════════════════════════════════════════════
  STEP 2: RECALL
═══════════════════════════════════════════════════════════════

  Ask about past solutions. Claude searches your memory.

  You: "What fixed the timeout issues we had?"

                              ↓

  Claude searches memory → Finds ExponentialBackoff → 
  Sees it SOLVES APITimeout → Returns the full context

  Claude: "We fixed the API timeouts using exponential backoff.
           The configuration was: 100ms initial delay, 
           max 5 retries, 2x multiplier between attempts."
```

### Step 3: Build On It
```
═══════════════════════════════════════════════════════════════
  STEP 3: BUILD ON IT
═══════════════════════════════════════════════════════════════

  Knowledge compounds. Claude gets smarter about YOUR project.

  Week 1: Claude learns your architecture
  Week 2: Claude learns your patterns
  Week 3: Claude learns what works and what doesn't
  Week 4: Claude suggests solutions based on what worked before

  Your AI assistant evolves from "helpful stranger" to
  "team member who's been on the project for months."
```

---

## COMPARISON SECTION

### Section Header
```
> VS THE ALTERNATIVES_
```

### Comparison: CLAUDE.md
```
┌─ VS CLAUDE.md ───────────────────────────────────────────────┐
│                                                              │
│  CLAUDE.md is great for static instructions:                 │
│  "Use pytest for testing. Follow PEP 8."                     │
│                                                              │
│  MemoryGraph is for dynamic learnings:                       │
│  "The caching bug was fixed by clearing Redis on deploy."    │
│  "The auth tokens expire after 1 hour, not 24."              │
│  "Don't use that library—it broke production last month."    │
│                                                              │
│  CLAUDE.md = what to do (instructions)                       │
│  MemoryGraph = what we learned (knowledge)                   │
│                                                              │
│  Use both. They complement each other.                       │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Comparison: basic-memory
```
┌─ VS BASIC-MEMORY ────────────────────────────────────────────┐
│                                                              │
│  basic-memory is excellent general-purpose PKM.              │
│  Markdown files, Obsidian integration, cloud sync.           │
│                                                              │
│  MemoryGraph is purpose-built for coding workflows:          │
│                                                              │
│  • Typed relationships (SOLVES, CAUSES, BLOCKED_BY)          │
│  • "What solved this?" not just "what mentions this?"        │
│  • Designed for how developers actually work                 │
│                                                              │
│  basic-memory = "remember what I said"                       │
│  MemoryGraph = "remember what actually worked"               │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Comparison: Native Anthropic Memory
```
┌─ VS ANTHROPIC'S BUILT-IN MEMORY ─────────────────────────────┐
│                                                              │
│  Anthropic's memory is convenient—zero setup.                │
│                                                              │
│  MemoryGraph gives you:                                      │
│                                                              │
│  ✓ Control: See exactly what's stored                        │
│  ✓ Portability: Export, backup, move your data               │
│  ✓ Privacy: Data never leaves your machine                   │
│  ✓ Structure: Relationships, not just facts                  │
│  ✓ Project separation: Clean context switching               │
│                                                              │
│  Your knowledge. Your machine. Your control.                 │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Comparison: No Memory (Status Quo)
```
┌─ VS DOING NOTHING ───────────────────────────────────────────┐
│                                                              │
│  The cost of no memory:                                      │
│                                                              │
│  • Re-explaining your architecture every session             │
│  • Re-discovering solutions you already found                │
│  • Re-making mistakes you already made                       │
│  • Context lost every time the window fills up               │
│                                                              │
│  Time spent re-explaining = time not shipping.               │
│                                                              │
│  MemoryGraph installs in 30 seconds.                         │
│  How much time will you save this week?                      │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## SOCIAL PROOF SECTION

### Section Header
```
> WHAT DEVELOPERS ARE SAYING_
```

### Stats Bar
```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│    ⭐ [XXX] GitHub Stars    📦 [XXX] PyPI Downloads          │
│                                                              │
│    🧪 409 Tests Passing    📝 MIT Licensed                   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Testimonial Placeholders
```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  "Finally, Claude Code doesn't forget everything between     │
│   sessions. This is what I've been waiting for."             │
│                                                              │
│                                        — Developer, GitHub   │
│                                                              │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  "The relationship tracking is the killer feature.           │
│   'What solved X?' actually works."                          │
│                                                              │
│                                        — Developer, Twitter  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## FAQ SECTION

### Section Header
```
> FREQUENTLY ASKED QUESTIONS_
```

### FAQ Items

**Q: How is my data stored?**
```
A: SQLite database on your local machine by default. 
   Your data never leaves your computer unless you 
   explicitly configure cloud sync (coming soon).
```

**Q: Does this work with Claude Desktop or just Claude Code?**
```
A: Works with any MCP-compatible client: Claude Code, 
   Claude Desktop, Cursor, Windsurf, and more.
```

**Q: Can I use this with multiple projects?**
```
A: Yes. MemoryGraph supports project-based organization. 
   Each project has its own memory space.
```

**Q: What happens if I want to switch to a different tool later?**
```
A: Your data is yours. Export to JSON or Markdown anytime. 
   No lock-in.
```

**Q: Is there a cloud/team version?**
```
A: Coming soon. The free local version will always exist. 
   Cloud sync and team features will be paid tiers.
   Join the Discord for updates.
```

**Q: How does this compare to RAG?**
```
A: RAG retrieves from static documents. MemoryGraph 
   captures dynamic learnings from your conversations 
   and tracks relationships between them. Different 
   tools for different jobs.
```

---

## FINAL CTA SECTION

### Section Header
```
> READY TO GIVE YOUR AI A MEMORY?_
```

### CTA Block
```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│           Stop re-explaining. Start shipping.                │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                                                        │  │
│  │  $ pip install memorygraphMCP                          │  │
│  │  $ claude mcp add memorygraph                          │  │
│  │                                                        │  │
│  │  # Try it now:                                         │  │
│  │  # "Remember: [something you learned today]"           │  │
│  │                                                        │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│        [COPY INSTALL COMMAND]  [READ THE DOCS]               │
│                                                              │
│                    [⭐ STAR ON GITHUB]                        │
│                                                              │
│                                                              │
│  Questions? Ideas? Join the community:                       │
│                                                              │
│                     [JOIN DISCORD]                           │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## FOOTER

```
═══════════════════════════════════════════════════════════════

  memorygraph_

  GitHub · PyPI · Discord · Documentation

  MIT License · Made with ♥ for Claude Code users

  © 2025 Gregory Dickson

═══════════════════════════════════════════════════════════════
```

---

## META CONTENT

### Page Title
```
MemoryGraph - Memory for AI Coding Agents | Never Re-explain Your Project Again
```

### Meta Description
```
Give Claude Code persistent memory. Store solutions, track what worked, 
recall context across sessions. Zero config, local-first, privacy by default. 
Install in 30 seconds.
```

### Open Graph Title
```
MemoryGraph - Memory for AI Coding Agents
```

### Open Graph Description
```
Never re-explain your project to Claude Code again. 
MemoryGraph remembers what worked.
```

### Keywords
```
Claude Code memory, MCP memory server, AI coding assistant memory, 
Claude context persistence, Claude Code tools, persistent AI memory,
developer tools, coding assistant
```

---

## COPY VARIATIONS (A/B Testing)

### Hero Headlines (alternatives)
1. "MEMORY FOR YOUR AI CODING AGENT" ← Primary
2. "YOUR AI FINALLY REMEMBERS"
3. "STOP RE-EXPLAINING. START SHIPPING."
4. "GIVE CLAUDE CODE A BRAIN"
5. "KNOWLEDGE THAT SURVIVES"

### Subheadlines (alternatives)
1. "Never re-explain your project again." ← Primary
2. "What if Claude remembered what worked?"
3. "Your solutions. Your patterns. Persistent."
4. "Context that survives across sessions."
5. "From session amnesia to project expertise."

### CTA Button Text (alternatives)
1. "GET STARTED" ← Primary
2. "INSTALL NOW"
3. "TRY IT FREE"
4. "START REMEMBERING"
5. "GIVE IT A MEMORY"

---

## TONE GUIDELINES

**Voice**: 
- Developer-to-developer (not corporate marketing)
- Slightly playful but not silly
- Confident but not arrogant
- Empathetic to the frustration of context loss

**Avoid**:
- "Revolutionary", "game-changing", "cutting-edge"
- Excessive exclamation points
- Vague promises
- Enterprise jargon

**Embrace**:
- Concrete examples
- Real pain points
- Honest comparisons
- Technical credibility
- A bit of personality
