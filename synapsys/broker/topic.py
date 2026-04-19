from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass(frozen=True)
class Topic:
    """Named, typed channel descriptor used by MessageBroker."""

    name: str
    shape: tuple[int, ...]
    dtype: np.dtype = field(default_factory=lambda: np.dtype(np.float64))

    @property
    def size(self) -> int:
        result = 1
        for d in self.shape:
            result *= d
        return result

    def validate(self, data: np.ndarray) -> np.ndarray:
        arr = np.asarray(data, dtype=self.dtype).reshape(self.shape)
        return np.ascontiguousarray(arr)


class TopicRegistry:
    def __init__(self) -> None:
        self._topics: dict[str, Topic] = {}

    def register(self, topic: Topic) -> None:
        if topic.name in self._topics:
            existing = self._topics[topic.name]
            if existing != topic:
                raise ValueError(
                    f"Topic '{topic.name}' already registered with different schema "
                    f"(existing shape={existing.shape}, new shape={topic.shape})"
                )
            return
        self._topics[topic.name] = topic

    def get(self, name: str) -> Topic:
        try:
            return self._topics[name]
        except KeyError:
            raise KeyError(f"Topic '{name}' not registered. Call broker.declare_topic() first.")

    @property
    def all(self) -> dict[str, Topic]:
        return dict(self._topics)
