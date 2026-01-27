# Session Log Design

**Date**: 2025-01-27
**Status**: Draft
**Problem**: Sitrep context bloat causing excessive context usage for new sessions

## Problem Statement

Current sitrep process mixes historical "what we did" with actionable "what to do next", causing:

- Context bloat at session start (loading irrelevant history)
- Scattered notes across RTMX requirements, /docs, and other locations
- Difficulty picking up interrupted sessions
- Opaque agent activity (especially Ralph)

## Solution Overview

Separate **session logs** from **requirement specs** with explicit linking:

```
┌─────────────────────────┐      ┌─────────────────────────┐
│   Requirement Specs     │      │     Session Logs        │
│   (what to build)       │◄────►│   (what happened)       │
│                         │ link │                         │
│ • REQ-AUTH-001.md       │      │ • session_log.csv       │
│ • database.csv          │      │ • searchable by REQ-ID  │
└─────────────────────────┘      └─────────────────────────┘
         │                                  │
         ▼                                  ▼
   Load at session start            Load on-demand
   (via rtmx backlog)            (via rtmx log for X)
```

**Key principle**: Actionable context loads at session start; historical context loads on-demand.

## Data Model

### Session Log Entry

Location: `.rtmx/session_log.csv`

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | string | Unique session identifier (e.g., `sess_001`) |
| `agent_id` | string | Agent that worked (e.g., `claude:abc123`, `ralph:xyz789`) |
| `timestamp` | ISO 8601 | When session ended |
| `req_id` | string | Requirement ID(s), pipe-separated if multiple |
| `status` | enum | `completed`, `interrupted`, `blocked`, `handed_off` |
| `context` | string | What was accomplished (brief) |
| `next_steps` | string | Exactly where to pick up (specific, actionable) |
| `blockers` | string | What's preventing progress (if any) |
| `tags` | string | Pipe-separated tags for cross-cutting concerns |
| `files_touched` | string | Pipe-separated file paths modified |

### Example Entry

```csv
session_id,agent_id,timestamp,req_id,status,context,next_steps,blockers,tags,files_touched
sess_001,claude:abc123,2025-01-26T14:30:00Z,REQ-AUTH-001,interrupted,"Completed token acquisition","Implement mutex in oauth.py:45","Race condition on concurrent refresh",auth|race-condition,src/auth/oauth.py|tests/test_oauth.py
```

## Actionable Layer: Enhanced Backlog

`rtmx backlog` surfaces pickup context for interrupted/handed-off work:

```
$ rtmx backlog

Priority Items:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. REQ-AUTH-001 [PARTIAL] OAuth user authentication
   Priority: HIGH | Phase: 3 | Effort: 1.5w

   ⚠️  PICKUP from claude:abc123 (2025-01-26 14:30)
   ├─ Context: Completed token acquisition
   ├─ Next: Implement mutex in oauth.py:45
   ├─ Blocker: Race condition on concurrent refresh
   └─ Files: src/auth/oauth.py, tests/test_oauth.py

2. REQ-CLI-002 [MISSING] Export RTM as JSON
   Priority: HIGH | Phase: 3 | Effort: 0.5w

   No previous work

3. REQ-API-001 [MISSING] REST API endpoints
   Priority: MEDIUM | Phase: 4 | Effort: 2w

   ✓ Handed off from ralph:xyz789 (2025-01-25)
   └─ Context: Schema designed, ready for implementation
```

**Behaviors**:
- Only shows **most recent** session entry per requirement
- Distinguishes `PICKUP` (interrupted) from `Handed off` (intentional)
- `Next:` field tells agent exactly where to start

## On-Demand Historical Access

### View requirement history

```bash
$ rtmx log REQ-AUTH-001

Session History for REQ-AUTH-001:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

2025-01-26 14:30 | claude:abc123 | interrupted
  Context: Completed token acquisition
  Next: Implement mutex in oauth.py:45
  Blocker: Race condition on concurrent refresh

2025-01-25 10:15 | ralph:xyz789 | completed
  Context: Basic login flow working, tests passing
  Next: Add OAuth provider support

2025-01-24 16:00 | claude:def456 | interrupted
  Context: Set up auth module structure
  Next: Implement login endpoint
```

