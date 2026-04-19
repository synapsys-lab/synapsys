import numpy as np
import pytest

from synapsys.broker.topic import Topic
from synapsys.broker.backends.shared_memory import SharedMemoryBackend


@pytest.fixture
def topics():
    return [
        Topic("plant/y", shape=(1,)),
        Topic("plant/u", shape=(1,)),
    ]


@pytest.fixture
def backend(topics):
    b = SharedMemoryBackend("test_broker_shm", topics, create=True)
    yield b
    b.close()


class TestSharedMemoryBackend:
    def test_write_and_read_roundtrip(self, backend, topics):
        t = topics[0]
        backend.write(t, np.array([3.14]))
        result = backend.read(t)
        np.testing.assert_allclose(result, [3.14])

    def test_read_returns_correct_shape(self, backend, topics):
        t = topics[0]
        backend.write(t, np.array([1.0]))
        result = backend.read(t)
        assert result.shape == (1,)

    def test_multidimensional_topic_roundtrip(self):
        topic = Topic("matrix", shape=(2, 2))
        b = SharedMemoryBackend("test_broker_shm_2d", [topic], create=True)
        try:
            data = np.array([[1.0, 2.0], [3.0, 4.0]])
            b.write(topic, data)
            result = b.read(topic)
            assert result.shape == (2, 2)
            np.testing.assert_allclose(result, data)
        finally:
            b.close()

    def test_supports_registered_topic(self, backend, topics):
        assert backend.supports(topics[0]) is True

    def test_does_not_support_unknown_topic(self, backend):
        unknown = Topic("unknown/topic", shape=(5,))
        assert backend.supports(unknown) is False

    def test_write_multiple_channels_independently(self, backend, topics):
        t_y, t_u = topics[0], topics[1]
        backend.write(t_y, np.array([1.0]))
        backend.write(t_u, np.array([9.0]))
        np.testing.assert_allclose(backend.read(t_y), [1.0])
        np.testing.assert_allclose(backend.read(t_u), [9.0])
