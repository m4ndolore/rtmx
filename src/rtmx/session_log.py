# src/rtmx/session_log.py
"""Session log models for tracking agent work sessions.

This module provides data structures for logging session work:
- SessionStatus: Session outcome status
- SessionEntry: Single session log entry
- SessionLog: Collection of session entries
"""

from __future__ import annotations

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
