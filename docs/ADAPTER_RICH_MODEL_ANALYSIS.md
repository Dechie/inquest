# Adapter Layer: Rich-Information Sufficiency Analysis

**Scope.** Assessment of the claim that the external-analyzer adapter layer
(`src/codeanalyzer/analyzers/`) is *not constructed* to harvest rich program
information — ASTs, control-flow graphs, call graphs, data flow, type
relations — from the ecosystem tools it wraps.

**Verdict.** The claim is **substantiated**, with an important qualification:
the narrowness is partly a *deliberate architectural boundary* (diagnostics as
verdicts; structure as a separate subsystem), and partly an *unintended
vacuum* — the structural subsystem that was supposed to supply richness is
scaffold-only, while the implemented adapter contract is diagnostic-centric by
construction. The net effect is a system whose only functioning external
source yields flat, span-anchored verdicts with no structural payload.

---

## 1. Evidence Base (file:line)

| Concern | Location | Status |
| --- | --- | --- |
| Adapter contract: single output channel | `analyzers/adapter.py:56-62` | `analyze() → list[ExternalDiagnostic]` only |
| Capability declaration: prose strings | `analyzers/adapter.py:25-28`; `provides: list[str]` in 5 adapters | No machine-readable kinds |
| Canonical diagnostic shape | `domain/diagnostics.py:13-32` | message + span + rule_id + opaque `raw_diagnostic` |
| `entity_ids` correlation field | `domain/diagnostics.py:30` | Declared; **never populated by any adapter** |
| Realized adapters (mypy, flutter) | `adapters/mypy.py:121-186`; `adapters/flutter_analyze.py:102-162` | JSONL / plain-text parsing → `ExternalDiagnostic` |
| Scaffold adapters (eslint, phpstan, tsc) | `adapters/base_stub.py:49-63`; `eslint.py`, `phpstan.py`, `typescript.py` | `analyze()` raises `NotImplementedError` |
| Adapter selection | `analyzers/registry.py:27-44` | By language/project heuristics; never by capability |
| Structural model facade | `program/model.py:14-37` | `entities / relationships / call_graph / cfg / data_flow` |
| Model construction default | `program/builder.py:30-38` | `empty_program_model_builder` → **empty model** |
| Language frontends | `program/frontends/` | Only the ABC `base.py:11-27`; zero implementations |
| Evidence surface for rich queries | `evidence/program_model.py` | Dominators, path conditions, definitions/uses, value & field provenance, object shape, entry/exit points, control flow → all return `[]` / `{}` defaults |
| Diagnostic ↔ entity binding | `evidence/program_model.py:213-221` | `get_external_diagnostics_for_entity` / `_for_scope` return `[]` unconditionally |
| Substrate analysis kinds | `analysis/program_model.py:39-40` | Only `CALL_PATH`, `REACHABILITY` |
| Pipeline wiring | `pipeline/orchestrator.py:142-144` | Builder default ⇒ empty model ⇒ vacuous evidence |

---

## 2. The Contract Is Diagnostic-Centric by Construction

`AnalyzerAdapter.analyze()` has exactly one return type:
`list[ExternalDiagnostic]`. `ExternalDiagnostic` normalizes to
`{analyzer, rule_id, severity, message, location, entity_ids, raw_diagnostic}`.
This is a *verdict* channel: it transmits *that* something is wrong, *where*,
and *why*, not *what the program looks like*. Any structural information the
underlying tool computed is discarded at the boundary or preserved only as an
opaque, unqueryable `raw_diagnostic` dict.

This is not accidental. The design intent is explicit — "where a mature
ecosystem analyzer already performs an analysis reliably, the system consumes
it rather than reimplementing it" (`adapter.py:2-5`). The adapter layer is
conceived as an *evidence-inlet for verdicts*, and the system's own
declaration of what adapters provide ("type diagnostics", "lint rules",
"AST-based rules") is human-readable prose, not a capability registry that the
orchestrator can negotiate against.

Three of five adapters (ESLint, PHPStan, tsc) are scaffolds: they advertise
capabilities and never execute. Of the two realized, neither emits anything
beyond diagnostics: mypy's JSONL lines (which internally carry full type
inference over a typed AST) and flutter's bulleted text are reduced to the
same flat shape.

---

## 3. The Richness Was Assigned Elsewhere — and Left Unbuilt

The architecture does not *omit* structural representation; it *relocates* it.
`ProgramModel` (`program/model.py`) exposes entities, relationships, a
`CallGraph`, per-function `ControlFlowGraph`, and `DataFlowGraph`, and
`LanguageFrontend` (`program/frontends/base.py`) is the declared producer. The
analysis substrate is meant to derive facts (call paths, reachability,
dominance, path conditions) over these structures on demand.

