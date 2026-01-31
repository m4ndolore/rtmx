# tests/test_session_log.py
"""Tests for session log functionality."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from rtmx.session_log import SessionEntry, SessionStatus

if TYPE_CHECKING:
    from rtmx.session_log import SessionLog


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


class TestSessionLog:
    """Tests for SessionLog collection."""

    @pytest.fixture
    def sample_log(self, tmp_path: Path) -> SessionLog:
        """Create a SessionLog with sample entries."""
        from rtmx.session_log import SessionLog

        log = SessionLog(tmp_path / "session_log.csv")
        log.add(
            SessionEntry(
                session_id="sess_001",
                agent_id="claude:abc123",
                timestamp=datetime(2025, 1, 26, 14, 30, 0),
                req_id="REQ-AUTH-001",
                status=SessionStatus.INTERRUPTED,
                context="Completed token acquisition",
                next_steps="Implement mutex in oauth.py:45",
                blockers="Race condition",
                tags=["auth"],
                files_touched=["src/auth/oauth.py"],
            )
        )
        log.add(
            SessionEntry(
                session_id="sess_002",
                agent_id="ralph:xyz789",
                timestamp=datetime(2025, 1, 25, 10, 15, 0),
                req_id="REQ-AUTH-001",
                status=SessionStatus.COMPLETED,
                context="Basic login flow working",
                next_steps="Add OAuth support",
                tags=["auth"],
                files_touched=["src/auth/login.py"],
            )
        )
        return log

    @pytest.mark.req("REQ-DX-001")
    @pytest.mark.scope_unit
    @pytest.mark.technique_nominal
    @pytest.mark.env_simulation
    def test_session_log_load_empty(self, tmp_path: Path) -> None:
        """SessionLog.load creates empty log if file doesn't exist."""
        from rtmx.session_log import SessionLog

        log = SessionLog.load(tmp_path / "session_log.csv")
        assert len(log) == 0

    @pytest.mark.req("REQ-DX-001")
    @pytest.mark.scope_unit
    @pytest.mark.technique_nominal
    @pytest.mark.env_simulation
    def test_session_log_add_and_save(self, tmp_path: Path) -> None:
        """SessionLog can add entries and save to CSV."""
        from rtmx.session_log import SessionLog

        csv_path = tmp_path / "session_log.csv"
        log = SessionLog(csv_path)

        entry = SessionEntry(
            session_id="sess_001",
            agent_id="claude:abc123",
            timestamp=datetime(2025, 1, 27, 14, 30, 0),
            req_id="REQ-AUTH-001",
            status=SessionStatus.INTERRUPTED,
            context="Completed token acquisition",
            next_steps="Implement mutex",
        )
        log.add(entry)
        log.save()

        assert csv_path.exists()
        loaded = SessionLog.load(csv_path)
        assert len(loaded) == 1
        assert loaded.entries[0].session_id == "sess_001"

    @pytest.mark.req("REQ-DX-001")
    @pytest.mark.scope_unit
    @pytest.mark.technique_nominal
    @pytest.mark.env_simulation
    def test_session_log_for_requirement(self, sample_log: SessionLog) -> None:
        """SessionLog.for_requirement returns entries for a req_id."""
        entries = sample_log.for_requirement("REQ-AUTH-001")
        assert len(entries) == 2
        # Should be sorted by timestamp descending (most recent first)
        assert entries[0].session_id == "sess_001"
        assert entries[1].session_id == "sess_002"

    @pytest.mark.req("REQ-DX-001")
    @pytest.mark.scope_unit
    @pytest.mark.technique_nominal
    @pytest.mark.env_simulation
    def test_session_log_latest_for_requirement(self, sample_log: SessionLog) -> None:
        """SessionLog.latest_for_requirement returns most recent entry."""
        entry = sample_log.latest_for_requirement("REQ-AUTH-001")
        assert entry is not None
        assert entry.session_id == "sess_001"

    @pytest.mark.req("REQ-DX-001")
    @pytest.mark.scope_unit
    @pytest.mark.technique_nominal
    @pytest.mark.env_simulation
    def test_session_log_latest_for_requirement_none(self, tmp_path: Path) -> None:
        """SessionLog.latest_for_requirement returns None if no entries."""
        from rtmx.session_log import SessionLog

        log = SessionLog(tmp_path / "session_log.csv")
        assert log.latest_for_requirement("REQ-NONEXISTENT") is None

    @pytest.mark.req("REQ-DX-001")
    @pytest.mark.scope_unit
    @pytest.mark.technique_nominal
    @pytest.mark.env_simulation
    def test_session_log_search_text(self, sample_log: SessionLog) -> None:
        """SessionLog.search finds entries by text."""
        results = sample_log.search("race condition")
        assert len(results) == 1
        assert results[0].session_id == "sess_001"

    @pytest.mark.req("REQ-DX-001")
    @pytest.mark.scope_unit
    @pytest.mark.technique_nominal
    @pytest.mark.env_simulation
    def test_session_log_search_tag(self, sample_log: SessionLog) -> None:
        """SessionLog.search finds entries by tag."""
        results = sample_log.search(tag="auth")
        assert len(results) == 2


class TestPublicExports:
    """Tests for public API exports."""

    @pytest.mark.req("REQ-DX-001")
    @pytest.mark.scope_unit
    @pytest.mark.technique_nominal
    @pytest.mark.env_simulation
    def test_session_log_exports_from_rtmx(self) -> None:
        """Session log classes are exported from rtmx package."""
        from rtmx import SessionEntry, SessionLog, SessionStatus

        assert SessionStatus.COMPLETED.value == "completed"
        assert hasattr(SessionEntry, "from_dict")
        assert hasattr(SessionLog, "load")
