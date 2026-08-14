"""Stub PropertyAPI backed by the seed catalog."""

from __future__ import annotations

from codeanalyzer.domain.properties import CorrectnessProperty
from codeanalyzer.domain.slices import LogicalSlice
from codeanalyzer.domain.snapshots import Snapshot
from codeanalyzer.properties.api import PropertyAPI
from codeanalyzer.properties.catalog import catalog_for_slice


class StubPropertyAPI(PropertyAPI):
    """Returns seed properties scoped to the logical slice name."""

    def list_for_slice(self, snapshot: Snapshot, slice_: LogicalSlice) -> list[CorrectnessProperty]:
        return [
            prop.model_copy(update={"snapshot_id": snapshot.id, "slice_id": slice_.id})
            for prop in catalog_for_slice(slice_.name)
        ]

    def get(self, property_id: str) -> CorrectnessProperty | None:
        for prop in catalog_for_slice(""):
            if prop.id == property_id:
                return prop
        return None

    def for_detector(self, detector_id: str, slice_: LogicalSlice) -> list[CorrectnessProperty]:
        return [
            prop
            for prop in catalog_for_slice(slice_.name)
            if detector_id in prop.detector_ids
        ]
