from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class TransportStrategy(ABC):
    """Abstract interface for all inter-process communication transports."""

    @abstractmethod
    def write(self, channel: str, data: np.ndarray) -> None:
        """Write a numpy array to a named channel."""

    @abstractmethod
    def read(self, channel: str) -> np.ndarray:
        """Read a numpy array from a named channel."""

    @abstractmethod
    def close(self) -> None:
        """Release all resources held by this transport."""

    def __enter__(self) -> TransportStrategy:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
