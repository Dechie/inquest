"""SQLite store layer for analysis metadata.

These stores are the write path for named slices, analyses, findings, and
evidence. Graph artifacts remain on the filesystem.
"""

from __future__ import annotations

from typing import Any

from codeanalyzer.domain.diagnostics import ExternalDiagnostic
from codeanalyzer.domain.enums import (
    EvidenceItemType,
    FindingSource,
    FindingStatus,
    MembershipClass,
    PropertyKind,
    PropertySource,
    ProvenanceKind,
    Severity,
    VerificationOutcome,
)
from codeanalyzer.domain.evidence import EvidenceItem, EvidenceRequirement, MinimalEvidenceSlice
from codeanalyzer.domain.findings import Finding
from codeanalyzer.domain.properties import CorrectnessProperty
from codeanalyzer.domain.provenance import Provenance
from codeanalyzer.domain.slices import LogicalSlice, SliceMember
from codeanalyzer.domain.snapshots import AnalysisRun, AnalysisStatus, Project, Snapshot
from codeanalyzer.persistence.codec import (
    dt_from_iso,
    dt_to_iso,
    dumps,
    loads,
    location_from_text,
    location_to_text,
)
from codeanalyzer.persistence.db import Database
from codeanalyzer.persistence.paths import AnalysisPaths


class ProjectStore:
    def __init__(self, db: Database) -> None:
        self._db = db

    def save(self, project: Project) -> None:
        conn = self._db.connect()
        with conn:
            conn.execute(
                """
                INSERT INTO projects (id, path, name, created_at, metadata)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    path = excluded.path,
                    name = excluded.name,
                    metadata = excluded.metadata
                """,
                (
                    project.id,
                    project.path,
                    project.name,
                    dt_to_iso(project.created_at),
                    dumps(project.metadata),
                ),
            )

    def get(self, project_id: str) -> Project | None:
        row = (
            self._db.connect()
            .execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            .fetchone()
        )
        return _project_from_row(row) if row is not None else None

    def get_by_path(self, path: str) -> Project | None:
        row = (
            self._db.connect()
            .execute(
                "SELECT * FROM projects WHERE path = ? ORDER BY created_at ASC LIMIT 1",
                (path,),
            )
            .fetchone()
        )
        return _project_from_row(row) if row is not None else None

    def list_all(self) -> list[Project]:
        rows = self._db.connect().execute("SELECT * FROM projects ORDER BY created_at").fetchall()
        return [_project_from_row(row) for row in rows]


class SnapshotStore:
    def __init__(self, db: Database) -> None:
        self._db = db

    def save(self, snapshot: Snapshot) -> None:
        conn = self._db.connect()
        with conn:
            conn.execute(
                """
                INSERT INTO snapshots (id, project_id, commit_hash, created_at, label, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    commit_hash = excluded.commit_hash,
                    label = excluded.label,
                    metadata = excluded.metadata
                """,
                (
                    snapshot.id,
                    snapshot.project_id,
                    snapshot.commit_hash,
                    dt_to_iso(snapshot.created_at),
                    snapshot.label,
                    dumps(snapshot.metadata),
                ),
            )

    def get(self, snapshot_id: str) -> Snapshot | None:
        row = (
            self._db.connect()
            .execute("SELECT * FROM snapshots WHERE id = ?", (snapshot_id,))
            .fetchone()
        )
        return _snapshot_from_row(row) if row is not None else None

    def list_for_project(self, project_id: str) -> list[Snapshot]:
        rows = (
            self._db.connect()
            .execute(
                "SELECT * FROM snapshots WHERE project_id = ? ORDER BY created_at",
                (project_id,),
            )
            .fetchall()
        )
        return [_snapshot_from_row(row) for row in rows]

    def list_all(self) -> list[Snapshot]:
        rows = self._db.connect().execute("SELECT * FROM snapshots ORDER BY created_at").fetchall()
        return [_snapshot_from_row(row) for row in rows]


