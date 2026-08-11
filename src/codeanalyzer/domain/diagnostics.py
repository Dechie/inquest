"""Canonical external diagnostic representation."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from codeanalyzer.domain.entities import Location
from codeanalyzer.domain.enums import Severity


class ExternalDiagnostic(BaseModel):
    """Normalized diagnostic from an ecosystem analyzer.

    Raw analyzer output and configuration remain available for provenance.
    External diagnostics are evidence providers — they may become findings
    directly, support another finding, or be supplied to the LLM.
    """

    id: str
    analysis_id: str | None = None
    snapshot_id: str
    analyzer: str
    analyzer_version: str | None = None
    rule_id: str | None = None
    severity: Severity = Severity.WARNING
    message: str
    location: Location | None = None
    entity_ids: list[str] = Field(default_factory=list)
    configuration: dict[str, Any] = Field(default_factory=dict)
    raw_diagnostic: dict[str, Any] = Field(default_factory=dict)
