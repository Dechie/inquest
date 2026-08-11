"""Internal program representation substrate.

AST / IR / Symbol Table / Call Graph / CFG / Data-Flow / Dominance.
Language-specific frontends produce language-specific representations;
the detector/evidence layer consumes normalized semantic abstractions.
"""

from codeanalyzer.program.model import ProgramModel

__all__ = ["ProgramModel"]
