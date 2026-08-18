"""Mypy adapter — real implementation.

Shells out to ``mypy --output json`` and normalizes each JSON diagnostic
line into a canonical ``ExternalDiagnostic``.

Mypy JSON line schema (one object per line on stdout):
    {
      "file":       "<path>",
      "line":       <int>,
      "column":     <int>,
      "end_line":   <int>,
      "end_column": <int>,
      "message":    "<str>",
      "hint":       "<str> | null",
      "code":       "<rule-id>",
      "severity":   "error" | "warning" | "note"
    }
"""

from __future__ import annotations

import json
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Any

from codeanalyzer.analyzers.adapter import AnalyzerAdapter, AnalyzerCapabilities
from codeanalyzer.domain.diagnostics import ExternalDiagnostic
from codeanalyzer.domain.entities import Location
from codeanalyzer.domain.enums import Severity
from codeanalyzer.domain.slices import LogicalSlice
from codeanalyzer.domain.snapshots import Snapshot
from codeanalyzer.domain.tooling import (
    AcquisitionMode,
    CapabilityKind,
    ToolCapabilityState,
    ToolFailure,
    ToolStatus,
)

# Map mypy severity strings to our canonical Severity enum.
_SEVERITY_MAP: dict[str, Severity] = {
    "error": Severity.ERROR,
    "warning": Severity.WARNING,
    "note": Severity.INFO,
}


