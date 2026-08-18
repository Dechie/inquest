"""PHPStan adapter (scaffold)."""

from __future__ import annotations

from codeanalyzer.analyzers.adapters.base_stub import StubAnalyzerAdapter
from codeanalyzer.domain.tooling import AcquisitionMode, CapabilityKind


class PHPStanAdapter(StubAnalyzerAdapter):
    def __init__(self) -> None:
        super().__init__(
            analyzer_id="phpstan",
            display_name="PHPStan",
            languages=["php"],
            capabilities={
                CapabilityKind.DIAGNOSTICS: AcquisitionMode.CLI_STRUCTURED,
                CapabilityKind.TYPES: AcquisitionMode.CLI_STRUCTURED,
                CapabilityKind.CFG: AcquisitionMode.CLI_STRUCTURED,
            },
            binary_name="phpstan",
        )
