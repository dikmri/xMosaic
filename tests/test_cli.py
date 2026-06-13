from __future__ import annotations

from typer.testing import CliRunner

from xmosaic.cli import app


def test_help_lists_core_commands() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "doctor" in result.output
    assert "inspect" in result.output
    assert "process" in result.output


def test_version_option() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert "xMosaic" in result.output