### Search across logs

```bash
# Text search
$ rtmx log search "race condition"

Found 2 entries matching "race condition":

REQ-AUTH-001 | 2025-01-26 | claude:abc123
  Blocker: Race condition on concurrent refresh

REQ-SYNC-003 | 2025-01-20 | ralph:xyz789
  Context: Fixed race condition in file watcher

# Tag search
$ rtmx log search --tag auth

Found 5 entries tagged #auth:
...
```

## Logging Workflow

### CLI Command

```bash
$ rtmx log add REQ-AUTH-001 \
    --status interrupted \
    --context "Completed token acquisition" \
    --next "Implement mutex in oauth.py:45" \
    --blocker "Race condition on concurrent refresh" \
    --tag auth --tag race-condition \
    --files src/auth/oauth.py tests/test_oauth.py
```

### MCP Tool (for agents like Ralph)

```python
rtmx_log_session(
    req_id="REQ-AUTH-001",
    status="interrupted",
    context="Completed token acquisition",
    next_steps="Implement mutex in oauth.py:45",
    blockers="Race condition on concurrent refresh",
    tags=["auth", "race-condition"],
    files_touched=["src/auth/oauth.py", "tests/test_oauth.py"]
)
```

## Session-End Prompting

### Context-Aware Hook (90% threshold)

Configuration in `.claude/hooks.yaml` or `rtmx.yaml`:

```yaml
hooks:
  context_warning:
    threshold: 90%
    message: |
      ⚠️ Context at {usage}%. Before ending, log your work:

      rtmx log add {current_req} --status interrupted \
        --context "..." --next "..." [--blocker "..."]
```

### CLAUDE.md Instruction

```markdown
## Session Continuity

Before ending any session where work is in-progress:

1. Run `rtmx log add` for each requirement you touched
2. Include specific `--next` steps (file:line if possible)
3. Note any blockers discovered

This enables seamless pickup by the next session.
```

## Context Reduction Summary

| Before | After |
|--------|-------|
| Sitreps mixed everywhere | Session logs in `.rtmx/session_log.csv` |
| "Completed this session" noise loaded every time | Historical context pulled on-demand only |
| Hard to find where to pick up | `rtmx backlog` shows pickup context inline |
| Full journaling in requirements | Requirement files stay focused on spec |
| Ralph's work opaque | Same logging format for all agents |

**Session start context**:
- `rtmx backlog` output (prioritized items + pickup context)
- NOT full session history
- NOT old "completed" entries

## Implementation Phases

### Phase 1: Core Session Log
- [ ] Add `session_log.csv` schema to RTMX
- [ ] Implement `rtmx log add` CLI command
- [ ] Implement `rtmx log <REQ-ID>` CLI command
- [ ] Implement `rtmx log search` CLI command

### Phase 2: Enhanced Backlog
- [ ] Modify `rtmx backlog` to read session log
- [ ] Display pickup context for interrupted/handed-off items
- [ ] Add `--no-context` flag for minimal output

### Phase 3: MCP Integration
- [ ] Add `rtmx_log_session` MCP tool
- [ ] Add `rtmx_log_search` MCP tool
- [ ] Update Ralph integration docs

### Phase 4: Hooks & Prompting
- [ ] Implement context-warning hook (90% threshold)
- [ ] Add CLAUDE.md template with session continuity instructions
- [ ] Document hook configuration

## Open Questions

1. **Log rotation**: Should old session log entries be archived after N days or N entries?
2. **Multi-requirement sessions**: How to handle sessions that touch 5+ requirements efficiently?
3. **Automatic file detection**: Should `--files` be auto-populated from git diff?

---

*Generated via brainstorming session 2025-01-27*
