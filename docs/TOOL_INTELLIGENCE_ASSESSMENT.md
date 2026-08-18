# External Tool Intelligence: Assessment of the Proposed Subsystem Against the Inquest Codebase

**Status:** Design assessment — no code changes.
**Subject:** The proposed "External Analysis Integration / Tool Intelligence" subsystem
(capability model, multi-mode acquisition, tool discovery, capability-level availability,
classified failure modes, capability negotiation, substrate dual-origin evidence).
**Method.** Each proposal element is mapped to concrete codebase anchors
(`src/codeanalyzer/…`, file:line), classified as *anticipates*, *conflicts*, or
*absent*, and assigned an implementation delta. Verdicts distinguish what the
architecture already half-declares from what it does not yet represent.

---

## 1. Executive Verdict

The proposal is **architecturally coherent with this codebase** — it does not
introduce a foreign paradigm but formalizes commitments the repository already
half-declares. Three anchors make this true:

1. **Provenance orthogonality.** `ProvenanceKind` already distinguishes
   `EXTERNAL_ANALYZER_FACT` from `DERIVED_FACT` and `PROGRAM_FACT`
   (`domain/enums.py:8-19`), and `EpistemicStatus` separates certainty from
   origin (`domain/enums.py:22-38`). The proposal's dual-origin fact model —
   `call(A,B) source=EXTERNAL_ANALYZER` vs. `source=INQUEST_DERIVED,
   derivation=AST+symbol resolution` — is a semantic the domain already
   supports and `ProvenancedFact.is_authoritative_structure()`
   (`domain/provenance.py:75-80`) already enforces.
2. **The UNKNOWN principle.** `VerificationOutcome` has `PROVEN / VIOLATED /
   UNKNOWN` (`domain/enums.py:185-190`), and the default program-model builder
   is documented to produce `UNKNOWN` outcomes when the model is empty
   (`program/builder.py:30-38`). "Missing infrastructure must degrade epistemic
   status, not pretend analysis happened" is therefore a restatement of an
   existing invariant, not a new one.
3. **The substrate-as-derivation-engine role.** `AnalysisKind` already declares
   `DOMINANCE, POST_DOMINANCE, DATA_FLOW, DEF_USE, PATH_CONDITIONS`
   (`domain/enums.py:165-174`) and `AnalysisRequest`/`SubstrateRunResult`
   (`domain/analysis.py:11-29`) give the substrate an on-demand request/result
   protocol. The proposal's "derive missing facts where possible" maps
   directly onto this interface.

The proposal is endorsed **with amendments**. Its principal shortcoming is
that it is stated as a subsystem taxonomy without binding it to the existing
types; the main risks are combinatorial explosion of the negotiation space,
unfrozen tool versions breaking the reproducibility of persisted analyses, and
an over-eager LSP acquisition channel. Sections 2–4 establish the gaps,
Section 5 specifies amendments, Section 6 gives a file-level delta.

---

## 2. Claim-by-Claim Analysis

### 2.1 "Reuse ecosystem analyzers is underspecified" — **substantiated**

The current statement of the principle is `analyzers/adapter.py:2-5`:
*"Where a mature ecosystem analyzer already performs an analysis reliably, the
system consumes it rather than reimplementing it."* It says what, not how.
Three underspecifications are visible in code:

- **No capability vocabulary.** `AnalyzerCapabilities.provides` is
  `list[str]` of prose (`adapter.py:25-28`); all five adapters fill it with
  human-readable claims ("AST-based rules", `eslint.py:16`). Nothing machine-
  readable can be negotiated over it.
- **No acquisition taxonomy.** The contract admits exactly one channel:
  `analyze() → list[ExternalDiagnostic]` (`adapter.py:56-62`). The two
  realized adapters are both CLI-subprocess integrations — `mypy --output
  json` (`adapters/mypy.py:121`) and `flutter analyze` plain text
  (`adapters/flutter_analyze.py:115-121`).
