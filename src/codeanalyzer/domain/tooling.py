"""External-tool capability, acquisition, and status models.

Declarative vocabulary for the adapter layer: what a tool can expose, how
that information is acquired, and what was actually available for a run.
Runtime probing validates these declarations; it does not discover them.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class CapabilityKind(StrEnum):
    """Machine-readable kinds of information an analyzer may expose."""

    DIAGNOSTICS = "diagnostics"
    AST = "ast"
    SYMBOLS = "symbols"
    TYPES = "types"
    REFERENCES = "references"
    CALL_GRAPH = "call_graph"
    CFG = "cfg"
    DATA_FLOW = "data_flow"


class AcquisitionMode(StrEnum):
    """How a capability is obtained from the tool, highest quality first.

    LSP is intentionally omitted: it is a long-lived daemon protocol, not a
    per-run acquisition channel.
    """

    LIBRARY_API = "library_api"
    PROTOCOL = "protocol"
    EXPORT = "export"
    CLI_STRUCTURED = "cli_structured"
    CLI_TEXTUAL = "cli_textual"


class ToolCapabilityState(StrEnum):
    """Runtime availability of one declared capability.

    Orthogonal to ToolFailure: a capability may be UNAVAILABLE without a
    failure (declared but not harvested), or FAILED when acquisition broke.
    """

    AVAILABLE = "available"
    DERIVABLE = "derivable"
    PARTIALLY_AVAILABLE = "partially_available"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"
    UNSUPPORTED = "unsupported"
    INCOMPATIBLE = "incompatible"


class ToolFailure(StrEnum):
    """Classified reason a tool or capability could not be used."""

    NOT_INSTALLED = "not_installed"
    VERSION_MISMATCH = "version_mismatch"
    INVALID_PROJECT = "invalid_project"
    TOOL_CRASH = "tool_crash"
    TIMEOUT = "timeout"
    PERMISSION_DENIED = "permission_denied"
    MALFORMED_OUTPUT = "malformed_output"
    PROTOCOL_FAILURE = "protocol_failure"
    UNSUPPORTED_FEATURE = "unsupported_feature"


class ToolStatus(BaseModel):
    """Frozen view of one analyzer's availability for a given analysis run."""

    analyzer_id: str
    executable: str | None = None
    version: str | None = None
    project_requirement: str | None = None
    capabilities: dict[CapabilityKind, ToolCapabilityState] = Field(default_factory=dict)
    failure: ToolFailure | None = None

    def is_usable(self) -> bool:
        """True when diagnostics (or any capability) can actually be acquired."""
        if self.failure is not None:
            return False
        return any(state == ToolCapabilityState.AVAILABLE for state in self.capabilities.values())


class StructuralArtifact(BaseModel):
    """Optional structural payload harvested from an analyzer.

    Complements ``ExternalDiagnostic``: diagnostics are verdicts; this is
    program structure (AST, CFG, types, …) the tool already computed.
    """

    analyzer_id: str
    kind: CapabilityKind
    acquisition: AcquisitionMode
    payload: dict[str, Any] = Field(default_factory=dict)
    version: str | None = None


def tool_statuses_to_metadata(statuses: list[ToolStatus]) -> dict[str, str]:
    """Flatten tool statuses into ``AnalysisRun.metadata`` string pairs."""

    out: dict[str, str] = {}
    for status in statuses:
        prefix = f"tool.{status.analyzer_id}"
        if status.executable:
            out[f"{prefix}.executable"] = status.executable
        if status.version:
            out[f"{prefix}.version"] = status.version
        if status.project_requirement:
            out[f"{prefix}.requirement"] = status.project_requirement
        if status.failure is not None:
            out[f"{prefix}.failure"] = status.failure.value
        for kind, state in status.capabilities.items():
            out[f"{prefix}.{kind.value}"] = state.value
    return out
