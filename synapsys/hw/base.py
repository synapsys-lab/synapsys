from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class HardwareInterface(ABC):
    """
    Abstract interface for physical hardware (FPGA, microcontrollers, PLCs, etc.).

    Implement this class to bridge a real device into the Synapsys simulation
    framework so it can act as the plant or controller in a HIL loop.

    Contract
    --------
    * ``n_inputs``  — number of scalar actuator channels written to hardware.
    * ``n_outputs`` — number of scalar sensor channels read from hardware.
    * ``read_outputs(timeout_ms)`` — must return an ``(n_outputs,)`` float64 array.
      Raises ``TimeoutError`` if hardware does not respond within ``timeout_ms``.
    * ``write_inputs(u, timeout_ms)`` — sends an ``(n_inputs,)`` float64 array.
      Raises ``TimeoutError`` on write failure.
    * Implementations must be **thread-safe** — a ``HardwareAgent`` will call
      ``read_outputs`` and ``write_inputs`` from a background thread.

    Example (Serial/UART bridge for ESP32) — planned for v0.5::

        class SerialHardwareInterface(HardwareInterface):
            def connect(self): self._ser = serial.Serial(self.port, self.baud)
            @property
            def n_inputs(self): return 1
            @property
            def n_outputs(self): return 1
            def read_outputs(self, timeout_ms=100): ...
            def write_inputs(self, u, timeout_ms=100): ...
            def disconnect(self): self._ser.close()
    """

    # ── mandatory metadata ────────────────────────────────────────────────────

    @property
    @abstractmethod
    def n_inputs(self) -> int:
        """Number of actuator (control input) channels sent to hardware."""

    @property
    @abstractmethod
    def n_outputs(self) -> int:
        """Number of sensor (plant output) channels received from hardware."""

    # ── lifecycle ─────────────────────────────────────────────────────────────

    @abstractmethod
    def connect(self) -> None:
        """Open connection to the hardware device."""

    @abstractmethod
    def disconnect(self) -> None:
        """Close the hardware connection cleanly."""

    # ── I/O ───────────────────────────────────────────────────────────────────

    @abstractmethod
    def read_outputs(self, timeout_ms: float = 100.0) -> np.ndarray:
        """
        Read current plant outputs (sensor measurements) from hardware.

        Returns
        -------
        np.ndarray
            Shape ``(n_outputs,)``, dtype ``float64``.

        Raises
        ------
        TimeoutError
            If hardware does not respond within *timeout_ms* milliseconds.
        """

    @abstractmethod
    def write_inputs(self, u: np.ndarray, timeout_ms: float = 100.0) -> None:
        """
        Write control inputs (actuator commands) to hardware.

        Parameters
        ----------
        u : np.ndarray
            Shape ``(n_inputs,)``, dtype ``float64``.
        timeout_ms : float
            Maximum time to wait for the write to be acknowledged.

        Raises
        ------
        TimeoutError
            If hardware does not acknowledge within *timeout_ms* milliseconds.
        """

    # ── context manager ───────────────────────────────────────────────────────

    def __enter__(self) -> HardwareInterface:
        self.connect()
        return self

    def __exit__(
        self,
        _exc_type: object,
        _exc_val: object,
        _exc_tb: object,
    ) -> None:
        self.disconnect()
