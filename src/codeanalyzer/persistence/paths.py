"""Filesystem layout under .codeanalyzer/.

.codeanalyzer/
├── analysis.db
├── graphs/
├── snapshots/
└── cache/
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ANALYSIS_DIR_NAME = ".codeanalyzer"


@dataclass(frozen=True)
class AnalysisPaths:
    """Paths for the authoritative SQLite store and artifact/cache layers."""

    root: Path

    @classmethod
    def for_project(cls, project_root: str | Path) -> AnalysisPaths:
        return cls(root=Path(project_root).resolve() / ANALYSIS_DIR_NAME)

    @property
    def db_path(self) -> Path:
        return self.root / "analysis.db"

    @property
    def graphs_dir(self) -> Path:
        return self.root / "graphs"

    @property
    def snapshots_dir(self) -> Path:
        return self.root / "snapshots"

    @property
    def cache_dir(self) -> Path:
        return self.root / "cache"

    def ensure(self) -> None:
        """Create the standard directory layout."""
        self.root.mkdir(parents=True, exist_ok=True)
        self.graphs_dir.mkdir(exist_ok=True)
        self.snapshots_dir.mkdir(exist_ok=True)
        self.cache_dir.mkdir(exist_ok=True)
