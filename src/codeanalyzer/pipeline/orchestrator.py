"""End-to-end operational flow (architecture §15).

Conceptual order with feedback loops:
  slice → program representation + external inputs → analysis substrate →
  evidence API → properties → detectors → evidence refinement →
  documentation → LLM → persistent artifacts.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, Field

from codeanalyzer.analysis.program_model import ProgramModelAnalysisSubstrate
from codeanalyzer.analyzers.adapters import (
    ESLintAdapter,
    FlutterAnalyzeAdapter,
    PHPStanAdapter,
    TypeScriptAdapter,
)
from codeanalyzer.analyzers.registry import AnalyzerRegistry
from codeanalyzer.config.settings import Settings
from codeanalyzer.detectors.base import DetectorContext, DetectorRegistry
from codeanalyzer.detectors.registry import build_detectors
from codeanalyzer.documentation.stub import StubDocumentationAPI
from codeanalyzer.domain.diagnostics import ExternalDiagnostic
from codeanalyzer.domain.evidence import MinimalEvidenceSlice, RefinementResult
from codeanalyzer.domain.findings import Finding
from codeanalyzer.domain.properties import CorrectnessProperty
from codeanalyzer.domain.slices import LogicalSlice
from codeanalyzer.domain.snapshots import AnalysisRun, AnalysisStatus, Project, Snapshot
from codeanalyzer.evidence.program_model import ProgramModelEvidenceAPI
from codeanalyzer.evidence.refiner import StubEvidenceRefiner
from codeanalyzer.llm.judgment import JudgmentResult, StubSemanticJudge
from codeanalyzer.persistence.paths import AnalysisPaths
from codeanalyzer.persistence.stores import Stores
from codeanalyzer.program.builder import ProgramModelBuilder, empty_program_model_builder
from codeanalyzer.properties.stub import StubPropertyAPI
from codeanalyzer.repository.manager import RepositoryManager
from codeanalyzer.scope.resolver import ScopeResolutionPipeline


class AnalysisResult(BaseModel):
    """Aggregated result of one analysis run."""

    analysis: AnalysisRun
    slice: LogicalSlice
    properties: list[CorrectnessProperty] = Field(default_factory=list)
    diagnostics: list[ExternalDiagnostic] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    refinements: list[RefinementResult] = Field(default_factory=list)
    evidence_slices: list[MinimalEvidenceSlice] = Field(default_factory=list)
    judgments: list[JudgmentResult] = Field(default_factory=list)


class AnalysisOrchestrator:
    """Wires subsystems for the property-aware analysis pipeline."""

    def __init__(
        self,
        settings: Settings | None = None,
        stores: Stores | None = None,
        program_model_builder: ProgramModelBuilder | None = None,
    ) -> None:
        self.settings = settings or Settings()
        self.stores = stores
        self._program_model_builder: ProgramModelBuilder = (
            program_model_builder or empty_program_model_builder
        )

        self.repo = RepositoryManager(stores=stores)
        self.scope = ScopeResolutionPipeline(
            slice_store=stores.slices if stores is not None else None
        )
        self.analyzers = AnalyzerRegistry()
        for adapter_cls in (
            FlutterAnalyzeAdapter,
            ESLintAdapter,
            PHPStanAdapter,
            TypeScriptAdapter,
        ):
            self.analyzers.register(adapter_cls())

        self.detectors = DetectorRegistry()
        for detector in build_detectors():
            self.detectors.register(detector)

        self.documentation_api = StubDocumentationAPI()
        self.property_api = StubPropertyAPI()
        self.judge = StubSemanticJudge()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def init_project(self, project_path: str) -> tuple[Project, Snapshot]:
        """Ensure persistence is initialised and return project + snapshot."""
        self._ensure_stores(project_path)
        assert self.stores is not None
        project = self.repo.register_project(project_path)
        snapshot = self.repo.create_snapshot(project)
        return project, snapshot

    def resolve_slice(
        self,
        snapshot: Snapshot,
        seed: str,
        *,
        project_path: str,
        auto_approve: bool | None = None,
    ) -> LogicalSlice | None:
        """Propose and optionally approve a logical slice for *seed*.

        Returns the approved slice, or None if auto-approval is disabled.
        Delegates to the scope pipeline; callers that need finer control
        can use `self.scope.propose` and `self.scope.approve` directly.
        """
        from codeanalyzer.scope.api import SeedSpecification

        proposal = self.scope.propose(
            snapshot,
            SeedSpecification(raw=seed),
            project_path=project_path,
        )
        approve = self.settings.auto_approve_scope if auto_approve is None else auto_approve
        if not approve:
            return None
        return self.scope.approve(snapshot, proposal)

    def run(
        self,
        project: Project,
        snapshot: Snapshot,
        slice_: LogicalSlice,
    ) -> AnalysisResult:
        """Execute a full analysis run for *slice_* against *snapshot*."""
        self._ensure_stores(project.path)

        # Build program model and wire real evidence + substrate for this run
        program_model = self._program_model_builder(snapshot, slice_)
        evidence_api = ProgramModelEvidenceAPI(program_model)
        substrate = ProgramModelAnalysisSubstrate(program_model)
        refiner = StubEvidenceRefiner(
            evidence_api,
            self.documentation_api,
            substrate,
        )

        analysis = AnalysisRun(
            id=f"an_{uuid.uuid4().hex[:12]}",
            slice_id=slice_.id,
            snapshot_id=snapshot.id,
            status=AnalysisStatus.RUNNING,
        )
        self._persist_analysis(analysis)

        properties = self.property_api.list_for_slice(snapshot, slice_)
        self._persist_properties(properties)

        diagnostics: list[ExternalDiagnostic] = []
        for adapter in self.analyzers.discover_available():
            try:
                diagnostics.extend(
                    adapter.analyze(snapshot, slice_, project_path=project.path)
                )
            except NotImplementedError:
                continue

        context = DetectorContext(
            evidence=evidence_api,
            documentation=self.documentation_api,
            properties=self.property_api,
            snapshot=snapshot,
            slice=slice_,
            analysis=analysis,
            active_properties=properties,
        )
        findings = self.detectors.run_all(context)

        refinements: list[RefinementResult] = []
        evidence_slices: list[MinimalEvidenceSlice] = []
        judgments: list[JudgmentResult] = []
        for finding in findings:
            refinement = refiner.refine_until_done(
                finding,
                snapshot=snapshot,
                slice_=slice_,
            )
            refinements.append(refinement)
            evidence_slices.append(refinement.slice)
            if self.settings.enable_llm:
                judgments.append(self.judge.judge(finding, refinement.slice))

        analysis.status = AnalysisStatus.COMPLETED
        analysis.completed_at = datetime.now(UTC)
        self._persist_result(analysis, diagnostics, findings, evidence_slices)

        return AnalysisResult(
            analysis=analysis,
            slice=slice_,
            properties=properties,
            diagnostics=diagnostics,
            findings=findings,
            refinements=refinements,
            evidence_slices=evidence_slices,
            judgments=judgments,
        )

    # ------------------------------------------------------------------
    # Internal helpers — kept below public API
    # ------------------------------------------------------------------

    def _ensure_stores(self, project_path: str) -> None:
        if self.stores is None:
            paths = AnalysisPaths.for_project(
                project_path,
                dir_name=self.settings.analysis_dir_name,
            )
            self.stores = Stores.open(paths)
            self.repo.paths = paths
        self.repo.stores = self.stores
        self.scope.slice_store = self.stores.slices

    def _persist_analysis(self, analysis: AnalysisRun) -> None:
        if self.stores is not None:
            self.stores.analyses.save(analysis)

    def _persist_properties(self, properties: list[CorrectnessProperty]) -> None:
        if self.stores is None:
            return
        for prop in properties:
            self.stores.properties.save(prop)

    def _persist_result(
        self,
        analysis: AnalysisRun,
        diagnostics: list[ExternalDiagnostic],
        findings: list[Finding],
        evidence_slices: list[MinimalEvidenceSlice],
    ) -> None:
        if self.stores is None:
            return
        self.stores.analyses.save(analysis)
        for diagnostic in diagnostics:
            self.stores.analyses.save_diagnostic(diagnostic)
        for finding in findings:
            self.stores.findings.save(finding)
        for evidence in evidence_slices:
            self.stores.evidence.save(evidence)

