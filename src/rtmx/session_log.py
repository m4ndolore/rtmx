# src/rtmx/session_log.py
"""Session log models for tracking agent work sessions.

This module provides data structures for logging session work:
- SessionStatus: Session outcome status
- SessionEntry: Single session log entry
- SessionLog: Collection of session entries
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


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
