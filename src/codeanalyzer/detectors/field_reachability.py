"""FieldReachabilityDetector — second real verification strategy.

Evaluates REACHABILITY properties of the form:
  "field_id must flow to consumer_id"

Uses only the Evidence API's data-flow surface. Never touches graph
internals or LLM prompts. Emits PROVEN, VIOLATED, or UNKNOWN.
"""

from __future__ import annotations

import uuid

from codeanalyzer.detectors.base import Detector, DetectorContext
from codeanalyzer.domain.enums import (
    EvidenceItemType,
    FindingSource,
    PropertyKind,
    Severity,
    VerificationOutcome,
)
from codeanalyzer.domain.evidence import EvidenceRequirement
from codeanalyzer.domain.findings import Finding


class FieldReachabilityDetector(Detector):
    """Verify that a required field flows to its expected consumer.

    For a REACHABILITY property with scope_entity_ids = [field_id, consumer_id]:
    - PROVEN   — a data-flow path from field_id to consumer_id exists
    - VIOLATED — field_id and/or consumer_id are in the data-flow graph
                 but no path connects them (field is dropped)
    - UNKNOWN  — neither node appears in the data-flow graph (no evidence)
    """

    @property
    def id(self) -> str:
        return "missing_field_propagation"

    @property
    def finding_types(self) -> list[str]:
        return ["missing_field_propagation", "value_fails_to_reach_consumer"]

    @property
    def required_evidence(self) -> list[EvidenceItemType]:
        return [EvidenceItemType.DATA_FLOW_FRAGMENT, EvidenceItemType.DOCUMENTATION]

    def detect(self, context: DetectorContext) -> list[Finding]:
        findings: list[Finding] = []

        for prop in context.active_properties:
            if prop.kind != PropertyKind.REACHABILITY:
                continue
            if len(prop.scope_entity_ids) < 2:
                continue

            field_id = prop.scope_entity_ids[0]
            consumer_id = prop.scope_entity_ids[1]

            outcome, message = self._evaluate(context, field_id, consumer_id)

            finding = Finding(
                id=f"f_{uuid.uuid4().hex[:12]}",
                analysis_id=context.analysis.id,
                snapshot_id=context.snapshot.id,
                source=FindingSource.INTERNAL_DETECTOR,
                detector=self.id,
                type="missing_field_propagation",
                property_id=prop.id,
                verification_outcome=outcome,
                severity=Severity.WARNING if outcome == VerificationOutcome.VIOLATED else Severity.INFO,
                message=message,
                affected_entity_ids=[field_id, consumer_id],
                evidence_requirements=[
                    EvidenceRequirement(
                        kind=EvidenceItemType.DATA_FLOW_FRAGMENT,
                        description=f"data-flow path from {field_id} to {consumer_id}",
                        entity_ids=[field_id, consumer_id],
                    ),
                    EvidenceRequirement(
                        kind=EvidenceItemType.DOCUMENTATION,
                        description=f"documented intent for property: {prop.statement}",
                        entity_ids=[],
                        required=False,
                    ),
                ],
            )
            findings.append(finding)

        return findings

    def _evaluate(
        self,
        context: DetectorContext,
        field_id: str,
        consumer_id: str,
    ) -> tuple[VerificationOutcome, str]:
        evidence = context.evidence

        # Primary check: does a data-flow path exist from field to consumer?
        paths = evidence.get_data_flow(field_id, consumer_id)
        if paths:
            return (
                VerificationOutcome.PROVEN,
                f"{field_id} flows to {consumer_id} — reachability property holds",
            )

        # No path found. Determine if either node is present in the graph.
        from codeanalyzer.evidence.program_model import ProgramModelEvidenceAPI  # local import

        if isinstance(evidence, ProgramModelEvidenceAPI):
            field_in_graph = evidence.node_in_data_flow(field_id)
            consumer_in_graph = evidence.node_in_data_flow(consumer_id)
        else:
            # Fallback: use field_consumers / field_producers for other backends
            field_in_graph = len(evidence.get_field_consumers(field_id, "")) > 0
            consumer_in_graph = len(evidence.get_field_producers(consumer_id, "")) > 0

        if not field_in_graph and not consumer_in_graph:
            return (
                VerificationOutcome.UNKNOWN,
                f"Insufficient data-flow evidence to evaluate reachability of "
                f"{field_id} → {consumer_id}",
            )

        # At least one node is present but field does not reach consumer.
        return (
            VerificationOutcome.VIOLATED,
            f"{field_id} does not reach {consumer_id} in the data-flow graph — "
            f"field may be dropped before reaching its consumer",
        )
