"""End-to-end operational flow (architecture §30).

User intent → scope → program model + external analyzers → detectors →
minimal evidence → LLM judgment → stored result.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, Field

from codeanalyzer.analyzers.adapters import (
    ESLintAdapter,
    FlutterAnalyzeAdapter,
    PHPStanAdapter,
    TypeScriptAdapter,
)
from codeanalyzer.analyzers.registry import AnalyzerRegistry
from codeanalyzer.detectors.base import DetectorContext, DetectorRegistry
from codeanalyzer.detectors.stubs import build_stub_detectors
from codeanalyzer.documentation.stub import StubDocumentationAPI
from codeanalyzer.domain.diagnostics import ExternalDiagnostic
from codeanalyzer.domain.evidence import MinimalEvidenceSlice
from codeanalyzer.domain.findings import Finding
from codeanalyzer.domain.slices import LogicalSlice
from codeanalyzer.domain.snapshots import AnalysisRun, AnalysisStatus, Project, Snapshot
from codeanalyzer.evidence.collector import StubEvidenceCollector
from codeanalyzer.evidence.stub import StubEvidenceAPI
from codeanalyzer.llm.judgment import JudgmentResult, StubSemanticJudge
from codeanalyzer.repository.manager import RepositoryManager
from codeanalyzer.scope.api import SeedSpecification
from codeanalyzer.scope.resolver import ScopeResolutionPipeline


class AnalysisResult(BaseModel):
    """Aggregated result of one analysis run."""

    analysis: AnalysisRun
    slice: LogicalSlice
    diagnostics: list[ExternalDiagnostic] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    evidence_slices: list[MinimalEvidenceSlice] = Field(default_factory=list)
    judgments: list[JudgmentResult] = Field(default_factory=list)


class AnalysisOrchestrator:
    """Wires subsystems for the scaffolded end-to-end pipeline.

    Real program models, analyzers, and LLM stages plug in without changing
    this orchestration shape.
    """

    def __init__(self) -> None:
        self.repo = RepositoryManager()
        self.scope = ScopeResolutionPipeline()
        self.analyzers = AnalyzerRegistry()
        for adapter_cls in (
            FlutterAnalyzeAdapter,
            ESLintAdapter,
            PHPStanAdapter,
            TypeScriptAdapter,
        ):
            self.analyzers.register(adapter_cls())

        self.detectors = DetectorRegistry()
        for detector in build_stub_detectors():
            self.detectors.register(detector)

        self.evidence_api = StubEvidenceAPI()
        self.documentation_api = StubDocumentationAPI()
        self.collector = StubEvidenceCollector(self.evidence_api, self.documentation_api)
        self.judge = StubSemanticJudge()

    def init_project(self, path: str, name: str | None = None) -> tuple[Project, Snapshot]:
        project = self.repo.register_project(path, name=name)
        snapshot = self.repo.create_snapshot(project)
        return project, snapshot

    def resolve_and_approve_slice(
        self,
        snapshot: Snapshot,
        seed: str,
        *,
        project_path: str,
        auto_approve: bool = False,
    ) -> LogicalSlice | None:
        """Propose a logical slice; auto-approve only when explicitly requested.

        Production flow requires human approval before expensive analysis.
        """
        proposal = self.scope.propose(
            snapshot,
            SeedSpecification(raw=seed),
            project_path=project_path,
        )
        if not auto_approve:
            return None  # caller should present proposal for approval
        return self.scope.approve(snapshot, proposal)

    def run(
        self,
        project: Project,
        snapshot: Snapshot,
        slice_: LogicalSlice,
    ) -> AnalysisResult:
        analysis = AnalysisRun(
            id=f"an_{uuid.uuid4().hex[:12]}",
            slice_id=slice_.id,
            snapshot_id=snapshot.id,
            status=AnalysisStatus.RUNNING,
        )

        diagnostics: list[ExternalDiagnostic] = []
        # Phase B: run discoverable analyzers; scaffold skips unavailable tools.
        for adapter in self.analyzers.discover_available():
            try:
                diagnostics.extend(
                    adapter.analyze(snapshot, slice_, project_path=project.path)
                )
            except NotImplementedError:
                continue

        context = DetectorContext(
            evidence=self.evidence_api,
            documentation=self.documentation_api,
            snapshot=snapshot,
            slice=slice_,
            analysis=analysis,
        )
        findings = self.detectors.run_all(context)

        evidence_slices: list[MinimalEvidenceSlice] = []
        judgments: list[JudgmentResult] = []
        for finding in findings:
            evidence = self.collector.collect(finding)
            evidence_slices.append(evidence)
            judgments.append(self.judge.judge(finding, evidence))

        analysis.status = AnalysisStatus.COMPLETED
        analysis.completed_at = datetime.now(UTC)

        return AnalysisResult(
            analysis=analysis,
            slice=slice_,
            diagnostics=diagnostics,
            findings=findings,
            evidence_slices=evidence_slices,
            judgments=judgments,
        )
