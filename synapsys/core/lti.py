from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class LTIModel(ABC):
    """Abstract base for all Linear Time-Invariant system representations."""

    @property
    @abstractmethod
    def n_inputs(self) -> int: ...

    @property
    @abstractmethod
    def n_outputs(self) -> int: ...

    @property
    @abstractmethod
    def n_states(self) -> int: ...

    @abstractmethod
    def poles(self) -> np.ndarray: ...

    @abstractmethod
    def zeros(self) -> np.ndarray: ...

    @abstractmethod
    def is_stable(self) -> bool: ...

    @abstractmethod
    def to_state_space(self) -> "LTIModel": ...

    @abstractmethod
    def to_transfer_function(self) -> "LTIModel": ...

    @staticmethod
    def _as_2d(data: object, shape: tuple[int, int] | None = None) -> np.ndarray:
        """Silently promote scalars, lists, and 1-D arrays to 2-D float64."""
        arr = np.atleast_2d(np.asarray(data, dtype=np.float64))
        if shape is not None and arr.shape != shape:
            raise ValueError(f"Expected shape {shape}, got {arr.shape}")
        return arr

    @staticmethod
    def _as_1d(data: object) -> np.ndarray:
        """Silently flatten scalars, lists, and arrays to 1-D float64."""
        return np.atleast_1d(np.asarray(data, dtype=np.float64)).flatten()
