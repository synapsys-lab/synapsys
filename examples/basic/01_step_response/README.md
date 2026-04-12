# 01 — Step Response of a Second-Order System

## Concept

A **transfer function** G(s) is a mathematical representation of a linear time-invariant (LTI) system in the Laplace domain. It relates the output Y(s) to the input U(s):

```
       Y(s)
G(s) = ----
       U(s)
```

For a **second-order underdamped system**, the standard form is:

```
           ωn²
G(s) = ─────────────────
        s² + 2ζωn·s + ωn²
```

Where:
- **ωn** (natural frequency) — controls how fast the system oscillates
- **ζ** (damping ratio) — controls how quickly oscillations decay
  - `ζ < 1` → underdamped (oscillates)
  - `ζ = 1` → critically damped (fastest non-oscillating response)
  - `ζ > 1` → overdamped (slow, no oscillation)

A **step response** is the output of the system when the input transitions from 0 to 1 instantaneously at t=0. It is the most common way to characterise a control system's dynamic behaviour.

Key metrics extracted from the step response:
| Metric | Description |
|---|---|
| Rise time | Time to go from 10% to 90% of the final value |
| Overshoot | Peak value above the setpoint (%) |
| Settling time | Time to stay within ±2% of the final value |
| Steady-state error | Difference between final output and setpoint |

---

## System in this example

```python
wn, zeta = 10.0, 0.5
G = tf([wn**2], [1, 2*zeta*wn, wn**2])
```

This creates:

```
          100
G(s) = ─────────────
        s² + 10s + 100
```

With `ζ = 0.5` the system is underdamped — it will overshoot and oscillate before settling.

---

## Code walkthrough

```python
from synapsys.api.matlab_compat import tf, step
```

`tf(num, den)` constructs a `TransferFunction` object from numerator and denominator coefficient lists (highest power first, MATLAB convention).

```python
G = tf([wn**2], [1, 2*zeta*wn, wn**2])
```

Builds G(s) = 100 / (s² + 10s + 100).

```python
print(G)
print(f"Poles   : {G.poles()}")
print(f"Stable  : {G.is_stable()}")
```

`G.poles()` returns the roots of the denominator — complex conjugate pair for underdamped systems. `is_stable()` checks that all poles have negative real parts (left half-plane).

```python
t, y = step(G)
```

`step()` computes the step response using `scipy.signal.step`. Returns time vector `t` and output `y`.

```python
plt.savefig("step_response.png", dpi=150)
```

Saves the plot as PNG for documentation or reports.

---

## How to run

```bash
uv run python examples/basic/01_step_response/step_response.py
```

Expected output: a plot window showing the step response with overshoot settling to `y=1`, and a saved `step_response.png`.