None of this is realized:

- `program/builder.py:30-38` — the default builder returns an **empty
  in-memory model**; detectors then produce `UNKNOWN` outcomes by design.
- `program/frontends/` — protocol only; no Python, JS/TS, PHP, or Dart
  frontend exists to populate entities or graphs.
- `evidence/program_model.py` — the Evidence API declares the full rich query
  surface (callers/callees are implemented; dominators, path conditions,
  reaching definitions, value provenance, object shape, control flow, entry/
  exit points are hard-coded empties).
- `analysis/program_model.py:39-40` — substrate `supported_kinds()` reports
  only `CALL_PATH` and `REACHABILITY`.

The result is an inverted maturity profile: the *deep* evidence surface is a
declaration; the *shallow* surface (diagnostics) is the only functional
source.

---

## 4. Integration Gap: The Two Subsystems Never Meet

Even where both sides exist, they are disjoint:

1. **No entity binding.** `ExternalDiagnostic.entity_ids` is declared but
   never populated, so a diagnostic cannot be joined to a program-model
   entity for reachability, scope, or slice-membership queries.
2. **No diagnostics on the Evidence API.** `get_external_diagnostics_for_entity`
   and `_for_scope` return `[]` unconditionally — the evidence layer that
   serves detectors cannot retrieve the diagnostics the adapters produced.
   Adapter output currently flows only to the orchestrator's finding layer,
   not into model-scoped evidence.
3. **No capability negotiation.** `get_analyzer_capabilities(analyzer_id)`
   returns `None`; adapters are selected by `supports(language/path)`, so the
   system cannot request a capability it knows the tool holds.

Consequence: a detector cannot ask "does an external analyzer flag this
entity?" and the pipeline cannot ask "which analyzer can give me a CFG?" —
both queries are declared by the domain and unmet by the wiring.

---

## 5. Harvesting vs. Re-derivation: The Cost of the Current Design

The tools being wrapped already compute the rich structures internally, and
each exposes a programmatic surface for them:

- **mypy** — typed AST, symbol table, fine-grained dependency graph, and an
  importable `mypy.api` (the current adapter shells out to JSONL and
  discards all of it).
- **tsc** — `Program` / `TypeChecker` with symbol resolution, call
  resolution, and declaration graphs; a `LanguageService` for on-demand
  requests.
- **ESLint** — every rule receives a full ESTree AST via rule context;
  `SourceCode` provides scope analysis.
- **PHPStan** — reflection layer, type inference, and a CFG over its own
  representation.
- **flutter analyze** — Dart analyzer summary/`AnalysisContext` with AST,
  element model, and call graph.

The current contract forfeits this. When the frontend layer matures, each
language will *re-derive* AST/CFG/call graphs from source, duplicating what
the wrapped tools already computed — a pure tax unless the adapter contract
gains a structural channel to harvest it. This is the concrete cost of the
claim: not merely absent data, but guaranteed future redundancy.

---

## 6. Recommended Contract Evolution

1. **Second output channel.** Extend `AnalyzerAdapter` with an optional
   `harvest(snapshot, scope, project_path) → StructuralArtifact | None`
   (typed AST, CFG, call-graph, type map), versioned per analyzer. Adapters
   opt in; the diagnostic channel remains the mandatory minimum.
2. **Machine-readable capabilities.** Replace prose `provides: list[str]`
   with an enum of `CapabilityKind` (`DIAGNOSTICS`, `TYPED_AST`, `CALL_GRAPH`,
   `CFG`, `DATA_FLOW`, `SYMBOL_TABLE`), and let the registry select by
   capability, feeding `get_analyzer_capabilities`.
3. **Bind diagnostics to entities.** Populate `ExternalDiagnostic.entity_ids`
   at normalization time (adapter-local symbol resolution, or a post-pass
   against the program model), and implement
   `get_external_diagnostics_for_entity/scope` over that binding.
4. **Prefer harvest over re-derivation.** For languages whose tool exposes a
   programmatic API (mypy.api, tsc LanguageService, ESLint SourceCode,
   PHPStan reflection), route the frontend through the adapter's harvest
   channel; reserve from-scratch parsing for languages without a suitable
   tool.

---

## 7. Conclusion

The claim holds: the adapter layer was **made** to fetch verdicts, not
structure. Its contract admits a single diagnostic shape, its capability
declarations are unnegotiable prose, and none of its output is bound to the
program model. The mitigating nuance — that structure was deliberately
assigned to a frontend/substrate subsystem — collapses under inspection,
because that subsystem is scaffold-only. The system's rich-information
capability is therefore *declared but absent*; its only realized external
information channel is lossy by design. Closing the gap is a contract
extension (structural output channel, capability negotiation, entity binding),
not a re-architecture.