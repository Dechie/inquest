"""Program entities, locations, and relationships."""

from __future__ import annotations

from pydantic import BaseModel, Field

from codeanalyzer.domain.enums import EntityType, RelationshipType


class Location(BaseModel):
    """Source location within a repository snapshot."""

    file: str
    start_line: int | None = None
    end_line: int | None = None
    start_column: int | None = None
    end_column: int | None = None

    def __str__(self) -> str:
        if self.start_line is None:
            return self.file
        if self.end_line is None or self.end_line == self.start_line:
            return f"{self.file}:{self.start_line}"
        return f"{self.file}:{self.start_line}-{self.end_line}"


class Entity(BaseModel):
    """A named program entity within a snapshot."""

    id: str
    snapshot_id: str
    type: EntityType
    name: str
    qualified_name: str | None = None
    location: Location | None = None
    language: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class Relationship(BaseModel):
    """Directed relationship between two entities."""

    id: str
    snapshot_id: str
    source_id: str
    target_id: str
    type: RelationshipType
    location: Location | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
