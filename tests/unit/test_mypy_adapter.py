"""Unit tests for MypyAdapter.

subprocess.run is mocked throughout so no real mypy invocation is needed.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from codeanalyzer.analyzers.adapters.mypy import MypyAdapter, _parse_json_lines
from codeanalyzer.domain.enums import Severity
from codeanalyzer.domain.snapshots import Snapshot
from codeanalyzer.domain.tooling import ToolFailure, ToolCapabilityState

SNAPSHOT = Snapshot(id="snap1", project_id="p1")

_ERROR_LINE = json.dumps({
    "file": "/proj/app.py", "line": 10, "column": 4,
    "end_line": 10, "end_column": 12,
    "message": "Incompatible return value type (got \"int\", expected \"str\")",
    "hint": None, "code": "return-value", "severity": "error",
})
_NOTE_LINE = json.dumps({
    "file": "/proj/app.py", "line": 5, "column": 0,
    "end_line": 5, "end_column": 0,
    "message": "See: https://mypy.rtfd.io",
    "hint": None, "code": None, "severity": "note",
})
_WARN_LINE = json.dumps({
    "file": "/proj/app.py", "line": 3, "column": 0,
    "end_line": 3, "end_column": 5,
    "message": "Name \"x\" is not defined",
    "hint": "Did you mean \"y\"?", "code": "name-defined", "severity": "warning",
})


# ---------------------------------------------------------------------------
# _parse_json_lines
# ---------------------------------------------------------------------------

def test_parse_json_lines_single():
    assert len(_parse_json_lines(_ERROR_LINE)) == 1

def test_parse_json_lines_multiple():
    assert len(_parse_json_lines("\n".join([_ERROR_LINE, _NOTE_LINE, _WARN_LINE]))) == 3

def test_parse_json_lines_skips_noise():
    assert len(_parse_json_lines("mypy: error: no files\n" + _ERROR_LINE)) == 1

def test_parse_json_lines_empty():
    assert _parse_json_lines("") == []


# ---------------------------------------------------------------------------
# capabilities / supports
# ---------------------------------------------------------------------------

def test_capabilities():
    caps = MypyAdapter().capabilities()
    assert caps.analyzer_id == "mypy"
    assert "python" in caps.languages
    # Check that capabilities dict is present
    assert len(caps.capabilities) > 0
    from codeanalyzer.domain.tooling import CapabilityKind
    assert CapabilityKind.DIAGNOSTICS in caps.capabilities

def test_supports_python_language():
    a = MypyAdapter()
    assert a.supports(language="python") is True
    assert a.supports(language="Python") is True
    assert a.supports(language="javascript") is False

def test_supports_project_path_with_py_files(tmp_path: Path):
    (tmp_path / "app.py").write_text("x = 1\n")
    assert MypyAdapter().supports(project_path=str(tmp_path)) is True

def test_supports_project_path_no_py_files(tmp_path: Path):
    (tmp_path / "readme.txt").write_text("hello\n")
    assert MypyAdapter().supports(project_path=str(tmp_path)) is False

def test_supports_no_args():
    assert MypyAdapter().supports() is False


# ---------------------------------------------------------------------------
# discover()
# ---------------------------------------------------------------------------

def test_discover_true_when_mypy_available():
    mock_result = MagicMock(returncode=0, stdout="mypy 1.10.0 (compiled: yes)\n")
    with patch("shutil.which", return_value="/usr/bin/mypy"), \
         patch("subprocess.run", return_value=mock_result):
        a = MypyAdapter()
        assert a.discover() is True
        assert "mypy" in a._version

def test_discover_false_when_not_on_path():
    with patch("shutil.which", return_value=None):
        assert MypyAdapter().discover() is False

def test_discover_false_on_nonzero_exit():
    mock_result = MagicMock(returncode=1)
    with patch("shutil.which", return_value="/usr/bin/mypy"), \
         patch("subprocess.run", return_value=mock_result):
        assert MypyAdapter().discover() is False


# ---------------------------------------------------------------------------
# probe()
# ---------------------------------------------------------------------------

def test_probe_returns_tool_status_when_available():
    mock_result = MagicMock(returncode=0, stdout="mypy 1.10.0 (compiled: yes)\n")
    with patch("shutil.which", return_value="/usr/bin/mypy"), \
         patch("subprocess.run", return_value=mock_result):
        a = MypyAdapter()
        status = a.probe()
        assert status.analyzer_id == "mypy"
        assert status.executable == "/usr/bin/mypy"
        assert status.version is not None
        assert status.failure is None
        assert status.is_usable() is True

def test_probe_not_installed_failure():
    with patch("shutil.which", return_value=None):
        a = MypyAdapter()
        status = a.probe()
        assert status.failure == ToolFailure.NOT_INSTALLED
        assert status.is_usable() is False

def test_probe_timeout_failure():
    from subprocess import TimeoutExpired
    with patch("shutil.which", return_value="/usr/bin/mypy"), \
         patch("subprocess.run", side_effect=TimeoutExpired("mypy", 10)):
        a = MypyAdapter()
        status = a.probe()
        assert status.failure == ToolFailure.TIMEOUT
        assert status.is_usable() is False

def test_probe_invalid_project_failure(tmp_path: Path):
    mock_result = MagicMock(returncode=0, stdout="mypy 1.10.0\n")
    # Create a directory without Python files
    (tmp_path / "readme.txt").write_text("hello\n")
    
    with patch("shutil.which", return_value="/usr/bin/mypy"), \
         patch("subprocess.run", return_value=mock_result):
        a = MypyAdapter()
        status = a.probe(project_path=str(tmp_path))
        assert status.failure == ToolFailure.INVALID_PROJECT
        assert status.is_usable() is False




# ---------------------------------------------------------------------------
# normalize()
# ---------------------------------------------------------------------------

def test_normalize_error_line():
    a = MypyAdapter()
    d = a.normalize(_ERROR_LINE, snapshot=SNAPSHOT)
    assert len(d) == 1
    assert d[0].severity == Severity.ERROR
    assert d[0].rule_id == "return-value"
    assert d[0].snapshot_id == "snap1"
    assert d[0].analyzer == "mypy"
    assert d[0].location is not None
    assert d[0].location.file == "/proj/app.py"
    assert d[0].location.start_line == 10
    assert "Incompatible return value" in d[0].message

def test_normalize_note_severity():
    d = MypyAdapter().normalize(_NOTE_LINE, snapshot=SNAPSHOT)
    assert d[0].severity == Severity.INFO
    assert d[0].rule_id is None

def test_normalize_hint_appended():
    d = MypyAdapter().normalize(_WARN_LINE, snapshot=SNAPSHOT)
    assert d[0].severity == Severity.WARNING
    assert "Did you mean" in d[0].message

def test_normalize_accepts_list_of_dicts():
    raw = _parse_json_lines(_ERROR_LINE)
    assert len(MypyAdapter().normalize(raw, snapshot=SNAPSHOT)) == 1

def test_normalize_empty_input():
    assert MypyAdapter().normalize([], snapshot=SNAPSHOT) == []

def test_normalize_unique_ids():
    text = "\n".join([_ERROR_LINE, _WARN_LINE])
    ds = MypyAdapter().normalize(text, snapshot=SNAPSHOT)
    ids = [d.id for d in ds]
    assert len(ids) == len(set(ids))

def test_normalize_raw_diagnostic_preserved():
    d = MypyAdapter().normalize(_ERROR_LINE, snapshot=SNAPSHOT)
    assert d[0].raw_diagnostic["code"] == "return-value"


# ---------------------------------------------------------------------------
# analyze() — subprocess mocked
# ---------------------------------------------------------------------------

def test_analyze_calls_mypy_with_json_flag(tmp_path: Path):
    (tmp_path / "app.py").write_text("x: int = 'bad'\n")
    mock_result = MagicMock(stdout=_ERROR_LINE, returncode=1)

    with patch("shutil.which", return_value="/usr/bin/mypy"), \
         patch("subprocess.run", return_value=mock_result) as mock_run:
        diagnostics = MypyAdapter().analyze(SNAPSHOT, project_path=str(tmp_path))

    cmd = mock_run.call_args[0][0]
    assert "--output" in cmd
    assert "json" in cmd
    assert "--no-error-summary" in cmd
    assert len(diagnostics) == 1

def test_analyze_raises_when_mypy_missing(tmp_path: Path):
    (tmp_path / "app.py").write_text("x = 1\n")
    with patch("shutil.which", return_value=None):
        with pytest.raises(RuntimeError, match="mypy not found"):
            MypyAdapter().analyze(SNAPSHOT, project_path=str(tmp_path))

def test_analyze_empty_on_clean_project(tmp_path: Path):
    (tmp_path / "app.py").write_text("x: int = 1\n")
    mock_result = MagicMock(stdout="", returncode=0)
    with patch("shutil.which", return_value="/usr/bin/mypy"), \
         patch("subprocess.run", return_value=mock_result):
        assert MypyAdapter().analyze(SNAPSHOT, project_path=str(tmp_path)) == []


# ---------------------------------------------------------------------------
# Registry integration
# ---------------------------------------------------------------------------

def test_mypy_adapter_registerable():
    from codeanalyzer.analyzers.registry import AnalyzerRegistry
    registry = AnalyzerRegistry()
    registry.register(MypyAdapter())
    assert registry.get("mypy") is not None

def test_mypy_adapter_found_for_python_project(tmp_path: Path):
    from codeanalyzer.analyzers.registry import AnalyzerRegistry
    (tmp_path / "app.py").write_text("x = 1\n")
    registry = AnalyzerRegistry()
    registry.register(MypyAdapter())
    results = registry.for_project(project_path=str(tmp_path), languages=["python"])
    assert any(a.capabilities().analyzer_id == "mypy" for a in results)
