"""Project, repository snapshot, and analysis-run models."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class AnalysisStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Project(BaseModel):
    """Analyzed project / repository root."""

    id: str
    path: str
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, str] = Field(default_factory=dict)


class Snapshot(BaseModel):
    """Immutable view of a repository at a point in time.

    Every analysis, finding, and evidence item must retain snapshot identity.
    """

    id: str
    project_id: str
    commit_hash: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    label: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class AnalysisRun(BaseModel):
    """One analysis of a logical slice against a snapshot."""

    id: str
    slice_id: str
    snapshot_id: str
    status: AnalysisStatus = AnalysisStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    error_message: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
