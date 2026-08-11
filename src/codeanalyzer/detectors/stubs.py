"""Stub detectors that declare identity but produce no findings yet."""

from __future__ import annotations

from codeanalyzer.detectors.base import Detector, DetectorContext
from codeanalyzer.detectors.catalog import INITIAL_DETECTOR_IDS
from codeanalyzer.domain.findings import Finding


class StubDetector(Detector):
    """Placeholder for a planned correctness detector."""

    def __init__(self, detector_id: str, finding_type: str | None = None) -> None:
        self._id = detector_id
        self._finding_type = finding_type or detector_id

    @property
    def id(self) -> str:
        return self._id

    @property
    def finding_types(self) -> list[str]:
        return [self._finding_type]

    def detect(self, context: DetectorContext) -> list[Finding]:
        return []


def build_stub_detectors() -> list[Detector]:
    return [StubDetector(detector_id) for detector_id in INITIAL_DETECTOR_IDS]
