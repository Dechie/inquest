"""Registry of external analyzer adapters."""

from __future__ import annotations

from codeanalyzer.analyzers.adapter import AnalyzerAdapter


class AnalyzerRegistry:
    """Discovers and selects applicable analyzer adapters."""

    def __init__(self) -> None:
        self._adapters: dict[str, AnalyzerAdapter] = {}

    def register(self, adapter: AnalyzerAdapter) -> None:
        caps = adapter.capabilities()
        self._adapters[caps.analyzer_id] = adapter

    def get(self, analyzer_id: str) -> AnalyzerAdapter | None:
        return self._adapters.get(analyzer_id)

    def all(self) -> list[AnalyzerAdapter]:
        return list(self._adapters.values())

    def discover_available(self) -> list[AnalyzerAdapter]:
        return [a for a in self._adapters.values() if a.discover()]

    def for_project(
        self,
        *,
        project_path: str,
        languages: list[str] | None = None,
    ) -> list[AnalyzerAdapter]:
        """Return adapters that support this project (and optionally languages)."""
        result: list[AnalyzerAdapter] = []
        for adapter in self._adapters.values():
            if languages:
                if any(
                    adapter.supports(language=lang, project_path=project_path)
                    for lang in languages
                ):
                    result.append(adapter)
            elif adapter.supports(project_path=project_path):
                result.append(adapter)
        return result
