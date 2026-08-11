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
from codeanalyzer.detectors.catalog import (
    DEFERRED_DOMAINS,
    DELEGATED_TO_EXTERNAL,
    INITIAL_DETECTOR_IDS,
)
from codeanalyzer.persistence.db import Database
from codeanalyzer.persistence.paths import AnalysisPaths
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

    sub.add_parser("detectors", help="List planned / stub detectors")
    sub.add_parser("analyzers", help="List analyzer adapter stubs")

    return parser


def cmd_init(path: str) -> int:
    root = Path(path).resolve()
    paths = AnalysisPaths.for_project(root)
    paths.ensure()
    db = Database(paths.db_path)
    db.initialize()
    db.close()
    print(f"Initialized analysis store at {paths.root}")
    print(f"  database: {paths.db_path}")
    print(f"  graphs:   {paths.graphs_dir}")
    print(f"  snapshots:{paths.snapshots_dir}")
    print(f"  cache:    {paths.cache_dir}")
    return 0


def cmd_status(path: str) -> int:
    root = Path(path).resolve()
    paths = AnalysisPaths.for_project(root)
    print(f"codeanalyzer {__version__}")
    print(f"project: {root}")
    print(f"analysis dir: {paths.root} ({'exists' if paths.root.exists() else 'missing'})")
    print(f"db: {paths.db_path} ({'exists' if paths.db_path.exists() else 'missing'})")
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
    orch = AnalysisOrchestrator()
    project, snapshot = orch.init_project(path)
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

    if approve:
        slice_ = pipeline.approve(snapshot, proposal)
        print(f"Approved and stored slice id={slice_.id}")
    else:
        print("Not persisted. Re-run with --approve after review (scaffold).")
    return 0


def cmd_analyze(seed: str, path: str) -> int:
    orch = AnalysisOrchestrator()
    project, snapshot = orch.init_project(path)
    proposal = orch.scope.propose(
        snapshot,
        SeedSpecification(raw=seed),
        project_path=str(Path(path).resolve()),
    )
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
        return cmd_analyze(args.seed, args.path)
    if args.command == "detectors":
        return cmd_detectors()
    if args.command == "analyzers":
        return cmd_analyzers()

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
