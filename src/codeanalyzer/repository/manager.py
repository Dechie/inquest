"""Repository / snapshot lifecycle."""

from __future__ import annotations

import subprocess
import uuid
from datetime import UTC, datetime
from pathlib import Path

from codeanalyzer.domain.snapshots import Project, Snapshot
from codeanalyzer.persistence.paths import AnalysisPaths


class RepositoryManager:
    """Registers projects and creates analysis snapshots."""

    def __init__(self, paths: AnalysisPaths | None = None) -> None:
        self.paths = paths
        self._projects: dict[str, Project] = {}
        self._snapshots: dict[str, Snapshot] = {}

    def register_project(self, path: str | Path, name: str | None = None) -> Project:
        root = Path(path).resolve()
        project = Project(
            id=f"proj_{uuid.uuid4().hex[:12]}",
            path=str(root),
            name=name or root.name,
        )
        self._projects[project.id] = project
        if self.paths is None:
            self.paths = AnalysisPaths.for_project(root)
            self.paths.ensure()
        return project

    def create_snapshot(
        self,
        project: Project,
        *,
        commit_hash: str | None = None,
        label: str | None = None,
    ) -> Snapshot:
        if commit_hash is None:
            commit_hash = self._detect_commit(project.path)
        snapshot = Snapshot(
            id=f"snap_{uuid.uuid4().hex[:12]}",
            project_id=project.id,
            commit_hash=commit_hash,
            created_at=datetime.now(UTC),
            label=label,
        )
        self._snapshots[snapshot.id] = snapshot
        return snapshot

    def get_project(self, project_id: str) -> Project | None:
        return self._projects.get(project_id)

    def get_snapshot(self, snapshot_id: str) -> Snapshot | None:
        return self._snapshots.get(snapshot_id)

    @staticmethod
    def _detect_commit(project_path: str) -> str | None:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=project_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip() or None
        except (OSError, subprocess.TimeoutExpired):
            pass
        return None
