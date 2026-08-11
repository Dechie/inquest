"""Flutter Analyze adapter (scaffold)."""

from __future__ import annotations

from codeanalyzer.analyzers.adapters.base_stub import StubAnalyzerAdapter


class FlutterAnalyzeAdapter(StubAnalyzerAdapter):
    def __init__(self) -> None:
        super().__init__(
            analyzer_id="flutter_analyze",
            display_name="Flutter Analyze",
            languages=["dart"],
            provides=[
                "type diagnostics",
                "undefined symbols",
                "analyzer diagnostics",
                "lint rules",
            ],
            binary_name="flutter",
        )
