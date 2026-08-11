"""Call graph — invocation relationships for reachability and workflow analysis."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CallEdge(BaseModel):
    caller_id: str
    callee_id: str
    call_site: str | None = None


class CallGraph(BaseModel):
    """Directed call graph over function/method entities."""

    edges: list[CallEdge] = Field(default_factory=list)

    def callers(self, function_id: str) -> list[str]:
        return [e.caller_id for e in self.edges if e.callee_id == function_id]

    def callees(self, function_id: str) -> list[str]:
        return [e.callee_id for e in self.edges if e.caller_id == function_id]

    def can_reach(self, source_id: str, target_id: str) -> bool:
        if source_id == target_id:
            return True
        seen: set[str] = set()
        stack = [source_id]
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            for callee in self.callees(node):
                if callee == target_id:
                    return True
                stack.append(callee)
        return False
