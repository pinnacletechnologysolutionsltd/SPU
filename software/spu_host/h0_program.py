"""H0-SW-2 transport-independent, bounded *software simulation* prototype."""
from dataclasses import dataclass
from enum import Enum
import hashlib
import hmac

from .h0_model import Identity


class State(Enum):
    EMPTY = "empty"
    LOADED = "loaded"
    VERIFIED = "verified"
    ACTIVE = "active"
    COMPLETE = "complete"


@dataclass(frozen=True)
class Reply:
    ok: bool
    reason: str
    identity: object = None
    value: object = None


def _valid_id(identity):
    return (type(identity) is Identity and type(identity.epoch) is int
            and type(identity.sequence) is int)


def _decode(program):
    """Admit only six S0 slices, SLD S0, SMUL S0,S0,S0, six SRD S0."""
    if len(program) != 112:
        return None
    words = tuple(int.from_bytes(program[i:i + 8], "big") for i in range(0, 112, 8))
    slices = []
    for i, word in enumerate(words[:6]):
        if (word >> 40) != (0x700000 + i) or word & 0xff:
            return None
        slices.append((word >> 8) & 0xffffffff)
    if words[6:8] != (0x7100000000000000, 0x7300000000000000):
        return None
    if words[8:] != tuple(0x7200000000000000 | (i << 40) for i in range(6)):
        return None
    # Restrict to nonnegative one-limb inputs and tiny raw products; no claim
    # about overflow, normalization, signed values or other instruction forms.
    a, ah, b, bh, d, dh = slices
    if ah or bh or dh or a > 1000 or b > 1000 or not 1 <= d <= 1000:
        return None
    return a, b, d


class ProgramController:
    """One installed candidate and one simulated execution; sequential calls only."""
    def __init__(self):
        self._epoch = 0
        self._sequence = 0
        self._state = State.EMPTY
        self._owner = None
        self._program = None
        self._digest = None
        self._decoded = None
        self._result = None

    @property
    def state(self):
        return self._state

    def _owns(self, identity):
        return _valid_id(identity) and identity == self._owner

    def load(self, program, digest):
        if self._state is State.ACTIVE:
            return Reply(False, "BUSY")
        if (type(program) is not bytes or len(program) != 112 or
                type(digest) is not str or len(digest) != 64 or
                any(c not in "0123456789abcdef" for c in digest)):
            return Reply(False, "INVALID_LOAD")
        identity = Identity(self._epoch, self._sequence + 1)
        self._sequence += 1
        self._owner, self._program, self._digest = identity, program, digest
        self._decoded, self._result = None, None
        self._state = State.LOADED
        return Reply(True, "LOADED", identity)

    def verify(self, identity):
        if not self._owns(identity):
            return Reply(False, "STALE_IDENTITY")
        if self._state is not State.LOADED:
            return Reply(False, "BAD_STATE")
        if not hmac.compare_digest(hashlib.sha256(self._program).hexdigest(), self._digest):
            return Reply(False, "INTEGRITY")
        decoded = _decode(self._program)
        if decoded is None:
            return Reply(False, "UNSUPPORTED_PROGRAM")
        self._decoded = decoded
        self._state = State.VERIFIED
        return Reply(True, "VERIFIED", identity)

    def execute(self, identity):
        if not self._owns(identity):
            return Reply(False, "STALE_IDENTITY")
        if self._state is not State.VERIFIED:
            return Reply(False, "BAD_STATE")
        self._state = State.ACTIVE
        return Reply(True, "STARTED_SIMULATION", identity)

    def advance_simulation(self, identity):
        if not self._owns(identity):
            return Reply(False, "STALE_IDENTITY")
        if self._state is not State.ACTIVE:
            return Reply(False, "BAD_STATE")
        a, b, d = self._decoded
        self._result = (a*a + 3*b*b, 2*a*b, d*d)
        self._state = State.COMPLETE
        return Reply(True, "SIMULATION_COMPLETE", identity)

    def result(self, identity):
        if not self._owns(identity):
            return Reply(False, "STALE_IDENTITY")
        if self._state is not State.COMPLETE:
            return Reply(False, "NOT_COMPLETE")
        return Reply(True, "SIMULATED_RESULT", identity, self._result)

    def reset(self):
        self._epoch += 1
        self._sequence = 0
        self._state = State.EMPTY
        self._owner = self._program = self._digest = None
        self._decoded = self._result = None
