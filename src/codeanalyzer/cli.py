"""Command-line entry point."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from codeanalyzer import __version__
from codeanalyzer.analyzers.adapters import (
    ESLintAdapter,
    FlutterAnalyzeAdapter,
    PHPStanAdapter,
    TypeScriptAdapter,
)
from codeanalyzer.config.settings import Settings
from codeanalyzer.detectors.catalog import (
    DEFERRED_DOMAINS,
    DELEGATED_TO_EXTERNAL,
    INITIAL_DETECTOR_IDS,
)
from codeanalyzer.persistence.paths import AnalysisPaths
from codeanalyzer.persistence.stores import Stores
from codeanalyzer.pipeline.orchestrator import AnalysisOrchestrator
from codeanalyzer.scope.api import SeedSpecification


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="codeanalyzer",
        description=(
            "Codebase Correctness Analysis System — "
            "program-evidence integration and reasoning engine"
        ),
    )
    parser.add_argument("--version", action="store_true", help="Print version and exit")

    sub = parser.add_subparsers(dest="command")

    sub.add_parser("version", help="Print version")

    init_p = sub.add_parser("init", help="Initialize .codeanalyzer/ storage for a project")
    init_p.add_argument("path", nargs="?", default=".", help="Project root (default: .)")

    status_p = sub.add_parser("status", help="Show scaffold status and planned capabilities")
    status_p.add_argument("path", nargs="?", default=".", help="Project root")

    scope_p = sub.add_parser("scope", help="Propose a logical slice from a seed (scaffold)")
    scope_p.add_argument("seed", help="Seed: path, symbol, feature name, or description")
    scope_p.add_argument("--path", default=".", help="Project root")
    scope_p.add_argument(
        "--approve",
        action="store_true",
        help="Auto-approve and persist the proposed slice (dev only)",
    )

    analyze_p = sub.add_parser(
        "analyze",
        help="Run scaffolded analysis pipeline (requires --approve for scope)",
    )
    analyze_p.add_argument("seed", help="Feature seed for scope resolution")
    analyze_p.add_argument("--path", default=".", help="Project root")
    analyze_p.add_argument(
        "--approve",
        action="store_true",
        help="Auto-approve the proposed slice before analysis (dev only)",
    )
    analyze_p.add_argument(
        "--enable-llm",
        action="store_true",
        help="Run the semantic judge (currently a Phase F stub)",
    )

    sub.add_parser("detectors", help="List planned / stub detectors")
    sub.add_parser("analyzers", help="List analyzer adapter stubs")

    return parser


def _settings_for(
    path: str,
    *,
    approve: bool = False,
    enable_llm: bool = False,
) -> Settings:
    root = str(Path(path).resolve())
    return Settings.from_environ().with_cli_overrides(
        project_path=root,
        auto_approve=approve,
        enable_llm=enable_llm,
    )


def cmd_init(path: str) -> int:
    settings = _settings_for(path)
    orch = AnalysisOrchestrator(settings=settings)
    project, snapshot = orch.init_project(path)
    paths = orch.repo.paths
    assert paths is not None
    print(f"Initialized analysis store at {paths.root}")
    print(f"  database: {paths.db_path}")
    print(f"  graphs:   {paths.graphs_dir}")
    print(f"  snapshots:{paths.snapshots_dir}")
    print(f"  cache:    {paths.cache_dir}")
    print(f"  project:  {project.id} ({project.name})")
    print(f"  snapshot: {snapshot.id}")
    return 0


def cmd_status(path: str) -> int:
    settings = _settings_for(path)
    root = Path(path).resolve()
    paths = AnalysisPaths.for_project(root, dir_name=settings.analysis_dir_name)
    print(f"codeanalyzer {__version__}")
    print(f"project: {root}")
    print(f"analysis dir: {paths.root} ({'exists' if paths.root.exists() else 'missing'})")
    print(f"db: {paths.db_path} ({'exists' if paths.db_path.exists() else 'missing'})")
    print()
    print("Settings:")
    print(f"  languages: {', '.join(settings.languages)}")
    print(f"  enable_llm: {settings.enable_llm}")
    print(f"  max_evidence_items: {settings.max_evidence_items}")
    print(f"  auto_approve_scope: {settings.auto_approve_scope}")
    if paths.db_path.exists():
        stores = Stores.open(paths)
        print()
        print("Persisted:")
        print(f"  projects: {len(stores.projects.list_all())}")
        print(f"  snapshots: {len(stores.snapshots.list_all())}")
        print(f"  slices: {len(stores.slices.list())}")
        print(f"  analyses: {len(stores.analyses.list_all())}")
        print(f"  findings: {len(stores.findings.list_all())}")
        stores.close()
    print()
    print("Roadmap phases:")
    print("  A  Repository + program substrate")
    print("  B  External analyzer layer")
    print("  C  Scope engine")
    print("  D  Evidence architecture")
    print("  E  Initial correctness detectors")
    print("  F  LLM reasoning")
    print("  G  Detector composition")
    print("  H  New analysis domains")
    print()
    print(f"Planned detectors: {len(INITIAL_DETECTOR_IDS)}")
    print(f"Delegated to external analyzers: {len(DELEGATED_TO_EXTERNAL)}")
    print(f"Deferred domains: {len(DEFERRED_DOMAINS)}")
    return 0


def cmd_scope(seed: str, path: str, approve: bool) -> int:
    settings = _settings_for(path, approve=approve)
    orch = AnalysisOrchestrator(settings=settings)
    _project, snapshot = orch.init_project(path)
    pipeline = orch.scope
    proposal = pipeline.propose(
        snapshot,
        SeedSpecification(raw=seed),
        project_path=str(Path(path).resolve()),
    )
    print(f"Proposed slice: {proposal.name}")
    print(f"Intent: {proposal.intent}")
    print()
    for membership in ("CORE", "RELATED", "EXCLUDED"):
        members = [m for m in proposal.members if m.membership.value == membership]
        if not members:
            continue
        print(membership)
        for m in members:
            mark = {"CORE": "✓", "RELATED": "?", "EXCLUDED": "✗"}[membership]
            reasons = "; ".join(m.reasons) if m.reasons else ""
            print(f"  {mark} {m.entity_id}" + (f"  ({reasons})" if reasons else ""))
        print()

    if settings.auto_approve_scope:
        slice_ = pipeline.approve(snapshot, proposal)
        print(f"Approved and stored slice id={slice_.id}")
    else:
        print("Not persisted. Re-run with --approve after review (scaffold).")
    return 0


def cmd_analyze(seed: str, path: str, approve: bool, enable_llm: bool) -> int:
    settings = _settings_for(path, approve=approve, enable_llm=enable_llm)
    orch = AnalysisOrchestrator(settings=settings)
    project, snapshot = orch.init_project(path)
    proposal = orch.scope.propose(
        snapshot,
        SeedSpecification(raw=seed),
        project_path=str(Path(path).resolve()),
    )
    if not settings.auto_approve_scope:
        print("Scope not approved. Re-run with --approve after review.")
        return 1
    slice_ = orch.scope.approve(snapshot, proposal)
    result = orch.run(project, snapshot, slice_)
    payload = {
        "analysis_id": result.analysis.id,
        "status": result.analysis.status.value,
        "slice_id": result.slice.id,
        "slice_name": result.slice.name,
        "members": len(result.slice.members),
        "diagnostics": len(result.diagnostics),
        "findings": len(result.findings),
        "evidence_slices": len(result.evidence_slices),
        "judgments": len(result.judgments),
        "note": (
            "Scaffold run: detectors and LLM are stubs; "
            "external analyzers run only when discoverable and implemented."
        ),
    }
    print(json.dumps(payload, indent=2))
    return 0


def cmd_detectors() -> int:
    print("Initial correctness detectors (Phase E targets):")
    for detector_id in INITIAL_DETECTOR_IDS:
        print(f"  - {detector_id}")
    print()
    print("Delegated to external analyzers:")
    for item in DELEGATED_TO_EXTERNAL:
        print(f"  - {item}")
    print()
    print("Deferred domains:")
    for item in DEFERRED_DOMAINS:
        print(f"  - {item}")
    return 0


def cmd_analyzers() -> int:
    adapters = [
        FlutterAnalyzeAdapter(),
        ESLintAdapter(),
        PHPStanAdapter(),
        TypeScriptAdapter(),
    ]
    print("Analyzer adapters (scaffold):")
    for adapter in adapters:
        caps = adapter.capabilities()
        available = adapter.discover()
        status = "available" if available else "not discovered / stub"
        print(f"  - {caps.analyzer_id}: {caps.display_name} [{status}]")
        print(f"      languages: {', '.join(caps.languages)}")
        print(f"      provides:  {', '.join(caps.provides)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version or args.command == "version":
        print(__version__)
        return 0

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "init":
        return cmd_init(args.path)
    if args.command == "status":
        return cmd_status(args.path)
    if args.command == "scope":
        return cmd_scope(args.seed, args.path, args.approve)
    if args.command == "analyze":
        return cmd_analyze(args.seed, args.path, args.approve, args.enable_llm)
    if args.command == "detectors":
        return cmd_detectors()
    if args.command == "analyzers":
        return cmd_analyzers()

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
