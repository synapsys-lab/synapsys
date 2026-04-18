# Example 06 — Quadcopter MIMO Neural-LQR with PyVista 3D

Real-time simulation and animation of a quadcopter controlled by a
physics-informed Neural-LQR controller, built entirely with synapsys.

## What this example demonstrates

| Concept | Detail |
|---------|--------|
| **MIMO LTI modelling** | 12-state linearised hover model (x, y, z, φ, θ, ψ + velocities) |
| **MIMO LQR** | `synapsys.algorithms.lqr()` on a 12-state / 4-input plant |
| **Neural-LQR** | Residual MLP δu = −K·e + net(e), output layer zeroed → starts at LQR |
| **synapsys API** | `ss()`, `c2d()`, `StateSpace.evolve()`, `lqr()` |
| **PyVista 3D** | Real-time drone pose animation + trajectory trail at 50 Hz |
| **PyVista charts** | Position tracking, Euler angles, control inputs — all in one window |

## Plant model

```
State  x  = [x, y, z, φ, θ, ψ, ẋ, ẏ, ż, p, q, r]   (12 × 1)
Input  δu = [δF, τφ, τθ, τψ]                           (4 × 1)
Output y  = [x, y, z, ψ]                               (4 × 1)

Linearised at hover.  Valid for |φ|, |θ| ≤ 15°.
```

## Neural-LQR architecture

```
δu = −K·e  +  MLP(e)
     ^^^^^^     ^^^^^^
   LQR term   residual (12→64→32→4, init to zero)
```

At t=0 the residual is zero → network == optimal LQR.  
Hidden layers can be fine-tuned via RL/imitation learning without  
changing the synapsys API.

## Installation

```bash
pip install synapsys[viz]   # pyvista
pip install torch            # optional — for Neural-LQR
```

## Running

### Option A — standalone (recommended)

```bash
cd examples/advanced/06_quadcopter_mimo
python 06b_neural_lqr_3d.py
```

A 1500×860 PyVista window opens with:
- **Left pane**: 3-D drone animation with trajectory trail and figure-8 reference
- **Right pane**: position tracking · Euler angles · control inputs (live charts)

### Option B — two-process SIL

```bash
# Terminal 1
python 06a_quadcopter_plant.py

# Terminal 2 (while plant is running)
# (adapt 06b to read from SharedMemoryTransport instead of running its own sim)
```

## Reference trajectory

- **0 – 3 s** : takeoff to hover at z = 1.5 m
- **3 – 45 s** : lemniscate of Bernoulli (figure-8) at z = 1.5 m, A = 0.8 m, ω = 0.35 rad/s

## Window controls

| Action | Key / Mouse |
|--------|-------------|
| Rotate | Left-drag |
| Zoom | Scroll |
| Pan | Right-drag |
| Reset camera | `r` |
| Close | `q` or close button |
