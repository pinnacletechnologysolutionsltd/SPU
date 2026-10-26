#!/usr/bin/env python3
"""Tensegrity balancer oracle for the SPU-13 state-machine harness.

The model is deliberately exact: rational coefficients, Q(sqrt(3)) sign
checks, and Z[phi] icosahedral coordinates. It contains no floating point and
no transcendental approximations.
"""

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Dict, List, Optional


def _gcd(a: int, b: int) -> int:
    a = abs(a)
    b = abs(b)
    while b:
        a, b = b, a % b
    return a or 1


class Fraction:
    """Small exact rational type used to keep this oracle self-contained."""

    __slots__ = ("num", "den")

    def __init__(self, num: int, den: int = 1):
        if den == 0:
            raise ZeroDivisionError
        if den < 0:
            num = -num
            den = -den
        g = _gcd(num, den)
        self.num = num // g
        self.den = den // g

    def __add__(self, other):
        other = _frac(other)
        return Fraction(self.num * other.den + other.num * self.den,
                        self.den * other.den)

    def __sub__(self, other):
        other = _frac(other)
        return Fraction(self.num * other.den - other.num * self.den,
                        self.den * other.den)

    def __mul__(self, other):
        other = _frac(other)
        return Fraction(self.num * other.num, self.den * other.den)

    def __truediv__(self, other):
        other = _frac(other)
        return Fraction(self.num * other.den, self.den * other.num)

    def __neg__(self):
        return Fraction(-self.num, self.den)

    def __eq__(self, other):
        other = _frac(other)
        return self.num == other.num and self.den == other.den

    def __lt__(self, other):
        other = _frac(other)
        return self.num * other.den < other.num * self.den

    def __le__(self, other):
        return self == other or self < other

    def __gt__(self, other):
        other = _frac(other)
        return other < self

    def __ge__(self, other):
        return self == other or self > other

    def __bool__(self):
        return self.num != 0

    def __repr__(self):
        return f"{self.num}/{self.den}" if self.den != 1 else str(self.num)

    def __hash__(self):
        return hash((self.num, self.den))


def _frac(value) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value)
    return NotImplemented


ZERO = Fraction(0)
ONE = Fraction(1)


@dataclass(frozen=True)
class RationalSurd:
    """Exact P + Q*sqrt(3)."""

    p: Fraction
    q: Fraction

    @staticmethod
    def zero() -> "RationalSurd":
        return RationalSurd(ZERO, ZERO)

    @staticmethod
    def one() -> "RationalSurd":
        return RationalSurd(ONE, ZERO)

    @staticmethod
    def from_int(n: int) -> "RationalSurd":
        return RationalSurd(Fraction(n), ZERO)

    def __add__(self, other: "RationalSurd") -> "RationalSurd":
        return RationalSurd(self.p + other.p, self.q + other.q)

    def __sub__(self, other: "RationalSurd") -> "RationalSurd":
        return RationalSurd(self.p - other.p, self.q - other.q)

    def __mul__(self, other):
        if isinstance(other, int):
            return RationalSurd(self.p * other, self.q * other)
        if isinstance(other, Fraction):
            return RationalSurd(self.p * other, self.q * other)
        if not isinstance(other, RationalSurd):
            return NotImplemented
        return RationalSurd(
            self.p * other.p + Fraction(3) * self.q * other.q,
            self.p * other.q + self.q * other.p,
        )

    def __rmul__(self, scalar):
        return self * scalar

    def __neg__(self):
        return RationalSurd(-self.p, -self.q)

    def div_by(self, n: int) -> "RationalSurd":
        return RationalSurd(self.p / n, self.q / n)

    def is_zero(self) -> bool:
        return self.p == 0 and self.q == 0

    def is_positive(self) -> bool:
        """Return P + Q*sqrt(3) > 0 using integer comparisons only."""
        p = self.p
        q = self.q
        if p >= 0 and q >= 0:
            return not (p == 0 and q == 0)
        if p <= 0 and q <= 0:
            return False

        p2 = p * p
        three_q2 = Fraction(3) * q * q
        assert p2 != three_q2, "nonzero rational equality to sqrt(3) boundary"
        if p > 0 and q < 0:
            return p2 > three_q2
        return three_q2 > p2


