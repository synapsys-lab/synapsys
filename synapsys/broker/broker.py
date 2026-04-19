from __future__ import annotations

import threading
from collections.abc import Callable

import numpy as np

from .backends.base import BrokerBackend
from .topic import Topic, TopicRegistry

SubscriberCallback = Callable[[str, np.ndarray], None]


class MessageBroker:
    """
    Central Mediator routing numpy arrays between agents via typed topics.

    Agents declare topics, publish data by name, and read the latest value
    (polling / ZOH). Push-model subscribers are notified synchronously inside
    publish() — callbacks must be fast to avoid stalling the publisher.

    Multiple BrokerBackend instances can coexist; the first backend that
    supports a topic handles it.
    """

    def __init__(self) -> None:
        self._registry = TopicRegistry()
        self._backends: list[BrokerBackend] = []
        self._subscriptions: dict[str, list[SubscriberCallback]] = {}
        self._lock = threading.Lock()

    # ── Configuration ─────────────────────────────────────────────────────────

    def declare_topic(self, topic: Topic) -> None:
        self._registry.register(topic)
        with self._lock:
            self._subscriptions.setdefault(topic.name, [])

    def add_backend(self, backend: BrokerBackend) -> None:
        with self._lock:
            self._backends.append(backend)

    # ── Pub/Sub API ───────────────────────────────────────────────────────────

    def publish(self, topic_name: str, data: np.ndarray) -> None:
        topic = self._registry.get(topic_name)
        validated = topic.validate(data)
        self._backend_for(topic).write(topic, validated)
        with self._lock:
            callbacks = list(self._subscriptions.get(topic_name, []))
        for cb in callbacks:
            cb(topic_name, validated.copy())

    def read(self, topic_name: str) -> np.ndarray:
        topic = self._registry.get(topic_name)
        return self._backend_for(topic).read(topic)

    def subscribe(self, topic_name: str, callback: SubscriberCallback) -> None:
        self._registry.get(topic_name)
        with self._lock:
            self._subscriptions[topic_name].append(callback)

    def unsubscribe(self, topic_name: str, callback: SubscriberCallback) -> None:
        with self._lock:
            self._subscriptions[topic_name].remove(callback)

    def read_wait(self, topic_name: str, timeout: float = 1.0) -> np.ndarray:
        """Block until a new publish() on topic_name or timeout, then return value."""
        event = threading.Event()
        result: list[np.ndarray] = []

        def _on_publish(name: str, data: np.ndarray) -> None:
            result.append(data)
            event.set()

        self.subscribe(topic_name, _on_publish)
        event.wait(timeout=timeout)
        self.unsubscribe(topic_name, _on_publish)
        return result[0] if result else self.read(topic_name)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def close(self) -> None:
        with self._lock:
            for backend in self._backends:
                backend.close()

    def __enter__(self) -> MessageBroker:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _backend_for(self, topic: Topic) -> BrokerBackend:
        with self._lock:
            for backend in self._backends:
                if backend.supports(topic):
                    return backend
        raise RuntimeError(
            f"No backend registered for topic '{topic.name}'. "
            "Call broker.add_backend() with a backend that supports this topic."
        )
