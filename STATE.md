# Current State

**Updated:** 2026-08-11

This file tracks the current state of the codebase, what is working, what is
scaffolded, and what should be done next. It is the operational companion to
`docs/DESIGN_SPEC.md` (the architecture baseline) and `README.md` (project
overview).

---

## 1. Summary

The repository contains **initial scaffolding** for the Codebase Correctness
Analysis System (Phases A–F of the roadmap are interface/stub level only).
All stable architectural interfaces from the design spec exist as ABCs, all
domain models are implemented, the SQLite schema is complete, and an
end-to-end orchestrator wires the subsystems together — but every heavy
component (frontends, graph construction, analyzer execution, evidence
collection, LLM reasoning) is a stub.

Verification status:

```text
pytest   14 passed
mypy     no issues (59 files, strict)
ruff     all checks passed
```

---

## 2. What Exists (Working)

### Domain models — complete (`src/codeanalyzer/domain/`)

- `ProvenanceKind` (5 epistemic categories from spec §2.6/§22)
- `ProvenancedFact.is_authoritative_structure()` — hypotheses never
  authoritative
- `Entity`, `Location`, `Relationship` with typed relationships
- `Finding` (§16/§19) with `FindingSource`, `FindingStatus`, `Severity`
- `LogicalSlice` / `SliceMember` (§6, explainable membership §5.3)
- `MinimalEvidenceSlice`, `EvidenceRequirement`, `EvidenceItem` (§20)
- `Project`, `Snapshot`, `AnalysisRun` (§27 snapshot identity)
- `ExternalDiagnostic` (§8.2), `DocumentationUnit`, `DocEntityLink`

### Stable interfaces — complete as ABCs (`§31`)

| Interface | Location | Status |
|-----------|----------|--------|
| Scope API | `scope/api.py` | ABC + working stub pipeline |
| Analyzer Adapter API | `analyzers/adapter.py` | ABC + stub adapters |
| Evidence API | `evidence/api.py` | Full ABC, stub backend |
| Documentation API | `documentation/api.py` | Full ABC, stub backend |
| Detector API | `detectors/base.py` | ABC + registries |
| Finding / MinimalEvidenceSlice | `domain/` | Concrete models |
| LLM hooks | `llm/scope.py`, `llm/judgment.py` | ABCs + stubs |

### Working logic (non-stub)

- `program/graphs/` — `CallGraph.can_reach`, callers/callees; CFG
  successors/predecessors; data-flow producers/consumers
- `program/algorithms/reachability.py` — BFS reachability + path finding
  (kept internal, per §11)
- `scope/resolver.py` — `ScopeResolutionPipeline`: propose → validate →
  approve flow with LLM hooks injectable; human-approval checkpoint
- `analyzers/registry.py` — adapter registration, discovery, per-project
  selection
- `persistence/` — SQLite schema (all §26 tables), DB bootstrap with
  migrations, `.codeanalyzer/` filesystem layout (`analysis.db`, `graphs/`,
  `snapshots/`, `cache/`)
- `repository/manager.py` — project registration, snapshot creation with
  git commit detection
- `pipeline/orchestrator.py` — end-to-end wiring (init → scope → analyzers
  → detectors → collector → judge → result)
- `cli.py` — `init`, `status`, `scope`, `analyze`, `detectors`, `analyzers`
- `detectors/catalog.py` — initial detector ids (§15), delegated-to-external
  list (§8.4), deferred domains (§17)

---

## 3. What Is Scaffolded (Stub Only)

| Component | Scaffold behavior | Phase |
|-----------|-------------------|-------|
| Language frontends | `LanguageFrontend` ABC only; no parsers | A |
| Program model | `ProgramModel` ABC only; no implementation | A |
| Dominance / post-dominance | Only EvidenceAPI signatures | A |
| AST / IR / symbol table | Not started | A |
| Analyzer adapters | `discover()` always False; `analyze`/`normalize` raise | B |
| Scope expansion | Ungrounded pass-through (`StubDeterministicScopeResolver`) | C |
| LLM scope interpretation | Passthrough/identity stubs | C |
| SQLite stores | Schema only — nothing is written to the DB | A |
| Evidence collection | Empty slice with requirement kinds noted | D |
| Detectors | Identity-only stubs returning no findings | E |
| LLM judgment | `INSUFFICIENT_EVIDENCE` verdict | F |
| Settings | `config/settings.py` exists but is unwired | — |

