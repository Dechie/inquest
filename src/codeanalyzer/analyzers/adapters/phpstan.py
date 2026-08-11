"""PHPStan adapter (scaffold)."""

from __future__ import annotations

from codeanalyzer.analyzers.adapters.base_stub import StubAnalyzerAdapter


class PHPStanAdapter(StubAnalyzerAdapter):
    def __init__(self) -> None:
        super().__init__(
            analyzer_id="phpstan",
            display_name="PHPStan",
            languages=["php"],
            provides=[
                "static analysis diagnostics",
                "type inference issues",
                "undefined property/method checks",
            ],
            binary_name="phpstan",
        )
