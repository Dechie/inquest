"""TypeScript compiler adapter (scaffold)."""

from __future__ import annotations

from codeanalyzer.analyzers.adapters.base_stub import StubAnalyzerAdapter
from codeanalyzer.domain.tooling import AcquisitionMode, CapabilityKind


class TypeScriptAdapter(StubAnalyzerAdapter):
    def __init__(self) -> None:
        super().__init__(
            analyzer_id="typescript",
            display_name="TypeScript Compiler",
            languages=["typescript"],
            capabilities={
                CapabilityKind.DIAGNOSTICS: AcquisitionMode.LIBRARY_API,
                CapabilityKind.TYPES: AcquisitionMode.LIBRARY_API,
                CapabilityKind.SYMBOLS: AcquisitionMode.LIBRARY_API,
                CapabilityKind.REFERENCES: AcquisitionMode.LIBRARY_API,
            },
            binary_name="tsc",
        )
