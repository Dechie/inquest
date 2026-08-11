"""Language frontend protocol (Phase A)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from codeanalyzer.domain.snapshots import Snapshot
from codeanalyzer.program.model import ProgramModel


class LanguageFrontend(ABC):
    """Parses source for one language family into a program model contribution."""

    @property
    @abstractmethod
    def language(self) -> str: ...

    @property
    @abstractmethod
    def extensions(self) -> list[str]: ...

    @abstractmethod
    def supports(self, project_path: str) -> bool: ...

    @abstractmethod
    def analyze(self, snapshot: Snapshot, *, project_path: str) -> ProgramModel:
        """Build (or contribute to) a program model for the snapshot."""
