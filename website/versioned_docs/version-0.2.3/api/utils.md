---
id: utils
title: synapsys.utils — Matrix Helpers
sidebar_position: 7
---

# synapsys.utils — Matrix Helpers

Ergonomic utilities for building NumPy arrays and state-space matrices by name,
reducing boilerplate when defining LTI models.

```python
from synapsys.utils import mat, col, row, StateEquations
# or
from synapsys import mat, col, row, StateEquations
```

## mat

Creates a 2-D NumPy array from nested Python lists.

```python
mat(data: list[list[float]]) -> np.ndarray
```

```python
A = mat([[0, 1], [-2, -3]])   # shape (2, 2)
```

## col

Creates a column vector (shape `(n, 1)`) from a flat list or 1-D array.

```python
col(data: list[float] | np.ndarray) -> np.ndarray
```

```python
B = col([0, 1])   # shape (2, 1)
```

## row

Creates a row vector (shape `(1, n)`) from a flat list or 1-D array.

```python
row(data: list[float] | np.ndarray) -> np.ndarray
```

```python
C = row([1, 0])   # shape (1, 2)
```

## StateEquations

Fluent builder that constructs **A** and **B** matrices by declaring each
differential equation by the names of its state and input variables.
Eliminates manual index management for multi-state models.

### Constructor

```python
StateEquations(
    states: list[str],   # names of state variables
    inputs: list[str],   # names of input variables
)
```

### Methods

| Method | Description |
|--------|-------------|
| `eq(state, **coeffs)` | Declares one equation. Keys matching a state name go to **A**; keys matching an input name go to **B** |
| `output(*state_names)` | Builds a **C** matrix that selects the named states as outputs |

### Properties

| Property | Description |
|----------|-------------|
| `A` | System matrix $(n \times n)$ as `np.ndarray` |
| `B` | Input matrix $(n \times m)$ as `np.ndarray` |
| `states` | Ordered list of state variable names |
| `inputs` | Ordered list of input variable names |

### Example — 2-DOF mass-spring-damper

State vector $\mathbf{x} = [x_1, x_2, v_1, v_2]^\top$, input $F$:

```python
from synapsys.utils import StateEquations
from synapsys.api import ss, c2d

m, c, k = 1.0, 0.1, 2.0

eqs = (
    StateEquations(states=["x1", "x2", "v1", "v2"], inputs=["F"])
    .eq("x1", v1=1)
    .eq("x2", v2=1)
    .eq("v1", x1=-2*k/m, x2=k/m,  v1=-c/m)
    .eq("v2", x1=k/m,  x2=-2*k/m, v2=-c/m, F=k/m)
)

# Build a StateSpace model directly from A and B
C = eqs.output("x1", "x2")   # select positions as outputs
plant = ss(eqs.A, eqs.B, C, [[0, 0]])
plant_d = c2d(plant, dt=0.01)
```

:::tip
`StateEquations` pairs naturally with `synapsys.algorithms.lqr`:
```python
from synapsys.algorithms import lqr
K, P = lqr(eqs.A, eqs.B, Q, R)
```
:::

## Source

See [`synapsys/utils/`](https://github.com/synapsys-lab/synapsys/tree/main/synapsys/utils) on GitHub.