class SliceStore:
    def __init__(self, db: Database) -> None:
        self._db = db

    def save(self, slice_: LogicalSlice) -> None:
        metadata = {
            "inclusion_rules": slice_.inclusion_rules,
            "exclusion_rules": slice_.exclusion_rules,
            "documentation_ids": slice_.documentation_ids,
            "metadata": slice_.metadata,
        }
        conn = self._db.connect()
        with conn:
            conn.execute(
                """
                INSERT INTO logical_slices (
                    id, snapshot_id, name, description, seed_specification,
                    approved, created_at, metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    description = excluded.description,
                    seed_specification = excluded.seed_specification,
                    approved = excluded.approved,
                    metadata = excluded.metadata
                """,
                (
                    slice_.id,
                    slice_.snapshot_id,
                    slice_.name,
                    slice_.description,
                    slice_.seed_specification,
                    1 if slice_.approved else 0,
                    dt_to_iso(slice_.created_at),
                    dumps(metadata),
                ),
            )
            conn.execute("DELETE FROM slice_members WHERE slice_id = ?", (slice_.id,))
            conn.executemany(
                """
                INSERT INTO slice_members (
                    slice_id, entity_id, membership_type, score, reason, signals
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        slice_.id,
                        member.entity_id,
                        member.membership.value,
                        member.score,
                        dumps(member.reasons),
                        dumps(member.signals),
                    )
                    for member in slice_.members
                ],
            )

    def get(self, slice_id: str) -> LogicalSlice | None:
        conn = self._db.connect()
        row = conn.execute("SELECT * FROM logical_slices WHERE id = ?", (slice_id,)).fetchone()
        if row is None:
            return None
        members = conn.execute(
            "SELECT * FROM slice_members WHERE slice_id = ?",
            (slice_id,),
        ).fetchall()
        return _slice_from_rows(row, members)

    def list(self, snapshot_id: str | None = None) -> list[LogicalSlice]:
        conn = self._db.connect()
        if snapshot_id is None:
            rows = conn.execute("SELECT * FROM logical_slices ORDER BY created_at").fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM logical_slices WHERE snapshot_id = ? ORDER BY created_at",
                (snapshot_id,),
            ).fetchall()
        result: list[LogicalSlice] = []
        for row in rows:
            members = conn.execute(
                "SELECT * FROM slice_members WHERE slice_id = ?",
                (row["id"],),
            ).fetchall()
            result.append(_slice_from_rows(row, members))
        return result


class AnalysisStore:
    def __init__(self, db: Database) -> None:
        self._db = db

    def save(self, analysis: AnalysisRun) -> None:
        conn = self._db.connect()
        with conn:
            conn.execute(
                """
                INSERT INTO analyses (
                    id, slice_id, snapshot_id, status, created_at,
                    completed_at, error_message, metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    status = excluded.status,
                    completed_at = excluded.completed_at,
                    error_message = excluded.error_message,
                    metadata = excluded.metadata
                """,
                (
                    analysis.id,
                    analysis.slice_id,
                    analysis.snapshot_id,
                    analysis.status.value,
                    dt_to_iso(analysis.created_at),
                    dt_to_iso(analysis.completed_at) if analysis.completed_at else None,
                    analysis.error_message,
                    dumps(analysis.metadata),
                ),
            )

    def get(self, analysis_id: str) -> AnalysisRun | None:
        row = (
            self._db.connect()
            .execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,))
            .fetchone()
        )
        return _analysis_from_row(row) if row is not None else None

    def list_all(self) -> list[AnalysisRun]:
        rows = self._db.connect().execute("SELECT * FROM analyses ORDER BY created_at").fetchall()
        return [_analysis_from_row(row) for row in rows]

    def save_diagnostic(self, diagnostic: ExternalDiagnostic) -> None:
        conn = self._db.connect()
        with conn:
            conn.execute(
                """
                INSERT INTO external_diagnostics (
                    id, analysis_id, snapshot_id, analyzer, analyzer_version,
                    rule_id, severity, message, location, configuration, raw_payload
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    analyzer_version = excluded.analyzer_version,
                    rule_id = excluded.rule_id,
                    severity = excluded.severity,
                    message = excluded.message,
                    location = excluded.location,
                    configuration = excluded.configuration,
                    raw_payload = excluded.raw_payload
                """,
                (
                    diagnostic.id,
                    diagnostic.analysis_id,
                    diagnostic.snapshot_id,
                    diagnostic.analyzer,
                    diagnostic.analyzer_version,
                    diagnostic.rule_id,
                    diagnostic.severity.value,
                    diagnostic.message,
                    location_to_text(diagnostic.location),
                    dumps(diagnostic.configuration),
                    dumps(
                        {
                            "raw_diagnostic": diagnostic.raw_diagnostic,
                            "entity_ids": diagnostic.entity_ids,
                        }
                    ),
                ),
            )

    def list_diagnostics(self, analysis_id: str | None = None) -> list[ExternalDiagnostic]:
        conn = self._db.connect()
        if analysis_id is None:
            rows = conn.execute("SELECT * FROM external_diagnostics").fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM external_diagnostics WHERE analysis_id = ?",
                (analysis_id,),
            ).fetchall()
        return [_diagnostic_from_row(row) for row in rows]


class PropertyStore:
    def __init__(self, db: Database) -> None:
        self._db = db

    def save(self, prop: CorrectnessProperty) -> None:
        conn = self._db.connect()
        with conn:
            conn.execute(
                """
                INSERT INTO properties (
                    id, snapshot_id, slice_id, kind, statement, source,
                    scope_entity_ids, formalization, provenance, detector_ids,
                    metadata, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    statement = excluded.statement,
                    scope_entity_ids = excluded.scope_entity_ids,
                    formalization = excluded.formalization,
                    provenance = excluded.provenance,
                    detector_ids = excluded.detector_ids,
                    metadata = excluded.metadata
                """,
                (
                    prop.id,
                    prop.snapshot_id,
                    prop.slice_id,
                    prop.kind.value,
                    prop.statement,
                    prop.source.value,
                    dumps(prop.scope_entity_ids),
                    dumps(prop.formalization) if prop.formalization else None,
                    dumps(prop.provenance.model_dump(mode="json")) if prop.provenance else None,
                    dumps(prop.detector_ids),
                    dumps(prop.metadata),
                    dt_to_iso(prop.created_at),
                ),
            )

    def list_for_slice(self, slice_id: str) -> list[CorrectnessProperty]:
        rows = (
            self._db.connect()
            .execute(
                "SELECT * FROM properties WHERE slice_id = ? ORDER BY created_at",
                (slice_id,),
            )
            .fetchall()
        )
        return [_property_from_row(row) for row in rows]


class FindingStore:
    def __init__(self, db: Database) -> None:
        self._db = db

    def save(self, finding: Finding) -> None:
        payload = {
            "affected_entity_ids": finding.affected_entity_ids,
            "property_id": finding.property_id,
            "verification_outcome": (
                finding.verification_outcome.value
                if finding.verification_outcome is not None
                else None
            ),
            "evidence_requirements": [
                req.model_dump(mode="json") for req in finding.evidence_requirements
            ],
            "payload": finding.payload,
        }
        conn = self._db.connect()
        with conn:
            conn.execute(
                """
                INSERT INTO findings (
                    id, analysis_id, snapshot_id, source, detector, type,
                    classification, severity, confidence, status, location,
                    message, analyzer, rule_id, payload, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    classification = excluded.classification,
                    severity = excluded.severity,
                    confidence = excluded.confidence,
                    status = excluded.status,
                    location = excluded.location,
                    message = excluded.message,
                    payload = excluded.payload
                """,
                (
                    finding.id,
                    finding.analysis_id,
                    finding.snapshot_id,
                    finding.source.value,
                    finding.detector,
                    finding.type,
                    finding.classification,
                    finding.severity.value,
                    finding.confidence,
                    finding.status.value,
                    location_to_text(finding.location),
                    finding.message,
                    finding.analyzer,
                    finding.rule_id,
                    dumps(payload),
                    dt_to_iso(finding.created_at),
                ),
            )

    def get(self, finding_id: str) -> Finding | None:
        row = (
            self._db.connect()
            .execute("SELECT * FROM findings WHERE id = ?", (finding_id,))
            .fetchone()
        )
        return _finding_from_row(row) if row is not None else None

    def list_for_analysis(self, analysis_id: str) -> list[Finding]:
        rows = (
            self._db.connect()
            .execute(
                "SELECT * FROM findings WHERE analysis_id = ? ORDER BY created_at",
                (analysis_id,),
            )
            .fetchall()
        )
        return [_finding_from_row(row) for row in rows]

    def list_all(self) -> list[Finding]:
        rows = self._db.connect().execute("SELECT * FROM findings ORDER BY created_at").fetchall()
        return [_finding_from_row(row) for row in rows]


class EvidenceStore:
    def __init__(self, db: Database) -> None:
        self._db = db

    def save(self, slice_: MinimalEvidenceSlice) -> None:
        metadata = slice_.model_dump(
            mode="json",
            exclude={"id", "finding_id", "created_at", "items"},
        )
        conn = self._db.connect()
        with conn:
            conn.execute(
                """
                INSERT INTO evidence_slices (id, finding_id, created_at, metadata)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    metadata = excluded.metadata
                """,
                (
                    slice_.id,
                    slice_.finding_id,
                    dt_to_iso(slice_.created_at),
                    dumps(metadata),
                ),
            )
            conn.execute("DELETE FROM evidence_items WHERE evidence_slice_id = ?", (slice_.id,))
            conn.executemany(
                """
                INSERT INTO evidence_items (
                    id, evidence_slice_id, type, entity_id, source, location, payload, summary
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        item.id,
                        slice_.id,
                        item.type.value,
                        item.entity_id,
                        item.provenance.source,
                        item.location,
                        dumps(
                            {
                                "payload": item.payload,
                                "provenance": item.provenance.model_dump(mode="json"),
                            }
                        ),
                        item.summary,
                    )
                    for item in slice_.items
                ],
            )

    def get(self, slice_id: str) -> MinimalEvidenceSlice | None:
        conn = self._db.connect()
        row = conn.execute("SELECT * FROM evidence_slices WHERE id = ?", (slice_id,)).fetchone()
        if row is None:
            return None
        items = conn.execute(
            "SELECT * FROM evidence_items WHERE evidence_slice_id = ?",
            (slice_id,),
        ).fetchall()
        return _evidence_from_rows(row, items)

    def list_for_finding(self, finding_id: str) -> list[MinimalEvidenceSlice]:
        conn = self._db.connect()
        rows = conn.execute(
            "SELECT * FROM evidence_slices WHERE finding_id = ? ORDER BY created_at",
            (finding_id,),
        ).fetchall()
        result: list[MinimalEvidenceSlice] = []
        for row in rows:
            items = conn.execute(
                "SELECT * FROM evidence_items WHERE evidence_slice_id = ?",
                (row["id"],),
            ).fetchall()
            result.append(_evidence_from_rows(row, items))
        return result


class Stores:
    """Facade over the relational stores that share one Database."""

    def __init__(self, db: Database) -> None:
        self.db = db
        self.projects = ProjectStore(db)
        self.snapshots = SnapshotStore(db)
        self.slices = SliceStore(db)
        self.analyses = AnalysisStore(db)
        self.findings = FindingStore(db)
        self.evidence = EvidenceStore(db)
        self.properties = PropertyStore(db)

    @classmethod
    def open(cls, paths: AnalysisPaths) -> Stores:
        paths.ensure()
        db = Database(paths.db_path)
        db.initialize()
        return cls(db)

    def close(self) -> None:
        self.db.close()


def _project_from_row(row: Any) -> Project:
    return Project(
        id=row["id"],
        path=row["path"],
        name=row["name"],
        created_at=dt_from_iso(row["created_at"]),
        metadata=loads(row["metadata"], {}),
    )


def _snapshot_from_row(row: Any) -> Snapshot:
    return Snapshot(
        id=row["id"],
        project_id=row["project_id"],
        commit_hash=row["commit_hash"],
        created_at=dt_from_iso(row["created_at"]),
        label=row["label"],
        metadata=loads(row["metadata"], {}),
    )


def _slice_from_rows(row: Any, member_rows: list[Any]) -> LogicalSlice:
    extra: dict[str, Any] = loads(row["metadata"], {})
    metadata = extra.get("metadata", extra) if isinstance(extra.get("metadata"), dict) else extra
    return LogicalSlice(
        id=row["id"],
        name=row["name"],
        description=row["description"] or "",
        snapshot_id=row["snapshot_id"],
        members=[_member_from_row(member) for member in member_rows],
        inclusion_rules=list(extra.get("inclusion_rules") or []),
        exclusion_rules=list(extra.get("exclusion_rules") or []),
        documentation_ids=list(extra.get("documentation_ids") or []),
        seed_specification=row["seed_specification"],
        created_at=dt_from_iso(row["created_at"]),
        approved=bool(row["approved"]),
        metadata=metadata if isinstance(metadata, dict) else {},
    )


def _member_from_row(row: Any) -> SliceMember:
    raw_reason = row["reason"] or ""
    reasons = loads(raw_reason, None)
    if reasons is None:
        reasons = [raw_reason] if raw_reason else []
    elif isinstance(reasons, str):
        reasons = [reasons]
    return SliceMember(
        entity_id=row["entity_id"],
        membership=MembershipClass(row["membership_type"]),
        score=row["score"],
        reasons=list(reasons),
        signals=loads(row["signals"], []),
    )


def _analysis_from_row(row: Any) -> AnalysisRun:
    completed = row["completed_at"]
    return AnalysisRun(
        id=row["id"],
        slice_id=row["slice_id"],
        snapshot_id=row["snapshot_id"],
        status=AnalysisStatus(row["status"]),
        created_at=dt_from_iso(row["created_at"]),
        completed_at=dt_from_iso(completed) if completed else None,
        error_message=row["error_message"],
        metadata=loads(row["metadata"], {}),
    )


def _diagnostic_from_row(row: Any) -> ExternalDiagnostic:
    raw: dict[str, Any] = loads(row["raw_payload"], {})
    raw_diagnostic = raw.get("raw_diagnostic", raw)
    entity_ids = raw.get("entity_ids", [])
    return ExternalDiagnostic(
        id=row["id"],
        analysis_id=row["analysis_id"],
        snapshot_id=row["snapshot_id"],
        analyzer=row["analyzer"],
        analyzer_version=row["analyzer_version"],
        rule_id=row["rule_id"],
        severity=Severity(row["severity"]),
        message=row["message"],
        location=location_from_text(row["location"]),
        entity_ids=list(entity_ids),
        configuration=loads(row["configuration"], {}),
        raw_diagnostic=raw_diagnostic if isinstance(raw_diagnostic, dict) else {},
    )


def _finding_from_row(row: Any) -> Finding:
    extra: dict[str, Any] = loads(row["payload"], {})
    requirements = extra.get("evidence_requirements") or []
    outcome_raw = extra.get("verification_outcome")
    return Finding(
        id=row["id"],
        analysis_id=row["analysis_id"],
        snapshot_id=row["snapshot_id"],
        source=FindingSource(row["source"]),
        property_id=extra.get("property_id"),
        verification_outcome=(
            VerificationOutcome(outcome_raw) if outcome_raw is not None else None
        ),
        detector=row["detector"],
        type=row["type"],
        classification=row["classification"],
        severity=Severity(row["severity"]),
        confidence=row["confidence"],
        location=location_from_text(row["location"]),
        affected_entity_ids=list(extra.get("affected_entity_ids") or []),
        evidence_requirements=[EvidenceRequirement.model_validate(req) for req in requirements],
        status=FindingStatus(row["status"]),
        message=row["message"] or "",
        analyzer=row["analyzer"],
        rule_id=row["rule_id"],
        payload=extra.get("payload") or {},
        created_at=dt_from_iso(row["created_at"]),
    )


def _evidence_from_rows(row: Any, item_rows: list[Any]) -> MinimalEvidenceSlice:
    extra: dict[str, Any] = loads(row["metadata"], {})
    return MinimalEvidenceSlice(
        id=row["id"],
        finding_id=row["finding_id"],
        property_id=extra.get("property_id"),
        program_entities=list(extra.get("program_entities") or []),
        call_edges=list(extra.get("call_edges") or []),
        control_flow_fragments=list(extra.get("control_flow_fragments") or []),
        data_flow_fragments=list(extra.get("data_flow_fragments") or []),
        external_diagnostic_ids=list(extra.get("external_diagnostic_ids") or []),
        relevant_conditions=list(extra.get("relevant_conditions") or []),
        documentation_ids=list(extra.get("documentation_ids") or []),
        items=[_evidence_item_from_row(item) for item in item_rows],
        facts=extra.get("facts") or [],
        created_at=dt_from_iso(row["created_at"]),
        metadata=extra.get("metadata") or {},
    )


def _property_from_row(row: Any) -> CorrectnessProperty:
    provenance_data = loads(row["provenance"], None)
    return CorrectnessProperty(
        id=row["id"],
        snapshot_id=row["snapshot_id"],
        slice_id=row["slice_id"],
        kind=PropertyKind(row["kind"]),
        statement=row["statement"],
        source=PropertySource(row["source"]),
        scope_entity_ids=loads(row["scope_entity_ids"], []),
        formalization=loads(row["formalization"], None),
        provenance=Provenance.model_validate(provenance_data) if provenance_data else None,
        detector_ids=loads(row["detector_ids"], []),
        metadata=loads(row["metadata"], {}),
        created_at=dt_from_iso(row["created_at"]),
    )


def _evidence_item_from_row(row: Any) -> EvidenceItem:
    extra: dict[str, Any] = loads(row["payload"], {})
    provenance_data = extra.get("provenance") or {
        "kind": ProvenanceKind.PROGRAM_FACT.value,
        "source": row["source"] or "",
    }
    return EvidenceItem(
        id=row["id"],
        type=EvidenceItemType(row["type"]),
        entity_id=row["entity_id"],
        location=row["location"],
        payload=extra.get("payload") or {},
        provenance=Provenance.model_validate(provenance_data),
        summary=row["summary"] or "",
    )
