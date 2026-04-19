---
id: core
title: synapsys.core — LTI Math Engine
sidebar_position: 2
---

# synapsys.core — LTI Math Engine

The mathematical core of Synapsys. All LTI system representations live here.

## LTIModel (Abstract Base Class)

Base class for all LTI systems. Defines the common interface.

| Method | Description |
|--------|-------------|
| `poles()` | Returns the system poles as a NumPy array |
| `zeros()` | Returns the system zeros as a NumPy array |
| `is_stable()` | `True` if all poles satisfy the stability criterion |
| `evaluate(s_or_z)` | Evaluates the transfer function at a given complex point |
| `step(t=None, n=200)` | Step response — `n` applies to discrete systems only |
| `bode(omega=None)` | Returns `(omega [rad/s], mag [dB], phase [deg])` |
| `simulate(t, u)` | Batch simulation for an arbitrary input array |

## TransferFunction

Represents a SISO LTI system as a ratio of polynomials: $G(s) = N(s)/D(s)$.

| Attribute / Method | Description |
|---|---|
| `num` | Numerator coefficients (NumPy array, highest power first) |
| `den` | Denominator coefficients (NumPy array, highest power first) |
| `dt` | Sample time (`0.0` = continuous) |
| `is_discrete` | `True` when `dt > 0` |
| `order` | Degree of the denominator polynomial |
| `evaluate(s)` | Evaluate $G(s)$ or $H(z)$ at a complex point |
| `feedback(sensor=None)` | Closed-loop $T = G\,/\,(1 + G H)$ with negative feedback |
| `to_state_space()` | Converts to `StateSpace` (controllable canonical form) |
| `c2d(dt, method='zoh')` | Discretises (equivalent to `c2d()` API call) |
| `evolve(x, u)` | One discrete step — requires `is_discrete == True` |
| `simulate(t, u)` | Batch simulation for arbitrary input |
| `__mul__`, `__add__`, `__truediv__`, `__neg__` | Block algebra operators |

:::note
`feedback(sensor=None)` uses only the `sensor` parameter — there is no `sign`
argument. Positive feedback must be implemented manually.
:::

## StateSpace

Represents an LTI system via $(A, B, C, D)$ matrices.

| Attribute / Method | Description |
|---|---|
| `A, B, C, D` | System matrices (NumPy arrays) |
| `dt` | Sample time (`0.0` = continuous) |
| `n_states`, `n_inputs`, `n_outputs` | System dimensions |
| `is_discrete` | `True` when `dt > 0` |
| `evaluate(s_or_z)` | Evaluate the transfer matrix at a complex point |
| `bode(omega=None)` | Returns `(omega [rad/s], mag [dB], phase [deg])` |
| `evolve(x, u)` | One discrete step — raises `RuntimeError` if continuous |
| `simulate(t, u)` | Batch simulation for arbitrary input |
| `to_transfer_function()` | Converts to `TransferFunction` |
| `c2d(dt, method='zoh')` | Discretises the continuous system |
| `__mul__`, `__add__`, `__neg__` | Block algebra operators |

:::warning
`evolve(x, u)` requires a **discrete** system. Call `c2d()` first if your model
is continuous. It does **not** mutate internal state — callers must store
`x_next` between steps.
:::

## Source

See [`synapsys/core/`](https://github.com/synapsys-lab/synapsys/tree/main/synapsys/core) on GitHub.
