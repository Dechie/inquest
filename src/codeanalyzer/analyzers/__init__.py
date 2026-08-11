"""External analyzer integration — first-class analysis providers."""

from codeanalyzer.analyzers.adapter import AnalyzerAdapter, AnalyzerCapabilities
from codeanalyzer.analyzers.registry import AnalyzerRegistry

__all__ = ["AnalyzerAdapter", "AnalyzerCapabilities", "AnalyzerRegistry"]
