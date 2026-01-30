# src/rtmx/cli/log.py
"""RTMX session log commands.

Commands for managing session work logs.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime
from pathlib import Path

import click

from rtmx.formatting import Colors, header
from rtmx.session_log import SessionEntry, SessionLog, SessionStatus


def get_session_log_path() -> Path:
    """Get session log path (defaults to .rtmx/session_log.csv)."""
    return Path.cwd() / ".rtmx" / "session_log.csv"


def generate_session_id() -> str:
    """Generate unique session ID."""
    return f"sess_{uuid.uuid4().hex[:8]}"


def _detect_agent_id() -> str:
    """Attempt to detect current agent ID from environment."""
    if os.environ.get("CLAUDE_SESSION_ID"):
        return f"claude:{os.environ['CLAUDE_SESSION_ID'][:8]}"
    if os.environ.get("CURSOR_SESSION_ID"):
        return f"cursor:{os.environ['CURSOR_SESSION_ID'][:8]}"
    return "unknown"


def run_log_add(
    req_id: str,
    status: str,
    context: str,
    next_steps: str,
    blockers: str,
    tags: tuple[str, ...],
    files_touched: tuple[str, ...],
    agent_id: str | None,
) -> None:
    """Add a session log entry.

    Args:
        req_id: Requirement ID being worked on
        status: Session outcome status
        context: What was accomplished
        next_steps: Where to pick up
        blockers: What's preventing progress
        tags: Tags for cross-cutting concerns
        files_touched: Files modified during session
        agent_id: Agent ID (auto-detected if None)
    """
    log_path = get_session_log_path()
    session_log = SessionLog.load(log_path)

    if agent_id is None:
        agent_id = _detect_agent_id()

    entry = SessionEntry(
        session_id=generate_session_id(),
        agent_id=agent_id,
        timestamp=datetime.now(),
        req_id=req_id,
        status=SessionStatus.from_string(status),
        context=context,
        next_steps=next_steps,
        blockers=blockers,
        tags=list(tags),
        files_touched=list(files_touched),
    )

    session_log.add(entry)
    session_log.save()

    click.echo(f"Session logged: {entry.session_id}")
    click.echo(f"  Requirement: {req_id}")
    click.echo(f"  Status: {status}")
    click.echo(f"  Next: {next_steps}")


def run_log_view(req_id: str) -> None:
    """Show session history for a requirement.

    Args:
        req_id: Requirement ID to show history for
    """
    log_path = get_session_log_path()
    session_log = SessionLog.load(log_path)

    entries = session_log.for_requirement(req_id)

    if not entries:
        click.echo(f"No session history for {req_id}")
        return

    click.echo(header(f"Session History for {req_id}", "="))
    click.echo()

    for entry in entries:
        status_color = {
            SessionStatus.COMPLETED: Colors.GREEN,
            SessionStatus.INTERRUPTED: Colors.YELLOW,
            SessionStatus.BLOCKED: Colors.RED,
            SessionStatus.HANDED_OFF: Colors.CYAN,
        }.get(entry.status, Colors.RESET)

        click.echo(
            f"{entry.timestamp.strftime('%Y-%m-%d %H:%M')} | "
            f"{entry.agent_id} | "
            f"{status_color}{entry.status.value}{Colors.RESET}"
        )
        click.echo(f"  Context: {entry.context}")
        if entry.next_steps:
            click.echo(f"  Next: {entry.next_steps}")
        if entry.blockers:
            click.echo(f"  {Colors.RED}Blocker: {entry.blockers}{Colors.RESET}")
        if entry.files_touched:
            click.echo(f"  Files: {', '.join(entry.files_touched)}")
        click.echo()
