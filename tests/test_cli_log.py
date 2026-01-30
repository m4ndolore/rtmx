# tests/test_cli_log.py
"""Tests for rtmx log CLI commands."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from rtmx.cli.main import main
from rtmx.session_log import SessionLog


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
        db.write_text("req_id,category,requirement_text,status\nREQ-TEST-001,TEST,Test req,MISSING\n")
        return tmp_path

    @pytest.mark.req("REQ-DX-001")
    @pytest.mark.scope_integration
    @pytest.mark.technique_nominal
    @pytest.mark.env_simulation
    def test_log_add_creates_entry(self, rtmx_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """rtmx log add creates a session log entry."""
        monkeypatch.chdir(rtmx_project)
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "log", "add", "REQ-TEST-001",
                "--status", "interrupted",
                "--context", "Completed initial work",
                "--next", "Continue with step 2",
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
    def test_log_add_with_all_options(self, rtmx_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """rtmx log add accepts all optional fields."""
        monkeypatch.chdir(rtmx_project)
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "log", "add", "REQ-TEST-001",
                "--status", "blocked",
                "--context", "Hit a wall",
                "--next", "Need help with auth",
                "--blocker", "Auth service down",
                "--tag", "auth",
                "--tag", "blocker",
                "--files", "src/auth.py",
                "--files", "tests/test_auth.py",
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.output

        log = SessionLog.load(rtmx_project / ".rtmx" / "session_log.csv")
        entry = log.entries[0]
        assert entry.blockers == "Auth service down"
        assert entry.tags == ["auth", "blocker"]
        assert entry.files_touched == ["src/auth.py", "tests/test_auth.py"]
