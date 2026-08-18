# Tool intelligence checklist

From `ADAPTER_RICH_MODEL_ANALYSIS.md` and `TOOL_INTELLIGENCE_ASSESSMENT.md`.
Do negotiation types before growing adapters or detectors.

## Implemented ✅

- [x] `domain/tooling.py`: CapabilityKind, AcquisitionMode, ToolCapabilityState, ToolFailure, ToolStatus
- [x] Replace prose `provides` with `capabilities: dict[CapabilityKind, AcquisitionMode]`
- [x] `probe() → ToolStatus` (keep `discover() → bool` as a binary wrapper)
- [x] Static capability manifests on mypy, flutter, eslint, phpstan, tsc
- [x] `analyzers/discovery.py`: detect ecosystems from pubspec / pyproject / package.json / composer.json
- [x] Classified failures (`NOT_INSTALLED`, `TIMEOUT`, …) instead of silent skip / empty
- [x] `get_analyzer_capabilities` reads `ToolStatus`, not `None`
- [x] Freeze probed tool versions and failures into `AnalysisRun.metadata`
- [x] Registry selects by capability, not only language/path
- [x] Orchestrator negotiation phase before `run` (expected tools → probe → acquire)

## Remaining ⏳

- [ ] Optional `harvest(kind) → StructuralArtifact | None`; keep `analyze()` for diagnostics
- [ ] Settings own discover/analyze timeouts; adapters stop hardcoding them
- [ ] Populate `ExternalDiagnostic.entity_ids`; implement evidence lookup by entity/scope
- [ ] Prefer harvest (mypy.api, tsc, ESLint SourceCode) over re-deriving AST/CFG
- [ ] Implement remaining AnalysisKinds (dominance, def-use, path conditions) gated by capabilities
- [ ] Defer LSP; ladder is library API → structured CLI → textual CLI
- [ ] Record derivation chains in `Provenance.extra` when a fact is DERIVABLE
- [ ] Project-requirements artifact so `VERSION_MISMATCH` has something to compare

## Implementation Notes

### Completed Items

**Domain Models (`domain/tooling.py`)**
- Implemented all required enums: `CapabilityKind`, `AcquisitionMode`, `ToolCapabilityState`, `ToolFailure`
- Implemented `ToolStatus` model with `is_usable()` method
- Implemented `StructuralArtifact` model for optional structural payload
- Added `tool_statuses_to_metadata()` helper function for freezing tool state

**Adapter Updates**
- Replaced prose `provides: list[str]` with machine-readable `capabilities: dict[CapabilityKind, AcquisitionMode]`
- Updated all adapters to use new capabilities dict:
  - `mypy.py`: DIAGNOSTICS, TYPES, SYMBOLS via CLI_STRUCTURED
  - `flutter_analyze.py`: DIAGNOSTICS, TYPES, SYMBOLS via CLI_TEXTUAL
  - `eslint.py`: DIAGNOSTICS via PROTOCOL, AST/SYMBOLS via LIBRARY_API
  - `phpstan.py`: DIAGNOSTICS, TYPES, CFG via CLI_STRUCTURED
  - `typescript.py`: DIAGNOSTICS, TYPES, SYMBOLS, REFERENCES via LIBRARY_API

**Enhanced Probe Methods**
- Implemented classified `probe()` methods with specific failure reasons:
  - `NOT_INSTALLED`: Binary not found on PATH
  - `TIMEOUT`: Version command timed out
  - `PERMISSION_DENIED`: OS permission error
  - `TOOL_CRASH`: Non-zero exit code
  - `INVALID_PROJECT`: Project doesn't match tool requirements
  - `UNSUPPORTED_FEATURE`: Scaffold adapters not yet implemented

**Evidence API**
- Implemented `get_analyzer_capabilities()` in `evidence/program_model.py`
- Added `set_tool_statuses()` method to register tool status information
- Returns comprehensive capability information including version, executable, and usability status

**Discovery System**
- `analyzers/discovery.py` already implemented with comprehensive ecosystem detection for:
  - Python (pyproject.toml, setup.py, setup.cfg, requirements.txt)
  - Flutter/Dart (pubspec.yaml with SDK constraints)
  - JavaScript/TypeScript (package.json, tsconfig.json)
  - PHP (composer.json)

**Registry Capability-Based Selection**
- Added `by_capability()` method to select adapters by single capability
- Added `by_capabilities()` method for complex capability queries with ANY/ALL semantics
- Both methods support optional project path filtering for combined capability + project selection
- Enables intelligent routing based on available capabilities rather than just language/path

**Orchestrator Negotiation Phase**
- Implemented `negotiate_tools()` method in `AnalysisOrchestrator`
- Integrates with existing `discovery.py` for ecosystem detection
- Probes all registered adapters and returns classified `ToolStatus` objects
- Called automatically during `run()` method before analysis execution

**Tool State Freezing**
- Integrated tool status freezing into `AnalysisRun.metadata` via `tool_statuses_to_metadata()`
- Tool versions, executables, capabilities, and failures are now persisted with each analysis run
- Critical for reproducibility and auditability of analysis results
- Metadata format: `tool.{analyzer_id}.{field}` (e.g., `tool.mypy.version`, `tool.flutter_analyze.failure`)

**Enhanced Analysis Execution**
- Modified `run()` method to use negotiation phase results
- Only executes adapters that are usable based on probe results
- Registers tool statuses with evidence API for capability queries during analysis
- Prevents silent failures by respecting classified failure modes

### Remaining Work Priority

**Medium Priority (Structural Harvesting)**
1. Implement harvest() methods in concrete adapters
2. Populate ExternalDiagnostic.entity_ids for evidence binding
3. Settings-based timeout management

**Lower Priority (Advanced Features)**
4. Remaining AnalysisKinds implementation
5. Derivation chain recording in Provenance
6. Project-requirements artifact for VERSION_MISMATCH
