"""Detector API.

A detector should not:
- construct LLM prompts
- retrieve arbitrary repository files
- implement its own graph model
- know how evidence will be serialized for the LLM

Instead: Detector → Finding → Evidence Requirements → Collector → MinimalEvidenceSlice
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from codeanalyzer.documentation.api import DocumentationAPI
from codeanalyzer.domain.findings import Finding
from codeanalyzer.domain.slices import LogicalSlice
from codeanalyzer.domain.snapshots import AnalysisRun, Snapshot
from codeanalyzer.evidence.api import EvidenceAPI


@dataclass
class DetectorContext:
    """Shared context provided to detectors for one analysis run."""

    evidence: EvidenceAPI
    documentation: DocumentationAPI
    snapshot: Snapshot
    slice: LogicalSlice
    analysis: AnalysisRun


class Detector(ABC):
    """Independent consumer of the Evidence API that produces findings."""

    @property
    @abstractmethod
    def id(self) -> str:
        """Stable detector identifier, e.g. 'possible_missing_call'."""

    @property
    @abstractmethod
    def finding_types(self) -> list[str]:
        """Finding type strings this detector may emit."""

    @abstractmethod
    def detect(self, context: DetectorContext) -> list[Finding]:
        """Run detection over the logical slice; return candidate findings."""


class DetectorRegistry:
    """Registry of available detectors."""

    def __init__(self) -> None:
        self._detectors: dict[str, Detector] = {}

    def register(self, detector: Detector) -> None:
        self._detectors[detector.id] = detector

    def get(self, detector_id: str) -> Detector | None:
        return self._detectors.get(detector_id)

    def all(self) -> list[Detector]:
        return list(self._detectors.values())

    def run_all(self, context: DetectorContext) -> list[Finding]:
        findings: list[Finding] = []
        for detector in self._detectors.values():
            findings.extend(detector.detect(context))
        return findings
