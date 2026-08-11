"""Initial correctness detector catalog (Phase E targets).

Prioritize structural / data-flow / call-flow correctness. Basic local issues
already handled well by existing analyzers should remain delegated.
"""

from __future__ import annotations

# Planned first-wave custom detectors (stubs registered later).
INITIAL_DETECTOR_IDS: list[str] = [
    "possible_missing_call",
    "missing_required_argument",
    "missing_field_propagation",
    "value_fails_to_reach_consumer",
    "unexpected_data_flow_termination",
    "use_before_definition",
    "possible_null_undefined_flow",
    "state_inconsistency",
    "resource_lifecycle_violation",
    "suspicious_control_flow_condition",
    "unexpected_workflow_deviation",
    "type_shape_inconsistency",
    "call_data_flow_anomaly",
]

# Categories intentionally delegated to external analyzers (Level-1).
DELEGATED_TO_EXTERNAL: list[str] = [
    "unreachable_code",
    "dead_branches",
    "unused_values",
    "unused_variables",
    "simple_type_errors",
]

# Deferred analysis domains (Phase H) — must not bypass architecture.
DEFERRED_DOMAINS: list[str] = [
    "taint_security",
    "concurrency_race",
    "specialized_numerical",
    "domain_specific_semantic",
]


def default_detector_ids() -> list[str]:
    return list(INITIAL_DETECTOR_IDS)
