"""Pipeline orchestration smoke tests."""

from __future__ import annotations

from pathlib import Path

from codeanalyzer.pipeline.orchestrator import AnalysisOrchestrator
from codeanalyzer.scope.api import SeedSpecification


def test_scaffold_analyze_run(tmp_path: Path) -> None:
    orch = AnalysisOrchestrator()
    project, snapshot = orch.init_project(str(tmp_path))
    proposal = orch.scope.propose(
        snapshot,
        SeedSpecification(raw="checkout"),
        project_path=str(tmp_path),
    )
    slice_ = orch.scope.approve(snapshot, proposal)
    result = orch.run(project, snapshot, slice_)

    assert result.analysis.status.value == "completed"
    assert result.slice.id == slice_.id
    assert len(result.properties) >= 1
    assert result.findings == []
    assert result.judgments == []
    assert orch.stores is not None
    assert len(orch.stores.properties.list_for_slice(slice_.id)) >= 1
