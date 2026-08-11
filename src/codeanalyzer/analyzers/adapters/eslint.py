"""ESLint adapter (scaffold)."""

from __future__ import annotations

from codeanalyzer.analyzers.adapters.base_stub import StubAnalyzerAdapter


class ESLintAdapter(StubAnalyzerAdapter):
    def __init__(self) -> None:
        super().__init__(
            analyzer_id="eslint",
            display_name="ESLint",
            languages=["javascript", "typescript"],
            provides=[
                "JavaScript/TypeScript lint diagnostics",
                "AST-based rules",
                "plugin diagnostics",
            ],
            binary_name="eslint",
        )
