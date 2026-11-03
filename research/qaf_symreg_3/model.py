"""Bounded universal joins over trusted predecessor facts; not a security boundary."""
from dataclasses import dataclass
from types import MappingProxyType

from research.qaf_symreg_1.model import Key, Machine, NORM_SCALES, VALUE_SCALES
from research.qaf_symreg_2.model import MAX_DEPTH, MAX_WORK, Proof, Sparse, validate

MAX_BRANCHES = 3
MAX_QUERIES = 16
MAX_BUNDLE_EDGES = 96
MAX_BUNDLE_NODES = 256


def valid_key(key):
    return (type(key) is Key and key.kind in ("value", "norm") and
            type(key.source) is int and type(key.target) is int and
            type(key.k) is int and type(key.flip) is bool and
            ((key.kind == "value" and key.k in VALUE_SCALES and (key.k != 0 or not key.flip)) or
             (key.kind == "norm" and key.k in NORM_SCALES and not key.flip)))


def snapshot(machine):
    # Proofs bind immutable identities, current bindings, exact fact objects and status.
    facts = tuple(sorted(((k.kind, k.source, k.target, k.k, k.flip, id(f))
                          for k, f in machine.facts.items())))
    return (tuple(machine.reg), frozenset(machine.known), facts, tuple(machine.facts.values()), machine.status)


def bundle_nodes(witnesses):
    seen = set(); stack = [f for _, proof in witnesses for f in proof.path]
    while stack:
        f = stack.pop()
        if id(f) in seen:
            continue
        seen.add(id(f))
        if len(seen) > MAX_BUNDLE_NODES:
            return None
        stack.extend(f.parents)
    return len(seen)


class BranchRoster:
    """Explicit declared-feasible branch set; changing it invalidates old joins."""
    def __init__(self, paths):
        self._paths = {}
        self.revision = 0
        for name, machine in paths:
            self.add(name, machine)
        if not self._paths:
            raise ValueError("no feasible branches")

    @property
    def paths(self):
        return MappingProxyType(self._paths)

    def add(self, name, machine):
        if (type(name) is not str or not name or name in self._paths or
                type(machine) is not Machine or len(self._paths) >= MAX_BRANCHES):
            raise ValueError("invalid branch")
        if self._paths and (machine.domain is not next(iter(self._paths.values())).domain or
                            machine.width != next(iter(self._paths.values())).width):
            raise ValueError("branches require a shared identity domain and width")
        self._paths[name] = machine
        self.revision += 1

    def remove(self, name):
        if name not in self._paths or len(self._paths) == 1:
            raise ValueError("invalid removal")
        del self._paths[name]
        self.revision += 1


@dataclass(frozen=True)
class JoinProof:
    proposition: Key
    rule: str
    branch_ids: tuple
    witnesses: tuple
    token: object
    bindings: object = None
    roster_revision: int = 0
    branch_snapshots: tuple = ()
    query_set: frozenset = frozenset()


