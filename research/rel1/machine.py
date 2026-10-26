"""REL-1 bounded machine, mirroring SSM-7 semantics over metric states. Six opcodes, immutable
handles, atomic failed commands, certificate dependency checks. Bounds: 32 commands, 8 transitions,
9 states, 36 certificates, 9 observations. UNRESOLVED = the command could not decide, not an error.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from fractions import Fraction as Fr

import exact as X
import geometry as G
from geometry import DependencyChanged
from field import QF

OPS = ("TRANSFORM", "MOVE", "VALIDATE", "QUERY", "REUSE", "OBSERVE")


class Refusal(ValueError):
    pass


def need(c, why):
    if not c:
        raise Refusal(why)


def num(v):
    return type(v) in (int, Fr)


class Machine:
    def __init__(self, backend, d=1, lemma=False, state_capacity=9, certificate_capacity=36,
                 skip_dependency_check=False):
        need(type(state_capacity) is int and 1 <= state_capacity <= 9, "BAD_CAPACITY")
        need(type(certificate_capacity) is int and 0 <= certificate_capacity <= 36, "BAD_CAPACITY")
        self.b, self.d, self.lemma, self.skip = backend, d, lemma, skip_dependency_check
        self.cap_s, self.cap_c = state_capacity, certificate_capacity
        self.cost, self.count = defaultdict(X.Ops), Counter()
        self.states = (backend.admit(d, self.cost["ADMIT"], self.count),)
        self.current, self.certs, self.obs, self.steps, self.transitions = 0, {}, {}, 0, 0

    def snapshot(self):
        return (self.current, self.transitions, tuple(s.gid for s in self.states),
                tuple(sorted((k, (c.name, c.gid, c.value, c.basis)) for k, c in self.certs.items())),
                tuple(sorted((h, r[0]) for h, r in self.obs.items())))

    def sizes(self):
        return [self.b.size(s) for s in self.states]

    def step(self, cmd):
        if self.steps == 32:
            return {"status": "REFUSED", "error": "COMMAND_LIMIT"}
        self.steps += 1
        try:
            need(type(cmd) is tuple and cmd and type(cmd[0]) is str, "BAD_COMMAND")
            op = cmd[0]
            need(op in OPS, "BAD_OPCODE")
            need(len(cmd) == {"MOVE": 3, "REUSE": 3, "QUERY": 3}.get(op, 2), "BAD_COMMAND")
            ops = self.cost[op]
            if op in ("TRANSFORM", "MOVE"):
                return self._edit(op, cmd, ops)
            h = cmd[1]
            need(type(h) is int and 0 <= h < len(self.states), "BAD_HANDLE")
            if op == "QUERY":
                need(cmd[2] in G.DECLARED, "BAD_ARGUMENT")
                v = self.b.compute(self.states[h], cmd[2], ops)
                return ({"status": "UNRESOLVED", "reason": "NOT_AN_EQUILIBRIUM"} if v is None
                        else {"status": "EXACT", "value": v})
            if op == "REUSE":
                return self._reuse(h, cmd[2], ops)
            need(h == self.current, "STALE_STATE")
            if op == "VALIDATE":
                missing = sum((h, n) not in self.certs for n in G.DECLARED)
                need(len(self.certs) + missing <= self.cap_c, "CERTIFICATE_CAPACITY")
                s = self.states[h]
                vals = [self.b.compute(s, n, ops) for n in G.DECLARED]
                need(all(v is True for v in vals), "INVALID_STATE")
                for n in G.DECLARED:
                    self.certs[(h, n)] = G.Cert(n, s.gid, True, "computed")
                return {"status": "VALID", "state_id": s.gid}
            miss = tuple(n for n in G.DECLARED if (h, n) not in self.certs)
            if miss:
                return {"status": "UNRESOLVED", "reason": "CURRENT_CERTIFICATES_MISSING", "missing": miss}
            s = self.states[h]
            try:
                pts = self.b.observe(s, self.d, ops, self.count)
            except ValueError:
                raise Refusal("OUT_OF_FIELD") from None
            rec = (s.gid, tuple(tuple(G.key(c) for c in p) for p in pts))
            self.obs[h] = rec
            return {"status": "EXACT", "receipt": rec}
        except Refusal as e:
            return {"status": "REFUSED", "error": str(e)}
        except OverflowError:
            return {"status": "REFUSED", "error": "ARITHMETIC_REFUSAL"}

    def _edit(self, op, cmd, ops):
        a = cmd[1]
        if op == "TRANSFORM":
            need(type(a) is tuple and len(a) == 3 and all(type(r) is tuple and len(r) == 3 and
                                                          all(num(v) for v in r) for r in a), "BAD_ARGUMENT")
        else:
            off = cmd[2]
            need(type(a) is tuple and 1 <= len(a) <= 2 and len(set(a)) == len(a) and
                 all(type(i) is int and 0 <= i < 12 for i in a), "BAD_ARGUMENT")
            need(type(off) is tuple and len(off) == 3 and all(num(v) for v in off) and
                 any(v != 0 for v in off), "BAD_ARGUMENT")
        need(self.transitions < 8, "TRANSITION_LIMIT")
        need(len(self.states) < self.cap_s, "STATE_CAPACITY")
        try:
            if op == "TRANSFORM":
                M = tuple(tuple(Fr(v) for v in r) for r in a)
                child = self.b.transform(self.states[self.current], M, self.d, ops, self.count)
            else:
                child = self.b.move(self.states[self.current], a, tuple(Fr(v) for v in cmd[2]),
                                    self.d, ops, self.count)
        except ValueError as e:
            raise Refusal("OUT_OF_FIELD" if str(e) == "OUT_OF_FIELD" else "INADMISSIBLE_EDIT") from None
        self.states += (child,)
        self.current, self.transitions = len(self.states) - 1, self.transitions + 1
        return {"status": "COMMITTED", "handle": self.current, "state_id": child.gid}

    def _reuse(self, h, name, ops):
        need(name in G.DECLARED, "BAD_ARGUMENT")
        old = self.certs.get((h, name))
        if old is None:
            return {"status": "UNRESOLVED", "reason": "SOURCE_CERTIFICATE_MISSING"}
        dest = (self.current, name)
        need(dest in self.certs or len(self.certs) < self.cap_c, "CERTIFICATE_CAPACITY")
        need(old.gid == self.states[h].gid, "INVALID_CERTIFICATE")
        try:
            new = self.b.reuse(old, self.states[h], self.states[self.current], self.lemma, ops, h,
                               self.skip)
        except DependencyChanged:
            raise Refusal("DEPENDENCIES_CHANGED") from None
        self.certs[dest] = new
        return {"status": "REUSED", "name": name, "state_id": new.gid, "basis": new.basis}
