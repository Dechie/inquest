"""Hybrid LLM/deterministic scope resolution."""

from codeanalyzer.scope.api import ScopeAPI, ScopeProposal
from codeanalyzer.scope.resolver import DeterministicScopeResolver, ScopeResolutionPipeline

__all__ = [
    "DeterministicScopeResolver",
    "ScopeAPI",
    "ScopeProposal",
    "ScopeResolutionPipeline",
]
