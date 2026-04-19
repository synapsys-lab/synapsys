from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from ...transport.shared_memory import SharedMemoryTransport
from ..topic import Topic
from .base import BrokerBackend


class SharedMemoryBackend(BrokerBackend):
    """Backend backed by a SharedMemoryTransport (same host, zero-copy)."""

    def __init__(
        self,
        bus_name: str,
        topics: Sequence[Topic],
        create: bool = False,
    ) -> None:
        self._topic_map = {t.name: t for t in topics}
        channels = {t.name: t.size for t in topics}
        self._transport = SharedMemoryTransport(bus_name, channels, create=create)

    def supports(self, topic: Topic) -> bool:
        return topic.name in self._topic_map

    def write(self, topic: Topic, data: np.ndarray) -> None:
        self._transport.write(topic.name, data.flatten())

    def read(self, topic: Topic) -> np.ndarray:
        flat = self._transport.read(topic.name)
        return flat.reshape(topic.shape)

    def close(self) -> None:
        self._transport.close()
