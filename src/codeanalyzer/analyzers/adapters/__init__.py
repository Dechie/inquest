"""Concrete analyzer adapter stubs.

Initial integrations prioritize common ecosystems; additional analyzers can
follow without changing the core architecture.
"""

from codeanalyzer.analyzers.adapters.base_stub import StubAnalyzerAdapter
from codeanalyzer.analyzers.adapters.eslint import ESLintAdapter
from codeanalyzer.analyzers.adapters.flutter_analyze import FlutterAnalyzeAdapter
from codeanalyzer.analyzers.adapters.phpstan import PHPStanAdapter
from codeanalyzer.analyzers.adapters.typescript import TypeScriptAdapter

__all__ = [
    "ESLintAdapter",
    "FlutterAnalyzeAdapter",
    "PHPStanAdapter",
    "StubAnalyzerAdapter",
    "TypeScriptAdapter",
]