class MypyAdapter(AnalyzerAdapter):
    """Run mypy against a Python project and normalize its diagnostics.

    ``discover()`` checks that ``mypy`` is available on PATH (or the
    executable path supplied at construction time).  ``analyze()`` shells
    out to mypy with ``--output json --no-error-summary`` and parses each
    output line; ``normalize()`` converts raw dicts to
    ``ExternalDiagnostic`` objects.
    """

    ANALYZER_ID = "mypy"

    def __init__(self, *, executable: str = "mypy") -> None:
        self._executable = executable
        self._version: str | None = None

    # ------------------------------------------------------------------
    # AnalyzerAdapter protocol
    # ------------------------------------------------------------------

    def discover(self) -> bool:
        """Return True if the mypy binary is reachable."""
        resolved = shutil.which(self._executable)
        if resolved is None:
            return False
        try:
            result = subprocess.run(
                [resolved, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                self._version = result.stdout.strip().split("\n")[0]
                self._executable = resolved
                return True
        except (OSError, subprocess.TimeoutExpired):
            pass
        return False

    def probe(self, *, project_path: str | None = None) -> ToolStatus:
        """Classified availability with specific failure reasons."""
        caps = self.capabilities()
        
        # Check if binary exists
        resolved = shutil.which(self._executable)
        if resolved is None:
            return ToolStatus(
                analyzer_id=caps.analyzer_id,
                executable=self._executable,
                version=None,
                capabilities={kind: ToolCapabilityState.UNAVAILABLE for kind in caps.capabilities},
                failure=ToolFailure.NOT_INSTALLED,
            )
        
        # Try to get version
        try:
            result = subprocess.run(
                [resolved, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                version = result.stdout.strip().split("\n")[0]
                self._version = version
                self._executable = resolved
                
                # Check if project path is valid
                if project_path and not _has_python_files(project_path):
                    return ToolStatus(
                        analyzer_id=caps.analyzer_id,
                        executable=resolved,
                        version=version,
                        capabilities={kind: ToolCapabilityState.UNAVAILABLE for kind in caps.capabilities},
                        failure=ToolFailure.INVALID_PROJECT,
                    )
                
                return ToolStatus(
                    analyzer_id=caps.analyzer_id,
                    executable=resolved,
                    version=version,
                    capabilities={
                        kind: (
                            ToolCapabilityState.AVAILABLE
                            if kind == CapabilityKind.DIAGNOSTICS
                            else ToolCapabilityState.UNAVAILABLE
                        )
                        for kind in caps.capabilities
                    },
                    failure=None,
                )
        except subprocess.TimeoutExpired:
            return ToolStatus(
                analyzer_id=caps.analyzer_id,
                executable=resolved,
                version=None,
                capabilities={kind: ToolCapabilityState.UNAVAILABLE for kind in caps.capabilities},
                failure=ToolFailure.TIMEOUT,
            )
        except OSError:
            return ToolStatus(
                analyzer_id=caps.analyzer_id,
                executable=resolved,
                version=None,
                capabilities={kind: ToolCapabilityState.UNAVAILABLE for kind in caps.capabilities},
                failure=ToolFailure.PERMISSION_DENIED,
            )
        
        return ToolStatus(
            analyzer_id=caps.analyzer_id,
            executable=resolved,
            version=None,
            capabilities={kind: ToolCapabilityState.UNAVAILABLE for kind in caps.capabilities},
            failure=ToolFailure.TOOL_CRASH,
        )

    def supports(
        self, *, language: str | None = None, project_path: str | None = None
    ) -> bool:
        """True for Python projects or when language is ``"python"``."""
        if language is not None:
            return language.lower() == "python"
        if project_path is not None:
            return _has_python_files(project_path)
        return False

    def capabilities(self) -> AnalyzerCapabilities:
        return AnalyzerCapabilities(
            analyzer_id=self.ANALYZER_ID,
            display_name="mypy",
            languages=["python"],
            capabilities={
                CapabilityKind.DIAGNOSTICS: AcquisitionMode.CLI_STRUCTURED,
                CapabilityKind.TYPES: AcquisitionMode.CLI_STRUCTURED,
                CapabilityKind.SYMBOLS: AcquisitionMode.CLI_STRUCTURED,
            },
            version_command="mypy --version",
        )

    def analyze(
        self,
        snapshot: Snapshot,
        scope: LogicalSlice | None = None,
        *,
        project_path: str,
    ) -> list[ExternalDiagnostic]:
        """Run mypy and return normalized diagnostics."""
        resolved = shutil.which(self._executable)
        if resolved is None:
            raise RuntimeError(
                f"mypy not found at '{self._executable}'. "
                "Run discover() before analyze()."
            )
        cmd = [resolved, "--output", "json", "--no-error-summary", project_path]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=project_path,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                f"mypy timed out analyzing '{project_path}'"
            ) from exc
        return self.normalize(_parse_json_lines(result.stdout), snapshot=snapshot)

    def normalize(
        self, raw_output: Any, *, snapshot: Snapshot
    ) -> list[ExternalDiagnostic]:
        """Convert raw mypy JSON dicts into ``ExternalDiagnostic`` objects.

        Accepts either a list of dicts (from ``_parse_json_lines``) or a
        raw newline-delimited JSON string.
        """
        if isinstance(raw_output, str):
            raw_output = _parse_json_lines(raw_output)

        diagnostics: list[ExternalDiagnostic] = []
        version = self._version

        for item in raw_output:
            if not isinstance(item, dict):
                continue

            severity = _SEVERITY_MAP.get(item.get("severity", "error"), Severity.WARNING)
            rule_id: str | None = item.get("code") or None
            file_path: str = item.get("file", "")

            location: Location | None = None
            if file_path:
                location = Location(
                    file=file_path,
                    start_line=item.get("line"),
                    end_line=item.get("end_line"),
                    start_column=item.get("column"),
                    end_column=item.get("end_column"),
                )

            message = item.get("message", "")
            if item.get("hint"):
                message = f"{message} [{item['hint']}]"

            diagnostics.append(
                ExternalDiagnostic(
                    id=str(uuid.uuid4()),
                    snapshot_id=snapshot.id,
                    analyzer=self.ANALYZER_ID,
                    analyzer_version=version,
                    rule_id=rule_id,
                    severity=severity,
                    message=message,
                    location=location,
                    raw_diagnostic=item,
                )
            )

        return diagnostics


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _parse_json_lines(text: str) -> list[dict[str, Any]]:
    """Parse newline-delimited JSON objects from mypy stdout."""
    results: list[dict[str, Any]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                results.append(obj)
        except json.JSONDecodeError:
            pass
    return results


def _has_python_files(project_path: str) -> bool:
    """Return True if the directory contains at least one .py file."""
    return any(Path(project_path).rglob("*.py"))
