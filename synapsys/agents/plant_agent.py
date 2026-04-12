from __future__ import annotations

import numpy as np

from ..core.state_space import StateSpace
from ..transport.base import TransportStrategy
from .lifecycle import BaseAgent
from .sync_engine import SyncEngine


class PlantAgent(BaseAgent):
    """
    Agent that simulates a discrete-time StateSpace plant in real-time.

    Each tick:
        1. Read ``u`` from transport.
        2. Compute  x(k+1) = A·x(k) + B·u(k),  y(k) = C·x(k) + D·u(k)
        3. Write ``y`` to transport.

    The plant must be discrete (``plant.is_discrete == True``).
    Use ``c2d()`` to discretise a continuous model before passing it here.

    Example::

        from synapsys.api import ss, c2d
        from synapsys.agents import PlantAgent, SyncEngine, SyncMode
        from synapsys.transport import SharedMemoryTransport

        plant_c = ss([[-1]], [[1]], [[1]], [[0]])   # G(s) = 1/(s+1)
        plant_d = c2d(plant_c, dt=0.05)

        transport = SharedMemoryTransport("bus", {"y": 1, "u": 1}, create=True)
        sync = SyncEngine(SyncMode.WALL_CLOCK, dt=0.05)
        agent = PlantAgent("plant", plant_d, transport, sync)
        agent.start()
    """

    def __init__(
        self,
        name: str,
        plant: StateSpace,
        transport: TransportStrategy,
        sync: SyncEngine,
        channel_y: str = "y",
        channel_u: str = "u",
        x0: np.ndarray | None = None,
    ):
        if not plant.is_discrete:
            raise ValueError(
                "PlantAgent requires a discrete plant (dt > 0). "
                "Discretise it with c2d() first."
            )
        super().__init__(name, transport, sync)
        self._plant = plant
        self._ch_y = channel_y
        self._ch_u = channel_u
        n = plant.n_states
        if x0 is None:
            self._x: np.ndarray = np.zeros(n)
        else:
            x0_arr = np.asarray(x0, dtype=np.float64).flatten()
            if x0_arr.size != n:
                raise ValueError(
                    f"x0 must have {n} element(s) to match plant.n_states, "
                    f"got {x0_arr.size}"
                )
            self._x = x0_arr

    def setup(self) -> None:
        u0 = np.zeros(self._plant.n_inputs)
        _, y0 = self._plant.evolve(self._x, u0)
        self.transport.write(self._ch_y, y0)

    def step(self) -> None:
        u = self.transport.read(self._ch_u)
        self._x, y = self._plant.evolve(self._x, u)
        self.transport.write(self._ch_y, y)

    def teardown(self) -> None:
        pass
