"""Evidence requirements and minimal evidence slices.

Optimization target: minimum sufficient evidence, not maximum available context.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from codeanalyzer.domain.analysis import AnalysisRequest
from codeanalyzer.domain.enums import EvidenceItemType, RefinementOutcome
from codeanalyzer.domain.provenance import Provenance, ProvenancedFact


class EvidenceRequirement(BaseModel):
    """What a detector needs collected to evaluate or explain a finding.

    Detectors declare requirements; they do not construct LLM prompts or
    retrieve arbitrary repository files themselves.
    """

    kind: EvidenceItemType
    description: str
    entity_ids: list[str] = Field(default_factory=list)
    required: bool = True
    metadata: dict[str, str] = Field(default_factory=dict)


class EvidenceItem(BaseModel):
    """One item in a minimal evidence slice, with provenance."""

    id: str
    type: EvidenceItemType
    entity_id: str | None = None
    location: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    provenance: Provenance
    summary: str = ""


class MinimalEvidenceSlice(BaseModel):
    """Smallest defensible evidence set for one finding.

    Contains only program facts, diagnostics, documentation, and provenance
    needed to evaluate that finding — never the full logical slice.
    """

    id: str
    finding_id: str
    property_id: str | None = None
    program_entities: list[str] = Field(default_factory=list)
    call_edges: list[str] = Field(default_factory=list)
    control_flow_fragments: list[dict[str, Any]] = Field(default_factory=list)
    data_flow_fragments: list[dict[str, Any]] = Field(default_factory=list)
    external_diagnostic_ids: list[str] = Field(default_factory=list)
    relevant_conditions: list[str] = Field(default_factory=list)
    documentation_ids: list[str] = Field(default_factory=list)
    items: list[EvidenceItem] = Field(default_factory=list)
    facts: list[ProvenancedFact] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, str] = Field(default_factory=dict)


class RefinementResult(BaseModel):
    """Outcome of iterative evidence refinement for one finding."""

    slice: MinimalEvidenceSlice
    outcome: RefinementOutcome
    pending_requests: list[AnalysisRequest] = Field(default_factory=list)
    rounds: int = 0
