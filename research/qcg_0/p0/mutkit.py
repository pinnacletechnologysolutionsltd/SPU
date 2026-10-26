"""Mutant harness helpers: temporary attribute patches and the Cell A / Cell B / sequential detectors."""
from contextlib import contextmanager
import campaign, refs
from events import P4096


@contextmanager
def patched(obj, name, new):
    old = getattr(obj, name)
    setattr(obj, name, new)
    try:
        yield old
    finally:
        setattr(obj, name, old)


def a_bad(cls, profile=P4096):
    """EQ-3 mismatches for one Cell A arm class."""
    chk = lambda o, row: [tuple(x) for x in o["values"]] == row[1] and o["ok"] == row[2]     # noqa: E731
    return campaign._run(cls(profile, refs.source("PH5")), refs.cell_a_ref(), chk)


def b_bad(cls, profile=P4096):
    src = dict(refs.source("PH3"), phi=refs.phi()["phi"])
    chk = lambda o, row: [tuple(x) for x in o["values"]] == row[1]                         # noqa: E731
    return campaign._run(cls(profile, src), refs.cell_b_ref(), chk)


def seq_bad(cls, tape="S1", curve="PH3", profile=P4096):
    a = cls(profile, refs.source(curve), tape)
    a.prepare()
    return campaign.seq_ok(a.run_tape(), refs.seq_ref(curve), tape, curve)


def killed(fn, *a):
    """True when the detector raises AssertionError (a conformance test failing) or returns a falsy 'passes' value."""
    try:
        return not fn(*a)
    except AssertionError:
        return True
