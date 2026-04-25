from __future__ import annotations

from typing import Callable

from numpy import ndarray


def euler(
    f: Callable[[ndarray, ndarray], ndarray], x: ndarray, u: ndarray, dt: float
) -> ndarray:
    return x + dt * f(x, u)


def rk4(
    f: Callable[[ndarray, ndarray], ndarray], x: ndarray, u: ndarray, dt: float
) -> ndarray:
    k1 = f(x, u)
    k2 = f(x + 0.5 * dt * k1, u)
    k3 = f(x + 0.5 * dt * k2, u)
    k4 = f(x + dt * k3, u)
    return x + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)  # type: ignore[no-any-return]


def rk45(
    f: Callable[[ndarray, ndarray], ndarray], x: ndarray, u: ndarray, dt: float
) -> ndarray:
    """Dormand-Prince RK45 — fixed step, no adaptive control."""
    k1 = f(x, u)
    k2 = f(x + (1 / 5) * dt * k1, u)
    k3 = f(x + (3 / 40) * dt * k1 + (9 / 40) * dt * k2, u)
    k4 = f(x + (44 / 45) * dt * k1 - (56 / 15) * dt * k2 + (32 / 9) * dt * k3, u)
    k5 = f(
        x
        + (19372 / 6561) * dt * k1
        - (25360 / 2187) * dt * k2
        + (64448 / 6561) * dt * k3
        - (212 / 729) * dt * k4,
        u,
    )
    k6 = f(
        x
        + (9017 / 3168) * dt * k1
        - (355 / 33) * dt * k2
        + (46732 / 5247) * dt * k3
        + (49 / 176) * dt * k4
        - (5103 / 18656) * dt * k5,
        u,
    )
    return x + dt * (
        (35 / 384) * k1
        + (500 / 1113) * k3
        + (125 / 192) * k4
        - (2187 / 6784) * k5
        + (11 / 84) * k6
    )
