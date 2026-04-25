from __future__ import annotations

from typing import TYPE_CHECKING, Union

import numpy as np

from ..core.state_space import StateSpace
from ..simulators.base import SimulatorBase
from ..transport.base import TransportStrategy
from .lifecycle import BaseAgent
from .sync_engine import SyncEngine

if TYPE_CHECKING:
    from ..broker.broker import MessageBroker

_Plant = Union[StateSpace, SimulatorBase]


class PlantAgent(BaseAgent):
    """Agent that simulates a plant in real-time.

    Accepts either:

    * A **discrete** ``StateSpace`` (legacy path) — use ``c2d()`` to discretise first.
    * A ``SimulatorBase`` (nonlinear continuous simulator) — pass ``dt`` so the agent
      knows the integration step to use on each tick.

    Each tick:
        1. Read ``u`` from transport.
        2. Advance the plant by one step.
        3. Write ``y`` to transport.

    Example (StateSpace)::

        plant_d = c2d(ss([[-1]], [[1]], [[1]], [[0]]), dt=0.05)
        agent = PlantAgent("plant", plant_d, transport, sync)

    Example (SimulatorBase)::

        sim = MassSpringDamperSim(m=1.0, c=0.5, k=2.0)
        agent = PlantAgent("plant", sim, transport, sync, dt=0.01)
    """

    def __init__(
        self,
        name: str,
        plant: _Plant,
        transport: TransportStrategy | None,
        sync: SyncEngine,
        channel_y: str = "y",
        channel_u: str = "u",
        x0: np.ndarray | None = None,
        dt: float | None = None,
        *,
        broker: "MessageBroker | None" = None,
    ):
        super().__init__(name, transport, sync, broker=broker)
        self._ch_y = channel_y
        self._ch_u = channel_u

        if isinstance(plant, SimulatorBase):
            self._sim: SimulatorBase | None = plant
            self._plant: StateSpace | None = None
            if dt is None:
                raise ValueError("dt is required when plant is a SimulatorBase.")
            self._dt = float(dt)
            self._sim.reset(**({"x0": x0} if x0 is not None else {}))
        else:
            self._sim = None
            self._plant = plant
            self._dt = plant.dt
            if not plant.is_discrete:
                raise ValueError(
                    "PlantAgent requires a discrete plant (dt > 0). "
                    "Discretise it with c2d() first."
                )
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
        if self._sim is not None:
            u0 = np.zeros(self._sim.input_dim)
            y0, _ = self._sim.step(u0, self._dt)
            self._sim.reset()
        else:
            assert self._plant is not None
            u0 = np.zeros(self._plant.n_inputs)
            _, y0 = self._plant.evolve(self._x, u0)
        self._write(self._ch_y, y0)

    def step(self) -> None:
        u = self._read(self._ch_u)
        if self._sim is not None:
            y, _ = self._sim.step(u, self._dt)
        else:
            assert self._plant is not None
            self._x, y = self._plant.evolve(self._x, u)
        self._write(self._ch_y, y)

    def teardown(self) -> None:
        pass
