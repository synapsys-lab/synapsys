"""Synapsys utilities — matrix helpers and state-space builders."""

from .builders import StateEquations
from .matrices import col, mat, row

__all__ = [
    "mat",
    "col",
    "row",
    "StateEquations",
]
