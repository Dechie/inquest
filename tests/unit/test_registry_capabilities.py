"""Unit tests for registry capability-based selection."""

from __future__ import annotations

from pathlib import Path

import pytest

from codeanalyzer.analyzers.adapters import MypyAdapter, FlutterAnalyzeAdapter
from codeanalyzer.analyzers.registry import AnalyzerRegistry
from codeanalyzer.domain.tooling import CapabilityKind


def test_registry_by_capability_basic():
    """Test basic capability-based selection."""
    registry = AnalyzerRegistry()
    registry.register(MypyAdapter())
    registry.register(FlutterAnalyzeAdapter())
    
    # Both adapters should have DIAGNOSTICS capability
    diagnostic_adapters = registry.by_capability(CapabilityKind.DIAGNOSTICS)
    assert len(diagnostic_adapters) == 2
    
    # Check analyzer IDs
    analyzer_ids = {a.capabilities().analyzer_id for a in diagnostic_adapters}
    assert "mypy" in analyzer_ids
    assert "flutter_analyze" in analyzer_ids


def test_registry_by_capability_project_filter(tmp_path: Path):
    """Test capability selection with project filtering."""
    registry = AnalyzerRegistry()
    registry.register(MypyAdapter())
    registry.register(FlutterAnalyzeAdapter())
    
    # Create a Python project
    (tmp_path / "app.py").write_text("x = 1\n")
    
    # Only mypy should match for Python project
    python_adapters = registry.by_capability(
        CapabilityKind.DIAGNOSTICS,
        project_path=str(tmp_path)
    )
    assert len(python_adapters) == 1
    assert python_adapters[0].capabilities().analyzer_id == "mypy"


def test_registry_by_capabilities_any():
    """Test capability selection with ANY matching."""
    registry = AnalyzerRegistry()
    registry.register(MypyAdapter())
    registry.register(FlutterAnalyzeAdapter())
    
    # Find adapters with EITHER DIAGNOSTICS OR AST
    adapters = registry.by_capabilities(
        {CapabilityKind.DIAGNOSTICS, CapabilityKind.AST},
        require_all=False
    )
    # Both have DIAGNOSTICS, so both should match
    assert len(adapters) == 2


def test_registry_by_capabilities_all():
    """Test capability selection with ALL matching."""
    registry = AnalyzerRegistry()
    registry.register(MypyAdapter())
    
    # mypy has both DIAGNOSTICS and TYPES
    adapters = registry.by_capabilities(
        {CapabilityKind.DIAGNOSTICS, CapabilityKind.TYPES},
        require_all=True
    )
    assert len(adapters) == 1
    assert adapters[0].capabilities().analyzer_id == "mypy"


def test_registry_by_capabilities_all_no_match():
    """Test capability selection when no adapter has all required capabilities."""
    registry = AnalyzerRegistry()
    registry.register(MypyAdapter())
    
    # No adapter has both DIAGNOSTICS and CALL_GRAPH
    adapters = registry.by_capabilities(
        {CapabilityKind.DIAGNOSTICS, CapabilityKind.CALL_GRAPH},
        require_all=True
    )
    assert len(adapters) == 0


def test_registry_by_capabilities_empty_set():
    """Test capability selection with empty capability set."""
    registry = AnalyzerRegistry()
    registry.register(MypyAdapter())
    
    # Empty set should return no adapters
    adapters = registry.by_capabilities(set(), require_all=False)
    assert len(adapters) == 0


def test_registry_capability_selection_vs_project_selection(tmp_path: Path):
    """Test that capability selection can be combined with project selection."""
    registry = AnalyzerRegistry()
    registry.register(MypyAdapter())
    registry.register(FlutterAnalyzeAdapter())
    
    # Create a Flutter project
    (tmp_path / "pubspec.yaml").write_text("name: test\n")
    
    # Only flutter should match for Flutter project with DIAGNOSTICS
    flutter_adapters = registry.by_capability(
        CapabilityKind.DIAGNOSTICS,
        project_path=str(tmp_path)
    )
    assert len(flutter_adapters) == 1
    assert flutter_adapters[0].capabilities().analyzer_id == "flutter_analyze"
