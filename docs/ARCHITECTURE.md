# Architecture Baseline

This document summarizes scaffolding alignment with the technical specification.
Full design detail lives in [DESIGN_SPEC.md](./DESIGN_SPEC.md).

**Status:** Rebuilt from abstractions upward — the eleven-layer conceptual order
replaces the original four-stage pipeline. Newer concepts replace older stages
where appropriate; runtime execution includes feedback loops.

## Design thesis

The system is a **program-evidence integration and reasoning engine**:

- Reuse mature ecosystem analyzers; do not rebuild them.
- Represent program semantics in reusable structures (not one graph type).
- Produce facts via a deterministic **analysis substrate**; expose them through the **Evidence API**.
- Evaluate **correctness properties / contracts** against evidence via **detectors**.
- Refine evidence iteratively into **minimal evidence slices**.
- Compare mechanical evidence with **documented intent**, then **LLM semantic interpretation**.
- Persist everything as auditable analysis artifacts.

Central question: not merely "find suspicious code" but whether intended properties are satisfied, violated, or unresolved.

## Conceptual layers

```text
 1. Codebase & External Inputs
 2. Logical Slice (named, persistent)
 3. Program Representation
 4. Analysis Substrate
 5. Evidence API          ← central boundary
 6. Correctness Properties / Contracts
 7. Detectors
 8. Evidence Refinement & Minimal Evidence Slices
 9. Documentation / Intended Behavior
10. LLM Semantic Reasoning
11. Findings & Persistent Analysis Artifacts
```

Feedback loops: detector ↔ analysis substrate (more evidence); LLM ↔ property/evidence refinement; slice expansion on discovered dependencies.

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

| Package | Layer(s) | Role |
|---------|----------|------|
| `domain` | 6, 7, 11 | Models: entities, properties, findings, slices, evidence, provenance |
| `repository` | 1 | Projects and snapshots |
| `scope` | 2 | Hybrid LLM/deterministic logical slice resolution |
| `program` | 3 | Frontends, representations (AST, symbols, graphs) |
| `analyzers` | 1 | External analyzer adapters |
| `analysis` | 4 | Analysis substrate (reachability, dominance, paths, …) |
| `evidence` | 5, 8 | Evidence API + refinement/collector |
| `properties` | 6 | Correctness properties / contracts |
| `documentation` | 9 | Documentation API, intent association |
| `detectors` | 7 | Property evaluators (not standalone analyzers) |
| `llm` | 2, 10 | Scope interpretation + semantic judgment |
| `persistence` | 11 | SQLite schema + `.codeanalyzer/` layout |
| `pipeline` | all | End-to-end orchestration with feedback loops |

## Displacement from original pipeline

| Original | Now |
| -------- | --- |
| Stage 1: identify files | Logical Slice |
| Stage 2: CFGs | Program Representation |
| Stage 3: BFS/DFS/dominance | Analysis Substrate → Evidence API |
| Stage 4: LLM | Evidence Refinement → Docs → LLM |
| Bug finding | Properties + Detectors |

## Implementation phases

See [DESIGN_SPEC.md §18](./DESIGN_SPEC.md) (Phases A–I). Scaffolding provides interfaces and stubs so work proceeds without collapsing into `source → LLM → probably buggy`.

When adding new concepts (temporal logic, alias analysis, concurrency, effects), ask: replace, generalize, merge, or genuinely add?
