"""Tests for ZMQ transport (PUB/SUB and REQ/REP)."""

from __future__ import annotations

import threading
import time

import numpy as np
import pytest

from synapsys.transport.network import ZMQReqRepTransport, ZMQTransport

# Use random high ports to avoid conflicts across parallel test runs
PUB_ADDR = "tcp://127.0.0.1:15555"
REQREP_ADDR = "tcp://127.0.0.1:15556"


class TestZMQTransport:
    """PUB/SUB — asynchronous broadcast."""

    def test_pubsub_roundtrip(self):
        """Publisher sends an array; subscriber receives it."""
        pub = ZMQTransport(PUB_ADDR, mode="pub")
        sub = ZMQTransport(PUB_ADDR, mode="sub")
        time.sleep(0.05)  # let ZMQ subscription propagate

        sent = np.array([1.0, 2.0, 3.0])
        result: list[np.ndarray] = []

        def recv():
            result.append(sub.read("y"))

        t = threading.Thread(target=recv, daemon=True)
        t.start()
        time.sleep(0.02)
        pub.write("y", sent)
        t.join(timeout=2.0)

        pub.close()
        sub.close()

        assert result, "subscriber did not receive a message"
        np.testing.assert_allclose(result[0], sent)

    def test_pubsub_invalid_mode_raises(self):
        with pytest.raises(ValueError, match="mode must be"):
            ZMQTransport(PUB_ADDR, mode="invalid")

    def test_pubsub_close_is_idempotent(self):
        """close() must not raise even if called twice."""
        pub = ZMQTransport(PUB_ADDR, mode="pub")
        pub.close()
        pub.close()


class TestZMQReqRepTransport:
    """REQ/REP — synchronous lock-step."""

    def test_reqrep_roundtrip(self):
        """Client sends a request; server echoes back the same data."""
        server = ZMQReqRepTransport(REQREP_ADDR, mode="server")
        client = ZMQReqRepTransport(REQREP_ADDR, mode="client")
        time.sleep(0.05)

        sent = np.array([7.0, 8.0])
        received_by_server: list[np.ndarray] = []

        def serve_one():
            data = server.read("u")
            received_by_server.append(data)
            server.write("u", data)  # echo

        t = threading.Thread(target=serve_one, daemon=True)
        t.start()
        time.sleep(0.02)

        client.write("u", sent)
        reply = client.read("u")

        t.join(timeout=2.0)
        server.close()
        client.close()

        np.testing.assert_allclose(reply, sent)
        np.testing.assert_allclose(received_by_server[0], sent)

    def test_reqrep_invalid_mode_raises(self):
        with pytest.raises(ValueError, match="mode must be"):
            ZMQReqRepTransport(REQREP_ADDR, mode="bogus")

    def test_reqrep_close_is_idempotent(self):
        srv = ZMQReqRepTransport(REQREP_ADDR, mode="server")
        srv.close()
        srv.close()
