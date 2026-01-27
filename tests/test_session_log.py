# tests/test_session_log.py
"""Tests for session log functionality."""

from __future__ import annotations

import pytest

from rtmx.session_log import SessionStatus


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
