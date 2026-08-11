"""Persistence schema and path tests."""

from __future__ import annotations

from pathlib import Path

from codeanalyzer.persistence.db import Database
from codeanalyzer.persistence.paths import AnalysisPaths


def test_analysis_paths(tmp_path: Path) -> None:
    paths = AnalysisPaths.for_project(tmp_path)
    paths.ensure()
    assert paths.db_path.parent == paths.root
    assert paths.graphs_dir.is_dir()
    assert paths.snapshots_dir.is_dir()
    assert paths.cache_dir.is_dir()


def test_database_schema(tmp_path: Path) -> None:
    db_path = tmp_path / "analysis.db"
    with Database(db_path) as db:
        conn = db.connect()
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
    expected = {
        "projects",
        "snapshots",
        "entities",
        "relationships",
        "logical_slices",
        "slice_members",
        "analyses",
        "external_diagnostics",
        "findings",
        "evidence_slices",
        "evidence_items",
        "documentation",
        "doc_entities",
        "schema_migrations",
    }
    assert expected.issubset(tables)
