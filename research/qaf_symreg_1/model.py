"""Finite relational discovery model; exact integers, not an ISA emulator."""
from collections import deque
from dataclasses import dataclass
from types import MappingProxyType

VALUE_SCALES = frozenset((-2, -1, 0, 1, 2))
NORM_SCALES = frozenset((-4, -2, -1, 0, 1, 2, 4))
MAX_VALUES, MAX_FACTS = 64, 256


@dataclass(frozen=True)
class Key:
    kind: str                 # value: target = k * conjugate^flip(source)
    source: int               # norm: N(target) = k * N(source)
    target: int
    k: int
    flip: bool = False


@dataclass(frozen=True)
class Fact:
    key: Key
    rule: str
    parents: tuple = ()       # immutable provenance DAG, not expressions
    valid: bool = True


class Domain:
    def __init__(self):
        self.values = {}
        self.reads = 0

    def new(self, a, b):
        if len(self.values) >= MAX_VALUES:
            raise OverflowError("value capacity")
        ident = len(self.values)
        self.values[ident] = (a, b)
        return ident

    def read(self, ident):
        self.reads += 1
        return self.values[ident]


class Machine:
    def __init__(self, domain=None, width=64):
        self.domain = domain or Domain()
        self.width = width
        self.reg = [None] * 8
        self.known = set()
        self.facts = {}
        self.inferences = 0
        self.status = None  # UNKNOWN initially, not a modeled reset value

    def fork(self):
        other = Machine(self.domain, self.width)
        other.reg = self.reg.copy()
        other.known = self.known.copy()
        other.facts = self.facts.copy()
        other.status = self.status
        return other

    def branch(self, condition):
        """None means both paths feasible; a bool chooses exactly one."""
        if condition is not None and type(condition) is not bool:
            raise ValueError("condition must be bool or unknown")
        return Branches(self, condition)

    @staticmethod
    def _merge(branches):
        if not branches or any(b.domain is not branches[0].domain or b.width != branches[0].width for b in branches):
            raise ValueError("branches must share a domain and width")
        out = Machine(branches[0].domain, branches[0].width)
        statuses = [b.status for b in branches]
        out.status = statuses[0] if all(s == statuses[0] for s in statuses) else None
        out.known = set.intersection(*(b.known for b in branches))
        for i in range(8):
            bindings = [b.reg[i] for b in branches]
            out.reg[i] = bindings[0] if all(x == bindings[0] for x in bindings) else None
        common = set(branches[0].facts)
        for b in branches[1:]:
            common.intersection_update(b.facts)
        for key in sorted(common, key=lambda k: (k.kind, k.source, k.target, k.k, k.flip)):
            out.facts[key] = Fact(key, "merge_all_feasible", tuple(b.facts[key] for b in branches))
        return out

    def write(self, reg, a, b):
        if type(reg) is not int or not 0 <= reg < 8:
            raise ValueError("register")
        if type(a) is not int or type(b) is not int:
            return "INVALID"
        limit = 1 << (self.width - 1)
        if not (-limit <= a < limit and -limit <= b < limit):
            return "OVERFLOW"
        ident = self.domain.new(a, b)
        self.known.add(ident)
        self.reg[reg] = ident
        return "OK"

    def identity(self, reg):
        if type(reg) is not int or not 0 <= reg < 8:
            raise ValueError("register")
        return self.reg[reg]

    def multiply(self, dst, left, right):
        """Integer d=1 subset of SMUL; status changes on refusal, destination does not."""
        if any(type(r) is not int or not 0 <= r < 8 for r in (dst, left, right)):
            raise ValueError("register")
        x, y = self.reg[left], self.reg[right]
        if x is None or y is None:
            self.status = "INVALID"
            return self.status
        a, b = self.domain.read(x); c, d = self.domain.read(y)
        result = self.write(dst, a*c + 3*b*d, a*d + b*c)
        self.status = result
        return result

    def _known_pair(self, source, target):
        return (type(source) is int and type(target) is int and
                source in self.known and target in self.known)

    def _store(self, fact):
        if fact.key not in self.facts and len(self.facts) >= MAX_FACTS:
            raise OverflowError("fact capacity")
        return self.facts.setdefault(fact.key, fact)

    def admit_value(self, source, target, k=1, flip=False):
        if not self._known_pair(source, target) or type(k) is not int or k not in VALUE_SCALES or type(flip) is not bool:
            return None
        a, b = self.domain.read(source); c, d = self.domain.read(target)
        if (c, d) != (k*a, -k*b if flip else k*b):
            return None
        return self._store(Fact(Key("value", source, target, k, flip if k else False), "concrete_checked"))

    def admit_norm(self, source, target, k=1):
        if not self._known_pair(source, target) or type(k) is not int or k not in NORM_SCALES:
            return None
        a, b = self.domain.read(source); c, d = self.domain.read(target)
        if c*c-3*d*d != k*(a*a-3*b*b):
            return None
        return self._store(Fact(Key("norm", source, target, k), "concrete_checked"))

    def compose(self, first, second):
        # Only actual stored objects can be parents; equal-looking fabricated records are refused.
        if self.facts.get(first.key) is not first or self.facts.get(second.key) is not second:
            return None
        x, y = first.key, second.key
        if x.target != y.source or x.kind != y.kind:
            return None
        k = x.k * y.k
        if k not in (VALUE_SCALES if x.kind == "value" else NORM_SCALES):
            return None
        flip = (x.flip != y.flip) if x.kind == "value" and k else False
        self.inferences += 1
        return self._store(Fact(Key(x.kind, x.source, y.target, k, flip), "compose", (first, second)))

    def project_norm(self, fact):
        if self.facts.get(fact.key) is not fact or fact.key.kind != "value":
            return None
        f = fact.key
        self.inferences += 1
        return self._store(Fact(Key("norm", f.source, f.target, f.k*f.k), "norm_of_value", (fact,)))

    def query(self, source_reg, target_reg, kind, k=1, flip=False, concrete=False):
        if any(type(r) is not int or not 0 <= r < 8 for r in (source_reg, target_reg)):
            raise ValueError("register")
        if kind not in ("value", "norm") or type(k) is not int or k not in (VALUE_SCALES if kind == "value" else NORM_SCALES) or type(flip) is not bool or (kind == "norm" and flip):
            raise ValueError("unsupported query")
        src, dst = self.reg[source_reg], self.reg[target_reg]
        if src is None or dst is None:
            return "UNKNOWN", ()
        goal = Key(kind, src, dst, k, flip if k else False)
        if src == dst and k == 1 and not flip:
            return "PROVEN", (Fact(goal, "identity"),)
        # Bounded closure over trusted facts, with a visited set. Does not inspect values.
        queue = deque([(src, 1, False, ())]); seen = {(src, 1, False)}
        while queue:
            here, scale, conj, proof = queue.popleft()
            for f in self.facts.values():
                self.inferences += 1
                edge = f.key
                if edge.kind != kind or edge.source != here:
                    continue
                nk = scale * edge.k
                if nk not in (VALUE_SCALES if kind == "value" else NORM_SCALES):
                    continue
                nf = (conj != edge.flip) if kind == "value" and nk else False
                path = proof + (f,)
                if (edge.target, nk, nf) == (dst, goal.k, goal.flip):
                    return "PROVEN", path
                state = (edge.target, nk, nf)
                if state not in seen:
                    seen.add(state); queue.append((*state, path))
        if concrete:
            a, b = self.domain.read(src); c, d = self.domain.read(dst)
            holds = ((c, d) == (k*a, -k*b if flip else k*b)) if kind == "value" else (c*c-3*d*d == k*(a*a-3*b*b))
            if not holds:
                return "DISPROVEN", ()
        return "UNKNOWN", ()


class Branches:
    """Join automatically includes every path declared feasible at branch creation."""
    def __init__(self, machine, condition):
        choices = (False, True) if condition is None else (condition,)
        self.paths = MappingProxyType({choice: machine.fork() for choice in choices})

    def join(self):
        return Machine._merge(list(self.paths.values()))
