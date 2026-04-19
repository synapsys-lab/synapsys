"""Quadcopter plant process — linearised 12-state MIMO via synapsys.

Discretises the hover model at 100 Hz and runs a PlantAgent on a
MessageBroker backed by shared memory.
Start this script FIRST, then run 06b_neural_lqr_3d.py.

Architecture
------------
  quad/state (12) ──► MessageBroker("quad") ──► controller
  controller       ──► MessageBroker("quad") ──► quad/u (4)

Usage
-----
  python 06a_quadcopter_plant.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from quadcopter_dynamics import U_MAX, U_MIN, build_matrices

from synapsys.agents import PlantAgent, SyncEngine, SyncMode
from synapsys.api import c2d, ss
from synapsys.broker import MessageBroker, SharedMemoryBackend, Topic

DT       = 0.01      # 100 Hz
BUS_NAME = "quad"
X0       = np.zeros(12)


def main() -> None:
    A, B, C, D = build_matrices()
    plant_c = ss(A, B, C, D)
    plant_d = c2d(plant_c, DT)

    print("Quadcopter linearised model")
    print(f"  States  : {plant_d.n_states}   (x,y,z,phi,theta,psi,xd,yd,zd,p,q,r)")
    print(f"  Inputs  : {plant_d.n_inputs}    (dF, tau_phi, tau_theta, tau_psi)")
    print(f"  Outputs : {plant_d.n_outputs}    (x, y, z, psi)")
    print(f"  dt      : {DT} s  (100 Hz)")

    # ── Broker + topics ───────────────────────────────────────────────────────
    topic_state = Topic("quad/state", shape=(plant_d.n_states,))
    topic_u     = Topic("quad/u",     shape=(plant_d.n_inputs,))

    broker = MessageBroker()
    broker.declare_topic(topic_state)
    broker.declare_topic(topic_u)
    broker.add_backend(
        SharedMemoryBackend(BUS_NAME, [topic_state, topic_u], create=True)
    )
    broker.publish("quad/state", X0.copy())
    broker.publish("quad/u",     np.zeros(plant_d.n_inputs))

    print(f"\nBroker bus '{BUS_NAME}' ready.")

    # Thin wrapper: clips control deviations before applying to linearised model
    _inner = plant_d

    class _ClippedPlant:
        n_states    = _inner.n_states
        n_inputs    = _inner.n_inputs
        n_outputs   = _inner.n_outputs
        is_discrete = _inner.is_discrete
        dt          = _inner.dt

        def evolve(self, x: np.ndarray, u: np.ndarray):
            return _inner.evolve(x, np.clip(u, U_MIN, U_MAX))

    sync  = SyncEngine(mode=SyncMode.WALL_CLOCK, dt=DT)
    agent = PlantAgent(
        "quad_plant", _ClippedPlant(), None, sync,  # type: ignore[arg-type]
        channel_y="quad/state", channel_u="quad/u",
        x0=X0.copy(), broker=broker,
    )
    agent.start(blocking=False)

    print("Plant running.  Waiting for controller…")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            time.sleep(1.0)
            state = broker.read("quad/state")
            print(
                f"  z={state[2]:+.3f} m  "
                f"phi={np.degrees(state[3]):+.1f}  "
                f"theta={np.degrees(state[4]):+.1f}  "
                f"psi={np.degrees(state[5]):+.1f}"
            )
    except KeyboardInterrupt:
        print("\nStopping plant.")
        agent.stop()
    finally:
        broker.close()


if __name__ == "__main__":
    main()
