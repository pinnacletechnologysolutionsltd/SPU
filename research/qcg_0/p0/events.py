"""Statuses, refusals, width profiles and event-id construction (contract Revision 3.2.1 §3)."""
from dataclasses import dataclass


class Refusal(Exception):
    """A REFUSED outcome; `event` is the unique first-refusal event id when the code is ARITH_LIMIT."""

    def __init__(self, code, event=None):
        super().__init__(code, event)
        self.code, self.event = code, event


class Invalid(Exception):
    """An INVALID outcome (DIV_ZERO, MALFORMED)."""

    def __init__(self, code, event=None):
        super().__init__(code, event)
        self.code, self.event = code, event


class OpBudget(BaseException):
    """The global counted-operation budget is exhausted: raised before the operation runs; never caught as a refusal."""

    def __init__(self, event):
        super().__init__(event)
        self.event = event


@dataclass(frozen=True)
class Profile:
    name: str
    red: int   # reduced numerator/denominator bound, in bits
    raw: int   # raw pre-reduction bound, in bits


P4096 = Profile("P4096", 4096, 16384)
W31 = Profile("W31", 31, 63)

STATUSES = ("OK", "REFUSED", "INVALID", "NOT_APPLICABLE")
REFUSED_CODES = ("ARITH_LIMIT", "NONMONOTONE", "NONREGULAR", "OUT_OF_DOMAIN",
                 "NOT_PRIMITIVE_RETIMING", "APPROX_NOT_EXACT")
INVALID_CODES = ("DIV_ZERO", "MALFORMED")


def event_id(arm, phase, qid, step, k, sub=None):
    """`arm.phase[.qNN].step.k[.sub]` exactly as the contract's grammar."""
    parts = [arm, phase]
    if qid is not None:
        parts.append("q%02d" % qid)
    parts += [str(step), str(k)]
    if sub:
        parts.append(sub)
    return ".".join(parts)


def result(status, code=None, event=None, outputs=None):
    assert status in STATUSES
    if status == "REFUSED":
        assert code in REFUSED_CODES
    if status == "INVALID":
        assert code in INVALID_CODES
    return {"status": status, "code": code, "event": event, "outputs": outputs}
