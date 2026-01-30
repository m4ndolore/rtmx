# tests/test_session_log_e2e.py
"""End-to-end tests for session log workflow."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest
from click.testing import CliRunner

from rtmx.cli.main import main
from rtmx.session_log import SessionLog


class TestSessionLogWorkflow:
    """E2E tests for session log workflow."""

    @pytest.fixture
    def rtmx_project(self, tmp_path: Path) -> Path:
        """Create full RTMX project structure."""
        rtmx_dir = tmp_path / ".rtmx"
        rtmx_dir.mkdir()

        # Create config
        config = rtmx_dir / "config.yaml"
        config.write_text("rtmx:\n  database: .rtmx/database.csv\n")

        # Create database
        headers = ["req_id", "category", "requirement_text", "status", "priority", "phase", "effort_weeks", "dependencies", "blocks"]
        rows = [
            {"req_id": "REQ-AUTH-001", "category": "AUTH", "requirement_text": "OAuth flow", "status": "PARTIAL", "priority": "HIGH", "phase": "3", "effort_weeks": "1.5", "dependencies": "", "blocks": "REQ-AUTH-002"},
            {"req_id": "REQ-AUTH-002", "category": "AUTH", "requirement_text": "Token refresh", "status": "MISSING", "priority": "MEDIUM", "phase": "3", "effort_weeks": "1.0", "dependencies": "REQ-AUTH-001", "blocks": ""},
        ]
        csv_path = rtmx_dir / "database.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)

        return tmp_path

    @pytest.mark.req("REQ-DX-001")
    @pytest.mark.scope_system
    @pytest.mark.technique_nominal
    @pytest.mark.env_simulation
    def test_full_session_workflow(self, rtmx_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test complete session log workflow: add -> view -> search -> backlog."""
        monkeypatch.chdir(rtmx_project)
        runner = CliRunner()

        # 1. Add first session log
        result = runner.invoke(main, [
            "log", "add", "REQ-AUTH-001",
            "--status", "interrupted",
            "--context", "Completed token acquisition",
            "--next", "Implement mutex in oauth.py:45",
            "--blocker", "Race condition on refresh",
            "--tag", "auth",
            "--files", "src/auth/oauth.py",
        ])
        assert result.exit_code == 0, result.output
        assert "Session logged" in result.output

        # 2. View session history
        result = runner.invoke(main, ["log", "view", "REQ-AUTH-001"])
        assert result.exit_code == 0, result.output
        assert "REQ-AUTH-001" in result.output
        assert "Completed token acquisition" in result.output
        assert "mutex" in result.output.lower()

        # 3. Search by text
        result = runner.invoke(main, ["log", "search", "race condition"])
        assert result.exit_code == 0, result.output
        assert "REQ-AUTH-001" in result.output

        # 4. Search by tag
        result = runner.invoke(main, ["log", "search", "--tag", "auth"])
        assert result.exit_code == 0, result.output
        assert "REQ-AUTH-001" in result.output

        # 5. Backlog shows pickup context
        result = runner.invoke(main, ["backlog"])
        assert result.exit_code == 0, result.output
        # Should show pickup context for interrupted work
        assert "PICKUP" in result.output or "mutex" in result.output.lower()

    @pytest.mark.req("REQ-DX-001")
    @pytest.mark.scope_system
    @pytest.mark.technique_nominal
    @pytest.mark.env_simulation
    def test_multiple_sessions_same_requirement(self, rtmx_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Multiple sessions on same requirement show history."""
        import time

        monkeypatch.chdir(rtmx_project)
        runner = CliRunner()

        # Add first session
        runner.invoke(main, [
            "log", "add", "REQ-AUTH-001",
            "--status", "interrupted",
            "--context", "First attempt",
            "--next", "Try again",
        ])

        # Wait to ensure different timestamp (CSV uses second precision)
        time.sleep(1.1)

        # Add second session
        runner.invoke(main, [
            "log", "add", "REQ-AUTH-001",
            "--status", "completed",
            "--context", "Finally done",
            "--next", "Ready for review",
        ])

        # View history shows both
        result = runner.invoke(main, ["log", "view", "REQ-AUTH-001"])
        assert result.exit_code == 0, result.output
        assert "First attempt" in result.output
        assert "Finally done" in result.output

        # Latest should be "completed"
        log = SessionLog.load(rtmx_project / ".rtmx" / "session_log.csv")
        latest = log.latest_for_requirement("REQ-AUTH-001")
        assert latest is not None
        assert latest.context == "Finally done"
