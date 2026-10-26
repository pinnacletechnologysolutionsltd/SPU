"""Proposed completion contract model; shared fabric must reset/drain with it."""

from lib.a31_field import a31_add
from sparse_jet_model import result_tag, schedule, validate
from sparse_jet_reference import ZERO


class Protocol:
    def __init__(self, n):
        self.n = n
        self.clear()

    def clear(self):
        self.state = "IDLE"
        self.result = tuple([ZERO] * (self.n + 1))
        self.tag = (self.n + 1, 0)
        self.work = [ZERO] * (self.n + 1)
        self.todo = []
        self.index = 0

    def tick(self, start=None, response=None, reset=False):
        done, issued, accepted = False, None, False
        if reset:
            self.clear()
        elif self.state == "IDLE":
            if start is not None:
                a, b, at, bt, mul = start
                validate(self.n, a, at)
                validate(self.n, b, bt)
                self.a, self.b = tuple(map(tuple, a)), tuple(map(tuple, b))
                self.next_tag = result_tag(self.n, at, bt, mul)
                self.todo = schedule(self.n, at, bt) if mul else []
                self.work = [ZERO] * (self.n + 1) if mul else [a31_add(x, y) for x, y in zip(a, b)]
                self.index = 0
                self.state = "ISSUE" if self.todo else "RETIRE"
                accepted = True
        elif self.state == "ISSUE":
            k, i, j = self.todo[self.index]
            issued = (k, i, j, self.a[i], self.b[j])
            self.state = "WAIT"
        elif self.state == "WAIT":
            if response is not None:
                validate(0, (response,), (0, 0))
                k = self.todo[self.index][0]
                self.work[k] = a31_add(self.work[k], response)
                self.index += 1
                self.state = "ISSUE" if self.index < len(self.todo) else "RETIRE"
        elif self.state == "RETIRE":
            self.result, self.tag = tuple(self.work), self.next_tag
            self.state, done = "IDLE", True
        return {"busy": self.state != "IDLE", "done": done, "issue": issued,
                "accepted": accepted, "reset": reset, "response": response,
                "result": self.result, "tag": self.tag}


def check_trace(trace, expected_pairs, expected_result, expected_tag):
    """Independent event scoreboard for one accepted operation or reset cancellation."""
    active, pending, issued, replies, completions, canceled = False, False, [], 0, 0, False
    for event in trace:
        if event["reset"]:
            assert not event["busy"] and not event["done"] and event["issue"] is None
            canceled = active
            active, pending = False, False
            continue
        if event["accepted"]:
            assert not active and not event["done"] and event["busy"]
            active = True
        if event["response"] is not None and pending:
            pending = False
            replies += 1
        if event["issue"] is not None:
            assert active and not pending
            pending = True
            issued.append(event["issue"][:3])
            assert issued == expected_pairs[:len(issued)]
        if event["done"]:
            assert active and not pending and not event["busy"]
            assert issued == expected_pairs and replies == len(expected_pairs)
            assert event["result"] == expected_result and event["tag"] == expected_tag
            completions += 1
            active = False
        elif active:
            assert event["busy"], "busy dropped before completion"
    assert not active and completions == (0 if canceled else 1)
