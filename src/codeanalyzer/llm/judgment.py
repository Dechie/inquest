"""LLM evaluation of findings against program evidence and documented intent."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum

from pydantic import BaseModel, Field

from codeanalyzer.domain.evidence import MinimalEvidenceSlice
from codeanalyzer.domain.findings import Finding
from codeanalyzer.domain.provenance import ProvenancedFact


class JudgmentVerdict(StrEnum):
    LIKELY_DEFECT = "likely_defect"
    POSSIBLE_DEFECT = "possible_defect"
    LIKELY_INTENDED = "likely_intended"
    DOCUMENTATION_ISSUE = "documentation_issue"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    UNCERTAIN = "uncertain"


class JudgmentResult(BaseModel):
    """Semantic judgment produced by the LLM over a minimal evidence slice."""

    finding_id: str
    verdict: JudgmentVerdict
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    explanation: str = ""
    remediation: str | None = None
    # Epistemic separation must be preserved in the result
    program_facts_used: list[ProvenancedFact] = Field(default_factory=list)
    documentation_facts_used: list[ProvenancedFact] = Field(default_factory=list)
    hypotheses: list[ProvenancedFact] = Field(default_factory=list)
    uncertainty_notes: list[str] = Field(default_factory=list)


class SemanticJudge(ABC):
    """Compares implementation evidence with intended behavior.

    Must not treat documentation as automatic ground truth, nor missing
    documentation as proof of incorrectness.
    """

    @abstractmethod
    def judge(
        self,
        finding: Finding,
        evidence: MinimalEvidenceSlice,
    ) -> JudgmentResult: ...


class StubSemanticJudge(SemanticJudge):
    """Phase F scaffold."""

    def judge(
        self,
        finding: Finding,
        evidence: MinimalEvidenceSlice,
    ) -> JudgmentResult:
        return JudgmentResult(
            finding_id=finding.id,
            verdict=JudgmentVerdict.INSUFFICIENT_EVIDENCE,
            explanation=(
                "Semantic judgment not yet implemented (Phase F). "
                "Deterministic finding and evidence slice are available for review."
            ),
            uncertainty_notes=["LLM judge is a scaffold stub"],
        )
