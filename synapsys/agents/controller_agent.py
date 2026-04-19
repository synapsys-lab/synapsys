from __future__ import annotations

from typing import TYPE_CHECKING, Callable

import numpy as np

from ..transport.base import TransportStrategy
from .lifecycle import BaseAgent
from .sync_engine import SyncEngine

if TYPE_CHECKING:
    from ..broker.broker import MessageBroker


class ControllerAgent(BaseAgent):
    """
    Agent that applies a control law in real-time.

    Each tick:
        1. Read ``y`` from transport.
        2. Apply ``control_law(y)`` → ``u``.
        3. Write ``u`` to transport.

    The ``control_law`` is any callable that maps a 1-D numpy array
    (measurement) to a 1-D numpy array (control action).  This makes
    the agent compatible with PID, LQR, MPC, or any Python function.

    Example::

        from synapsys.algorithms import PID
        from synapsys.agents import ControllerAgent, SyncEngine, SyncMode
        from synapsys.transport import SharedMemoryTransport

        pid = PID(Kp=3.0, Ki=0.5, dt=0.025)
        law = lambda y: np.array([pid.compute(setpoint=5.0, measurement=y[0])])

        transport = SharedMemoryTransport("bus", {"y": 1, "u": 1}, create=False)
        sync = SyncEngine(SyncMode.WALL_CLOCK, dt=0.025)
        agent = ControllerAgent("controller", law, transport, sync)
        agent.start()
    """

    def __init__(
        self,
        name: str,
        control_law: Callable[[np.ndarray], np.ndarray],
        transport: TransportStrategy | None,
        sync: SyncEngine,
        channel_y: str = "y",
        channel_u: str = "u",
        *,
        broker: "MessageBroker | None" = None,
    ):
        super().__init__(name, transport, sync, broker=broker)
        self._law = control_law
        self._ch_y = channel_y
        self._ch_u = channel_u

    def setup(self) -> None:
        pass

    def step(self) -> None:
        y = self._read(self._ch_y)
        u = np.asarray(self._law(y), dtype=np.float64).flatten()
        self._write(self._ch_u, u)

    def teardown(self) -> None:
        pass
