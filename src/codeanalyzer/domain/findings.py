"""Finding model — a concrete suspected correctness problem.

A finding is distinct from its evidence. Detectors establish candidate
findings; the Evidence Engine materializes supporting evidence.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from codeanalyzer.domain.entities import Location
from codeanalyzer.domain.enums import FindingSource, FindingStatus, Severity
from codeanalyzer.domain.evidence import EvidenceRequirement


class Finding(BaseModel):
    """Suspected correctness defect from an external analyzer or internal detector."""

    id: str
    analysis_id: str
    snapshot_id: str
    source: FindingSource
    detector: str = Field(
        description="Detector id or analyzer rule producer, e.g. 'missing_required_field_flow'"
    )
    type: str = Field(
        description="Finding type, e.g. 'missing_field_propagation', 'unreachable_code'"
    )
    property_id: str | None = Field(
        default=None,
        description="Correctness property this finding evaluates, if any",
    )
    classification: str | None = None
    severity: Severity = Severity.WARNING
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    location: Location | None = None
    affected_entity_ids: list[str] = Field(default_factory=list)
    evidence_requirements: list[EvidenceRequirement] = Field(default_factory=list)
    status: FindingStatus = FindingStatus.NEW
    message: str = ""
    # External analyzer linkage (when source is EXTERNAL_ANALYZER)
    analyzer: str | None = None
    rule_id: str | None = None
    # Free-form structured payload for detector-specific detail
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
