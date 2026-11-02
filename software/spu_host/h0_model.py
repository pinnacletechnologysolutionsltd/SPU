"""H0-SW-1: abstract, in-memory lifecycle model; no transport or hardware."""

from dataclasses import dataclass, replace
from enum import Enum
from typing import Optional


class Phase(Enum):
    IDLE = "idle"
    ACTIVE = "active"
    COMPLETE = "complete"


class Outcome(Enum):
    SUCCESS = "success"
    REFUSED = "refused"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class Identity:
    epoch: int
    sequence: int


@dataclass(frozen=True)
class Request:
    operation: str
    operand: int


@dataclass(frozen=True)
class Record:
    identity: Identity
    request: Request
    phase: Phase
    outcome: Optional[Outcome] = None
    result: Optional[int] = None


@dataclass(frozen=True)
class Admission:
    accepted: bool
    identity: Optional[Identity]
    reason: Optional[str] = None


class H0Model:
    """Single owner, with a synthetic ECHO operation and trusted event tags."""

    def __init__(self):
        self._epoch = 0
        self._sequence = 0
        self._record = None
        self._committed = False
        self._terminal = None

    @property
    def record(self):
        return self._record

    def submit(self, request):
        # Admission is evaluated before any record or identity mutation.
        if self._record is not None and self._record.phase is Phase.ACTIVE:
            return Admission(False, None, "BUSY")
        if (not isinstance(request, Request) or
                not isinstance(request.operation, str) or
                type(request.operand) is not int):
            return Admission(False, None, "INVALID_REQUEST")
        identity = Identity(self._epoch, self._sequence + 1)
        supported = request.operation == "ECHO"
        record = Record(identity, request, Phase.ACTIVE) if supported else Record(
            identity, request, Phase.COMPLETE, Outcome.UNSUPPORTED)
        self._sequence += 1
        self._record = record
        self._committed = False
        self._terminal = None
        return Admission(True, identity)

    def _active(self, identity):
        return (type(identity) is Identity and type(identity.epoch) is int
                and type(identity.sequence) is int
                and self._record is not None and self._record.phase is Phase.ACTIVE
                and self._record.identity == identity)

    def effect_committed(self, identity):
        """Record an abstract, already-committed effect; duplicates are inert."""
        if not self._active(identity) or self._committed:
            return False
        self._committed = True
        self._publish_if_ready()
        return True

    def terminal(self, identity, outcome, result=None):
        """Accept one matching terminal; malformed or stale events are inert."""
        if not self._active(identity) or self._terminal is not None:
            return False
        if outcome is Outcome.SUCCESS:
            if type(result) is not int or result != self._record.request.operand:
                return False
        elif outcome is Outcome.REFUSED:
            if result is not None or self._committed:
                return False
        else:
            return False
        self._terminal = (outcome, result)
        self._publish_if_ready()
        return True

    def _publish_if_ready(self):
        if self._terminal is None:
            return
        outcome, result = self._terminal
        if outcome is Outcome.SUCCESS and not self._committed:
            return
        self._record = replace(self._record, phase=Phase.COMPLETE,
                               outcome=outcome, result=result)

    def reset(self):
        """Model a known reset; does not claim physical cancellation or rollback."""
        self._epoch += 1
        self._sequence = 0
        self._record = None
        self._committed = False
        self._terminal = None
