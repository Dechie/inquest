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
from codeanalyzer.domain.tooling import (
    AcquisitionMode,
    CapabilityKind,
    StructuralArtifact,
    ToolCapabilityState,
    ToolFailure,
    ToolStatus,
)


class AnalyzerCapabilities(BaseModel):
    """Static, declarative manifest of what an analyzer can expose and how.

    ``capabilities`` maps each kind to the acquisition channel that would
    harvest it. Runtime availability is ``ToolStatus``, not this record.
    """

    analyzer_id: str
    display_name: str
    languages: list[str] = Field(default_factory=list)
    capabilities: dict[CapabilityKind, AcquisitionMode] = Field(default_factory=dict)
    version_command: str | None = None


class AnalyzerAdapter(ABC):
    """Integration surface for one external analyzer.

    Adapter contract:
        discover() → is the tool binary present? (bool wrapper over probe)
        probe() → classified ToolStatus for this machine/project
        supports(language/project) → is it applicable?
        capabilities() → static capability → acquisition manifest
        analyze(snapshot, scope) → diagnostic channel (mandatory)
        harvest(snapshot, scope, kind) → structural channel (optional)
        normalize(output) → canonical ExternalDiagnostic list
    """

    _version: str | None = None
    _executable: str | None = None

    @abstractmethod
    def discover(self) -> bool:
        """Return True if the analyzer tool is available on this machine."""

    def probe(self, *, project_path: str | None = None) -> ToolStatus:
        """Classified availability. Default wraps ``discover()`` + the manifest."""
        del project_path
        return status_from_discover(
            self,
            installed=self.discover(),
            version=self._version,
            executable=self._executable,
        )

    @abstractmethod
    def supports(self, *, language: str | None = None, project_path: str | None = None) -> bool:
        """Return True if this adapter applies to the given project/language."""

    @abstractmethod
    def capabilities(self) -> AnalyzerCapabilities:
        """Declarative capability manifest for this analyzer."""

    @abstractmethod
    def analyze(
        self,
        snapshot: Snapshot,
        scope: LogicalSlice | None = None,
        *,
        project_path: str,
    ) -> list[ExternalDiagnostic]:
        """Run the analyzer against a snapshot (optionally scoped) and normalize."""

    def harvest(
        self,
        snapshot: Snapshot,
        scope: LogicalSlice | None = None,
        *,
        project_path: str,
        kind: CapabilityKind,
    ) -> StructuralArtifact | None:
        """Optional structural channel. Adapters opt in; default is no harvest."""
        del snapshot, scope, project_path, kind
        return None

    def normalize(self, raw_output: Any, *, snapshot: Snapshot) -> list[ExternalDiagnostic]:
        """Normalize raw tool output into canonical diagnostics.

        Subclasses should override; default raises.
        """
        raise NotImplementedError(f"{type(self).__name__}.normalize not implemented")


def status_from_discover(
    adapter: AnalyzerAdapter,
    *,
    installed: bool,
    version: str | None = None,
    executable: str | None = None,
) -> ToolStatus:
    """Build ToolStatus from a binary discover result and the static manifest.

    Installed tools mark ``DIAGNOSTICS`` available (the implemented channel)
    and every other declared kind unavailable until ``harvest()`` is wired.
    """
    caps = adapter.capabilities()
    if not installed:
        return ToolStatus(
            analyzer_id=caps.analyzer_id,
            executable=executable,
            version=version,
            capabilities={kind: ToolCapabilityState.UNAVAILABLE for kind in caps.capabilities},
            failure=ToolFailure.NOT_INSTALLED,
        )
    return ToolStatus(
        analyzer_id=caps.analyzer_id,
        executable=executable,
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
