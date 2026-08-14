"""JSON / datetime helpers for SQLite TEXT columns."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, TypeVar, cast

from codeanalyzer.domain.entities import Location

T = TypeVar("T")


def dumps(value: object) -> str:
    return json.dumps(value, default=_json_default)


def loads(text: str | None, default: T) -> T:
    if text is None or text == "":
        return default
    return cast(T, json.loads(text))


def dt_to_iso(value: datetime) -> str:
    return value.isoformat()


def dt_from_iso(value: str) -> datetime:
    return datetime.fromisoformat(value)


def location_to_text(location: Location | None) -> str | None:
    if location is None:
        return None
    return location.model_dump_json()


def location_from_text(text: str | None) -> Location | None:
    if not text:
        return None
    return Location.model_validate_json(text)


def _json_default(value: object) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")
