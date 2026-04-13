"""Plant process — 2-DOF mass-spring-damper.

Topology
--------
  [k]         [k]
──/\/\/──[m1]──/\/\/──[m2]──→ F(t)
  [c]                  [c]

State:  x = [x1, x2, v1, v2]  (positions + velocities of m1, m2)
Input:  F  (force on m2 via the coupling spring)
Output: full state vector written to the shared-memory bus every 10 ms.

Run FIRST, then start 02b_sil_ai_controller.py in a second terminal.
"""
import time

import numpy as np

from synapsys.agents import PlantAgent, SyncEngine, SyncMode
from synapsys.api import c2d, ss
from synapsys.transport import SharedMemoryTransport
from synapsys.utils import StateEquations

# ── System parameters ─────────────────────────────────────────────────────────
M, C_DAMP, K_SPR = 1.0, 0.1, 2.0      # mass (kg), damping (N·s/m), stiffness (N/m)
DT = 0.01                               # sample period — 100 Hz

# ── 2-DOF model via named equations ──────────────────────────────────────────
eqs = (
    StateEquations(states=["x1", "x2", "v1", "v2"], inputs=["F"])
    .eq("x1", v1=1)
    .eq("x2", v2=1)
    .eq("v1", x1=-2*K_SPR/M, x2=K_SPR/M,  v1=-C_DAMP/M)
    .eq("v2", x1=K_SPR/M,  x2=-2*K_SPR/M, v2=-C_DAMP/M, F=K_SPR/M)
)

# Full-state output: y = [x1, x2, v1, v2]
plant_c = ss(eqs.A, eqs.B, np.eye(4), np.zeros((4, 1)))
plant_d = c2d(plant_c, dt=DT)

print("=" * 58)
print("  2-DOF Mass-Spring-Damper — SIL Plant")
print("=" * 58)
print(f"  m={M} kg   c={C_DAMP} N·s/m   k={K_SPR} N/m   Ts={DT*1000:.0f} ms")
print(f"  n_states={plant_d.n_states}  stable={plant_d.is_stable()}")
print("=" * 58)


def main() -> None:
    print("\nAllocating shared-memory bus 'sil_2dof'…")
    bus = SharedMemoryTransport("sil_2dof", {"state": 4, "u": 1}, create=True)
    bus.write("state", np.zeros(4))
    bus.write("u", np.zeros(1))

    agent_bus = SharedMemoryTransport("sil_2dof", {"state": 4, "u": 1})
    sync = SyncEngine(mode=SyncMode.WALL_CLOCK, dt=DT)
    plant = PlantAgent("2dof_plant", plant_d, agent_bus, sync)

    print("Starting PlantAgent — waiting for AI controller…")
    print("Press Ctrl+C to stop.\n")
    try:
        plant.start(blocking=True)
    except KeyboardInterrupt:
        print("\nStopping plant.")
        plant.stop()
        bus.close()


if __name__ == "__main__":
    main()
