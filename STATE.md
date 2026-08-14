# Current State

**Updated:** 2026-08-14

Operational companion to [DESIGN_SPEC.md](docs/DESIGN_SPEC.md) (eleven-layer
architectural baseline) and [ARCHITECTURE.md](docs/ARCHITECTURE.md) (scaffolding
map).

---

## 1. Summary

Scaffolding has been **re-aligned to the rebuilt architecture**. The original
four-stage pipeline (`identify files → CFGs → BFS/DFS → LLM`) is replaced in
code by the most critical new layers:

```text
Properties (Layer 6)
    ↕
Detectors (Layer 7)  →  Evidence Refinement (Layer 8)
                              ↕ feedback
                    Analysis Substrate (Layer 4)
                              ↓
                       Evidence API (Layer 5)
```

What is **implemented now** (still stub-level for heavy work):

- Domain models for **CorrectnessProperty**, **AnalysisRequest**, **RefinementResult**
- **PropertyAPI** + seed catalog + **StubPropertyAPI**
- **AnalysisSubstrate** + **StubAnalysisSubstrate** (records refinement requests)
- **EvidenceRefiner** + **StubEvidenceRefiner** (iterative refinement loop)
- **DetectorContext** is property-aware; registry binds properties per detector
- **AnalysisOrchestrator** runs: properties → detectors → refine-until-done → LLM
- SQLite **`properties`** table + **PropertyStore** (schema v2 migration)

Everything else from the prior scaffold remains (domain models, Evidence API
ABC, scope pipeline, analyzer adapters, persistence stores, CLI) but is not
yet backed by real program analysis.

---

## 2. Architectural alignment

| Layer | Package | Status |
| ----- | ------- | ------ |
| 1 Codebase & external inputs | `analyzers/`, `repository/` | Adapters stubbed; no execution |
| 2 Logical slice | `scope/` | Hybrid pipeline works; expansion stubbed |
| 3 Program representation | `program/` | Graph classes + ABCs; no frontend |
| 4 Analysis substrate | `analysis/` | **New** — ABC + stub; no real facts |
| 5 Evidence API | `evidence/api.py` | Full ABC; stub backend |
| 6 Properties / contracts | `properties/` | **New** — API + catalog + persistence |
| 7 Detectors | `detectors/` | **Updated** — property-aware; still no findings |
| 8 Evidence refinement | `evidence/refiner.py` | **New** — loop wired; minimal collection |
| 9 Documentation | `documentation/` | ABC + stub |
| 10 LLM | `llm/` | ABC + stub judgment |
| 11 Persistent artifacts | `persistence/`, `pipeline/` | Stores write slices/analyses/properties |

Conceptual order ≠ runtime order. The orchestrator already models one feedback
loop: refinement → substrate → refinement.

---

## 3. What works (non-stub)

- **ScopeResolutionPipeline** — propose → validate → approve with injectable LLM hooks
- **CallGraph / CFG / data-flow graph** classes + BFS reachability (internal to substrate)
- **Persistence** — projects, snapshots, slices, analyses, findings, evidence, **properties**
- **Orchestrator** — end-to-end run loads properties, runs detectors, refines evidence, persists
- **CLI** — `init`, `status`, `scope`, `analyze`, `detectors`, `analyzers`

Run verification:

```bash
pytest && mypy --strict && ruff check .
```

---

## 4. What is scaffolded (stub only)

| Component | Behavior |
| --------- | -------- |
| Language frontends / ProgramModel | ABC only |
| AnalysisSubstrate | Accepts requests; returns no derived facts |
| Evidence API backend | All queries empty |
| Property catalog | Fixed seed properties; heuristic by slice name |
| Detectors | Declare evidence needs; return no findings |
| Evidence refiner | Maps requirements → queries; requests analysis when data missing |
| Analyzer adapters | `discover()` false; `analyze` raises |
| LLM judgment | `INSUFFICIENT_EVIDENCE` |
| Scope expansion | Passthrough stub resolver |

---

## 5. Known gaps (prioritized)

1. **No real program representation** — Evidence API and substrate have nothing to query; refinement always requests analysis or stays empty.
2. **No real detectors** — property binding exists but no detector evaluates properties against facts.
3. **No analyzer execution** — external diagnostics never enter evidence.
4. **Documentation layer unused in pipeline** — associated during refinement only when findings exist.
5. **Substrate ↔ Evidence API not connected** — substrate facts don't feed back into evidence queries yet.
6. Incremental analysis, detector composition, formal property evaluation — unstarted (by design).

---

## 6. What to do next

### Immediate (complete Layer 4 ↔ 5 bridge)

- [ ] Implement a minimal `ProgramModel` + `EvidenceAPI` backend over call graph
- [ ] Wire `AnalysisSubstrate.run()` to use `program/algorithms/` and register facts the Evidence API can serve
- [ ] After substrate produces facts, refiner should re-query (second round resolves)

### First real detector (Layer 7)

- [ ] Implement `possible_missing_call` against `RESERVE_BEFORE_PERSIST` using only Evidence API
- [ ] Finding carries `property_id`; refiner builds minimal slice from call path + doc invariant

### Phase A/B continuation

- [ ] Language frontend for first target ecosystem
- [ ] One working analyzer adapter (`normalize` + persist diagnostics)

### Hygiene

- Keep pytest / mypy / ruff green
- New subsystems must go through Evidence API and Property API — no bypass
- Design changes → `docs/DESIGN_SPEC.md`; scaffold map → `docs/ARCHITECTURE.md`; this file → operational state

---

## 7. Key files (new / changed)

```text
src/codeanalyzer/
├── analysis/           # Layer 4 — substrate ABC + stub
├── properties/         # Layer 6 — property API + catalog + stub
├── domain/
│   ├── properties.py   # CorrectnessProperty
│   └── analysis.py     # AnalysisRequest, SubstrateRunResult
├── evidence/
│   └── refiner.py      # Layer 8 — iterative refinement
├── detectors/base.py   # property-aware DetectorContext
└── pipeline/orchestrator.py  # property → detector → refine loop
```

---

## 8. Design invariant (unchanged intent, new shape)

```text
Logical Slice
    → Evidence API (+ external inputs)
    → Properties
    → Detectors
    → Evidence Refinement ↔ Analysis Substrate
    → Documentation
    → LLM
    → Persistent artifacts
```

Never: `source → LLM → "probably buggy"`.
