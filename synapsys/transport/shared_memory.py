from __future__ import annotations

from multiprocessing import shared_memory

import numpy as np

from .base import TransportStrategy


class SharedMemoryTransport(TransportStrategy):
    """
    Ultra-low-latency transport backed by OS shared memory (zero-copy).

    The owner process (create=True) allocates the memory block and must
    call close() to release it.  Client processes (create=False) attach
    to an existing block by name.

    Memory layout: one flat float64 array.  Each channel maps to a
    contiguous slice defined at construction time via the `channels` dict.

    Example::

        # Owner (plant)
        transport = SharedMemoryTransport(
            "ctrl_bus", {"y": 2, "u": 1}, create=True
        )

        # Client (controller — separate process)
        transport = SharedMemoryTransport(
            "ctrl_bus", {"y": 2, "u": 1}, create=False
        )
    """

    def __init__(
        self,
        name: str,
        channels: dict[str, int],
        create: bool = False,
    ):
        self._channels = channels
        self._offsets: dict[str, int] = {}
        total = 0
        for ch, size in channels.items():
            self._offsets[ch] = total
            total += size

        byte_size = total * np.dtype(np.float64).itemsize

        if create:
            self._shm = shared_memory.SharedMemory(
                name=name, create=True, size=byte_size
            )
        else:
            self._shm = shared_memory.SharedMemory(name=name)

        self._buf = np.ndarray((total,), dtype=np.float64, buffer=self._shm.buf)
        self._create = create

    def write(self, channel: str, data: np.ndarray) -> None:
        offset = self._offsets[channel]
        size = self._channels[channel]
        self._buf[offset : offset + size] = (
            np.asarray(data, dtype=np.float64).flatten()[:size]
        )

    def read(self, channel: str) -> np.ndarray:
        offset = self._offsets[channel]
        size = self._channels[channel]
        return np.array(self._buf[offset : offset + size])

    def close(self) -> None:
        self._shm.close()
        if self._create:
            self._shm.unlink()