class Join:
    """Query-directed ALL_FEASIBLE_PATHS; no numerical reads during proof."""
    def __init__(self, roster, candidates, max_work=MAX_WORK, max_edges=MAX_BUNDLE_EDGES):
        candidates = tuple(candidates)
        if (type(roster) is not BranchRoster or not 1 <= len(candidates) <= MAX_QUERIES or
                not all(valid_key(k) for k in candidates) or len(set(candidates)) != len(candidates)):
            raise ValueError("invalid roster or candidate query set")
        if type(max_work) is not int or not 0 <= max_work <= MAX_WORK:
            raise ValueError("work budget")
        if type(max_edges) is not int or not 0 <= max_edges <= MAX_BUNDLE_EDGES:
            raise ValueError("proof budget")
        self.roster = roster
        self.candidates = frozenset(candidates)
        self.max_work, self.max_edges = max_work, max_edges
        self.ids = tuple(sorted(roster.paths))
        self.revision = roster.revision
        self.snapshots = tuple((name, snapshot(roster.paths[name])) for name in self.ids)
        self.token = object()
        self.issued = []
        self.work = 0

    def stable(self):
        return (self.roster.revision == self.revision and tuple(sorted(self.roster.paths)) == self.ids and
                self.snapshots == tuple((name, snapshot(self.roster.paths[name])) for name in self.ids))

    def syntactic(self, key):
        if not self.stable() or not valid_key(key) or key not in self.candidates:
            return "UNKNOWN"
        joined = Machine._merge([self.roster.paths[name] for name in self.ids])
        result, _ = Sparse(joined).prove(key.source, key.target, key.k, key.flip, key.kind == "norm")
        return result

    def prove(self, key, current=None):
        self.work = 0
        if not self.stable() or not valid_key(key) or key not in self.candidates:
            return "UNKNOWN", None
        if len(self.issued) >= MAX_QUERIES:
            return "RESOURCE_LIMIT", None
        if current is not None:
            if (type(current) is not tuple or len(current) != 2 or
                    any(type(r) is not int or not 0 <= r < 8 for r in current)):
                return "UNKNOWN", None
            for name in self.ids:
                machine = self.roster.paths[name]
                if (machine.reg[current[0]], machine.reg[current[1]]) != (key.source, key.target):
                    return "UNKNOWN", None
        witnesses = []
        for name in self.ids:
            remaining = self.max_work - self.work
            if remaining <= 0:
                return "RESOURCE_LIMIT", None
            machine = self.roster.paths[name]
            graph = Sparse(machine, max_work=remaining, max_depth=MAX_DEPTH)
            result, proof = graph.prove(key.source, key.target, key.k, key.flip, key.kind == "norm")
            self.work += graph.work
            if result == "RESOURCE_LIMIT":
                return "RESOURCE_LIMIT", None
            if result != "PROVEN" or not validate(machine, proof, key.source, key.target, key.k, key.flip, key.kind == "norm"):
                return "UNKNOWN", None
            witnesses.append((name, proof))
            if sum(len(w.path) for _, w in witnesses) > self.max_edges or bundle_nodes(witnesses) is None:
                return "RESOURCE_LIMIT", None
        if not self.stable():
            return "UNKNOWN", None
        proof = JoinProof(key, "ALL_FEASIBLE_PATHS", self.ids, tuple(witnesses), self.token, current,
                          self.revision, self.snapshots, self.candidates)
        self.issued.append(proof)
        return "PROVEN", proof

    def validate(self, proof):
        if (not self.stable() or type(proof) is not JoinProof or proof.token is not self.token or
                not any(p is proof for p in self.issued) or proof.rule != "ALL_FEASIBLE_PATHS" or
                not valid_key(proof.proposition) or proof.proposition not in self.candidates or proof.branch_ids != self.ids or
                proof.roster_revision != self.revision or proof.branch_snapshots is not self.snapshots or
                proof.query_set is not self.candidates or
                type(proof.witnesses) is not tuple or
                any(type(w) is not tuple or len(w) != 2 or type(w[0]) is not str or type(w[1]) is not Proof for w in proof.witnesses) or
                tuple(n for n, _ in proof.witnesses) != self.ids):
            return False
        if proof.bindings is not None and (type(proof.bindings) is not tuple or len(proof.bindings) != 2 or
                any(type(r) is not int or not 0 <= r < 8 for r in proof.bindings)):
            return False
        key = proof.proposition
        if any(type(w.path) is not tuple for _, w in proof.witnesses):
            return False
        if sum(len(w.path) for _, w in proof.witnesses) > self.max_edges:
            return False
        for name, witness in proof.witnesses:
            m = self.roster.paths[name]
            if proof.bindings is not None and (m.reg[proof.bindings[0]], m.reg[proof.bindings[1]]) != (key.source, key.target):
                return False
            if not validate(m, witness, key.source, key.target, key.k, key.flip, key.kind == "norm"):
                return False
        return bundle_nodes(proof.witnesses) is not None
