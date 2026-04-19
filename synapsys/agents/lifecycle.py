from __future__ import annotations

import logging
import threading
from abc import ABC, abstractmethod

import numpy as np

from ..transport.base import TransportStrategy
from .sync_engine import SyncEngine

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Base class for all Synapsys agents (plant, controller, observer).

    Subclass this and implement ``setup``, ``step``, and ``teardown``.
    Call ``start()`` to launch the agent in a background thread, or
    ``start(blocking=True)`` to run it in the current thread.

    Accepts either a legacy ``TransportStrategy`` or a ``MessageBroker``
    (pass ``transport=None, broker=<broker>``). Use ``self._read()`` /
    ``self._write()`` in subclasses to stay transport-agnostic.

    Lifecycle::

        setup()  ->  [step() + sync.tick()] * N  ->  teardown()
    """

    def __init__(
        self,
        name: str,
        transport: TransportStrategy | None,
        sync: SyncEngine,
        *,
        broker: object | None = None,
    ):
        self.name = name
        self.transport = transport
        self.sync = sync
        self.broker = broker
        self._running = False
        self._thread: threading.Thread | None = None

        # Transport/broker lifetime is owned by the caller, not the agent.

    # ------------------------------------------------------------------
    # Unified I/O helpers (transport-agnostic)
    # ------------------------------------------------------------------

    def _read(self, channel: str) -> np.ndarray:
        if self.broker is not None:
            return self.broker.read(channel)  # type: ignore[union-attr]
        assert self.transport is not None, "Agent has neither transport nor broker."
        return self.transport.read(channel)

    def _write(self, channel: str, data: np.ndarray) -> None:
        if self.broker is not None:
            self.broker.publish(channel, data)  # type: ignore[union-attr]
        else:
            assert self.transport is not None, "Agent has neither transport nor broker."
            self.transport.write(channel, data)

    # ------------------------------------------------------------------
    # Interface to implement
    # ------------------------------------------------------------------

    @abstractmethod
    def setup(self) -> None:
        """Initialise resources. Called once before the loop."""

    @abstractmethod
    def step(self) -> None:
        """Execute one simulation tick."""

    @abstractmethod
    def teardown(self) -> None:
        """Release resources. Called once after the loop exits."""

    # ------------------------------------------------------------------
    # Lifecycle control
    # ------------------------------------------------------------------

    def start(self, blocking: bool = False) -> None:
        self._running = True
        if blocking:
            self._run()
        else:
            self._thread = threading.Thread(
                target=self._run, daemon=True, name=self.name
            )
            self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=5.0)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _run(self) -> None:
        logger.info("Agent '%s' starting.", self.name)
        self.setup()
        try:
            while self._running:
                self.step()
                self.sync.tick()
        except Exception:
            logger.exception("Agent '%s' raised an unhandled exception.", self.name)
        finally:
            self.teardown()
            logger.info("Agent '%s' stopped.", self.name)
