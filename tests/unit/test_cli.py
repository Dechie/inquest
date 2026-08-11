"""CLI smoke tests."""

from __future__ import annotations

from pathlib import Path

from codeanalyzer.cli import main


def test_version() -> None:
    assert main(["version"]) == 0


def test_detectors() -> None:
    assert main(["detectors"]) == 0


def test_analyzers() -> None:
    assert main(["analyzers"]) == 0


def test_init_and_status(tmp_path: Path, capsys) -> None:
    assert main(["init", str(tmp_path)]) == 0
    assert (tmp_path / ".codeanalyzer" / "analysis.db").exists()
    assert main(["status", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "codeanalyzer" in out
