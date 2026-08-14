"""Stub detectors — declare properties and evidence needs; produce no findings yet."""

from __future__ import annotations

from codeanalyzer.detectors.base import Detector, DetectorContext
from codeanalyzer.detectors.catalog import INITIAL_DETECTOR_IDS
from codeanalyzer.domain.enums import EvidenceItemType
from codeanalyzer.domain.findings import Finding


class StubDetector(Detector):
    """Placeholder that declares detector identity and typical evidence needs."""

    _EVIDENCE_BY_DETECTOR: dict[str, list[EvidenceItemType]] = {
        "possible_missing_call": [
            EvidenceItemType.CALL_EDGE,
            EvidenceItemType.CFG_FRAGMENT,
            EvidenceItemType.DOCUMENTATION,
        ],
        "missing_field_propagation": [
            EvidenceItemType.DATA_FLOW_FRAGMENT,
            EvidenceItemType.DOCUMENTATION,
        ],
        "resource_lifecycle_violation": [
            EvidenceItemType.CFG_FRAGMENT,
            EvidenceItemType.DERIVED_FACT,
        ],
    }

    def __init__(self, detector_id: str, finding_type: str | None = None) -> None:
        self._id = detector_id
        self._finding_type = finding_type or detector_id

    @property
    def id(self) -> str:
        return self._id

    @property
    def finding_types(self) -> list[str]:
        return [self._finding_type]

    @property
    def required_evidence(self) -> list[EvidenceItemType]:
        return list(self._EVIDENCE_BY_DETECTOR.get(self._id, []))

    def detect(self, context: DetectorContext) -> list[Finding]:
        # Scaffold: properties are loaded but no graph facts exist yet.
        _ = context.active_properties
        return []


def build_stub_detectors() -> list[Detector]:
    return [StubDetector(detector_id) for detector_id in INITIAL_DETECTOR_IDS]
