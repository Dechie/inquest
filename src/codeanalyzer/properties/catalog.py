"""Seed correctness properties for scaffolding and tests."""

from __future__ import annotations

from codeanalyzer.domain.enums import PropertyKind, PropertySource, ProvenanceKind
from codeanalyzer.domain.properties import CorrectnessProperty
from codeanalyzer.domain.provenance import Provenance

RESERVE_BEFORE_PERSIST = CorrectnessProperty(
    id="prop_reserve_before_persist",
    snapshot_id="",
    kind=PropertyKind.ORDERING,
    statement="reserve(order) must precede persist(order)",
    source=PropertySource.DOCUMENTATION,
    provenance=Provenance(
        kind=ProvenanceKind.DOCUMENTATION_FACT,
        source="docs/orders.md",
    ),
    detector_ids=["possible_missing_call"],
    scope_entity_ids=["InventoryService.reserve", "OrderRepository.save"],
)

REQUIRED_FIELD_REACHES_CONSUMER = CorrectnessProperty(
    id="prop_required_field_reaches_consumer",
    snapshot_id="",
    kind=PropertyKind.REACHABILITY,
    statement="Required customer fields must reach persistence",
    source=PropertySource.DOCUMENTATION,
    provenance=Provenance(
        kind=ProvenanceKind.DOCUMENTATION_FACT,
        source="docs/orders.md",
    ),
    detector_ids=["missing_field_propagation", "value_fails_to_reach_consumer"],
    scope_entity_ids=["Order.customerId", "OrderRepository.save"],
)

RESOURCE_MUST_BE_RELEASED = CorrectnessProperty(
    id="prop_resource_released",
    snapshot_id="",
    kind=PropertyKind.RESOURCE,
    statement="Every acquired resource must be released",
    source=PropertySource.DETECTOR_RULE,
    detector_ids=["resource_lifecycle_violation"],
)

CATALOG: list[CorrectnessProperty] = [
    RESERVE_BEFORE_PERSIST,
    REQUIRED_FIELD_REACHES_CONSUMER,
    RESOURCE_MUST_BE_RELEASED,
]


def catalog_for_slice(slice_name: str) -> list[CorrectnessProperty]:
    """Return catalog properties whose scope matches *slice_name* (scaffold heuristic)."""
    name = slice_name.lower()
    selected: list[CorrectnessProperty] = []
    if any(token in name for token in ("checkout", "order", "persist", "reserve")):
        selected.extend([RESERVE_BEFORE_PERSIST, REQUIRED_FIELD_REACHES_CONSUMER])
    if any(token in name for token in ("resource", "io", "file", "connection")):
        selected.append(RESOURCE_MUST_BE_RELEASED)
    if not selected:
        selected = list(CATALOG)
    return selected
