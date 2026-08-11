"""Application settings (scaffold)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Runtime configuration for analysis runs."""

    project_path: str | None = None
    analysis_dir_name: str = ".codeanalyzer"
    enable_llm: bool = False
    llm_model: str | None = None
    max_evidence_items: int = Field(default=50, ge=1)
    auto_approve_scope: bool = False
    languages: list[str] = Field(default_factory=list)
