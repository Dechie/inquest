"""Correctness detectors — consumers of the Evidence API."""

from codeanalyzer.detectors.base import Detector, DetectorContext, DetectorRegistry
from codeanalyzer.detectors.catalog import default_detector_ids

__all__ = [
    "Detector",
    "DetectorContext",
    "DetectorRegistry",
    "default_detector_ids",
]
