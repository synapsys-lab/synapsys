from __future__ import annotations

import logging
import threading
from abc import ABC, abstractmethod

from ..transport.base import TransportStrategy
from .sync_engine import SyncEngine

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Base class for all Synapsys agents (plant, controller, observer).

    Subclass this and implement ``setup``, ``step``, and ``teardown``.
    Call ``start()`` to launch the agent in a background thread, or
    ``start(blocking=True)`` to run it in the current thread.

    Lifecycle::

        setup()  ->  [step() + sync.tick()] * N  ->  teardown()
    """

    def __init__(
        self,
        name: str,
        transport: TransportStrategy,
        sync: SyncEngine,
    ):
        self.name = name
        self.transport = transport
        self.sync = sync
        self._running = False
        self._thread: threading.Thread | None = None

        # Transport lifetime is owned by the caller, not the agent.
        # The agent does NOT close the transport on exit.

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
