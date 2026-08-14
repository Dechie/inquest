"""Property API — load and query correctness properties for a slice."""

from __future__ import annotations

from abc import ABC, abstractmethod

from codeanalyzer.domain.properties import CorrectnessProperty
from codeanalyzer.domain.slices import LogicalSlice
from codeanalyzer.domain.snapshots import Snapshot


class PropertyAPI(ABC):
    """Provides correctness properties applicable to a logical slice."""

    @abstractmethod
    def list_for_slice(self, snapshot: Snapshot, slice_: LogicalSlice) -> list[CorrectnessProperty]:
        """Return properties in scope for *slice_*."""

    @abstractmethod
    def get(self, property_id: str) -> CorrectnessProperty | None:
        """Look up a property by id."""

    @abstractmethod
    def for_detector(self, detector_id: str, slice_: LogicalSlice) -> list[CorrectnessProperty]:
        """Properties a detector may evaluate over *slice_*."""
