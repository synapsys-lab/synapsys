# 01 — Custom Signal Injection (MIL / Batch Simulation)

## Concept

**MIL (Model-in-the-Loop)** is a simulation methodology where both the plant model and the controller logic run entirely in software, with no hardware involved and no real-time constraint. Time advances as fast as the computer can compute — ideal for batch testing, validation, and signal analysis.

This example demonstrates **arbitrary signal injection**: instead of a step, you feed any custom waveform into the LTI model and observe the output. This is useful for:

- Testing how a system responds to **mechanical vibrations** (sinusoids)
- Simulating **disturbance injection** (step at a specific time)
- Validating the **principle of superposition**: the response to a sum of inputs equals the sum of individual responses

### Principle of Superposition

For a linear system, if:
- `y₁(t)` is the response to `u₁(t)`
- `y₂(t)` is the response to `u₂(t)`

Then the response to `u₁(t) + u₂(t)` is exactly `y₁(t) + y₂(t)`.

This example exploits superposition by combining:
1. A **1.5 Hz sine wave** — simulating periodic mechanical vibration
2. A **step of amplitude 2 at t=5s** — simulating a sudden load change

---

## System in this example

```
        10
G(s) = ────────────
        s² + 5s + 10
```

Natural frequency ωn = √10 ≈ 3.16 rad/s, damping ratio ζ ≈ 0.79 (underdamped but well-damped).

---

## Code walkthrough

```python
t = np.linspace(0, 10, 1000)
```

Creates a dense time vector from 0 to 10 seconds (1000 points = 100 Hz equivalent).

```python
u_sine = np.sin(2 * np.pi * 1.5 * t)
```

Sinusoid at 1.5 Hz — represents an oscillatory disturbance (e.g., motor vibration).

```python
u_step = np.where(t >= 5, 2.0, 0.0)
```

Step signal: zero until t=5s, then amplitude 2. `np.where` is a vectorised if-else.

```python
u_total = u_sine + u_step
```

Combined input. Due to superposition, the output `y_out` will be the sum of both individual responses.

```python
t_out, y_out = G.simulate(t, u_total)
```

`simulate(t, u)` uses `scipy.signal.lsim` internally to compute the system response to an arbitrary input array `u` over time vector `t`. This is a **batch** (non-real-time) computation.

---

## How to run

```bash
uv run python examples/advanced/01_custom_signals/01_custom_signals.py
```

The plot shows the input signal (dashed) overlaid with the filtered output. After t=5s, the step shifts the DC level of the output while the sine oscillation continues — demonstrating superposition visually.