@dataclass(frozen=True)
class Phi:
    """Exact a + b*phi with phi^2 = phi + 1."""

    a: Fraction = ZERO
    b: Fraction = ZERO

    @staticmethod
    def from_int(n: int) -> "Phi":
        return Phi(Fraction(n), ZERO)

    def __add__(self, other: "Phi") -> "Phi":
        return Phi(self.a + other.a, self.b + other.b)

    def __sub__(self, other: "Phi") -> "Phi":
        return Phi(self.a - other.a, self.b - other.b)

    def __mul__(self, other):
        if isinstance(other, int):
            return Phi(self.a * other, self.b * other)
        if isinstance(other, Fraction):
            return Phi(self.a * other, self.b * other)
        if not isinstance(other, Phi):
            return NotImplemented
        return Phi(
            self.a * other.a + self.b * other.b,
            self.a * other.b + self.b * other.a + self.b * other.b,
        )

    def __rmul__(self, scalar):
        return self * scalar

    def __truediv__(self, other: "Phi") -> "Phi":
        if not isinstance(other, Phi):
            return NotImplemented
        norm = other.a * other.a + other.a * other.b - other.b * other.b
        if norm == 0:
            raise ZeroDivisionError
        conj = Phi(other.a + other.b, -other.b)
        return (self * conj) * (ONE / norm)

    def __neg__(self):
        return Phi(-self.a, -self.b)

    def __eq__(self, other):
        return isinstance(other, Phi) and self.a == other.a and self.b == other.b

    def is_zero(self) -> bool:
        return self.a == 0 and self.b == 0

    def is_positive(self) -> bool:
        """Return a + b*phi > 0 exactly via (2a+b) + b*sqrt(5)."""
        r = self.a * 2 + self.b
        s = self.b
        if r >= 0 and s >= 0:
            return not (r == 0 and s == 0)
        if r <= 0 and s <= 0:
            return False
        r2 = r * r
        five_s2 = Fraction(5) * s * s
        assert r2 != five_s2, "nonzero rational equality to sqrt(5) boundary"
        if r > 0 and s < 0:
            return r2 > five_s2
        return five_s2 > r2

    def __repr__(self):
        return f"({self.a}+{self.b}phi)"


PHI_ZERO = Phi.from_int(0)
PHI_ONE = Phi.from_int(1)
PHI_UNIT = Phi(ZERO, ONE)


@dataclass(frozen=True)
class Vec3Phi:
    """Exact Cartesian vector over Z[phi]."""

    x: Phi
    y: Phi
    z: Phi

    def __sub__(self, other: "Vec3Phi") -> "Vec3Phi":
        return Vec3Phi(self.x - other.x, self.y - other.y, self.z - other.z)

    def quadrance_to(self, other: "Vec3Phi") -> Phi:
        d = self - other
        return d.x * d.x + d.y * d.y + d.z * d.z

    @staticmethod
    def origin() -> "Vec3Phi":
        return Vec3Phi(PHI_ZERO, PHI_ZERO, PHI_ZERO)


class EdgeType(IntEnum):
    CABLE = 0
    STRUT = 1
    GAP = 2


@dataclass
class Edge:
    node_a: int
    node_b: int
    edge_type: EdgeType
    rest_quadrance: Optional[Phi] = None


class GridState(IntEnum):
    UNTAGGED = 0
    MAIN = 1
    CONJ = 2


class TensegrityState(IntEnum):
    IDLE = 0
    CONFIGURING = 1
    BALANCED = 2
    ROTATING = 3
    FAULT_CABLE_SLACK = 4
    FAULT_STRUT_COLLISION = 5
    FAULT_GRID_MISMATCH = 6
    FAULT_TOPOLOGY = 7
    FAULT_NOT_IN_EQUILIBRIUM = 8
    FAULT_STRUT_INTERSECTION = 9


class TensegrityFault(IntEnum):
    NONE = 0
    CABLE_SLACK = 1
    STRUT_COLLISION = 2
    GRID_MISMATCH = 3
    TOPOLOGY_ERROR = 4
    NOT_IN_EQUILIBRIUM = 5
    STRUT_INTERSECTION = 6


@dataclass
class EquilibriumResult:
    ok: bool
    densities: List[Phi] = field(default_factory=list)


