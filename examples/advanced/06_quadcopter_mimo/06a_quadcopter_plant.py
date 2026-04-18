"""Quadcopter plant process — linearised 12-state MIMO via synapsys.

Discretises the hover model at 100 Hz and runs a PlantAgent on shared memory.
Start this script FIRST, then run 06b_neural_lqr_3d.py.

Architecture
------------
  state (12) ──► SharedMemoryTransport("quad") ──► controller
  controller ──► SharedMemoryTransport("quad") ──► δu (4)

Usage
-----
  python 06a_quadcopter_plant.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

# allow running from this directory
sys.path.insert(0, str(Path(__file__).parent))

from synapsys.agents import PlantAgent, SyncEngine, SyncMode
from synapsys.api import c2d, ss
from synapsys.transport import SharedMemoryTransport

from quadcopter_dynamics import F_HOVER, U_MAX, U_MIN, build_matrices

# ── Constants ─────────────────────────────────────────────────────────────────
DT          = 0.01      # 100 Hz
BUS_NAME    = "quad"
X0          = np.zeros(12)   # start on the ground, at rest


def main() -> None:
    A, B, C, D = build_matrices()
    plant_c = ss(A, B, C, D)
    plant_d = c2d(plant_c, DT)

    print("Quadcopter linearised model")
    print(f"  States  : {plant_d.n_states}   (x,y,z,φ,θ,ψ,ẋ,ẏ,ż,p,q,r)")
    print(f"  Inputs  : {plant_d.n_inputs}    (δF, τφ, τθ, τψ  — deviations from hover)")
    print(f"  Outputs : {plant_d.n_outputs}    (x, y, z, ψ)")
    print(f"  dt      : {DT} s  (100 Hz)")
    print(f"\nCreating shared-memory bus '{BUS_NAME}'…")

    # Expose full 12-state vector + 4 inputs on the bus
    channels = {"state": plant_d.n_states, "u": plant_d.n_inputs}

    with SharedMemoryTransport(BUS_NAME, channels, create=True) as bus:
        bus.write("state", X0.copy())
        bus.write("u",     np.zeros(plant_d.n_inputs))

        # Wrap the PlantAgent to clip control inputs and add hover equilibrium
        _inner = plant_d

        class _ClippedPlant:
            """Thin wrapper: clips δu, adds F_HOVER to thrust channel."""
            n_states  = _inner.n_states
            n_inputs  = _inner.n_inputs
            n_outputs = _inner.n_outputs
            is_discrete = _inner.is_discrete
            dt = _inner.dt

            def evolve(
                self, x: np.ndarray, u: np.ndarray
            ) -> tuple[np.ndarray, np.ndarray]:
                u_clipped = np.clip(u, U_MIN, U_MAX)
                return _inner.evolve(x, u_clipped)

        sync  = SyncEngine(mode=SyncMode.WALL_CLOCK, dt=DT)
        agent = PlantAgent(
            "quad_plant", _ClippedPlant(), bus, sync,  # type: ignore[arg-type]
            x0=X0.copy(),
        )
        agent.start(blocking=False)

        print("Plant running.  Waiting for controller…")
        print("Press Ctrl+C to stop.\n")

        try:
            while True:
                time.sleep(1.0)
                state = bus.read("state")
                print(
                    f"  z={state[2]:+.3f} m  "
                    f"φ={np.degrees(state[3]):+.1f}°  "
                    f"θ={np.degrees(state[4]):+.1f}°  "
                    f"ψ={np.degrees(state[5]):+.1f}°"
                )
        except KeyboardInterrupt:
            print("\nStopping plant.")
            agent.stop()


if __name__ == "__main__":
    main()
