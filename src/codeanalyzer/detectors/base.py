"""Detector API.

A detector evaluates correctness properties against evidence available through
the Evidence API. It must not construct LLM prompts, retrieve arbitrary files,
or implement its own graph model.

Flow: Property → Detector → Evidence queries → Candidate violation → Refinement
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from codeanalyzer.documentation.api import DocumentationAPI
from codeanalyzer.domain.enums import EvidenceItemType
from codeanalyzer.domain.findings import Finding
from codeanalyzer.domain.properties import CorrectnessProperty
from codeanalyzer.domain.slices import LogicalSlice
from codeanalyzer.domain.snapshots import AnalysisRun, Snapshot
from codeanalyzer.evidence.api import EvidenceAPI
from codeanalyzer.properties.api import PropertyAPI


@dataclass
class DetectorContext:
    """Shared context provided to detectors for one analysis run."""

    evidence: EvidenceAPI
    documentation: DocumentationAPI
    properties: PropertyAPI
    snapshot: Snapshot
    slice: LogicalSlice
    analysis: AnalysisRun
    active_properties: list[CorrectnessProperty] = field(default_factory=list)


class Detector(ABC):
    """Evaluates properties using the Evidence API; produces candidate findings."""

    @property
    @abstractmethod
    def id(self) -> str:
        """Stable detector identifier, e.g. 'possible_missing_call'."""

    @property
    @abstractmethod
    def finding_types(self) -> list[str]:
        """Finding type strings this detector may emit."""

    @property
    def required_evidence(self) -> list[EvidenceItemType]:
        """Evidence kinds this detector needs for a typical evaluation."""
        return []

    @abstractmethod
    def detect(self, context: DetectorContext) -> list[Finding]:
        """Evaluate applicable properties; return candidate findings."""


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
            prop_subset = context.properties.for_detector(detector.id, context.slice)
            detector_context = DetectorContext(
                evidence=context.evidence,
                documentation=context.documentation,
                properties=context.properties,
                snapshot=context.snapshot,
                slice=context.slice,
                analysis=context.analysis,
                active_properties=prop_subset,
            )
            findings.extend(detector.detect(detector_context))
        return findings
