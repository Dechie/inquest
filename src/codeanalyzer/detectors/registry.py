"""Detector registry — builds the active detector set for the orchestrator.

Real detectors live here once implemented. Stub detectors fill unimplemented
slots so the rest of the catalog remains declared without crashing.
"""

from __future__ import annotations

from codeanalyzer.detectors.base import Detector
from codeanalyzer.detectors.catalog import INITIAL_DETECTOR_IDS
from codeanalyzer.detectors.field_reachability import FieldReachabilityDetector
from codeanalyzer.detectors.missing_call import MissingCallDetector
from codeanalyzer.detectors.resource_lifecycle import ResourceLifecycleDetector
from codeanalyzer.detectors.stubs import StubDetector

# Map detector_id → concrete class for all real implementations.
_REAL_DETECTORS: dict[str, type[Detector]] = {
    "possible_missing_call": MissingCallDetector,
    "missing_field_propagation": FieldReachabilityDetector,
    "resource_lifecycle_violation": ResourceLifecycleDetector,
}


def build_detectors() -> list[Detector]:
    """Return the full detector list: real implementations + stubs for the rest."""
    detectors: list[Detector] = []
    for detector_id in INITIAL_DETECTOR_IDS:
        cls = _REAL_DETECTORS.get(detector_id)
        if cls is not None:
            detectors.append(cls())
        else:
            detectors.append(StubDetector(detector_id))
    return detectors

