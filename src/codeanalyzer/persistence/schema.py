"""SQLite schema for analysis metadata and relationships.

SQLite is the authoritative persistence layer. Large derived graph artifacts
may be materialized separately under graphs/.
"""

from __future__ import annotations

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS projects (
    id          TEXT PRIMARY KEY,
    path        TEXT NOT NULL,
    name        TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    metadata    TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS snapshots (
    id           TEXT PRIMARY KEY,
    project_id   TEXT NOT NULL REFERENCES projects(id),
    commit_hash  TEXT,
    created_at   TEXT NOT NULL,
    label        TEXT,
    metadata     TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS entities (
    id           TEXT PRIMARY KEY,
    snapshot_id  TEXT NOT NULL REFERENCES snapshots(id),
    type         TEXT NOT NULL,
    name         TEXT NOT NULL,
    qualified_name TEXT,
    file         TEXT,
    start_line   INTEGER,
    end_line     INTEGER,
    language     TEXT,
    metadata     TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_entities_snapshot ON entities(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(snapshot_id, name);

CREATE TABLE IF NOT EXISTS relationships (
    id           TEXT PRIMARY KEY,
    snapshot_id  TEXT NOT NULL REFERENCES snapshots(id),
    source_id    TEXT NOT NULL REFERENCES entities(id),
    target_id    TEXT NOT NULL REFERENCES entities(id),
    type         TEXT NOT NULL,
    location     TEXT,
    metadata     TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_rel_source ON relationships(source_id);
CREATE INDEX IF NOT EXISTS idx_rel_target ON relationships(target_id);

CREATE TABLE IF NOT EXISTS logical_slices (
    id                  TEXT PRIMARY KEY,
    snapshot_id         TEXT NOT NULL REFERENCES snapshots(id),
    name                TEXT NOT NULL,
    description         TEXT NOT NULL DEFAULT '',
    seed_specification  TEXT,
    approved            INTEGER NOT NULL DEFAULT 0,
    created_at          TEXT NOT NULL,
    metadata            TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS slice_members (
    slice_id         TEXT NOT NULL REFERENCES logical_slices(id),
    entity_id        TEXT NOT NULL,
    membership_type  TEXT NOT NULL,
    score            REAL,
    reason           TEXT NOT NULL DEFAULT '',
    signals          TEXT NOT NULL DEFAULT '[]',
    PRIMARY KEY (slice_id, entity_id)
);

CREATE TABLE IF NOT EXISTS analyses (
    id           TEXT PRIMARY KEY,
    slice_id     TEXT NOT NULL REFERENCES logical_slices(id),
    snapshot_id  TEXT NOT NULL REFERENCES snapshots(id),
    status       TEXT NOT NULL,
    created_at   TEXT NOT NULL,
    completed_at TEXT,
    error_message TEXT,
    metadata     TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS external_diagnostics (
    id                TEXT PRIMARY KEY,
    analysis_id       TEXT REFERENCES analyses(id),
    snapshot_id       TEXT NOT NULL REFERENCES snapshots(id),
    analyzer          TEXT NOT NULL,
    analyzer_version  TEXT,
    rule_id           TEXT,
    severity          TEXT NOT NULL,
    message           TEXT NOT NULL,
    location          TEXT,
    configuration     TEXT NOT NULL DEFAULT '{}',
    raw_payload       TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_diag_analysis ON external_diagnostics(analysis_id);
CREATE INDEX IF NOT EXISTS idx_diag_rule ON external_diagnostics(analyzer, rule_id);

CREATE TABLE IF NOT EXISTS findings (
    id            TEXT PRIMARY KEY,
    analysis_id   TEXT NOT NULL REFERENCES analyses(id),
    snapshot_id   TEXT NOT NULL REFERENCES snapshots(id),
    source        TEXT NOT NULL,
    detector      TEXT NOT NULL,
    type          TEXT NOT NULL,
    classification TEXT,
    severity      TEXT NOT NULL,
    confidence    REAL,
    status        TEXT NOT NULL,
    location      TEXT,
    message       TEXT NOT NULL DEFAULT '',
    analyzer      TEXT,
    rule_id       TEXT,
    payload       TEXT NOT NULL DEFAULT '{}',
    created_at    TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_findings_analysis ON findings(analysis_id);
CREATE INDEX IF NOT EXISTS idx_findings_status ON findings(status);

CREATE TABLE IF NOT EXISTS evidence_slices (
    id          TEXT PRIMARY KEY,
    finding_id  TEXT NOT NULL REFERENCES findings(id),
    created_at  TEXT NOT NULL,
    metadata    TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS evidence_items (
    id                 TEXT PRIMARY KEY,
    evidence_slice_id  TEXT NOT NULL REFERENCES evidence_slices(id),
    type               TEXT NOT NULL,
    entity_id          TEXT,
    source             TEXT,
    location           TEXT,
    payload            TEXT NOT NULL DEFAULT '{}',
    summary            TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS documentation (
    id           TEXT PRIMARY KEY,
    snapshot_id  TEXT NOT NULL REFERENCES snapshots(id),
    source       TEXT NOT NULL,
    location     TEXT,
    title        TEXT,
    content      TEXT NOT NULL,
    kind         TEXT,
    metadata     TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS doc_entities (
    doc_id        TEXT NOT NULL REFERENCES documentation(id),
    entity_id     TEXT NOT NULL,
    relationship  TEXT NOT NULL,
    PRIMARY KEY (doc_id, entity_id)
);

CREATE TABLE IF NOT EXISTS schema_migrations (
    version     INTEGER PRIMARY KEY,
    applied_at  TEXT NOT NULL
);
"""

SCHEMA_VERSION = 1