@dataclass
class TensegritySystem:
    nodes: List[Vec3Phi] = field(default_factory=list)
    grid_states: List[GridState] = field(default_factory=list)
    edges: List[Edge] = field(default_factory=list)
    state: TensegrityState = TensegrityState.IDLE
    fault: TensegrityFault = TensegrityFault.NONE
    fault_detail: str = ""
    equilibrium_densities: List[Phi] = field(default_factory=list)

    def guard_valid_topology(self) -> bool:
        if len(self.nodes) < 6:
            self.fault_detail = "Fewer than 6 nodes"
            return False
        structural = sum(1 for e in self.edges
                         if e.edge_type in (EdgeType.STRUT, EdgeType.GAP))
        if structural < 6:
            self.fault_detail = f"Only {structural} structural edges (need >=6)"
            return False
        visited = {0} if self.nodes else set()
        changed = True
        while changed:
            changed = False
            for e in self.edges:
                if e.node_a in visited and e.node_b not in visited:
                    visited.add(e.node_b)
                    changed = True
                elif e.node_b in visited and e.node_a not in visited:
                    visited.add(e.node_a)
                    changed = True
        if len(visited) != len(self.nodes):
            self.fault_detail = f"Disconnected: {len(visited)}/{len(self.nodes)} reachable"
            return False
        return True

    def guard_struts_separated(self) -> bool:
        strut_count: Dict[int, int] = {}
        for e in self.edges:
            if e.edge_type != EdgeType.STRUT:
                continue
            if e.node_a == e.node_b:
                self.fault_detail = f"Strut {e.node_a}-{e.node_b} has zero length"
                return False
            if self.nodes[e.node_a].quadrance_to(self.nodes[e.node_b]).is_zero():
                self.fault_detail = f"Strut {e.node_a}-{e.node_b} collapsed"
                return False
            strut_count[e.node_a] = strut_count.get(e.node_a, 0) + 1
            strut_count[e.node_b] = strut_count.get(e.node_b, 0) + 1
        for node, count in strut_count.items():
            if count > 1:
                self.fault_detail = f"Node {node} touches {count} struts"
                return False
        return True

    def guard_struts_disjoint_interior(self) -> bool:
        struts = [e for e in self.edges if e.edge_type == EdgeType.STRUT]
        for i, a in enumerate(struts):
            for b in struts[i + 1:]:
                if {a.node_a, a.node_b} & {b.node_a, b.node_b}:
                    continue
                if segments_contact_closed(
                        self.nodes[a.node_a], self.nodes[a.node_b],
                        self.nodes[b.node_a], self.nodes[b.node_b]):
                    self.fault_detail = (
                        f"Struts {a.node_a}-{a.node_b} and "
                        f"{b.node_a}-{b.node_b} touch or intersect")
                    return False
        return True

    def guard_cables_taut(self) -> bool:
        for e in self.edges:
            if e.edge_type not in (EdgeType.CABLE, EdgeType.GAP):
                continue
            q = self.nodes[e.node_a].quadrance_to(self.nodes[e.node_b])
            if q.is_zero() or not q.is_positive():
                self.fault_detail = f"{e.edge_type.name} {e.node_a}-{e.node_b} has zero/nonpositive quadrance"
                return False
        return True

    def guard_grid_consistency(self) -> bool:
        for e in self.edges:
            ga = self.grid_states[e.node_a]
            gb = self.grid_states[e.node_b]
            if ga != gb and ga != GridState.UNTAGGED and gb != GridState.UNTAGGED:
                if e.edge_type != EdgeType.GAP:
                    self.fault_detail = (
                        f"Edge {e.node_a}({ga.name})-{e.node_b}({gb.name}) "
                        f"crosses grids but is {e.edge_type.name}")
                    return False
        return True

    def guard_equilibrium(self) -> bool:
        result = solve_equilibrium(self.nodes, self.edges)
        if not result.ok:
            self.fault_detail = "No force-density self-stress with cable/GAP positive and strut negative signs"
            return False
        self.equilibrium_densities = result.densities
        return True

    def configure(self) -> "TensegritySystem":
        assert self.state == TensegrityState.IDLE
        if not self.guard_valid_topology():
            self.state = TensegrityState.FAULT_TOPOLOGY
            self.fault = TensegrityFault.TOPOLOGY_ERROR
            return self
        self.state = TensegrityState.CONFIGURING
        return self

    def verify_balance(self) -> "TensegritySystem":
        assert self.state == TensegrityState.CONFIGURING
        if not self.guard_struts_separated():
            self.state = TensegrityState.FAULT_STRUT_COLLISION
            self.fault = TensegrityFault.STRUT_COLLISION
            return self
        if not self.guard_cables_taut():
            self.state = TensegrityState.FAULT_CABLE_SLACK
            self.fault = TensegrityFault.CABLE_SLACK
            return self
        if not self.guard_struts_disjoint_interior():
            self.state = TensegrityState.FAULT_STRUT_INTERSECTION
            self.fault = TensegrityFault.STRUT_INTERSECTION
            return self
        if not self.guard_grid_consistency():
            self.state = TensegrityState.FAULT_GRID_MISMATCH
            self.fault = TensegrityFault.GRID_MISMATCH
            return self
        if not self.guard_equilibrium():
            self.state = TensegrityState.FAULT_NOT_IN_EQUILIBRIUM
            self.fault = TensegrityFault.NOT_IN_EQUILIBRIUM
            return self
        self.state = TensegrityState.BALANCED
        return self

    def reset(self) -> "TensegritySystem":
        self.state = TensegrityState.IDLE
        self.fault = TensegrityFault.NONE
        self.fault_detail = ""
        self.equilibrium_densities = []
        return self


