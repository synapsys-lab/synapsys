from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np

from ..hw.base import HardwareInterface
from ..transport.base import TransportStrategy
from .lifecycle import BaseAgent
from .sync_engine import SyncEngine

if TYPE_CHECKING:
    from ..broker.broker import MessageBroker

logger = logging.getLogger(__name__)


class HardwareAgent(BaseAgent):
    """
    Agent that bridges a physical hardware device into the Synapsys transport layer.

    Replaces ``PlantAgent`` in a HIL (Hardware-in-the-Loop) setup.  The plant
    simulation is removed; the real hardware becomes the "plant".

    Each tick:
        1. Read ``y`` (sensor measurements) from hardware via ``HardwareInterface``.
        2. Write ``y`` to transport so the controller can consume it.
        3. Read ``u`` (control command) from transport.
        4. Write ``u`` (actuator command) to hardware via ``HardwareInterface``.

    If hardware read/write times out (``TimeoutError``), the last known ``y``
    and ``u`` are held (Zero-Order Hold) and a warning is logged.

    Parameters
    ----------
    name : str
        Human-readable agent identifier.
    hardware : HardwareInterface
        Concrete hardware bridge (Serial, OPC-UA, mock, …).
    transport : TransportStrategy
        Bus shared with the controller agent.
    sync : SyncEngine
        Timing strategy for this agent's loop.
    channel_y : str
        Channel name for plant output (default ``"y"``).
    channel_u : str
        Channel name for control input (default ``"u"``).
    timeout_ms : float
        Per-call hardware I/O timeout in milliseconds (default 100 ms).

    Example — HIL with a mock device::

        from synapsys.hw import MockHardwareInterface
        from synapsys.agents import HardwareAgent, SyncEngine, SyncMode
        from synapsys.transport import SharedMemoryTransport

        hw    = MockHardwareInterface(n_inputs=1, n_outputs=1)
        bus   = SharedMemoryTransport("hil_bus", {"y": 1, "u": 1}, create=True)
        sync  = SyncEngine(SyncMode.WALL_CLOCK, dt=0.01)
        agent = HardwareAgent("hw_plant", hw, bus, sync)

        with hw:
            agent.start(blocking=False)
            # ... controller agent running on the same bus ...
            agent.stop()
    """

    def __init__(
        self,
        name: str,
        hardware: HardwareInterface,
        transport: TransportStrategy | None,
        sync: SyncEngine,
        channel_y: str = "y",
        channel_u: str = "u",
        timeout_ms: float = 100.0,
        *,
        broker: "MessageBroker | None" = None,
    ):
        super().__init__(name, transport, sync, broker=broker)
        self._hw = hardware
        self._ch_y = channel_y
        self._ch_u = channel_u
        self._timeout_ms = timeout_ms

        # ZOH state — held values on timeout
        self._last_y: np.ndarray = np.zeros(hardware.n_outputs)
        self._last_u: np.ndarray = np.zeros(hardware.n_inputs)

    def setup(self) -> None:
        self._write(self._ch_y, self._last_y.copy())

    def step(self) -> None:
        # ── Read sensors from hardware (ZOH on timeout) ────────────────────
        try:
            y = self._hw.read_outputs(timeout_ms=self._timeout_ms)
            self._last_y = np.asarray(y, dtype=np.float64).flatten()
        except TimeoutError:
            logger.warning(
                "Agent '%s': hardware read_outputs timed out — holding last y.",
                self.name,
            )

        self._write(self._ch_y, self._last_y)

        u = self._read(self._ch_u)
        self._last_u = np.asarray(u, dtype=np.float64).flatten()

        # ── Send actuator command to hardware (ZOH on timeout) ────────────
        try:
            self._hw.write_inputs(self._last_u, timeout_ms=self._timeout_ms)
        except TimeoutError:
            logger.warning(
                "Agent '%s': hardware write_inputs timed out — holding last u.",
                self.name,
            )

    def teardown(self) -> None:
        # Send zero command on shutdown to leave actuators in safe state
        try:
            self._hw.write_inputs(
                np.zeros(self._hw.n_inputs), timeout_ms=self._timeout_ms
            )
        except TimeoutError:
            logger.warning(
                "Agent '%s': hardware write_inputs timed out during teardown.",
                self.name,
            )
        except Exception:
            logger.exception(
                "Agent '%s': unexpected error during teardown.",
                self.name,
            )
