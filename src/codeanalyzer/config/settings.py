"""Application settings.

Python is the first language frontend (Phase A). External analyzer adapters
remain language-specific and independent of this default.
"""

from __future__ import annotations

import os
from collections.abc import Mapping

from pydantic import BaseModel, Field

_TRUE = {"1", "true", "yes", "on"}


def _env_bool(value: str) -> bool:
    return value.strip().lower() in _TRUE


def _default_languages() -> list[str]:
    return ["python"]


class Settings(BaseModel):
    """Runtime configuration for analysis runs."""

    project_path: str | None = None
    analysis_dir_name: str = ".codeanalyzer"
    enable_llm: bool = False
    llm_model: str | None = None
    max_evidence_items: int = Field(default=50, ge=1)
    auto_approve_scope: bool = False
    languages: list[str] = Field(default_factory=_default_languages)
    discover_timeout_seconds: int = Field(default=30, ge=1)
    analyze_timeout_seconds: int = Field(default=120, ge=1)

    @classmethod
    def from_environ(cls, environ: Mapping[str, str] | None = None) -> Settings:
        """Load settings from process environment (``CODEANALYZER_*``)."""
        env = os.environ if environ is None else environ
        kwargs: dict[str, object] = {}
        if value := env.get("CODEANALYZER_PROJECT_PATH"):
            kwargs["project_path"] = value
        if value := env.get("CODEANALYZER_ANALYSIS_DIR"):
            kwargs["analysis_dir_name"] = value
        if value := env.get("CODEANALYZER_ENABLE_LLM"):
            kwargs["enable_llm"] = _env_bool(value)
        if value := env.get("CODEANALYZER_LLM_MODEL"):
            kwargs["llm_model"] = value
        if value := env.get("CODEANALYZER_MAX_EVIDENCE_ITEMS"):
            kwargs["max_evidence_items"] = int(value)
        if value := env.get("CODEANALYZER_AUTO_APPROVE_SCOPE"):
            kwargs["auto_approve_scope"] = _env_bool(value)
        if value := env.get("CODEANALYZER_LANGUAGES"):
            kwargs["languages"] = [part.strip() for part in value.split(",") if part.strip()]
        if value := env.get("CODEANALYZER_DISCOVER_TIMEOUT"):
            kwargs["discover_timeout_seconds"] = int(value)
        if value := env.get("CODEANALYZER_ANALYZE_TIMEOUT"):
            kwargs["analyze_timeout_seconds"] = int(value)
        return cls.model_validate(kwargs)

    def with_cli_overrides(
        self,
        *,
        project_path: str | None = None,
        auto_approve: bool = False,
        enable_llm: bool = False,
    ) -> Settings:
        """Return a copy with CLI flags applied (flags only turn features on)."""
        updates: dict[str, object] = {}
        if project_path is not None:
            updates["project_path"] = project_path
        if auto_approve:
            updates["auto_approve_scope"] = True
        if enable_llm:
            updates["enable_llm"] = True
        return self.model_copy(update=updates) if updates else self
