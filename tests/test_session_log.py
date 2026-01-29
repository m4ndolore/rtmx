# tests/test_session_log.py
"""Tests for session log functionality."""

from __future__ import annotations

from datetime import datetime

import pytest

from rtmx.session_log import SessionEntry, SessionStatus


class TestSessionStatus:
    """Tests for SessionStatus enum."""

    @pytest.mark.req("REQ-DX-001")
    @pytest.mark.scope_unit
    @pytest.mark.technique_nominal
    @pytest.mark.env_simulation
    def test_session_status_values(self) -> None:
        """SessionStatus has expected values."""
        assert SessionStatus.COMPLETED.value == "completed"
        assert SessionStatus.INTERRUPTED.value == "interrupted"
        assert SessionStatus.BLOCKED.value == "blocked"
        assert SessionStatus.HANDED_OFF.value == "handed_off"

    @pytest.mark.req("REQ-DX-001")
    @pytest.mark.scope_unit
    @pytest.mark.technique_nominal
    @pytest.mark.env_simulation
    def test_session_status_from_string(self) -> None:
        """SessionStatus.from_string handles variations."""
        assert SessionStatus.from_string("completed") == SessionStatus.COMPLETED
        assert SessionStatus.from_string("INTERRUPTED") == SessionStatus.INTERRUPTED
        assert SessionStatus.from_string("handed-off") == SessionStatus.HANDED_OFF
        assert SessionStatus.from_string("unknown") == SessionStatus.INTERRUPTED  # default


class TestSessionEntry:
    """Tests for SessionEntry dataclass."""

    @pytest.mark.req("REQ-DX-001")
    @pytest.mark.scope_unit
    @pytest.mark.technique_nominal
    @pytest.mark.env_simulation
    def test_session_entry_creation(self) -> None:
        """SessionEntry can be created with required fields."""
        entry = SessionEntry(
            session_id="sess_001",
            agent_id="claude:abc123",
            timestamp=datetime(2025, 1, 27, 14, 30, 0),
            req_id="REQ-AUTH-001",
            status=SessionStatus.INTERRUPTED,
            context="Completed token acquisition",
            next_steps="Implement mutex in oauth.py:45",
        )
        assert entry.session_id == "sess_001"
        assert entry.agent_id == "claude:abc123"
        assert entry.req_id == "REQ-AUTH-001"
        assert entry.status == SessionStatus.INTERRUPTED

    @pytest.mark.req("REQ-DX-001")
    @pytest.mark.scope_unit
    @pytest.mark.technique_nominal
    @pytest.mark.env_simulation
    def test_session_entry_optional_fields(self) -> None:
        """SessionEntry has sensible defaults for optional fields."""
        entry = SessionEntry(
            session_id="sess_002",
            agent_id="ralph:xyz789",
            timestamp=datetime.now(),
            req_id="REQ-CLI-001",
            status=SessionStatus.COMPLETED,
            context="Finished implementation",
            next_steps="",
        )
        assert entry.blockers == ""
        assert entry.tags == []
        assert entry.files_touched == []

    @pytest.mark.req("REQ-DX-001")
    @pytest.mark.scope_unit
    @pytest.mark.technique_nominal
    @pytest.mark.env_simulation
    def test_session_entry_to_dict(self) -> None:
        """SessionEntry.to_dict produces CSV-compatible dict."""
        entry = SessionEntry(
            session_id="sess_001",
            agent_id="claude:abc123",
            timestamp=datetime(2025, 1, 27, 14, 30, 0),
            req_id="REQ-AUTH-001",
            status=SessionStatus.INTERRUPTED,
            context="Completed token acquisition",
            next_steps="Implement mutex",
            blockers="Race condition",
            tags=["auth", "race-condition"],
            files_touched=["src/auth/oauth.py", "tests/test_oauth.py"],
        )
        d = entry.to_dict()
        assert d["session_id"] == "sess_001"
        assert d["tags"] == "auth|race-condition"
        assert d["files_touched"] == "src/auth/oauth.py|tests/test_oauth.py"
        assert d["timestamp"] == "2025-01-27T14:30:00"

    @pytest.mark.req("REQ-DX-001")
    @pytest.mark.scope_unit
    @pytest.mark.technique_nominal
    @pytest.mark.env_simulation
    def test_session_entry_from_dict(self) -> None:
        """SessionEntry.from_dict parses CSV row."""
        row = {
            "session_id": "sess_001",
            "agent_id": "claude:abc123",
            "timestamp": "2025-01-27T14:30:00",
            "req_id": "REQ-AUTH-001",
            "status": "interrupted",
            "context": "Completed token acquisition",
            "next_steps": "Implement mutex",
            "blockers": "Race condition",
            "tags": "auth|race-condition",
            "files_touched": "src/auth/oauth.py|tests/test_oauth.py",
        }
        entry = SessionEntry.from_dict(row)
        assert entry.session_id == "sess_001"
        assert entry.status == SessionStatus.INTERRUPTED
        assert entry.tags == ["auth", "race-condition"]
        assert entry.files_touched == ["src/auth/oauth.py", "tests/test_oauth.py"]
