"""Unit tests for FlutterAnalyzeAdapter.

All subprocess calls are mocked. Raw output strings use the exact format
captured from a live ``flutter analyze`` run against pass_mgr.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from codeanalyzer.analyzers.adapters.flutter_analyze import (
    FlutterAnalyzeAdapter,
    _extract_issue_blocks,
    _parse_location,
)
from codeanalyzer.domain.enums import Severity
from codeanalyzer.domain.snapshots import Snapshot
from codeanalyzer.domain.tooling import ToolFailure, CapabilityKind

SNAPSHOT = Snapshot(id="snap1", project_id="p1")

# Exact output format captured from live flutter analyze run
_SINGLE_ERROR = (
    "Analyzing pass_mgr...\n\n"
    "  error • A value of type 'String' can't be returned from the\n"
    "         function 'badFunc' because it has a return type of\n"
    "         'int' • lib/utils/functions.dart:136:24 •\n"
    "         return_of_invalid_type\n\n"
    "1 issue found. (ran in 1.7s)\n"
)

_ERROR_AND_WARNING = (
    "Analyzing pass_mgr...\n\n"
    "  error • A value of type 'String' can't be returned from the\n"
    "         function 'badFunc' because it has a return type of\n"
    "         'int' • lib/utils/functions.dart:136:24 •\n"
    "         return_of_invalid_type\n"
    "  warning • The value of the local variable 'x' isn't used •\n"
    "         lib/utils/functions.dart:138:24 •\n"
    "         unused_local_variable\n\n"
    "2 issues found. (ran in 1.6s)\n"
)

_NO_ISSUES = "Analyzing pass_mgr...\n\nNo issues found! (ran in 2.1s)\n"

_HINT_ISSUE = (
    "Analyzing proj...\n"
    "  hint • Prefer const with constant constructors • "
    "lib/main.dart:10:5 • prefer_const_constructors\n"
    "1 issue found.\n"
)

_INFO_ISSUE = (
    "Analyzing proj...\n"
    "  info • Unnecessary import • lib/main.dart:1:1 • unnecessary_import\n"
    "1 issue found.\n"
)


# ---------------------------------------------------------------------------
# _parse_location
# ---------------------------------------------------------------------------

def test_parse_location_valid():
    loc = _parse_location("lib/utils/functions.dart:136:24")
    assert loc is not None
    assert loc.file == "lib/utils/functions.dart"
    assert loc.start_line == 136
    assert loc.start_column == 24

def test_parse_location_invalid():
    assert _parse_location("not_a_location") is None
    assert _parse_location("") is None

def test_parse_location_nested_path():
    loc = _parse_location("lib/screens/home/home_screen.dart:42:7")
    assert loc is not None
    assert loc.file == "lib/screens/home/home_screen.dart"


# ---------------------------------------------------------------------------
# _extract_issue_blocks
# ---------------------------------------------------------------------------

def test_extract_single_error_block():
    blocks = _extract_issue_blocks(_SINGLE_ERROR)
    assert len(blocks) == 1
    assert "error" in blocks[0]

# ---------------------------------------------------------------------------
# capabilities / supports
# ---------------------------------------------------------------------------

def test_capabilities():
    caps = FlutterAnalyzeAdapter().capabilities()
    assert caps.analyzer_id == "flutter_analyze"
    assert "dart" in caps.languages
    # Check that capabilities dict is present
    assert len(caps.capabilities) > 0
    assert CapabilityKind.DIAGNOSTICS in caps.capabilities

def test_supports_dart_language():
    a = FlutterAnalyzeAdapter()
    assert a.supports(language="dart") is True
    assert a.supports(language="flutter") is True
    assert a.supports(language="python") is False

def test_supports_flutter_project(tmp_path: Path):
    (tmp_path / "pubspec.yaml").write_text("name: test\n")
    assert FlutterAnalyzeAdapter().supports(project_path=str(tmp_path)) is True

def test_supports_non_flutter_project(tmp_path: Path):
    assert FlutterAnalyzeAdapter().supports(project_path=str(tmp_path)) is False

def test_supports_no_args():
    assert FlutterAnalyzeAdapter().supports() is False


# ---------------------------------------------------------------------------
# discover()
# ---------------------------------------------------------------------------

def test_discover_true_when_flutter_available():
    mock_result = MagicMock(
        returncode=0,
        stdout="Flutter 3.41.6 • channel stable\nFramework ...\n",
    )
    with patch("shutil.which", return_value="/opt/flutter/bin/flutter"), \
         patch("subprocess.run", return_value=mock_result):
        a = FlutterAnalyzeAdapter()
        assert a.discover() is True
        assert "Flutter" in a._version

def test_discover_false_when_not_on_path():
    with patch("shutil.which", return_value=None):
        assert FlutterAnalyzeAdapter().discover() is False

def test_discover_false_on_nonzero_exit():
    with patch("shutil.which", return_value="/opt/flutter/bin/flutter"), \
         patch("subprocess.run", return_value=MagicMock(returncode=1)):
        assert FlutterAnalyzeAdapter().discover() is False


# ---------------------------------------------------------------------------
# probe()
# ---------------------------------------------------------------------------

def test_probe_returns_tool_status_when_available():
    mock_result = MagicMock(
        returncode=0,
        stdout="Flutter 3.41.6 • channel stable\nFramework ...\n",
    )
    with patch("shutil.which", return_value="/opt/flutter/bin/flutter"), \
         patch("subprocess.run", return_value=mock_result):
        a = FlutterAnalyzeAdapter()
        status = a.probe()
        assert status.analyzer_id == "flutter_analyze"
        assert status.executable == "/opt/flutter/bin/flutter"
        assert status.version is not None
        assert status.failure is None
        assert status.is_usable() is True

def test_probe_not_installed_failure():
    with patch("shutil.which", return_value=None):
        a = FlutterAnalyzeAdapter()
        status = a.probe()
        assert status.failure == ToolFailure.NOT_INSTALLED
        assert status.is_usable() is False

def test_probe_timeout_failure():
    from subprocess import TimeoutExpired
    with patch("shutil.which", return_value="/opt/flutter/bin/flutter"), \
         patch("subprocess.run", side_effect=TimeoutExpired("flutter", 30)):
        a = FlutterAnalyzeAdapter()
        status = a.probe()
        assert status.failure == ToolFailure.TIMEOUT
        assert status.is_usable() is False

def test_probe_invalid_project_failure(tmp_path: Path):
    mock_result = MagicMock(
        returncode=0,
        stdout="Flutter 3.41.6 • channel stable\n",
    )
    # Create a directory without pubspec.yaml
    (tmp_path / "readme.txt").write_text("hello\n")
    
    with patch("shutil.which", return_value="/opt/flutter/bin/flutter"), \
         patch("subprocess.run", return_value=mock_result):
        a = FlutterAnalyzeAdapter()
        status = a.probe(project_path=str(tmp_path))
        assert status.failure == ToolFailure.INVALID_PROJECT
        assert status.is_usable() is False


def test_extract_two_blocks():
    blocks = _extract_issue_blocks(_ERROR_AND_WARNING)
    assert len(blocks) == 2

def test_extract_no_issues_returns_empty():
    assert _extract_issue_blocks(_NO_ISSUES) == []

def test_extract_strips_header_and_footer():
    for b in _extract_issue_blocks(_SINGLE_ERROR):
        assert not b.startswith("Analyzing")
        assert "issue found" not in b


# ---------------------------------------------------------------------------
# normalize()
# ---------------------------------------------------------------------------

def test_normalize_single_error():
    ds = FlutterAnalyzeAdapter().normalize(_SINGLE_ERROR, snapshot=SNAPSHOT)
    assert len(ds) == 1
    d = ds[0]
    assert d.severity == Severity.ERROR
    assert d.rule_id == "return_of_invalid_type"
    assert d.snapshot_id == "snap1"
    assert d.analyzer == "flutter_analyze"
    assert d.location is not None
    assert d.location.file == "lib/utils/functions.dart"
    assert d.location.start_line == 136

def test_normalize_error_and_warning():
    ds = FlutterAnalyzeAdapter().normalize(_ERROR_AND_WARNING, snapshot=SNAPSHOT)
    assert len(ds) == 2
    severities = {d.severity for d in ds}
    assert Severity.ERROR in severities
    assert Severity.WARNING in severities

def test_normalize_no_issues_returns_empty():
    assert FlutterAnalyzeAdapter().normalize(_NO_ISSUES, snapshot=SNAPSHOT) == []

def test_normalize_hint_maps_to_info():
    ds = FlutterAnalyzeAdapter().normalize(_HINT_ISSUE, snapshot=SNAPSHOT)
    assert len(ds) == 1
    assert ds[0].severity == Severity.INFO
    assert ds[0].rule_id == "prefer_const_constructors"

def test_normalize_info_severity():
    ds = FlutterAnalyzeAdapter().normalize(_INFO_ISSUE, snapshot=SNAPSHOT)
    assert ds[0].severity == Severity.INFO

def test_normalize_unique_ids():
    ds = FlutterAnalyzeAdapter().normalize(_ERROR_AND_WARNING, snapshot=SNAPSHOT)
    ids = [d.id for d in ds]
    assert len(ids) == len(set(ids))

def test_normalize_raw_diagnostic_preserved():
    ds = FlutterAnalyzeAdapter().normalize(_SINGLE_ERROR, snapshot=SNAPSHOT)
    assert "raw" in ds[0].raw_diagnostic
    assert ds[0].raw_diagnostic["severity"] == "error"

# ---------------------------------------------------------------------------
# analyze() — subprocess mocked
# ---------------------------------------------------------------------------

def test_analyze_uses_correct_flags(tmp_path: Path):
    (tmp_path / "pubspec.yaml").write_text("name: test\n")
    mock_result = MagicMock(stdout=_SINGLE_ERROR, stderr="", returncode=1)
    with patch("shutil.which", return_value="/opt/flutter/bin/flutter"), \
         patch("subprocess.run", return_value=mock_result) as mock_run:
        ds = FlutterAnalyzeAdapter().analyze(SNAPSHOT, project_path=str(tmp_path))
    cmd = mock_run.call_args[0][0]
    assert "analyze" in cmd
    assert "--no-congratulate" in cmd
    assert "--no-pub" in cmd
    assert "--no-fatal-infos" in cmd
    assert "--no-fatal-warnings" in cmd
    assert len(ds) == 1

def test_analyze_raises_when_flutter_missing(tmp_path: Path):
    (tmp_path / "pubspec.yaml").write_text("name: test\n")
    with patch("shutil.which", return_value=None):
        with pytest.raises(RuntimeError, match="flutter not found"):
            FlutterAnalyzeAdapter().analyze(SNAPSHOT, project_path=str(tmp_path))

def test_analyze_clean_project_returns_empty(tmp_path: Path):
    (tmp_path / "pubspec.yaml").write_text("name: test\n")
    mock_result = MagicMock(stdout=_NO_ISSUES, stderr="", returncode=0)
    with patch("shutil.which", return_value="/opt/flutter/bin/flutter"), \
         patch("subprocess.run", return_value=mock_result):
        assert FlutterAnalyzeAdapter().analyze(SNAPSHOT, project_path=str(tmp_path)) == []


# ---------------------------------------------------------------------------
# Integration — real pass_mgr project
# ---------------------------------------------------------------------------

PASS_MGR = "/home/dechasa/Dev/Side/Flutter/pass_mgr"

@pytest.mark.skipif(
    not Path(PASS_MGR).exists(),
    reason="pass_mgr project not present",
)
def test_real_flutter_analyze_clean_project():
    """Run against the real pass_mgr project — expects no issues."""
    import shutil as _shutil
    if not _shutil.which("flutter"):
        pytest.skip("flutter not on PATH")
    a = FlutterAnalyzeAdapter()
    assert a.discover() is True
    ds = a.analyze(SNAPSHOT, project_path=PASS_MGR)
    assert ds == [], f"Expected clean project but got: {[d.message for d in ds]}"


# ---------------------------------------------------------------------------
# Registry integration
# ---------------------------------------------------------------------------

def test_flutter_adapter_registerable():
    from codeanalyzer.analyzers.registry import AnalyzerRegistry
    registry = AnalyzerRegistry()
    registry.register(FlutterAnalyzeAdapter())
    assert registry.get("flutter_analyze") is not None

def test_flutter_adapter_found_for_dart_project(tmp_path: Path):
    from codeanalyzer.analyzers.registry import AnalyzerRegistry
    (tmp_path / "pubspec.yaml").write_text("name: test\n")
    registry = AnalyzerRegistry()
    registry.register(FlutterAnalyzeAdapter())
    results = registry.for_project(project_path=str(tmp_path), languages=["dart"])
    assert any(a.capabilities().analyzer_id == "flutter_analyze" for a in results)


def test_normalize_non_string_input():
    assert FlutterAnalyzeAdapter().normalize(None, snapshot=SNAPSHOT) == []
    assert FlutterAnalyzeAdapter().normalize(42, snapshot=SNAPSHOT) == []