def _edge_sign_ok(edge: Edge, density: Phi) -> bool:
    if edge.edge_type == EdgeType.STRUT:
        return (not density.is_zero()) and (-density).is_positive()
    return density.is_positive()


def _phi_to_fraction(value: Phi) -> Fraction:
    assert value.b == 0, "segment intersection for this fixture expects rational coordinates"
    return value.a


def _vec_to_frac3(v: Vec3Phi) -> tuple[Fraction, Fraction, Fraction]:
    return (_phi_to_fraction(v.x), _phi_to_fraction(v.y), _phi_to_fraction(v.z))


def _phi_lt(a: Phi, b: Phi) -> bool:
    return (b - a).is_positive()


def _phi_le(a: Phi, b: Phi) -> bool:
    return a == b or _phi_lt(a, b)


def _phi_gt(a: Phi, b: Phi) -> bool:
    return _phi_lt(b, a)


def _phi_ge(a: Phi, b: Phi) -> bool:
    return a == b or _phi_gt(a, b)


def _phi_min(a: Phi, b: Phi) -> Phi:
    return a if _phi_le(a, b) else b


def _phi_max(a: Phi, b: Phi) -> Phi:
    return a if _phi_ge(a, b) else b


def _vec_to_phi3(v: Vec3Phi) -> tuple[Phi, Phi, Phi]:
    return (v.x, v.y, v.z)


def _dot(u: tuple[Phi, Phi, Phi],
         v: tuple[Phi, Phi, Phi]) -> Phi:
    return u[0] * v[0] + u[1] * v[1] + u[2] * v[2]


def _sub3(a: tuple[Phi, Phi, Phi],
          b: tuple[Phi, Phi, Phi]) -> tuple[Phi, Phi, Phi]:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(u: tuple[Phi, Phi, Phi],
           v: tuple[Phi, Phi, Phi]) -> tuple[Phi, Phi, Phi]:
    return (
        u[1] * v[2] - u[2] * v[1],
        u[2] * v[0] - u[0] * v[2],
        u[0] * v[1] - u[1] * v[0],
    )


def _is_zero3(v: tuple[Phi, Phi, Phi]) -> bool:
    return v[0].is_zero() and v[1].is_zero() and v[2].is_zero()


def _same_point(a: tuple[Phi, Phi, Phi], b: tuple[Phi, Phi, Phi]) -> bool:
    return a[0] == b[0] and a[1] == b[1] and a[2] == b[2]


def _is_antipodal_through_origin(a: Vec3Phi, b: Vec3Phi) -> bool:
    return (
        (a.x + b.x).is_zero() and
        (a.y + b.y).is_zero() and
        (a.z + b.z).is_zero()
    )


