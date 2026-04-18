"""
Linearised quadcopter hover model — 12-state MIMO.

State  x  = [x, y, z, φ, θ, ψ, ẋ, ẏ, ż, p, q, r]   (12 × 1)
Input  δu = [δF, τφ, τθ, τψ]                           (4 × 1, deviations from hover)
Output y  = [x, y, z, ψ]                               (4 × 1)

Linearised at hover: φ = θ = ψ = 0, all velocities zero.
Full derivation in docs/examples/quadcopter-mimo.
"""
from __future__ import annotations

import numpy as np

# ── Physical parameters (500 mm racing quad) ──────────────────────────────────
MASS: float = 0.500        # kg
G:    float = 9.81         # m/s²
IXX:  float = 4.856e-3     # kg·m²  (roll)
IYY:  float = 4.856e-3     # kg·m²  (pitch)
IZZ:  float = 8.801e-3     # kg·m²  (yaw)
ARM:  float = 0.175        # m  (centre → motor)

F_HOVER: float = MASS * G  # N — equilibrium total thrust

# ── Input deviation limits ────────────────────────────────────────────────────
U_MIN = np.array([-0.90 * F_HOVER, -0.50, -0.50, -0.30])  # [N, Nm, Nm, Nm]
U_MAX = np.array([ 3.00 * F_HOVER,  0.50,  0.50,  0.30])

# ── LQR weight matrices ───────────────────────────────────────────────────────
Q_LQR = np.diag([
    20.0, 20.0, 30.0,   # x, y, z    — position
     3.0,  3.0,  8.0,   # φ, θ, ψ   — attitude (yaw weighted more)
     2.0,  2.0,  4.0,   # ẋ, ẏ, ż   — linear velocity
     0.5,  0.5,  1.0,   # p, q, r   — angular rates
])
R_LQR = np.diag([0.5, 3.0, 3.0, 5.0])   # δF, τφ, τθ, τψ


def build_matrices() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return (A, B, C, D) for the linearised hover model."""
    A = np.zeros((12, 12))
    # Kinematics: ṗos = vel
    A[0, 6] = A[1, 7] = A[2, 8] = 1.0
    # Small-angle attitude kinematics: angle_rate = body_rate
    A[3, 9] = A[4, 10] = A[5, 11] = 1.0
    # Gravity coupling (linearised): ẍ = g·θ,  ÿ = −g·φ
    A[6, 4] =  G
    A[7, 3] = -G

    B = np.zeros((12, 4))
    B[8,  0] = 1.0 / MASS   # z̈  ← δF / m
    B[9,  1] = 1.0 / IXX    # φ̈  ← τφ / Ixx
    B[10, 2] = 1.0 / IYY    # θ̈  ← τθ / Iyy
    B[11, 3] = 1.0 / IZZ    # ψ̈  ← τψ / Izz

    C = np.zeros((4, 12))
    C[0, 0] = C[1, 1] = C[2, 2] = 1.0   # x, y, z
    C[3, 5] = 1.0                         # ψ

    D = np.zeros((4, 4))
    return A, B, C, D


def figure8_ref(
    t: float,
    amp: float = 0.80,
    omega: float = 0.35,
    z_hover: float = 1.50,
) -> np.ndarray:
    """Lemniscate of Bernoulli reference trajectory.

    Returns a 12-state reference with kinematically consistent
    position only (velocity feedforward omitted — suitable for ω ≤ 0.5 rad/s).
    """
    s = np.sin(omega * t)
    c = np.cos(omega * t)
    denom = 1.0 + s ** 2
    ref = np.zeros(12)
    ref[0] = amp * c / denom            # x
    ref[1] = amp * s * c / denom        # y
    ref[2] = z_hover                    # z (constant altitude)
    return ref
