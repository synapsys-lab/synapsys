from __future__ import annotations

import numpy as np
import zmq

from .base import TransportStrategy


class ZMQTransport(TransportStrategy):
    """
    Asynchronous network transport using ZeroMQ PUB/SUB.

    The publisher binds to an address; subscribers connect to it.
    Data is broadcast: all subscribers receive every message.

    Use this when plant and controller run on different machines, or
    when you want multiple observers listening to the same channel.
    """

    def __init__(self, address: str, mode: str = "pub"):
        """
        Args:
            address: ZMQ endpoint, e.g. ``"tcp://localhost:5555"``
            mode: ``"pub"`` to publish, ``"sub"`` to subscribe
        """
        self._ctx = zmq.Context.instance()
        if mode == "pub":
            self._socket = self._ctx.socket(zmq.PUB)
            self._socket.bind(address)
        elif mode == "sub":
            self._socket = self._ctx.socket(zmq.SUB)
            self._socket.connect(address)
            self._socket.setsockopt_string(zmq.SUBSCRIBE, "")
        else:
            raise ValueError(f"mode must be 'pub' or 'sub', got '{mode}'")
        self._mode = mode

    def write(self, channel: str, data: np.ndarray) -> None:
        arr = np.asarray(data, dtype=np.float64)
        self._socket.send_multipart([channel.encode(), arr.tobytes()])

    def read(self, channel: str) -> np.ndarray:
        _, raw = self._socket.recv_multipart()
        return np.array(np.frombuffer(raw, dtype=np.float64))

    def close(self) -> None:
        self._socket.close()


class ZMQReqRepTransport(TransportStrategy):
    """
    Synchronous network transport using ZeroMQ REQ/REP.

    The server blocks until a request arrives; the client blocks until
    the reply comes back.  This enforces lock-step synchronisation over
    the network.
    """

    def __init__(self, address: str, mode: str = "server"):
        self._ctx = zmq.Context.instance()
        if mode == "server":
            self._socket = self._ctx.socket(zmq.REP)
            self._socket.bind(address)
        elif mode == "client":
            self._socket = self._ctx.socket(zmq.REQ)
            self._socket.connect(address)
        else:
            raise ValueError(f"mode must be 'server' or 'client', got '{mode}'")
        self._mode = mode

    def write(self, channel: str, data: np.ndarray) -> None:
        arr = np.asarray(data, dtype=np.float64)
        self._socket.send_multipart([channel.encode(), arr.tobytes()])

    def read(self, channel: str) -> np.ndarray:
        _, raw = self._socket.recv_multipart()
        return np.array(np.frombuffer(raw, dtype=np.float64))

    def close(self) -> None:
        self._socket.close()
