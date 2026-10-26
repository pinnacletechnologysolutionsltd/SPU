"""Adversarial boundary checks for the proposed software handshake."""

from sparse_jet_protocol import Protocol, check_trace
from sparse_jet_reference import P, ZERO, dense, multiply, pairs
from sparse_jet_model import result_tag


def run_controls():
    n = 2
    a = [(1, 0, 0, 0)] * 3
    b = [(2, 0, 0, 0)] * 3
    request = (a, b, (0, 2), (0, 2), True)
    expected = dense(a, b)
    model = Protocol(n)
    assert model.tick(start=request)["accepted"]
    a[0] = ZERO  # Acceptance captures source data, including aliased caller lists.
    pending = None
    for _ in range(100):
        event = model.tick(start=request, response=pending)
        assert not event["accepted"]  # Busy starts and retirement-edge start ignored.
        pending = multiply(event["issue"][3], event["issue"][4]) if event["issue"] else None
        if event["done"]:
            assert event["result"] == expected
            break
    else:
        raise AssertionError("no completion")
    # Next edge accepts a new empty operation, never completing on that edge.
    zero = (ZERO,) * 3
    event = model.tick(start=(zero, zero, (3, 0), (3, 0), True))
    assert event["accepted"] and event["busy"] and not event["done"]
    event = model.tick()
    assert event["done"] and not event["busy"] and event["issue"] is None
    assert event["result"] == zero and event["tag"] == (3, 0)
    assert not model.tick(response=(1, 0, 0, 0))["done"]
    assert model.result == zero  # Unsolicited idle response cannot write.
    model.tick(start=(zero, zero, (0, 2), (0, 2), False))
    event = model.tick(reset=True, start=request, response=(1, 0, 0, 0))
    assert not any(event[k] for k in ("accepted", "busy", "done", "issue"))
    assert event["result"] == zero and event["tag"] == (3, 0)
    return 5


def drive(n, request, latency, cancel=None):
    model, trace, pending, delay = Protocol(n), [], None, 0
    a, b, at, bt, mul = request
    expected = dense(a, b) if mul else tuple(tuple((x + y) % P for x, y in zip(u, v)) for u, v in zip(a, b))
    # Independent rectangular enumeration; output tags checked separately below.
    expected_pairs = pairs(n, at, bt) if mul else []
    for cycle in range(500):
        state = model.state
        reset = cancel == state
        response = pending if pending is not None and delay == 0 else None
        if response is not None:
            pending = None
        event = model.tick(start=request if cycle == 0 or state != "IDLE" else None,
                           response=response, reset=reset)
        trace.append(event)
        if reset:
            pending = None  # Fabric cancellation is part of reset ownership contract.
            trace.append(model.tick(response=ZERO))  # Stray idle response cannot commit.
            break
        if event["issue"] is not None:
            assert pending is None
            pending, delay = multiply(event["issue"][3], event["issue"][4]), latency
        elif pending is not None:
            delay -= 1
        if event["done"]:
            assert not model.tick()["done"], "completion pulse wider than one cycle"
            break
    else:
        raise AssertionError("bounded protocol did not complete")
    check_trace(trace, expected_pairs, expected, result_tag(n, at, bt, mul))
    return trace

