import numpy as np
import pytest

from synapsys.transport.shared_memory import SharedMemoryTransport

BUS_NAME = "synapsys_test_bus"


class TestSharedMemoryTransport:
    def test_write_read_roundtrip(self):
        channels = {"y": 2, "u": 1}
        with SharedMemoryTransport(BUS_NAME, channels, create=True) as owner:
            owner.write("y", np.array([1.0, 2.0]))
            owner.write("u", np.array([3.0]))

            # Client attaches to the same block
            with SharedMemoryTransport(BUS_NAME, channels, create=False) as client:
                y = client.read("y")
                u = client.read("u")

        np.testing.assert_allclose(y, [1.0, 2.0])
        np.testing.assert_allclose(u, [3.0])

    def test_client_attaches_after_write(self):
        channels = {"signal": 3}
        with SharedMemoryTransport(BUS_NAME, channels, create=True) as owner:
            owner.write("signal", np.array([10.0, 20.0, 30.0]))
            with SharedMemoryTransport(BUS_NAME, channels, create=False) as client:
                result = client.read("signal")
        np.testing.assert_allclose(result, [10.0, 20.0, 30.0])

    def test_missing_bus_raises(self):
        channels = {"x": 1}
        with pytest.raises(FileNotFoundError):
            SharedMemoryTransport("nonexistent_bus_xyz", channels, create=False)
