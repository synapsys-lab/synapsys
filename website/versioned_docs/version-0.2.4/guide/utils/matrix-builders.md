---
id: matrix-builders
title: Matrix Builders
sidebar_position: 1
---

# Matrix Builders

`synapsys.utils` provides concise helpers to construct NumPy arrays and build
$(A, B, C, D)$ matrices from named differential equations — no raw
`np.array` boilerplate required.

## Helpers: `mat`, `col`, `row`

| Helper | Output shape | Use for |
|---|---|---|
| `mat(rows)` | $(m \times n)$ | any 2-D matrix |
| `col(*values)` | $(n \times 1)$ | input matrix **B**, column vector |
| `row(*values)` | $(1 \times n)$ | output matrix **C**, row selector |

```python
from synapsys.utils import mat, col, row

A = mat([
    [ 0,  1],
    [-2, -3],
])                    # shape (2, 2)

B = col(0, 1)         # shape (2, 1)
C = row(1, 0)         # shape (1, 2)
```

All three return `np.ndarray` with `dtype=float64` and are drop-in replacements
for `np.array(...)`.

---

## `StateEquations` — named differential equations

`StateEquations` lets you declare each differential equation **by name** instead
of managing matrix indices manually.

$$\dot{x}_i = \sum_j a_{ij}\,x_j + \sum_k b_{ik}\,u_k$$

Each call to `.eq(state, **coeffs)` fills the corresponding row of **A** (for
state names) and **B** (for input names). The builder is **fluent** — every
`.eq()` returns `self`.

### Example — 2-DOF mass–spring–damper

$$
\begin{bmatrix} \dot{x}_1 \\ \dot{x}_2 \\ \dot{v}_1 \\ \dot{v}_2 \end{bmatrix}
=
\underbrace{\begin{bmatrix}
0 & 0 & 1 & 0 \\
0 & 0 & 0 & 1 \\
-2k/m & k/m & -c/m & 0 \\
k/m & -2k/m & 0 & -c/m
\end{bmatrix}}_{A}
\begin{bmatrix} x_1 \\ x_2 \\ v_1 \\ v_2 \end{bmatrix}
+
\underbrace{\begin{bmatrix} 0 \\ 0 \\ 0 \\ k/m \end{bmatrix}}_{B}
F
$$

```python
from synapsys.utils import StateEquations

m, c, k = 1.0, 0.1, 2.0

eqs = (
    StateEquations(states=["x1", "x2", "v1", "v2"], inputs=["F"])
    .eq("x1", v1=1)                                         # ẋ1 = v1
    .eq("x2", v2=1)                                         # ẋ2 = v2
    .eq("v1", x1=-2*k/m, x2=k/m,  v1=-c/m)                # v̇1 = …
    .eq("v2", x1=k/m,  x2=-2*k/m, v2=-c/m, F=k/m)         # v̇2 = …
)

A = eqs.A                       # np.ndarray (4, 4)
B = eqs.B                       # np.ndarray (4, 1)
C = eqs.output("x1", "x2")     # np.ndarray (2, 4) — observe positions
```

### Building the `StateSpace` model

```python
import numpy as np
from synapsys.api import ss

D = np.zeros((2, 1))
G = ss(eqs.A, eqs.B, eqs.output("x1", "x2"), D)

print(G.is_stable())   # True
print(G.n_states)      # 4
```

### `output()` — selecting outputs

`output(*state_names)` generates the **C** matrix that selects the given states
as system outputs:

```python
# observe only positions
C_pos = eqs.output("x1", "x2")     # shape (2, 4)

# observe all states
C_all = eqs.output("x1", "x2", "v1", "v2")   # shape (4, 4) == np.eye(4)
```

---

## Error handling

Both `.eq()` and `.output()` raise `ValueError` with a descriptive message if a
name is not declared:

```python
eqs.eq("z", x1=1.0)        # ValueError: 'z' is not a declared state
eqs.eq("v1", q=1.0)        # ValueError: 'q' is not a declared state or input
eqs.output("z")             # ValueError: 'z' is not a declared state
```

---

## Top-level import

All helpers are re-exported from the `synapsys` root package:

```python
from synapsys import mat, col, row, StateEquations
```

## API Reference

See the full reference at [synapsys.utils](../../api/core).
