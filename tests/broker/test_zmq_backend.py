import time

import numpy as np
import pytest

from synapsys.broker.topic import Topic
from synapsys.broker.backends.zmq import ZMQBrokerBackend

ADDR = "tcp://127.0.0.1:15779"


@pytest.fixture
def topics():
    return [Topic("sensor/x", shape=(2,))]


class TestZMQBrokerBackend:
    def test_read_before_publish_returns_zeros(self, topics):
        sub = ZMQBrokerBackend(ADDR, subscribe_topics=topics)
        try:
            result = sub.read(topics[0])
            np.testing.assert_allclose(result, np.zeros((2,)))
        finally:
            sub.close()

    def test_publish_subscribe_cache_update(self, topics):
        pub = ZMQBrokerBackend(ADDR, publish_topics=topics)
        sub = ZMQBrokerBackend(ADDR, subscribe_topics=topics)
        try:
            time.sleep(0.05)  # allow ZMQ slow-joiner to settle
            pub.write(topics[0], np.array([1.5, 2.5]))
            time.sleep(0.05)  # allow recv thread to pick up message
            result = sub.read(topics[0])
            np.testing.assert_allclose(result, [1.5, 2.5])
        finally:
            pub.close()
            sub.close()

    def test_supports_registered_topic(self, topics):
        b = ZMQBrokerBackend(ADDR, publish_topics=topics)
        try:
            assert b.supports(topics[0]) is True
        finally:
            b.close()

    def test_does_not_support_unknown_topic(self, topics):
        b = ZMQBrokerBackend(ADDR, publish_topics=topics)
        try:
            assert b.supports(Topic("unknown", shape=(1,))) is False
        finally:
            b.close()

    def test_close_stops_recv_thread(self, topics):
        b = ZMQBrokerBackend(ADDR, subscribe_topics=topics)
        b.close()
        if b._recv_thread is not None:
            b._recv_thread.join(timeout=1.0)
            assert not b._recv_thread.is_alive()
