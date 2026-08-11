"""TypeScript compiler adapter (scaffold)."""

from __future__ import annotations

from codeanalyzer.analyzers.adapters.base_stub import StubAnalyzerAdapter


class TypeScriptAdapter(StubAnalyzerAdapter):
    def __init__(self) -> None:
        super().__init__(
            analyzer_id="typescript",
            display_name="TypeScript Compiler",
            languages=["typescript"],
            provides=[
                "type diagnostics",
                "compiler errors",
                "declaration checks",
            ],
            binary_name="tsc",
        )
