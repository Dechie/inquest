"""Evidence collector — materializes MinimalEvidenceSlice from requirements.

Aggressively minimize context. Optimization target:
minimum sufficient evidence, not maximum available context.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from codeanalyzer.documentation.api import DocumentationAPI
from codeanalyzer.domain.evidence import MinimalEvidenceSlice
from codeanalyzer.domain.findings import Finding
from codeanalyzer.evidence.api import EvidenceAPI


class EvidenceCollector(ABC):
    """Builds a MinimalEvidenceSlice for a finding from its evidence requirements."""

    def __init__(self, evidence: EvidenceAPI, documentation: DocumentationAPI) -> None:
        self.evidence = evidence
        self.documentation = documentation

    @abstractmethod
    def collect(self, finding: Finding) -> MinimalEvidenceSlice:
        """Collect the smallest evidence set sufficient to evaluate *finding*."""

    def empty_slice(self, finding: Finding) -> MinimalEvidenceSlice:
        """Helper for scaffolding / tests: empty slice bound to a finding."""
        return MinimalEvidenceSlice(
            id=f"evslice_{uuid.uuid4().hex[:12]}",
            finding_id=finding.id,
        )


class StubEvidenceCollector(EvidenceCollector):
    """Phase D scaffold — returns an empty slice with declared requirements noted."""

    def collect(self, finding: Finding) -> MinimalEvidenceSlice:
        slice_ = self.empty_slice(finding)
        # Record requirement kinds so downstream can see intent without full collection.
        for req in finding.evidence_requirements:
            slice_.metadata[f"req:{req.kind.value}"] = req.description
        return slice_
