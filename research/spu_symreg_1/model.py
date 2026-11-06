"""Bounded, exact relational experiment; not an ISA or production VM."""
from dataclasses import dataclass

VALUE_SCALES = frozenset((-2, -1, 0, 1, 2))
NORM_SCALES = frozenset((0, 1, 4))
MAX_IDENTITIES = 64
MAX_RELATIONS = 256


@dataclass(frozen=True)
class Relation:
    source: int
    target: int
    kind: str  # value: target = scale * conjugate^flip(source); norm: N(target) = scale*N(source)
    scale: int
    flip: bool = False


class Bank:
    """Immutable value identities, checked base facts and bounded compositions."""
    def __init__(self):
        self.registers = [None] * 8
        self.values = {}
        self.relations = set()
        self.next_id = 0
        self.value_reads = 0

    def write(self, reg, a, b):
        if type(reg) is not int or not 0 <= reg < len(self.registers):
            raise ValueError("register")
        if type(a) is not int or type(b) is not int:
            raise ValueError("integer coefficients required")
        if len(self.values) >= MAX_IDENTITIES:
            raise OverflowError("identity capacity")
        ident = self.next_id
        self.next_id += 1
        self.values[ident] = (a, b)
        self.registers[reg] = ident
        return ident

    def current(self, reg, identity):
        return type(reg) is int and 0 <= reg < 8 and self.registers[reg] == identity

    def _value(self, identity):
        self.value_reads += 1
        return self.values[identity]

    def _record(self, fact):
        if fact not in self.relations and len(self.relations) >= MAX_RELATIONS:
            raise OverflowError("relation capacity")
        self.relations.add(fact)
        return fact

    def check_value(self, source, target, scale, flip=False):
        if type(scale) is not int or scale not in VALUE_SCALES or type(flip) is not bool:
            return None
        a, b = self._value(source)
        actual = self._value(target)
        expected = (scale * a, scale * (-b if flip else b))
        if actual != expected:
            return None
        fact = Relation(source, target, "value", scale, flip)
        return self._record(fact)

    def check_norm(self, source, target, scale):
        if type(scale) is not int or scale not in NORM_SCALES:
            return None
        a, b = self._value(source)
        c, d = self._value(target)
        if c*c - 3*d*d != scale * (a*a - 3*b*b):
            return None
        fact = Relation(source, target, "norm", scale)
        return self._record(fact)

    def compose(self, first, second):
        if first not in self.relations or second not in self.relations:
            return None
        if first.target != second.source or first.kind != second.kind:
            return None
        scale = first.scale * second.scale
        allowed = VALUE_SCALES if first.kind == "value" else NORM_SCALES
        if scale not in allowed:
            return None
        fact = Relation(first.source, second.target, first.kind, scale,
                        first.flip != second.flip if first.kind == "value" else False)
        return self._record(fact)

    def norm_from_value(self, fact):
        if fact not in self.relations or fact.kind != "value" or fact.scale**2 not in NORM_SCALES:
            return None
        result = Relation(fact.source, fact.target, "norm", fact.scale**2)
        return self._record(result)
