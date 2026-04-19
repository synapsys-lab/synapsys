import numpy as np
import pytest

from synapsys.broker.topic import Topic
from synapsys.broker.broker import MessageBroker
from synapsys.broker.backends.base import BrokerBackend


class InMemoryBackend(BrokerBackend):
    """Simple in-memory backend for testing."""

    def __init__(self, topics: list[Topic]) -> None:
        self._store: dict[str, np.ndarray] = {
            t.name: np.zeros(t.shape) for t in topics
        }
        self._topic_map = {t.name: t for t in topics}

    def supports(self, topic: Topic) -> bool:
        return topic.name in self._topic_map

    def write(self, topic: Topic, data: np.ndarray) -> None:
        self._store[topic.name] = data.copy()

    def read(self, topic: Topic) -> np.ndarray:
        return self._store[topic.name].copy()

    def close(self) -> None:
        pass


@pytest.fixture
def topic_y():
    return Topic("plant/y", shape=(1,))


@pytest.fixture
def topic_u():
    return Topic("plant/u", shape=(1,))


@pytest.fixture
def broker(topic_y, topic_u):
    b = MessageBroker()
    b.declare_topic(topic_y)
    b.declare_topic(topic_u)
    backend = InMemoryBackend([topic_y, topic_u])
    b.add_backend(backend)
    return b


class TestMessageBroker:
    def test_publish_and_read_roundtrip(self, broker):
        broker.publish("plant/y", np.array([7.5]))
        result = broker.read("plant/y")
        np.testing.assert_allclose(result, [7.5])

    def test_read_before_publish_returns_zeros(self, broker):
        result = broker.read("plant/u")
        np.testing.assert_allclose(result, [0.0])

    def test_publish_validates_shape(self, broker):
        with pytest.raises(ValueError):
            broker.publish("plant/y", np.array([1.0, 2.0]))

    def test_read_undeclared_topic_raises(self, broker):
        with pytest.raises(KeyError):
            broker.read("nonexistent/topic")

    def test_publish_undeclared_topic_raises(self, broker):
        with pytest.raises(KeyError):
            broker.publish("nonexistent/topic", np.array([1.0]))

    def test_no_backend_for_topic_raises(self):
        b = MessageBroker()
        topic = Topic("orphan", shape=(1,))
        b.declare_topic(topic)
        with pytest.raises(RuntimeError, match="No backend"):
            b.publish("orphan", np.array([1.0]))

    def test_subscribe_callback_called_on_publish(self, broker):
        received = []
        broker.subscribe("plant/y", lambda name, data: received.append(data.copy()))
        broker.publish("plant/y", np.array([3.0]))
        assert len(received) == 1
        np.testing.assert_allclose(received[0], [3.0])

    def test_multiple_subscribers_all_notified(self, broker):
        calls = []
        broker.subscribe("plant/y", lambda n, d: calls.append("cb1"))
        broker.subscribe("plant/y", lambda n, d: calls.append("cb2"))
        broker.publish("plant/y", np.array([1.0]))
        assert calls == ["cb1", "cb2"]

    def test_unsubscribe_stops_notifications(self, broker):
        calls = []

        def cb(name, data):
            calls.append(data.copy())

        broker.subscribe("plant/y", cb)
        broker.publish("plant/y", np.array([1.0]))
        broker.unsubscribe("plant/y", cb)
        broker.publish("plant/y", np.array([2.0]))
        assert len(calls) == 1

    def test_context_manager_closes_cleanly(self, topic_y):
        b = MessageBroker()
        b.declare_topic(topic_y)
        backend = InMemoryBackend([topic_y])
        b.add_backend(backend)
        with b:
            b.publish("plant/y", np.array([1.0]))

    def test_read_wait_unblocks_when_publish_arrives(self, broker):
        import threading

        def publish_later():
            import time
            time.sleep(0.05)
            broker.publish("plant/y", np.array([42.0]))

        t = threading.Thread(target=publish_later)
        t.start()
        result = broker.read_wait("plant/y", timeout=1.0)
        t.join()
        np.testing.assert_allclose(result, [42.0])

    def test_read_wait_returns_cached_on_timeout(self, broker):
        broker.publish("plant/y", np.array([5.0]))
        result = broker.read_wait("plant/y", timeout=0.01)
        np.testing.assert_allclose(result, [5.0])
