"""Shared stub base for analyzer adapters not yet fully implemented."""

from __future__ import annotations

from typing import Any

from codeanalyzer.analyzers.adapter import AnalyzerAdapter, AnalyzerCapabilities
from codeanalyzer.domain.diagnostics import ExternalDiagnostic
from codeanalyzer.domain.slices import LogicalSlice
from codeanalyzer.domain.snapshots import Snapshot
from codeanalyzer.domain.tooling import (
    AcquisitionMode,
    CapabilityKind,
    ToolCapabilityState,
    ToolFailure,
    ToolStatus,
)


class StubAnalyzerAdapter(AnalyzerAdapter):
    """Placeholder adapter that reports capabilities but does not run yet."""

    def __init__(
        self,
        *,
        analyzer_id: str,
        display_name: str,
        languages: list[str],
        capabilities: dict[CapabilityKind, AcquisitionMode],
        binary_name: str | None = None,
    ) -> None:
        self._analyzer_id = analyzer_id
        self._display_name = display_name
        self._languages = languages
        self._capabilities = capabilities
        self._binary_name = binary_name

    def discover(self) -> bool:
        # Scaffold: real discovery will probe PATH / project config.
        return False

    def probe(self, *, project_path: str | None = None) -> ToolStatus:
        """Classified availability with specific failure reasons."""
        caps = self.capabilities()
        
        # Check if binary exists
        if self._binary_name:
            import shutil
            resolved = shutil.which(self._binary_name)
            if resolved is None:
                return ToolStatus(
                    analyzer_id=self._analyzer_id,
                    executable=self._binary_name,
                    version=None,
                    capabilities={kind: ToolCapabilityState.UNAVAILABLE for kind in self._capabilities},
                    failure=ToolFailure.NOT_INSTALLED,
                )
        
        # Scaffold adapters are not yet implemented
        return ToolStatus(
            analyzer_id=self._analyzer_id,
            executable=self._binary_name,
            version=None,
            capabilities={kind: ToolCapabilityState.UNSUPPORTED for kind in self._capabilities},
            failure=ToolFailure.UNSUPPORTED_FEATURE,
        )

    def supports(self, *, language: str | None = None, project_path: str | None = None) -> bool:
        if language is not None:
            return language.lower() in {lang.lower() for lang in self._languages}
        return False

    def capabilities(self) -> AnalyzerCapabilities:
        return AnalyzerCapabilities(
            analyzer_id=self._analyzer_id,
            display_name=self._display_name,
            languages=list(self._languages),
            capabilities=dict(self._capabilities),
            version_command=self._binary_name,
        )

    def analyze(
        self,
        snapshot: Snapshot,
        scope: LogicalSlice | None = None,
        *,
        project_path: str,
    ) -> list[ExternalDiagnostic]:
        raise NotImplementedError(
            f"{self._display_name} adapter is scaffolded but not yet implemented "
            f"(Phase B — External Analyzer Layer)"
        )

    def normalize(self, raw_output: Any, *, snapshot: Snapshot) -> list[ExternalDiagnostic]:
        raise NotImplementedError(
            f"{self._display_name} normalize is scaffolded but not yet implemented"
        )