def _param_in_unit_interval(value: Phi, closed: bool) -> bool:
    if closed:
        return _phi_ge(value, PHI_ZERO) and _phi_le(value, PHI_ONE)
    return _phi_gt(value, PHI_ZERO) and _phi_lt(value, PHI_ONE)


def _collinear_segments_contact(p0: tuple[Phi, Phi, Phi],
                                p1: tuple[Phi, Phi, Phi],
                                q0: tuple[Phi, Phi, Phi],
                                q1: tuple[Phi, Phi, Phi],
                                closed: bool) -> bool:
    u = _sub3(p1, p0)
    v = _sub3(q1, q0)

    if _is_zero3(u):
        if _is_zero3(v):
            return closed and _same_point(p0, q0)
        return False
    if _is_zero3(v):
        return False

    axis = next(i for i, coord in enumerate(u) if not coord.is_zero())
    q0_param = (q0[axis] - p0[axis]) / u[axis]
    q1_param = (q1[axis] - p0[axis]) / u[axis]
    lo = _phi_max(PHI_ZERO, _phi_min(q0_param, q1_param))
    hi = _phi_min(PHI_ONE, _phi_max(q0_param, q1_param))
    if closed:
        return _phi_le(lo, hi)
    return _phi_lt(lo, hi)


def _point_on_segment_closed(point: tuple[Phi, Phi, Phi],
                             start: tuple[Phi, Phi, Phi],
                             end: tuple[Phi, Phi, Phi]) -> bool:
    u = _sub3(end, start)
    w = _sub3(point, start)
    if _is_zero3(u):
        return _same_point(point, start)
    if not _is_zero3(_cross(w, u)):
        return False
    axis = next(i for i, coord in enumerate(u) if not coord.is_zero())
    param = w[axis] / u[axis]
    return _param_in_unit_interval(param, closed=True)


def _segments_contact(p0: Vec3Phi, p1: Vec3Phi,
                      q0: Vec3Phi, q1: Vec3Phi,
                      closed: bool) -> bool:
    if (_is_antipodal_through_origin(p0, p1) and
            _is_antipodal_through_origin(q0, q1)):
        return True

    p0v = _vec_to_phi3(p0)
    p1v = _vec_to_phi3(p1)
    q0v = _vec_to_phi3(q0)
    q1v = _vec_to_phi3(q1)
    u = _sub3(p1v, p0v)
    v = _sub3(q1v, q0v)
    w = _sub3(q0v, p0v)

    if _is_zero3(u) or _is_zero3(v):
        if not closed:
            return False
        if _is_zero3(u):
            return _point_on_segment_closed(p0v, q0v, q1v)
        return _point_on_segment_closed(q0v, p0v, p1v)

    # Solve s*u - t*v = w by trying the three 2x2 coordinate minors in Q(phi).
    pairs = ((0, 1), (0, 2), (1, 2))
    for a, b in pairs:
        det = (-u[a] * v[b]) + (u[b] * v[a])
        if det.is_zero():
            continue
        s = (-w[a] * v[b] + w[b] * v[a]) / det
        t = (u[a] * w[b] - u[b] * w[a]) / det
        if (not _param_in_unit_interval(s, closed) or
                not _param_in_unit_interval(t, closed)):
            return False
        hit_p = (p0v[0] + u[0] * s, p0v[1] + u[1] * s, p0v[2] + u[2] * s)
        hit_q = (q0v[0] + v[0] * t, q0v[1] + v[1] * t, q0v[2] + v[2] * t)
        return hit_p == hit_q

    if _is_zero3(_cross(w, u)):
        return _collinear_segments_contact(p0v, p1v, q0v, q1v, closed)
    return False


def segments_intersect_interior(p0: Vec3Phi, p1: Vec3Phi,
                                q0: Vec3Phi, q1: Vec3Phi) -> bool:
    """Exact open-interval segment intersection over Q(phi).

    Coordinates are exact Fraction pairs a + b*phi. All ordering is done by
    Phi.is_positive(), which maps a + b*phi to (2a+b) + b*sqrt(5) and uses
    conjugate square comparisons; no floats or epsilon tests are used.
    Collinear segments return True only when their open interiors overlap.
    Endpoint touches, including T-junctions, are reserved for
    segments_contact_closed().
    """
    return _segments_contact(p0, p1, q0, q1, closed=False)


