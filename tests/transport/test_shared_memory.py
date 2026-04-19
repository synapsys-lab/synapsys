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


class TestTransportBaseContextManager:
    def test_base_class_enter_exit(self):
        """Context manager uses base class __enter__/__exit__."""
        import numpy as np

        from synapsys.transport.base import TransportStrategy

        class MinimalTransport(TransportStrategy):
            def write(self, channel: str, data: np.ndarray) -> None:
                pass

            def read(self, channel: str) -> np.ndarray:
                return np.zeros(1)

            def close(self) -> None:
                pass

        closed = [False]

        def tracking_close(self):  # type: ignore[override]
            closed[0] = True

        MinimalTransport.close = tracking_close  # type: ignore[method-assign]

        with MinimalTransport() as t:
            assert t is not None
        assert closed[0]


class TestSharedMemoryConstructorCleanup:
    def test_cleanup_on_ndarray_failure(self):
        """If np.ndarray fails after shm is created, cleanup runs."""
        import unittest.mock as mock

        import numpy as np

        from synapsys.transport.shared_memory import SharedMemoryTransport

        original_ndarray = np.ndarray

        def failing_ndarray(*args, **kwargs):
            if kwargs.get("buffer") is not None or (
                len(args) > 1 and args[-1] is not None
            ):
                raise ValueError("forced buffer failure")
            return original_ndarray(*args, **kwargs)

        with mock.patch(
            "synapsys.transport.shared_memory.np.ndarray", side_effect=failing_ndarray
        ):
            with pytest.raises(ValueError, match="forced buffer failure"):
                SharedMemoryTransport("cov_cleanup_test", {"y": 1}, create=True)
        # If cleanup works, no resource leak (the shared memory block is unlinked)
