"""Registry of external analyzer adapters."""

from __future__ import annotations

from codeanalyzer.analyzers.adapter import AnalyzerAdapter
from codeanalyzer.domain.tooling import CapabilityKind


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

    def by_capability(
        self,
        capability: CapabilityKind,
        *,
        project_path: str | None = None,
    ) -> list[AnalyzerAdapter]:
        """Return adapters that declare a specific capability.

        Optionally filters by project support. Useful for capability-based
        routing in the negotiation phase.
        """
        result: list[AnalyzerAdapter] = []
        for adapter in self._adapters.values():
            caps = adapter.capabilities()
            if capability in caps.capabilities:
                if project_path is None or adapter.supports(project_path=project_path):
                    result.append(adapter)
        return result

    def by_capabilities(
        self,
        capabilities: set[CapabilityKind],
        *,
        project_path: str | None = None,
        require_all: bool = False,
    ) -> list[AnalyzerAdapter]:
        """Return adapters that declare the given capabilities.

        Args:
            capabilities: Set of capability kinds to match
            project_path: Optional project path to filter by project support
            require_all: If True, adapter must have ALL capabilities; if False, ANY capability

        Returns:
            List of adapters matching the capability criteria
        """
        result: list[AnalyzerAdapter] = []
        for adapter in self._adapters.values():
            caps = adapter.capabilities()
            adapter_caps = set(caps.capabilities.keys())
            
            if require_all:
                matches = capabilities.issubset(adapter_caps)
            else:
                matches = not capabilities.isdisjoint(adapter_caps)
            
            if matches:
                if project_path is None or adapter.supports(project_path=project_path):
                    result.append(adapter)
        return result