def segments_contact_closed(p0: Vec3Phi, p1: Vec3Phi,
                            q0: Vec3Phi, q1: Vec3Phi) -> bool:
    """Exact closed-interval segment contact over Q(phi)."""
    return _segments_contact(p0, p1, q0, q1, closed=True)


def _matrix_rows(nodes: List[Vec3Phi], edges: List[Edge]) -> List[List[Fraction]]:
    rows: List[List[Fraction]] = []
    for node_idx in range(len(nodes)):
        for axis in ("x", "y", "z"):
            for coeff in ("a", "b"):
                row = [ZERO for _ in range(2 * len(edges))]
                for col, e in enumerate(edges):
                    if e.node_a == node_idx:
                        delta = getattr(nodes[e.node_a], axis) - getattr(nodes[e.node_b], axis)
                    elif e.node_b == node_idx:
                        delta = getattr(nodes[e.node_b], axis) - getattr(nodes[e.node_a], axis)
                    else:
                        continue
                    row[2 * col] = getattr(delta, coeff)
                    phi_delta = delta * PHI_UNIT
                    row[2 * col + 1] = getattr(phi_delta, coeff)
                if any(row):
                    rows.append(row)
    return rows


def _rref(matrix: List[List[Fraction]]) -> tuple[List[List[Fraction]], List[int]]:
    if not matrix:
        return [], []
    m = [row[:] for row in matrix]
    n_rows = len(m)
    n_cols = len(m[0])
    pivots: List[int] = []
    r = 0
    for c in range(n_cols):
        pivot = None
        for i in range(r, n_rows):
            if m[i][c] != 0:
                pivot = i
                break
        if pivot is None:
            continue
        m[r], m[pivot] = m[pivot], m[r]
        inv = m[r][c]
        m[r] = [v / inv for v in m[r]]
        for i in range(n_rows):
            if i != r and m[i][c] != 0:
                factor = m[i][c]
                m[i] = [m[i][j] - factor * m[r][j] for j in range(n_cols)]
        pivots.append(c)
        r += 1
        if r == n_rows:
            break
    return m, pivots


def _nullspace(matrix: List[List[Fraction]], n_cols: int) -> List[List[Fraction]]:
    rref, pivots = _rref(matrix)
    pivot_set = set(pivots)
    free_cols = [c for c in range(n_cols) if c not in pivot_set]
    basis: List[List[Fraction]] = []
    for free in free_cols:
        vec = [ZERO for _ in range(n_cols)]
        vec[free] = ONE
        for row_idx, pivot_col in enumerate(pivots):
            vec[pivot_col] = -rref[row_idx][free]
        basis.append(vec)
    return basis


def _combine_basis(basis: List[List[Fraction]], coeffs: List[int]) -> List[Fraction]:
    n = len(basis[0])
    out = [ZERO for _ in range(n)]
    for coeff, vec in zip(coeffs, basis):
        if coeff == 0:
            continue
        for i, v in enumerate(vec):
            out[i] = out[i] + v * coeff
    return out


def _candidate_coeffs(width: int, bound: int = 3):
    if width == 0:
        yield []
        return
    values = list(range(-bound, bound + 1))

    def rec(prefix: List[int]):
        if len(prefix) == width:
            if any(prefix):
                yield prefix
            return
        for v in values:
            yield from rec(prefix + [v])

    yield from rec([])


def solve_equilibrium(nodes: List[Vec3Phi], edges: List[Edge]) -> EquilibriumResult:
    """Find exact force densities q_e satisfying sum q_e*(x_i-x_j)=0."""
    if not edges:
        return EquilibriumResult(False)
    uniform = _solve_type_uniform_equilibrium(nodes, edges)
    if uniform.ok:
        return uniform
    basis = _nullspace(_matrix_rows(nodes, edges), 2 * len(edges))
    if not basis:
        return EquilibriumResult(False)
    if len(basis) > 5:
        # The canonical oracle is intentionally small. If a future structure
        # has a broad self-stress cone, add a targeted solver rather than an
        # exponential search here.
        return EquilibriumResult(False)
    for coeffs in _candidate_coeffs(len(basis)):
        candidate = _combine_basis(basis, coeffs)
        densities = [Phi(candidate[2 * i], candidate[2 * i + 1])
                     for i in range(len(edges))]
        if all(_edge_sign_ok(e, q) for e, q in zip(edges, densities)):
            return EquilibriumResult(True, densities)
    return EquilibriumResult(False)


