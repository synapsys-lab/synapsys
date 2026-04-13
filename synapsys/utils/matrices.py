"""Concise numpy matrix constructors."""

from __future__ import annotations

from typing import Sequence

import numpy as np

__all__ = ["mat", "col", "row"]


def mat(rows: Sequence[Sequence[float]]) -> np.ndarray:
    """Build a 2-D float array from a nested list — no ``np.array`` boilerplate.

    Example
    -------
    >>> A = mat([
    ...     [0,  1],
    ...     [-2, -3],
    ... ])
    """
    return np.asarray(rows, dtype=float)


def col(*values: float) -> np.ndarray:
    """Build a column vector (shape ``(n, 1)``) from positional arguments.

    Example
    -------
    >>> B = col(0, 0, 1)   # shape (3, 1)
    """
    return np.asarray(values, dtype=float).reshape(-1, 1)


def row(*values: float) -> np.ndarray:
    """Build a row vector (shape ``(1, n)``) from positional arguments.

    Example
    -------
    >>> v = row(1, 0, 0, 0)   # shape (1, 4)
    """
    return np.asarray(values, dtype=float).reshape(1, -1)
