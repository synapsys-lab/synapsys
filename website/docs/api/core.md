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
| `evaluate(s_or_z)` | Evaluates the transfer function at a given frequency point |
| `step(...)` | Computes the step response |
| `bode(...)` | Returns Bode diagram data `(w, mag_dB, phase_deg)` |

## TransferFunction

Represents a SISO LTI system as a ratio of polynomials: $G(s) = N(s)/D(s)$.

| Attribute / Method | Description |
|---|---|
| `num` | Numerator coefficients (NumPy array) |
| `den` | Denominator coefficients (NumPy array) |
| `dt` | Sample time (`0` = continuous) |
| `is_discrete` | `True` when `dt > 0` |
| `order` | Degree of the denominator polynomial |
| `feedback(H=None, sign=-1)` | Returns the closed-loop system |
| `to_state_space()` | Converts to `StateSpace` |
| `c2d(dt, method='zoh')` | Discretises (equivalent to `c2d()` API call) |
| `__mul__`, `__add__`, `__truediv__`, `__neg__` | Block algebra operators |

## StateSpace

Represents an LTI system via $(A, B, C, D)$ matrices.

| Attribute / Method | Description |
|---|---|
| `A, B, C, D` | System matrices (NumPy arrays) |
| `dt` | Sample time |
| `n_states`, `n_inputs`, `n_outputs` | System dimensions |
| `is_discrete` | `True` when `dt > 0` |
| `evolve(x, u)` | One-step simulation: returns `(x_next, y)` |
| `simulate(t, u)` | Batch simulation for arbitrary input |
| `to_transfer_function()` | Converts to `TransferFunction` |

## Source

See [`synapsys/core/`](https://github.com/synapsys-lab/synapsys/tree/main/synapsys/core) on GitHub.
