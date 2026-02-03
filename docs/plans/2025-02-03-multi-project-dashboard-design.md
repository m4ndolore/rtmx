# Multi-Project Dashboard Design

**Date:** 2025-02-03
**Status:** Approved

## Overview

Add multi-project support to the RTMX web dashboard, allowing a single server to track multiple RTM databases with tab navigation.

## Configuration

Add to `rtmx.yaml`:

```yaml
dashboard:
  projects:
    - name: SigmaBlox
      database: ~/Dev/sigmablox/.rtmx/database.csv
    - name: RTMX
      database: ~/Dev/rtmx/docs/rtm_database.csv
```

Rules:
- If `dashboard.projects` is defined, multi-project mode is enabled
- If not defined, fall back to single-project behavior (uses `rtmx.database` or `--rtm-csv`)
- `name` is required, used as tab label and URL slug (slugified)
- `database` supports `~` expansion
- First project is default when visiting `/dashboard`

## URL Structure

Multi-project mode:
- `/dashboard` → redirects to `/dashboard/{first-project}`
- `/dashboard/{slug}` → project dashboard
- `/backlog/{slug}` → project backlog

Single-project fallback:
- `/dashboard` and `/backlog` (no slug)
- No project tabs shown
- Behaves exactly as current implementation

## Navigation

- Project tabs appear below main navbar: `[SigmaBlox] [RTMX]`
- Active tab highlighted
- Project name in page header: "SigmaBlox - Requirements Status"
- Dashboard/Backlog links relative to current project

## Real-time Updates

- One file watcher per project CSV
- Broadcast includes project slug: `{event: "rtm-update", project: "sigmablox"}`
- Client JS filters updates by current project
- Single WebSocket connection (unchanged)

Watcher lifecycle:
- All watchers start at server startup
- Skip watcher if CSV doesn't exist (log warning)
- Restart server to pick up config changes

## Implementation Files

| File | Change |
|------|--------|
| `src/rtmx/config.py` | Add `DashboardProject` model, parse `dashboard.projects` |
| `src/rtmx/web/app.py` | Store projects in app state, create watchers per project |
| `src/rtmx/web/routes/pages.py` | Add `project` path param, load correct CSV, pass context |
| `src/rtmx/web/routes/websocket.py` | Include project slug in broadcast |
| `src/rtmx/web/templates/base.html` | Add project tabs below navbar |
| `src/rtmx/web/templates/dashboard.html` | Show project name in header |
| `src/rtmx/web/watcher.py` | Accept project slug, pass to notify callback |

## Fallback Behavior

When `dashboard.projects` is not configured:
- Single-project mode (current behavior)
- No tabs displayed
- Uses `rtmx.database` config or `--rtm-csv` CLI flag
