from __future__ import annotations

import numpy as np
from scipy import linalg


def lqr(
    A: np.ndarray,
    B: np.ndarray,
    Q: np.ndarray,
    R: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Solve the continuous-time Linear Quadratic Regulator problem.

    Finds K such that u = -Kx minimizes J = integral(x'Qx + u'Ru)dt.

    Args:
        A: System matrix (n x n)
        B: Input matrix (n x m)
        Q: State cost matrix (n x n, positive semi-definite)
        R: Input cost matrix (m x m, positive definite)

    Returns:
        K: State-feedback gain (m x n)
        P: Solution to the algebraic Riccati equation (n x n)
    """
    A = np.atleast_2d(np.asarray(A, dtype=np.float64))
    B = np.atleast_2d(np.asarray(B, dtype=np.float64))
    Q = np.atleast_2d(np.asarray(Q, dtype=np.float64))
    R = np.atleast_2d(np.asarray(R, dtype=np.float64))

    P = linalg.solve_continuous_are(A, B, Q, R)
    K = np.linalg.solve(R, B.T @ P)
    return K, P
