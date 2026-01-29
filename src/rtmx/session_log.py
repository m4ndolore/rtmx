# src/rtmx/session_log.py
"""Session log models for tracking agent work sessions.

This module provides data structures for logging session work:
- SessionStatus: Session outcome status
- SessionEntry: Single session log entry
- SessionLog: Collection of session entries
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

SESSION_LOG_HEADERS = [
    "session_id",
    "agent_id",
    "timestamp",
    "req_id",
    "status",
    "context",
    "next_steps",
    "blockers",
    "tags",
    "files_touched",
]


class SessionStatus(str, Enum):
    """Session outcome status."""

    COMPLETED = "completed"
    INTERRUPTED = "interrupted"
    BLOCKED = "blocked"
    HANDED_OFF = "handed_off"

    @classmethod
    def from_string(cls, value: str) -> SessionStatus:
        """Parse status from string, handling variations."""
        normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
        for member in cls:
            if member.value == normalized:
                return member
        return cls.INTERRUPTED  # default for unknown


@dataclass
class SessionEntry:
    """Single session log entry.

    Attributes:
        session_id: Unique session identifier (e.g., sess_001)
        agent_id: Agent that worked (e.g., claude:abc123, ralph:xyz789)
        timestamp: When session ended
        req_id: Requirement ID(s), pipe-separated if multiple
        status: Session outcome status
        context: What was accomplished (brief)
        next_steps: Exactly where to pick up (specific, actionable)
        blockers: What's preventing progress (if any)
        tags: Tags for cross-cutting concerns
        files_touched: File paths modified during session
    """

    session_id: str
    agent_id: str
    timestamp: datetime
    req_id: str
    status: SessionStatus
    context: str
    next_steps: str
    blockers: str = ""
    tags: list[str] = field(default_factory=list)
    files_touched: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, str]:
        """Convert to CSV-compatible dictionary."""
        return {
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp.isoformat(timespec="seconds"),
            "req_id": self.req_id,
            "status": self.status.value,
            "context": self.context,
            "next_steps": self.next_steps,
            "blockers": self.blockers,
            "tags": "|".join(self.tags),
            "files_touched": "|".join(self.files_touched),
        }

    @classmethod
    def from_dict(cls, row: dict[str, str]) -> SessionEntry:
        """Create SessionEntry from CSV row dictionary."""
        return cls(
            session_id=row["session_id"],
            agent_id=row["agent_id"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            req_id=row["req_id"],
            status=SessionStatus.from_string(row["status"]),
            context=row["context"],
            next_steps=row["next_steps"],
            blockers=row.get("blockers", ""),
            tags=[t for t in row.get("tags", "").split("|") if t],
            files_touched=[f for f in row.get("files_touched", "").split("|") if f],
        )


class SessionLog:
    """Collection of session log entries.

    Manages session log CSV with add/query operations.
    """

    def __init__(self, path: Path) -> None:
        """Initialize SessionLog with path.

        Args:
            path: Path to session_log.csv file
        """
        self.path = path
        self.entries: list[SessionEntry] = []

    def __len__(self) -> int:
        """Return number of entries."""
        return len(self.entries)

    @classmethod
    def load(cls, path: Path) -> SessionLog:
        """Load SessionLog from CSV file.

        Args:
            path: Path to session_log.csv

        Returns:
            SessionLog with loaded entries (empty if file doesn't exist)
        """
        log = cls(path)
        if path.exists():
            with open(path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    log.entries.append(SessionEntry.from_dict(row))
        return log

    def add(self, entry: SessionEntry) -> None:
        """Add a session entry."""
        self.entries.append(entry)

    def save(self) -> None:
        """Save entries to CSV file."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=SESSION_LOG_HEADERS)
            writer.writeheader()
            for entry in self.entries:
                writer.writerow(entry.to_dict())

    def for_requirement(self, req_id: str) -> list[SessionEntry]:
        """Get all entries for a requirement, sorted by timestamp descending."""
        matches = [e for e in self.entries if req_id in e.req_id.split("|")]
        return sorted(matches, key=lambda e: e.timestamp, reverse=True)

    def latest_for_requirement(self, req_id: str) -> SessionEntry | None:
        """Get most recent entry for a requirement."""
        entries = self.for_requirement(req_id)
        return entries[0] if entries else None

    def search(self, text: str | None = None, tag: str | None = None) -> list[SessionEntry]:
        """Search entries by text or tag.

        Args:
            text: Text to search in context, next_steps, blockers
            tag: Tag to filter by

        Returns:
            Matching entries sorted by timestamp descending
        """
        results = []
        for entry in self.entries:
            if tag and tag not in entry.tags:
                continue
            if text:
                searchable = f"{entry.context} {entry.next_steps} {entry.blockers}".lower()
                if text.lower() not in searchable:
                    continue
            results.append(entry)
        return sorted(results, key=lambda e: e.timestamp, reverse=True)