def _solve_type_uniform_equilibrium(nodes: List[Vec3Phi],
                                    edges: List[Edge]) -> EquilibriumResult:
    """Derive the symmetric cable/GAP-vs-strut density ratio exactly."""
    rows = []
    for row in _matrix_rows(nodes, edges):
        agg = [ZERO, ZERO, ZERO, ZERO]
        for i, edge in enumerate(edges):
            if edge.edge_type == EdgeType.STRUT:
                agg[2] = agg[2] + row[2 * i]
                agg[3] = agg[3] + row[2 * i + 1]
            else:
                agg[0] = agg[0] + row[2 * i]
                agg[1] = agg[1] + row[2 * i + 1]
        if any(agg):
            rows.append(agg)
    basis = _nullspace(rows, 4)
    if not basis:
        return EquilibriumResult(False)
    for coeffs in _candidate_coeffs(len(basis)):
        candidate = _combine_basis(basis, coeffs)
        cable_density = Phi(candidate[0], candidate[1])
        strut_density = Phi(candidate[2], candidate[3])
        if cable_density.is_positive() and (-strut_density).is_positive():
            densities = [
                strut_density if e.edge_type == EdgeType.STRUT else cable_density
                for e in edges
            ]
            return EquilibriumResult(True, densities)
    return EquilibriumResult(False)


def _v(x: int, y: int, z: int) -> Vec3Phi:
    return Vec3Phi(Phi.from_int(x), Phi.from_int(y), Phi.from_int(z))


def make_tensegrity_six_strut() -> TensegritySystem:
    """Build Fuller's expanded-octahedron six-strut fixture."""
    nodes = [
        _v(0, 1, 2), _v(0, 1, -2), _v(0, -1, 2), _v(0, -1, -2),
        _v(1, 2, 0), _v(1, -2, 0), _v(-1, 2, 0), _v(-1, -2, 0),
        _v(2, 0, 1), _v(2, 0, -1), _v(-2, 0, 1), _v(-2, 0, -1),
    ]

    edges: List[Edge] = []
    cable_q = Phi.from_int(6)
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            if nodes[i].quadrance_to(nodes[j]) == cable_q:
                edges.append(Edge(i, j, EdgeType.CABLE, cable_q))

    for a, b in [(0, 1), (2, 3), (4, 5), (6, 7), (8, 10), (9, 11)]:
        edges.append(Edge(a, b, EdgeType.STRUT, nodes[a].quadrance_to(nodes[b])))

    return TensegritySystem(
        nodes=nodes,
        grid_states=[GridState.MAIN] * len(nodes),
        edges=edges,
    )


def make_tensegrity_antipodal_counterexample() -> TensegritySystem:
    """Old regular-icosahedron/antipodal-strut fixture kept as a negative test."""
    p = PHI_UNIT
    n = -PHI_UNIT
    z = PHI_ZERO
    one = PHI_ONE
    neg_one = -PHI_ONE
    nodes = [
        Vec3Phi(z, one, p), Vec3Phi(z, one, n),
        Vec3Phi(z, neg_one, p), Vec3Phi(z, neg_one, n),
        Vec3Phi(one, p, z), Vec3Phi(one, n, z),
        Vec3Phi(neg_one, p, z), Vec3Phi(neg_one, n, z),
        Vec3Phi(p, z, one), Vec3Phi(p, z, neg_one),
        Vec3Phi(n, z, one), Vec3Phi(n, z, neg_one),
    ]
    edges: List[Edge] = []
    edge_q = Phi.from_int(4)
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            if nodes[i].quadrance_to(nodes[j]) == edge_q:
                edges.append(Edge(i, j, EdgeType.CABLE, edge_q))
    for a, b in [(0, 3), (1, 2), (4, 7), (5, 6), (8, 11), (9, 10)]:
        edges.append(Edge(a, b, EdgeType.STRUT, nodes[a].quadrance_to(nodes[b])))
    return TensegritySystem(
        nodes=nodes,
        grid_states=[GridState.MAIN] * len(nodes),
        edges=edges,
    )
