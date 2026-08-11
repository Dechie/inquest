"""Scope resolution scaffold tests."""

from __future__ import annotations

from codeanalyzer.domain.enums import MembershipClass
from codeanalyzer.domain.snapshots import Snapshot
from codeanalyzer.scope.api import SeedSpecification
from codeanalyzer.scope.resolver import ScopeResolutionPipeline


def test_propose_and_approve() -> None:
    pipeline = ScopeResolutionPipeline()
    snapshot = Snapshot(id="snap_1", project_id="proj_1", commit_hash="abc")
    proposal = pipeline.propose(
        snapshot,
        SeedSpecification(raw="checkout workflow", kind="natural_language"),
        project_path=".",
    )
    assert proposal.name
    assert proposal.members
    assert any(m.membership == MembershipClass.CORE for m in proposal.members)

    slice_ = pipeline.approve(snapshot, proposal)
    assert slice_.approved
    assert pipeline.get_slice(slice_.id) is not None
