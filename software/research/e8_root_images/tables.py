"""Immutable ordered roots, simple-basis coefficients and left-reflection table."""
from bisect import bisect_left
from dataclasses import dataclass
from functools import lru_cache
import hashlib
import json
from ..lattice_symmetry.roots import roots
from ..lattice_symmetry.fixtures import simple_roots
from .linear import columns, inverse, apply, integers


def fingerprint(data):
    return hashlib.sha256(json.dumps(data,separators=(',',':')).encode()).hexdigest()


@dataclass(frozen=True)
class Context:
    roots: tuple
    basis: tuple
    gram: tuple
    inverse_basis: tuple
    coefficients: tuple
    reflections: tuple
    basis_ids: tuple
    positive_ids: tuple
    root_hash: str
    basis_hash: str

    def index(self, vector):
        vector = tuple(vector)
        i = bisect_left(self.roots,vector)
        if i == len(self.roots) or self.roots[i] != vector:
            raise ValueError('NOT_AN_E8_ROOT')
        return i


@lru_cache(maxsize=1)
def context():
    ordered, basis = roots('E8'), simple_roots('E8')
    if len(ordered) != 240 or tuple(sorted(set(ordered))) != ordered:
        raise ValueError('ROOT_TABLE_ORDER')
    inv = inverse(columns(basis))
    coefficients = tuple(integers(apply(inv,x)) for x in ordered)
    gram = tuple(tuple(sum(a*b for a,b in zip(x,y))//4 for y in basis) for x in basis)
    def index(vector):
        i = bisect_left(ordered,vector)
        if i == len(ordered) or ordered[i] != tuple(vector):
            raise ValueError('REFLECTION_CLOSURE')
        return i
    reflections = []
    for alpha in basis:
        row = []
        for x in ordered:
            dot = sum(a*b for a,b in zip(x,alpha))
            if dot % 4:
                raise ValueError('REFLECTION_DIVISIBILITY')
            row.append(index(tuple(a-dot//4*b for a,b in zip(x,alpha))))
        reflections.append(tuple(row))
    positive = tuple(i for i,c in enumerate(coefficients) if all(v >= 0 for v in c) and any(c))
    negative = tuple(i for i,c in enumerate(coefficients) if all(v <= 0 for v in c) and any(c))
    if len(positive) != 120 or len(negative) != 120:
        raise ValueError('ROOT_SIGN_PARTITION')
    basis_aliases = tuple(ordered[index(x)] for x in basis)
    return Context(ordered,basis_aliases,gram,inv,coefficients,tuple(reflections),
                   tuple(index(x) for x in basis),positive,fingerprint(ordered),fingerprint(basis))


def storage_inventory(ctx):
    # Logical fixed layout, not measured Python dictionary/object memory.
    arrays = dict(roots=64+240*(64+8*64), basis_ids=64+8*8,
                  reflection_ids=64+8*(64+240*8), gram=64+8*(64+8*64),
                  inverse_basis=64+8*(64+8*128),
                  root_coefficients=64+240*(64+8*64), positive_ids=64+120*8,
                  context_hashes=2*256, context_header=32)
    return dict(static_objects_bits=arrays, static_total_bits=sum(arrays.values()),
                descriptor_payload_bits=64, descriptor_serialized_bytes=76,
                root_search='bisect on existing ordered roots; no additional hash lookup table',
                workspace_peak='UNMEASURED', python_memory='UNMEASURED',
                arithmetic_work='NOT INSTRUMENTED', fixed_slots='proposed signed64 / rational128')
