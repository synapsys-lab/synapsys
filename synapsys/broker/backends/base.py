from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from ..topic import Topic


class BrokerBackend(ABC):
    """Pluggable transport adapter for MessageBroker."""

    @abstractmethod
    def supports(self, topic: Topic) -> bool:
        """Return True if this backend handles the given topic."""

    @abstractmethod
    def write(self, topic: Topic, data: np.ndarray) -> None:
        """Write validated data to the underlying transport."""

    @abstractmethod
    def read(self, topic: Topic) -> np.ndarray:
        """Read latest data from the underlying transport (non-blocking, ZOH)."""

    @abstractmethod
    def close(self) -> None:
        """Release all resources."""

    def __enter__(self) -> BrokerBackend:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
