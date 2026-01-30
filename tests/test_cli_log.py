# tests/test_cli_log.py
"""Tests for rtmx log CLI commands."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
from click.testing import CliRunner

from rtmx.cli.main import main
from rtmx.session_log import SessionEntry, SessionLog, SessionStatus


class TestLogAdd:
    """Tests for rtmx log add command."""

    @pytest.fixture
    def rtmx_project(self, tmp_path: Path) -> Path:
        """Create minimal RTMX project structure."""
        rtmx_dir = tmp_path / ".rtmx"
        rtmx_dir.mkdir()
        # Create minimal config
        config = rtmx_dir / "config.yaml"
        config.write_text("rtmx:\n  database: .rtmx/database.csv\n")
        # Create minimal database
        db = rtmx_dir / "database.csv"
        db.write_text(
            "req_id,category,requirement_text,status\nREQ-TEST-001,TEST,Test req,MISSING\n"
        )
        return tmp_path

    @pytest.mark.req("REQ-DX-001")
    @pytest.mark.scope_integration
    @pytest.mark.technique_nominal
    @pytest.mark.env_simulation
    def test_log_add_creates_entry(
        self, rtmx_project: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """rtmx log add creates a session log entry."""
        monkeypatch.chdir(rtmx_project)
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "log",
                "add",
                "REQ-TEST-001",
                "--status",
                "interrupted",
                "--context",
                "Completed initial work",
                "--next",
                "Continue with step 2",
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.output

        # Verify entry was created
        log = SessionLog.load(rtmx_project / ".rtmx" / "session_log.csv")
        assert len(log) == 1
        assert log.entries[0].req_id == "REQ-TEST-001"
        assert log.entries[0].context == "Completed initial work"

    @pytest.mark.req("REQ-DX-001")
    @pytest.mark.scope_integration
    @pytest.mark.technique_nominal
    @pytest.mark.env_simulation
    def test_log_add_with_all_options(
        self, rtmx_project: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """rtmx log add accepts all optional fields."""
        monkeypatch.chdir(rtmx_project)
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "log",
                "add",
                "REQ-TEST-001",
                "--status",
                "blocked",
                "--context",
                "Hit a wall",
                "--next",
                "Need help with auth",
                "--blocker",
                "Auth service down",
                "--tag",
                "auth",
                "--tag",
                "blocker",
                "--files",
                "src/auth.py",
                "--files",
                "tests/test_auth.py",
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.output

        log = SessionLog.load(rtmx_project / ".rtmx" / "session_log.csv")
        entry = log.entries[0]
        assert entry.blockers == "Auth service down"
        assert entry.tags == ["auth", "blocker"]
        assert entry.files_touched == ["src/auth.py", "tests/test_auth.py"]


class TestLogView:
    """Tests for rtmx log <REQ-ID> command."""

    @pytest.fixture
    def rtmx_project(self, tmp_path: Path) -> Path:
        """Create minimal RTMX project structure."""
        rtmx_dir = tmp_path / ".rtmx"
        rtmx_dir.mkdir()
        config = rtmx_dir / "config.yaml"
        config.write_text("rtmx:\n  database: .rtmx/database.csv\n")
        db = rtmx_dir / "database.csv"
        db.write_text(
            "req_id,category,requirement_text,status\nREQ-TEST-001,TEST,Test req,MISSING\n"
        )
        return tmp_path

    @pytest.fixture
    def project_with_logs(self, rtmx_project: Path) -> Path:
        """Create project with existing session logs."""
        log = SessionLog(rtmx_project / ".rtmx" / "session_log.csv")
        log.add(
            SessionEntry(
                session_id="sess_001",
                agent_id="claude:abc123",
                timestamp=datetime(2025, 1, 26, 14, 30, 0),
                req_id="REQ-TEST-001",
                status=SessionStatus.INTERRUPTED,
                context="Completed initial work",
                next_steps="Continue with step 2",
                blockers="Found bug in auth",
                tags=["auth"],
                files_touched=["src/auth.py"],
            )
        )
        log.add(
            SessionEntry(
                session_id="sess_002",
                agent_id="ralph:xyz789",
                timestamp=datetime(2025, 1, 25, 10, 0, 0),
                req_id="REQ-TEST-001",
                status=SessionStatus.COMPLETED,
                context="Set up project",
                next_steps="Add main feature",
                tags=[],
                files_touched=[],
            )
        )
        log.save()
        return rtmx_project

    @pytest.mark.req("REQ-DX-001")
    @pytest.mark.scope_integration
    @pytest.mark.technique_nominal
    @pytest.mark.env_simulation
    def test_log_view_requirement(
        self, project_with_logs: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """rtmx log view REQ-ID shows session history."""
        monkeypatch.chdir(project_with_logs)
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["log", "view", "REQ-TEST-001"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.output
        assert "REQ-TEST-001" in result.output
        assert "claude:abc123" in result.output
        assert "interrupted" in result.output.lower()
        assert "Completed initial work" in result.output

    @pytest.mark.req("REQ-DX-001")
    @pytest.mark.scope_integration
    @pytest.mark.technique_nominal
    @pytest.mark.env_simulation
    def test_log_view_no_entries(self, rtmx_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """rtmx log view REQ-ID shows message when no entries."""
        monkeypatch.chdir(rtmx_project)
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["log", "view", "REQ-NONEXISTENT"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.output
        assert "No session history" in result.output
