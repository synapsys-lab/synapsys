import time

import numpy as np
import pytest

from synapsys.agents import ControllerAgent, PlantAgent, SyncEngine, SyncMode
from synapsys.api.matlab_compat import c2d, ss
from synapsys.transport import SharedMemoryTransport

BUS = "synapsys_test_agents"
CHANNELS = {"y": 1, "u": 1}


@pytest.fixture()
def discrete_plant():
    plant_c = ss([[-1.0]], [[1.0]], [[1.0]], [[0.0]])
    return c2d(plant_c, dt=0.01)


class TestPlantAgent:
    def test_requires_discrete_plant(self):
        plant_c = ss([[-1.0]], [[1.0]], [[1.0]], [[0.0]])
        # Need a valid transport just to instantiate; discard it after
        with SharedMemoryTransport(BUS, CHANNELS, create=True) as t:
            sync = SyncEngine(SyncMode.WALL_CLOCK, dt=0.01)
            with pytest.raises(ValueError, match="discrete"):
                PlantAgent("plant", plant_c, t, sync)

    def test_plant_and_controller_converge(self, discrete_plant):
        """
        Plant and controller each hold their own transport handle to the same
        shared-memory bus.  This mirrors the real multi-process setup.
        """
        setpoint = 5.0

        # Owner allocates the block; keeps it alive for the whole test.
        owner = SharedMemoryTransport(BUS, CHANNELS, create=True)
        owner.write("u", np.array([0.0]))
        owner.write("y", np.array([0.0]))

        # Each agent gets its own client view (as they would in separate processes).
        t_plant = SharedMemoryTransport(BUS, CHANNELS, create=False)
        t_ctrl  = SharedMemoryTransport(BUS, CHANNELS, create=False)

        sync_p = SyncEngine(SyncMode.WALL_CLOCK, dt=0.01)
        sync_c = SyncEngine(SyncMode.WALL_CLOCK, dt=0.01)

        plant = PlantAgent("plant", discrete_plant, t_plant, sync_p)

        def law(y: np.ndarray) -> np.ndarray:
            return np.array([3.0 * (setpoint - y[0])])

        ctrl = ControllerAgent("ctrl", law, t_ctrl, sync_c)

        plant.start(blocking=False)
        ctrl.start(blocking=False)

        time.sleep(0.5)

        plant.stop()
        ctrl.stop()

        y_final = owner.read("y")[0]

        t_plant.close()
        t_ctrl.close()
        owner.close()

        # With Kp=3 and G(s)=1/(s+1) → closed-loop DC gain = 3/4 = 0.75
        # steady-state y = 0.75 * setpoint = 3.75
        assert y_final == pytest.approx(3.75, abs=0.5)
