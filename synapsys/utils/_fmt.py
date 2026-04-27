"""Internal display helpers — box renderer, matrix/pole formatters."""

from __future__ import annotations

import numpy as np

_MIN_WIDTH = 40
_MAT_THRESHOLD = 8  # max rows or cols before switching to shape-only


# ── Box renderer ─────────────────────────────────────────────────────────────


def box(title: str, lines: list[str]) -> str:
    """Render an ASCII box with a title banner and indented content.

    Example output::

        ======= TransferFunction ===========
          domain : continuous
          order  : 2
        =====================================
    """
    header = f"======= {title} ".ljust(_MIN_WIDTH, "=")
    footer = "=" * len(header)
    body = "\n".join(f"  {line}" for line in lines)
    return f"{header}\n{body}\n{footer}"


# ── Scalar / array formatters ─────────────────────────────────────────────────


def _g(v: float, digits: int = 5) -> str:
    """Format a float with up to `digits` significant figures."""
    return f"{v:.{digits}g}"


def fmt_arr(a: np.ndarray, digits: int = 5) -> str:
    """Format a 1-D array as [v0, v1, ...]."""
    return "[" + ", ".join(_g(float(v), digits) for v in a) + "]"


# ── Matrix formatter ──────────────────────────────────────────────────────────


def fmt_matrix(M: np.ndarray, label: str, digits: int = 4) -> list[str]:
    """Format a 2-D matrix as a bordered table under *label*.

    Uses sign-aware fixed-point formatting with column-aligned values::

        A = |  0.0000   1.0000 |
            | -2.0000  -5.0000 |

    Falls back to a compact shape description for large matrices.
    """
    rows, cols = M.shape
    if rows > _MAT_THRESHOLD or cols > _MAT_THRESHOLD:
        return [f"{label} : ({rows}×{cols}) array"]

    # Sign-aware fixed-point: positive values get a leading space so columns align
    cells = [
        [f"{float(M[r, c]): .{digits}f}" for c in range(cols)] for r in range(rows)
    ]
    col_w = [max(len(cells[r][c]) for r in range(rows)) for c in range(cols)]

    prefix_first = f"{label} = "
    prefix_rest = " " * len(prefix_first)
    out = []
    for r, row_cells in enumerate(cells):
        inner = "  ".join(v.rjust(col_w[c]) for c, v in enumerate(row_cells))
        prefix = prefix_first if r == 0 else prefix_rest
        out.append(f"{prefix}| {inner} |")
    return out


# ── Pole formatter ────────────────────────────────────────────────────────────


def fmt_poles(poles: np.ndarray, is_discrete: bool = False) -> list[str]:
    """Format an array of poles, grouping conjugate pairs.

    Continuous: shows σ ± jω with ζ and ωₙ annotations.
    Discrete:   shows z = r∠θ with |z| stability indicator.
    """
    if poles.size == 0:
        return ["(none)"]

    tol = 1e-6
    lines: list[str] = []
    used: set[int] = set()

    for i, p in enumerate(poles):
        if i in used:
            continue
        used.add(i)

        if abs(p.imag) > tol:
            # Look for the conjugate partner
            conj_found = False
            for j in range(i + 1, len(poles)):
                if j not in used and abs(poles[j] - p.conjugate()) < tol:
                    used.add(j)
                    conj_found = True
                    break

            if is_discrete:
                r = abs(p)
                stable_str = "" if r < 1.0 else "  ← UNSTABLE"
                if conj_found:
                    lines.append(
                        f"{p.real:.4f} ± {abs(p.imag):.4f}j  (|z|={r:.4f}){stable_str}"
                    )
                else:
                    lines.append(
                        f"{p.real:.4f}{p.imag:+.4f}j  (|z|={r:.4f}){stable_str}"
                    )
            else:
                sigma = p.real
                omega_d = abs(p.imag)
                omega_n = abs(p)
                zeta = -sigma / omega_n if omega_n > 1e-10 else 0.0
                stable_str = "" if sigma < 0 else "  ← UNSTABLE"
                if conj_found:
                    lines.append(
                        f"{sigma:.4f} ± {omega_d:.4f}j"
                        f"  (ζ={zeta:.3f}, ωₙ={omega_n:.4f} rad/s){stable_str}"
                    )
                else:
                    lines.append(f"{p.real:.4f}{p.imag:+.4f}j{stable_str}")
        else:
            # Real pole
            pr = p.real
            if is_discrete:
                stable_str = "" if abs(pr) < 1.0 else "  ← UNSTABLE"
                lines.append(f"{pr:.4f}  (real){stable_str}")
            else:
                stable_str = "" if pr < 0 else "  ← UNSTABLE"
                lines.append(f"{pr:.4f}  (real){stable_str}")

    return lines if lines else ["(none)"]
