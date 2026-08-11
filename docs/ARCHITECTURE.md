# Architecture Baseline

This document summarizes the scaffolding alignment with the technical
specification. Full design detail lives in the project architecture baseline.

## Design thesis

The system is a **program-evidence integration and reasoning engine**:

- Reuse mature ecosystem analyzers; do not rebuild them.
- Establish program facts deterministically (graphs, reachability, data flow).
- Treat documentation as intent evidence, not automatic ground truth.
- Give the LLM only a **minimal evidence slice** per finding.

## Scope hierarchy

```text
Repository  →  Logical Slice  →  Finding  →  Minimal Evidence Slice  →  LLM
```

These remain distinct abstractions.

## Provenance

| Kind | Role |
|------|------|
| `PROGRAM_FACT` | Observed structure |
| `EXTERNAL_ANALYZER_FACT` | Ecosystem tool diagnostic |
| `DERIVED_FACT` | Mechanically derived |
| `DOCUMENTATION_FACT` | Stated intent |
| `HYPOTHESIS` | Semantic interpretation only |

## Stable packages

| Package | Role |
|---------|------|
| `domain` | Models: entities, findings, slices, evidence, provenance |
| `repository` | Projects and snapshots |
| `scope` | Hybrid LLM/deterministic scope resolution |
| `program` | Frontends, graphs, algorithms |
| `analyzers` | External analyzer adapters |
| `evidence` | Evidence API + collector |
| `documentation` | Documentation API |
| `detectors` | Correctness detectors |
| `llm` | Scope interpretation + semantic judgment |
| `persistence` | SQLite schema + `.codeanalyzer/` layout |
| `pipeline` | End-to-end orchestration |

## Implementation phases

See README roadmap (Phases A–H). Scaffolding provides interfaces and stubs
for each phase so work can proceed without collapsing into
`source → LLM → probably buggy`.
