"""MissingCallDetector — first real verification strategy.

Evaluates ORDERING properties of the form:
  "caller_before must be called before caller_after on any path to target"

Uses only the Evidence API. Never touches graph internals or LLM prompts.
Emits a Finding with a VerificationOutcome of PROVEN, VIOLATED, or UNKNOWN.
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


class MissingCallDetector(Detector):
    """Verify that a required call appears on the path to a target call.

    For an ORDERING property with scope_entity_ids = [before_id, after_id]:
    - Asks whether 'after_id' is reachable at all (via any entry in the graph)
    - If reachable: checks whether 'before_id' is also reachable (i.e. present
      somewhere in the call graph), as a proxy for ordering until full path
      condition analysis is available
    - Emits PROVEN if before appears on a path that reaches after
    - Emits VIOLATED if after is reachable but before is not
    - Emits UNKNOWN if the call graph has no data about either node
    """

    @property
    def id(self) -> str:
        return "possible_missing_call"

    @property
    def finding_types(self) -> list[str]:
        return ["possible_missing_call"]

    @property
    def required_evidence(self) -> list[EvidenceItemType]:
        return [EvidenceItemType.CALL_EDGE, EvidenceItemType.DOCUMENTATION]

    def detect(self, context: DetectorContext) -> list[Finding]:
        findings: list[Finding] = []

        for prop in context.active_properties:
            if prop.kind != PropertyKind.ORDERING:
                continue
            if len(prop.scope_entity_ids) < 2:
                continue

            before_id = prop.scope_entity_ids[0]
            after_id = prop.scope_entity_ids[1]

            outcome, message = self._evaluate(context, before_id, after_id)

            finding = Finding(
                id=f"f_{uuid.uuid4().hex[:12]}",
                analysis_id=context.analysis.id,
                snapshot_id=context.snapshot.id,
                source=FindingSource.INTERNAL_DETECTOR,
                detector=self.id,
                type="possible_missing_call",
                property_id=prop.id,
                verification_outcome=outcome,
                severity=Severity.WARNING if outcome == VerificationOutcome.VIOLATED else Severity.INFO,
                message=message,
                affected_entity_ids=[before_id, after_id],
                evidence_requirements=[
                    EvidenceRequirement(
                        kind=EvidenceItemType.CALL_EDGE,
                        description=f"call path involving {before_id} and {after_id}",
                        entity_ids=[before_id, after_id],
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
        before_id: str,
        after_id: str,
    ) -> tuple[VerificationOutcome, str]:
        evidence = context.evidence

        # Strongest check first: does before_id directly reach after_id?
        path = evidence.get_call_path(before_id, after_id)
        if path is not None:
            return (
                VerificationOutcome.PROVEN,
                f"{before_id} reaches {after_id} — ordering property holds",
            )

        # before cannot reach after. Determine whether either node actually
        # appears in the call graph (has at least one edge). Use the concrete
        # node_in_graph helper on ProgramModelEvidenceAPI; fall back to
        # checking callers for other backends.
        from codeanalyzer.evidence.program_model import ProgramModelEvidenceAPI  # local to avoid circular

        if isinstance(evidence, ProgramModelEvidenceAPI):
            after_in_graph = evidence.node_in_graph(after_id)
            before_in_graph = evidence.node_in_graph(before_id)
        else:
            # Fallback: non-empty callers or callees means the node exists.
            # get_callers/get_callees return Entity lists (registered entities only);
            # a length > 0 is a sufficient (but not necessary) signal.
            after_in_graph = len(evidence.get_callers(after_id)) > 0 or len(evidence.get_callees(after_id)) > 0
            before_in_graph = len(evidence.get_callers(before_id)) > 0 or len(evidence.get_callees(before_id)) > 0

        if not after_in_graph and not before_in_graph:
            return (
                VerificationOutcome.UNKNOWN,
                f"Insufficient call graph evidence to evaluate ordering of "
                f"{before_id} → {after_id}",
            )

        # At least one of the nodes is in the graph but before does not
        # precede after — ordering property is violated.
        return (
            VerificationOutcome.VIOLATED,
            f"{after_id} is in the call graph but {before_id} does not precede it — "
            f"ordering property may be violated",
        )
