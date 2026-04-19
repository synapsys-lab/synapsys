from __future__ import annotations

import threading
from collections.abc import Sequence

import numpy as np
import zmq

from ..topic import Topic
from .base import BrokerBackend


class ZMQBrokerBackend(BrokerBackend):
    """
    Backend backed by ZMQ PUB/SUB.

    A background thread keeps a cache of the latest received value per
    topic so that read() is always non-blocking (ZOH semantics).

    Parameters
    ----------
    address          : ZMQ endpoint, e.g. "tcp://localhost:5555"
    publish_topics   : Topics this instance will write (PUB socket, binds)
    subscribe_topics : Topics this instance will read (SUB socket, connects)
    """

    def __init__(
        self,
        address: str,
        publish_topics: Sequence[Topic] = (),
        subscribe_topics: Sequence[Topic] = (),
    ) -> None:
        self._pub_topics = {t.name: t for t in publish_topics}
        self._sub_topics = {t.name: t for t in subscribe_topics}
        self._cache: dict[str, np.ndarray] = {
            t.name: np.zeros(t.shape, dtype=t.dtype) for t in subscribe_topics
        }
        self._cache_lock = threading.Lock()
        self._running = False

        ctx = zmq.Context.instance()
        self._pub_socket: zmq.Socket | None = None
        self._sub_socket: zmq.Socket | None = None
        self._recv_thread: threading.Thread | None = None

        if publish_topics:
            self._pub_socket = ctx.socket(zmq.PUB)
            self._pub_socket.bind(address)

        if subscribe_topics:
            self._sub_socket = ctx.socket(zmq.SUB)
            self._sub_socket.connect(address)
            self._sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")
            self._running = True
            self._recv_thread = threading.Thread(
                target=self._recv_loop, daemon=True, name="zmq-broker-recv"
            )
            self._recv_thread.start()

    def _recv_loop(self) -> None:
        assert self._sub_socket is not None
        while self._running:
            try:
                parts = self._sub_socket.recv_multipart(flags=zmq.NOBLOCK)
                if len(parts) == 2:
                    name = parts[0].decode()
                    if name in self._sub_topics:
                        t = self._sub_topics[name]
                        arr = np.frombuffer(parts[1], dtype=t.dtype).reshape(t.shape).copy()
                        with self._cache_lock:
                            self._cache[name] = arr
            except zmq.Again:
                pass

    def supports(self, topic: Topic) -> bool:
        return topic.name in self._pub_topics or topic.name in self._sub_topics

    def write(self, topic: Topic, data: np.ndarray) -> None:
        if self._pub_socket is None:
            raise RuntimeError(f"No PUB socket configured for topic '{topic.name}'")
        self._pub_socket.send_multipart([
            topic.name.encode(),
            np.asarray(data, dtype=topic.dtype).tobytes(),
        ])

    def read(self, topic: Topic) -> np.ndarray:
        with self._cache_lock:
            return self._cache[topic.name].copy()

    def close(self) -> None:
        self._running = False
        if self._pub_socket:
            self._pub_socket.close(linger=0)
        if self._sub_socket:
            self._sub_socket.close(linger=0)
