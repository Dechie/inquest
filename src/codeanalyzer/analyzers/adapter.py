"""AnalyzerAdapter protocol.

Where a mature ecosystem analyzer already performs an analysis reliably,
the system consumes it rather than reimplementing it.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from codeanalyzer.domain.diagnostics import ExternalDiagnostic
from codeanalyzer.domain.slices import LogicalSlice
from codeanalyzer.domain.snapshots import Snapshot


class AnalyzerCapabilities(BaseModel):
    """What an analyzer provides."""

    analyzer_id: str
    display_name: str
    languages: list[str] = Field(default_factory=list)
    provides: list[str] = Field(
        default_factory=list,
        description="e.g. type diagnostics, undefined symbols, lint rules",
    )
    version_command: str | None = None


class AnalyzerAdapter(ABC):
    """Integration surface for one external analyzer.

    Adapter contract:
        discover() → is the tool available?
        supports(language/project) → is it applicable?
        capabilities() → what does it provide?
        analyze(snapshot, scope) → run analysis
        normalize(output) → canonical ExternalDiagnostic list
    """

    @abstractmethod
    def discover(self) -> bool:
        """Return True if the analyzer tool is available on this machine."""

    @abstractmethod
    def supports(self, *, language: str | None = None, project_path: str | None = None) -> bool:
        """Return True if this adapter applies to the given project/language."""

    @abstractmethod
    def capabilities(self) -> AnalyzerCapabilities:
        """Describe what this analyzer provides."""

    @abstractmethod
    def analyze(
        self,
        snapshot: Snapshot,
        scope: LogicalSlice | None = None,
        *,
        project_path: str,
    ) -> list[ExternalDiagnostic]:
        """Run the analyzer against a snapshot (optionally scoped) and normalize."""

    def normalize(self, raw_output: Any, *, snapshot: Snapshot) -> list[ExternalDiagnostic]:
        """Normalize raw tool output into canonical diagnostics.

        Subclasses should override; default raises.
        """
        raise NotImplementedError(f"{type(self).__name__}.normalize not implemented")
