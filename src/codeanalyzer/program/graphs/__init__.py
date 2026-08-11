"""Internal graph structures."""

from codeanalyzer.program.graphs.call_graph import CallGraph
from codeanalyzer.program.graphs.cfg import ControlFlowGraph
from codeanalyzer.program.graphs.data_flow import DataFlowGraph

__all__ = ["CallGraph", "ControlFlowGraph", "DataFlowGraph"]
