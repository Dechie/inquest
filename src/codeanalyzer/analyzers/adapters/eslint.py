"""ESLint adapter (scaffold)."""

from __future__ import annotations

from codeanalyzer.analyzers.adapters.base_stub import StubAnalyzerAdapter
from codeanalyzer.domain.tooling import AcquisitionMode, CapabilityKind


class ESLintAdapter(StubAnalyzerAdapter):
    def __init__(self) -> None:
        super().__init__(
            analyzer_id="eslint",
            display_name="ESLint",
            languages=["javascript", "typescript"],
            capabilities={
                CapabilityKind.DIAGNOSTICS: AcquisitionMode.PROTOCOL,
                CapabilityKind.AST: AcquisitionMode.LIBRARY_API,
                CapabilityKind.SYMBOLS: AcquisitionMode.LIBRARY_API,
            },
            binary_name="eslint",
        )
