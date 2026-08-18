"""ResourceLifecycleDetector — third real verification strategy.

Evaluates RESOURCE properties of the form:
  "acquire_id must be followed by release_id on all paths"

A resource leak is when an acquire call is reachable in the call graph
but no corresponding release call is reachable from any acquire site.

Uses only the Evidence API's call-graph surface. Emits PROVEN, VIOLATED,
or UNKNOWN. Never touches graph internals or LLM prompts.
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


class ResourceLifecycleDetector(Detector):
    """Verify that every resource acquire is paired with a release.

    For a RESOURCE property with scope_entity_ids = [acquire_id, release_id]:
    - PROVEN   — acquire_id can reach release_id in the call graph
    - VIOLATED — acquire_id is reachable but release_id is not reachable
                 from any node that can reach acquire_id (leak path exists)
    - UNKNOWN  — acquire_id does not appear in the call graph (no evidence)
    """

    @property
    def id(self) -> str:
        return "resource_lifecycle_violation"

    @property
    def finding_types(self) -> list[str]:
        return ["resource_lifecycle_violation"]

    @property
    def required_evidence(self) -> list[EvidenceItemType]:
        return [EvidenceItemType.CALL_EDGE, EvidenceItemType.CFG_FRAGMENT]

    def detect(self, context: DetectorContext) -> list[Finding]:
        findings: list[Finding] = []

        for prop in context.active_properties:
            if prop.kind != PropertyKind.RESOURCE:
                continue
            if len(prop.scope_entity_ids) < 2:
                continue

            acquire_id = prop.scope_entity_ids[0]
            release_id = prop.scope_entity_ids[1]

            outcome, message = self._evaluate(context, acquire_id, release_id)

            finding = Finding(
                id=f"f_{uuid.uuid4().hex[:12]}",
                analysis_id=context.analysis.id,
                snapshot_id=context.snapshot.id,
                source=FindingSource.INTERNAL_DETECTOR,
                detector=self.id,
                type="resource_lifecycle_violation",
                property_id=prop.id,
                verification_outcome=outcome,
                severity=Severity.ERROR if outcome == VerificationOutcome.VIOLATED else Severity.INFO,
                message=message,
                affected_entity_ids=[acquire_id, release_id],
                evidence_requirements=[
                    EvidenceRequirement(
                        kind=EvidenceItemType.CALL_EDGE,
                        description=f"call path from {acquire_id} to {release_id}",
                        entity_ids=[acquire_id, release_id],
                    ),
                    EvidenceRequirement(
                        kind=EvidenceItemType.CFG_FRAGMENT,
                        description=f"control-flow paths through {acquire_id}",
                        entity_ids=[acquire_id],
                        required=False,
                    ),
                ],
            )
            findings.append(finding)

        return findings

    def _evaluate(
        self,
        context: DetectorContext,
        acquire_id: str,
        release_id: str,
    ) -> tuple[VerificationOutcome, str]:
        evidence = context.evidence

        # Best case: acquire directly reaches release in the call graph.
        path = evidence.get_call_path(acquire_id, release_id)
        if path is not None:
            return (
                VerificationOutcome.PROVEN,
                f"{acquire_id} reaches {release_id} — resource is released on this path",
            )

        # No path. Check whether acquire appears in the call graph at all.
        from codeanalyzer.evidence.program_model import ProgramModelEvidenceAPI  # local to avoid circular

        if isinstance(evidence, ProgramModelEvidenceAPI):
            acquire_in_graph = evidence.node_in_graph(acquire_id)
            release_in_graph = evidence.node_in_graph(release_id)
        else:
            acquire_in_graph = (
                len(evidence.get_callers(acquire_id)) > 0
                or len(evidence.get_callees(acquire_id)) > 0
            )
            release_in_graph = (
                len(evidence.get_callers(release_id)) > 0
                or len(evidence.get_callees(release_id)) > 0
            )

        if not acquire_in_graph:
            return (
                VerificationOutcome.UNKNOWN,
                f"Insufficient call graph evidence to evaluate resource lifecycle of "
                f"{acquire_id} / {release_id}",
            )

        # acquire is in the graph but release is not reachable from it.
        if not release_in_graph:
            return (
                VerificationOutcome.VIOLATED,
                f"{acquire_id} is called but {release_id} does not appear in the call "
                f"graph — resource may never be released",
            )

        return (
            VerificationOutcome.VIOLATED,
            f"{acquire_id} is called but does not reach {release_id} — "
            f"resource may leak on some paths",
        )
