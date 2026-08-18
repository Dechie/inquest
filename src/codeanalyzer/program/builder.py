"""ProgramModel builder protocol.

Provides an injection seam so the orchestrator can obtain a populated
InMemoryProgramModel without coupling to a specific language frontend.
The default implementation returns an empty model (scaffold behaviour).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from codeanalyzer.domain.slices import LogicalSlice
from codeanalyzer.domain.snapshots import Snapshot
from codeanalyzer.program.in_memory import InMemoryProgramModel


@runtime_checkable
class ProgramModelBuilder(Protocol):
    """Callable that constructs a program model for a snapshot + slice.

    Implementations are responsible for populating entities, relationships,
    and the call graph. The orchestrator calls this once per analysis run.
    """

    def __call__(
        self, snapshot: Snapshot, slice_: LogicalSlice
    ) -> InMemoryProgramModel: ...


def empty_program_model_builder(
    snapshot: Snapshot, slice_: LogicalSlice  # noqa: ARG001
) -> InMemoryProgramModel:
    """Default builder: returns an empty in-memory model.

    Used by the orchestrator when no real language frontend is available.
    Detectors receiving this model will produce UNKNOWN outcomes.
    """
    return InMemoryProgramModel(snapshot)



