"""Analysis substrate request/result models (architecture Layer 4)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from codeanalyzer.domain.enums import AnalysisKind
from codeanalyzer.domain.provenance import ProvenancedFact


class AnalysisRequest(BaseModel):
    """On-demand deterministic analysis requested during evidence refinement."""

    kind: AnalysisKind
    source_id: str | None = None
    target_id: str | None = None
    node_id: str | None = None
    scope_entity_ids: list[str] = Field(default_factory=list)
    reason: str = Field(
        default="",
        description="Why refinement requested this analysis (for provenance/debugging)",
    )


class SubstrateRunResult(BaseModel):
    """Facts produced by the analysis substrate for one batch of requests."""

    requests: list[AnalysisRequest] = Field(default_factory=list)
    facts: list[ProvenancedFact] = Field(default_factory=list)