---

## 4. Known Gaps (Prioritized)

1. **No persistence writes** — `Database` applies the schema but no store
   layer exists; `ScopeResolutionPipeline` keeps slices in memory. The
   "named persistent logical slice" (§6) is not yet persistent, and
   `AnalysisResult` is never stored (§25/§27).
2. **No real program representation** — nothing builds entities,
   relationships, call graph, CFG, or data flow from actual source. The
   Evidence API has no real backend, so detectors have no facts to consume.
3. **No analyzer execution** — adapters cannot run tools, parse output, or
   capture versions/configuration (§8.2).
4. **No real detectors or LLM reasoning** — Phase E/F are the eventual
   payoff; the interfaces they need already exist.
5. **Incremental analysis (§28)** and **detector composition (§18)** are
   unstarted (by design — later phases).
6. **Settings/config not wired** — `enable_llm`, `max_evidence_items`,
   `auto_approve_scope` are ignored by the pipeline.

---

## 5. What to Do Next

### Immediate (before starting Phase A work)

- [ ] Decide the first target language/framework for the frontend
      (e.g. Python or TypeScript; nothing language-specific exists yet)
- [ ] Add a SQLite store layer (ProjectStore, SnapshotStore, SliceStore,
      AnalysisStore, FindingStore, EvidenceStore) implementing the schema
- [ ] Wire persistence into `ScopeResolutionPipeline.approve()` and
      `AnalysisOrchestrator.run()`
- [ ] Wire `Settings` into the orchestrator and CLI

### Phase A — Program substrate

- [ ] Implement a `LanguageFrontend` for the first language: parse source
      into entities + relationships, then build call graph, CFG, data-flow
- [ ] Implement `ProgramModel` concrete class backed by the frontend
- [ ] Implement dominance/post-dominance algorithms behind the existing
      EvidenceAPI signatures
- [ ] Persist entities/relationships per snapshot

### Phase B — External analyzers

- [ ] Implement real `discover()` (PATH/config probing) and process
      execution in `analyze()`
- [ ] Implement `normalize()` for at least one adapter (e.g. PHPStan JSON
      or ESLint JSON output), capturing analyzer version + configuration
- [ ] Persist `ExternalDiagnostic` rows

### Phase C — Scope engine

- [ ] Implement deterministic expansion over real imports/call graph
      (replace `StubDeterministicScopeResolver`)
- [ ] Implement `validate_structural_claims` against the program model
- [ ] Wire an actual LLM provider into `ScopeInterpreter`/`ScopeReviewer`
      (or keep them as pure interfaces until Phase F)

### Phase D — Evidence architecture

- [ ] Implement a real `EvidenceCollector` that maps
      `EvidenceRequirement`s to concrete EvidenceAPI queries and
      materializes minimal slices (this is architecturally critical per §33)

### Phase E/F — Detectors + LLM

- [ ] Implement the first detector from the catalog
      (e.g. `possible_missing_call` or `missing_field_propagation`) using
      only EvidenceAPI/DocumentationAPI
- [ ] Implement `SemanticJudge` against a provider once evidence slices are
      real

---

## 6. Ongoing Hygiene

- Keep `pytest`, `mypy --strict`, and `ruff` green — currently all pass
- New subsystems must go through the stable interfaces (§31); nothing may
  bypass the Evidence API or write LLM-derived structure into the graphs
- Design spec changes belong in `docs/DESIGN_SPEC.md`; scaffold alignment
  notes in `docs/ARCHITECTURE.md`; this file tracks operational state
