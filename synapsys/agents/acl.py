from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Performative(str, Enum):
    """FIPA ACL performatives relevant to control-system agents."""
    INFORM    = "inform"     # agent reports a fact (e.g. plant state)
    REQUEST   = "request"    # agent asks another to perform an action
    AGREE     = "agree"      # accept a request
    REFUSE    = "refuse"     # decline a request
    FAILURE   = "failure"    # report a failed action
    SUBSCRIBE = "subscribe"  # subscribe to periodic updates
    CANCEL    = "cancel"     # cancel a previous request/subscription


@dataclass
class ACLMessage:
    """
    FIPA Agent Communication Language message.

    Agents exchange ACLMessages to coordinate simulation steps,
    report plant states, and issue control commands.
    """
    performative: Performative
    sender: str
    receiver: str
    content: Any
    ontology: str = "synapsys-control-v1"
    timestamp: float = field(default_factory=time.monotonic)

    def reply(self, performative: Performative, content: Any) -> ACLMessage:
        """Create a reply with swapped sender/receiver."""
        return ACLMessage(
            performative=performative,
            sender=self.receiver,
            receiver=self.sender,
            content=content,
            ontology=self.ontology,
        )

    def __repr__(self) -> str:
        return (
            f"ACLMessage({self.performative.value!r} "
            f"{self.sender!r} -> {self.receiver!r})"
        )