- **No degradation policy.** `discover()` is a binary probe
  (`mypy.py:64-81`, `flutter_analyze.py:63-77`); failure outcomes
  (`RuntimeError` on missing binary, `mypy.py:115-120`) are unclassified and
  the orchestrator swallows scaffold `NotImplementedError` with `continue`
  (`pipeline/orchestrator.py:168-169`).

### 2.2 Capability model per analyzer — **valid; codebase anticipates the shape**

The proposal's `ToolCapabilities{diagnostics, ast, symbols, types, references,
call_graph, cfg, data_flow}` with per-capability acquisition provenance is
congruent with two existing declarations:

- `EvidenceAPI.get_analyzer_capabilities(analyzer_id)` exists as an abstract
  method (`evidence/api.py:137-138`) and returns `None` unconditionally in
  the only implementation (`evidence/program_model.py:226-227`) — the
  capability API is *declared but vacant*.
- The evidence-item taxonomy already names the capability outputs:
  `EvidenceItemType` includes `CALL_EDGE, CFG_FRAGMENT, DATA_FLOW_FRAGMENT,
  PATH_CONDITION, EXTERNAL_DIAGNOSTIC, DERIVED_FACT` (`domain/enums.py:126-137`).

The proposal's critical refinement — "do not assume Flutter Analyze gives you
a CFG; distinguish *exposed*, *derivable*, *unavailable*" — is precisely what
the current prose `provides` cannot express.

### 2.3 Acquisition modes — **valid; current code is the anti-example**

The priority ladder (native API → machine-readable protocol/export → CLI
structured → CLI textual) is a policy the codebase inverts:

- **mypy**: a library API (`mypy.api`) exists but the adapter shells out and
  parses JSONL, discarding the typed AST, symbol table, and fine-grained
  dependency graph it could have harvested in-process (`mypy.py:121-134`).
- **flutter analyze**: the adapter parses *terminal text* — bullets, wrapped
  continuation lines, spinner animation characters stripped via
  `_SPINNER_RE` (`flutter_analyze.py:170-209`). The proposal's lowest-quality
  tier is the only tier implemented.
- **ESLint/PHPStan/tsc**: scaffolds only (`base_stub.py:49-63`), despite each
  tool exposing a programmatic surface (ESTree rule context, PHPStan
  reflection/CFG, tsc `Program`/`TypeChecker`).

The distinction between *linter diagnostics* and *underlying toolchain
structure* (ESLint diagnostics vs. AST/scope/types) names the single largest
information loss in the current adapter layer.

### 2.4 Tool discovery subsystem — **valid; present only as heuristics**

Project detection today is per-adapter `supports()` heuristics: presence of
`pubspec.yaml` (`flutter_analyze.py:84-86`), presence of `*.py` files
(`mypy.py:209-211`), or explicit language strings. Discovery is
`shutil.which` + `--version` (`mypy.py:64-81`), selected via
`AnalyzerRegistry.for_project` by language/project (`analyzers/registry.py:27-44`).

Missing relative to the proposal: manifest-driven ecosystem detection
(`pubspec.yaml` → expected toolchain), project-local binaries, package-manager
environments, toolchain managers, and — critically — **exact version capture
into the analysis record**. `_version` is stored on the adapter instance
(`mypy.py:58,77`) and forwarded to `ExternalDiagnostic.analyzer_version`
(`domain/diagnostics.py:25`), but nothing records *which tools existed at
which versions for a given run* — an auditability gap that contradicts the
project's persistence commitments (`snapshots.py:29-40` snapshot identity).

### 2.5 Capability-level availability — **valid; conflicts with `discover()`**

`discover() → bool` (`adapter.py:43-46`) is the proposal's "Flutter available
= true" — binary. The needed granularity (installed/usable/version +
per-capability `AVAILABLE | DERIVABLE | UNAVAILABLE`) has no representation
anywhere in the domain. `AnalysisRun.metadata: dict[str,str]`
(`snapshots.py:52`) is a viable sink but is unused for this purpose today.
This is a **conflict** in the sense that the ABC's return contract must change
or be supplemented, not just extended.

### 2.6 Failure modes — **valid; all three exist today in crude form**

The proposal's three failure modes map onto existing behaviors:

| Proposed mode | Current behavior | Classification |
| --- | --- | --- |
| NOT_INSTALLED | `discover()` False → adapter silently skipped (`registry.py:24-25`, `orchestrator.py:163-169`) | Silent skip — no record, no degradation signal |
| VERSION_MISMATCH | Version captured, never compared to project expectations | Absent |
| Capability gap | Substrate silently produces no facts for unsupported kinds; evidence methods return `[]` | Silent empties |

Notably, the two worst failure semantics — **silent skip** and **silent
empty** — are both present today and both violate the proposal's core rule
("missing infrastructure must degrade epistemic status, not pretend
analysis happened"). `_parse_json_lines` drops malformed lines without a
trace (`mypy.py:193-206`); `normalize()` returns `[]` on non-string input
(`flutter_analyze.py:136-137`); the orchestrator's `except NotImplementedError:
continue` (`orchestrator.py:168-169`) turns scaffolded analyzers into
invisible absences. The proposal's failure taxonomy
(`NOT_INSTALLED, VERSION_MISMATCH, INVALID_PROJECT, TOOL_CRASH, TIMEOUT,
PERMISSION_DENIED, MALFORMED_OUTPUT, PROTOCOL_FAILURE, UNSUPPORTED_FEATURE`)
is the missing vocabulary for converting these silent paths into recorded,
epistemic-status-bearing outcomes.

### 2.7 Capability states — **valid; new vocabulary, low risk**

`AVAILABLE / DERIVABLE / PARTIALLY_AVAILABLE / UNAVAILABLE / FAILED /
UNSUPPORTED / INCOMPATIBLE` and the separate failure taxonomy are orthogonal
dimensions, consistent with the project's existing refusal to conflate
provenance with epistemic status (`provenance.py:6-11`). Two domain notes:

- `PARTIALLY_AVAILABLE` should be **slice-scoped** as well as project-scoped:
  an analyzer may cover only part of a logical slice, which the current
  `ExternalDiagnostic`/`LogicalSlice` model cannot express.
- `DERIVABLE` must carry its derivation precondition (e.g., "CFG derivable if
  AST + symbols available"), which is naturally expressible as a
  `Provenance.extra` entry or a declarative rule in the capability record.

### 2.8 Substrate role change — **valid; the machinery exists, the policy doesn't**

The proposal's "facts obtainable via external tool, inquest analysis, or
composition, with provenance preserved" is exactly what
`AnalysisRequest → SubstrateRunResult → ProvenancedFact`
(`domain/analysis.py`, `analysis/program_model.py:24-40`) implements — for
two kinds only. `supported_kinds()` returns `CALL_PATH, REACHABILITY`
(`analysis/program_model.py:39-40`) while the enum declares `DOMINANCE,
POST_DOMINANCE, DATA_FLOW, DEF_USE, PATH_CONDITIONS` (`enums.py:170-174`).
The declared-but-unbuilt substrate is the *derivation engine* the proposal
needs; what is missing is the **decision procedure** that routes a fact
request to external acquisition, internal derivation, or UNKNOWN — i.e., the
capability negotiation phase.

### 2.9 Capability negotiation runtime — **valid; maps onto the orchestrator**

The ten-phase runtime collapses cleanly onto existing components:

| Proposal phase | Codebase anchor | Delta |
| --- | --- | --- |
| Identify project | `RepositoryManager.register_project` (`orchestrator.py:98-104`) | Manifest parsing (Section 6) |
| Discover expected tools | `AnalyzerRegistry.for_project` (`registry.py:27-44`) | Requirements extraction from manifests |
| Discover installed tools | `discover()` probes (`registry.py:24-25`) | Multi-source search + version capture |
| Negotiate capabilities | — | **New phase** (Section 6) |
| Select acquisition strategies | `AnalyzerAdapter` channel (single) | Multi-channel selection |
| Build program representation | `ProgramModelBuilder` (`orchestrator.py:142`, `program/builder.py:18-38`) | Frontend injection from negotiation result |
| Run available analyses | Adapter loop (`orchestrator.py:162-169`) | Classified failures, recorded status |
| Derive missing facts | `ProgramModelAnalysisSubstrate` (`orchestrator.py:144`) | Implement remaining `AnalysisKind`s |
| Normalize into Evidence | `ProgramModelEvidenceAPI` (`orchestrator.py:143`) | Populate diagnostic/entity binding |
| Detect/refine findings | Detectors + `StubEvidenceRefiner` (`orchestrator.py:145-194`) | Unchanged |

The proposal's own Flutter-unavailable branch (fallback frontend → reduced
analysis → UNKNOWN) is behaviorally the *default* today (`builder.py:36`
documented UNKNOWN) — but accidentally, via an empty model, rather than by
negotiation.

---

## 3. Alignment Summary

| Proposal concept | Codebase state | Classification |
| --- | --- | --- |
| Tool = capability provider | `provides: list[str]` prose (`adapter.py:25-28`) | Underspecified |
| Per-capability acquisition provenance | `EvidenceItemType` taxonomy (`enums.py:126-137`) | Anticipated |
| Multi-mode acquisition | CLI-only; textual CLI for flutter | Absent (inverted priority) |
| Discovery via manifests + versions | `supports()` heuristics, `_version` on adapter instance | Partial; version unfrozen |
| Capability-level availability | `discover() → bool` (`adapter.py:43-46`) | Conflicting contract |
| Classified failure modes | Silent skip / silent empty / unclassified `RuntimeError` | Absent; worst forms present |
| State/failure taxonomy orthogonality | Provenance/EpistemicStatus orthogonality (`provenance.py:6-11`) | Philosophically aligned |
| Substrate dual-origin evidence | `ProvenanceKind.EXTERNAL_ANALYZER_FACT` / `DERIVED_FACT`; substrate implements 2 of 7 kinds | Anticipated, incomplete |
| Negotiation runtime | Linear orchestrator (`orchestrator.py:132-209`) | Needs insertion, not replacement |
| Three explicit APIs | `get_analyzer_capabilities` stub (`evidence/api.py:137-138`) | Declared, vacant |

---

## 4. Integration Hazards — Amendments to the Proposal

### 4.1 Bound the negotiation space

Capabilities × acquisition channels × failure states × tools is a
multiplicative space. The proposal's runtime must not probe every channel to
discover capability; it should be **declarative-first**: each adapter carries a
static capability manifest (capability → acquisition channel → preconditions),
and runtime probing is limited to validating availability and version. This
mirrors the project's own declarative style (`properties` are declarative
specifications; detectors are strategies).

### 4.2 Freeze tool state into the analysis record

Analysis runs are persisted artifacts (`orchestrator.py:236-251`). Tool
availability and versions must be captured **during** negotiation and recorded
into `AnalysisRun.metadata` (or a `ToolStatus` persisted alongside
diagnostics), so that a later replay of a finding can reconstruct *what
infrastructure produced it*. Otherwise version drift silently changes the
meaning of persisted `UNKNOWN`s — the proposal's own principle (§5: "part of
the analysis snapshot") demands this, and the codebase has the sink.

### 4.3 Defer LSP; prefer library/compiler APIs

LSP is a stateful, long-lived, bidirectional protocol — a poor fit for the
current per-run subprocess model with hardcoded timeouts (10s/30s/120s,
`mypy.py:71,127`, `flutter_analyze.py:70,125`). Recommendation: implement the
ladder as **library API → machine-readable export → CLI structured → CLI
textual**, treat LSP as a separate long-running daemon tier outside the run
transaction, and move all timeouts into `Settings`. Timeout and resource
management belong to the acquisition layer, not to each adapter.

### 4.4 Record derivation chains

When a fact is derived (`DERIVABLE` → `INQUEST_DERIVED`), the derivation
precondition and inputs must be recorded (e.g., in `Provenance.extra`):
`CFG = f(AST_external, symbols_external, language_semantics_inquest)`. This
keeps `is_authoritative_structure()` truthful — a fact derived from external
AST + inquest semantics is neither purely external nor purely internal, and
its epistemic status must reflect the weakest link.

### 4.5 Define the requirements side

`VERSION_MISMATCH` requires a *declared* project expectation
("Project expects Flutter 3.41"). Project requirements are a new domain
artifact (manifest-derived, but overridable — e.g., via configuration), with a
compatibility predicate (`compatible | partially_compatible | unsupported`)
that is itself a capability-provenance statement, not a boolean.

---

## 5. File-Level Implementation Delta

1. **`domain/tooling.py` (new).** `CapabilityKind` enum (diagnostics, ast,
   symbols, types, references, call_graph, cfg, data_flow); `AcquisitionMode`
   enum (library_api, protocol, export, cli_structured, cli_textual);
   `ToolCapabilityState` enum (available, derivable, partially_available,
   unavailable, failed, unsupported, incompatible); `ToolFailure` enum
   (not_installed, version_mismatch, invalid_project, tool_crash, timeout,
   permission_denied, malformed_output, protocol_failure,
   unsupported_feature); `ToolStatus` model (analyzer_id, executable, version,
   project_requirement, capabilities: dict[CapabilityKind,
   ToolCapabilityState], failure: ToolFailure | None).
2. **`analyzers/adapter.py`.** Replace prose `provides` with
   `capabilities: dict[CapabilityKind, AcquisitionMode]`; add optional
   `acquire(kind, request) → StructuredArtifact | None` channel while
   retaining `analyze()` for diagnostic compatibility; change/annotate
   `discover()` to yield `ToolStatus` rather than `bool`.
3. **`analyzers/discovery.py` (new).** Manifest-driven project detection
   (`pubspec.yaml`, `package.json` + `package-lock.json` + `tsconfig.json`,
   `composer.json`, `pyproject.toml`) → expected toolchain + version
   requirements; multi-source executable search; version capture.
4. **`pipeline/orchestrator.py`.** Insert negotiation phase between
   `init_project` and `run`: detect ecosystem → resolve expected tools →
   probe installed → build `ToolStatus` set → select acquisition strategies →
   record statuses into `AnalysisRun.metadata`; route derived-requirement
   `AnalysisRequest`s to the substrate.
5. **`analysis/program_model.py`.** Implement the five unbuilt
   `AnalysisKind`s (dominance, post_dominance, data_flow, def_use,
   path_conditions) as derivation strategies gated by capability
   preconditions.
6. **`evidence/program_model.py`.** Implement `get_analyzer_capabilities`
   against the registry + `ToolStatus`; implement
   `get_external_diagnostics_for_entity/_for_scope` once `entity_ids`
   binding exists.
7. **`config/settings.py`.** Own timeouts, negotiation bounds, and tool
   requirement overrides.

Sequencing recommendation — and agreement with the proposal's "before more
detectors": the negotiation phase (items 1–4) precedes adapter growth; the
Evidence API is only as useful as the coverage and provenance of its sources.

---

## 6. Conclusion

The proposal is **correct in substance and safe in direction**: it names the
underspecification of the reuse principle, the CLI-first inversion of
acquisition quality, the binary availability model, and the silent failure
paths — all verifiable in the current code. The codebase anticipates more of
it than the proposal assumes (provenance duality, UNKNOWN semantics, the
substrate protocol, the vacant capability API), which lowers the cost of
adoption: this is *formalization and completion*, not re-architecture. The
amendments (Section 4) — declarative capability manifests, frozen tool state
in the analysis record, LSP deferral, derivation-chain provenance, and a
declared project-requirements artifact — are the binding constraints that
prevent the subsystem from becoming an unverifiable probing matrix and keep it
consistent with the project's two non-negotiables: provenance on every fact,
and honest UNKNOWN over silent absence.