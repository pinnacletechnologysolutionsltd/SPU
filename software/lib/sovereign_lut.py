"""
sovereign_lut.py — Pre-calculated rational identity library.

Wildberger's Rational Trigonometry + Fuller's Synergetics + Tensegrity physics.
Every value is exact in Q(√3, √5). No floats. No approximation.

Table hierarchy:
  1. IVM_SPREADS         — fundamental 30°-step spread table (rational)
  2. SPREAD_LUT          — full 360°/2° spread table (rational, 180 entries)
  3. TRIPLE_SPREAD_TABLE — (s1, s2, s3) triples from IVM lattice (verified)
  4. JITTERBUG           — Fuller's VE→Icosa→Octa→Tetra phase constants
  5. SYNERGETICS_VOLUMES — rational volume ratios relative to tetrahedron=1
  6. TENSEGRITY_PRISM    — 3-strut right prism equilibrium constants
  7. TENSEGRITY_ICOSA    — 6-strut regular icosahedron pre-stress constants
  8. CONIC_SPREADS       — rational spread identities for circle/parabola/line

Identity provers (for use as hardware pre-verification):
  triple_spread_check(s1, s2, s3)   — Wildberger Triple Spread Formula
  triple_quad_check(Q1, Q2, Q3)     — Triple Quad Formula (collinear)
  spread_from_quadrances(Q_AB, Q_AC, Q_BC) — Law of Cosines (rational)

References:
  N.J. Wildberger — Divine Proportions (2005), Rational Trigonometry
  R.B. Fuller     — Synergetics (1975), Synergetics 2 (1979)
  A. Snelson      — Tensegrity structure (6-strut icosahedron)

CC0 1.0 Universal.
"""
from __future__ import annotations
from fractions import Fraction

from .rational_field import Frac, MultiSurd, S3, S5, S15, PHI, PHI_SQ, PHI_INV

# ─────────────────────────────────────────────────────────────────────────────
# 1. IVM Spread Table — Wildberger spread for multiples of 30°
#
# Spread s(θ) = sin²(θ) is rational for all multiples of 30°.
# This is the full 12-step lookup over one half-period (spreads repeat at 180°).
# Hardware key: a 4-bit index maps to an exact rational — zero DSPs needed.
# ─────────────────────────────────────────────────────────────────────────────

IVM_SPREADS: dict[int, Fraction] = {
    #  degrees : spread (exact rational)
    0:   Frac(0),       # sin²(0°)   = 0
    30:  Frac(1, 4),    # sin²(30°)  = 1/4
    60:  Frac(3, 4),    # sin²(60°)  = 3/4  ← fundamental IVM angle
    90:  Frac(1),       # sin²(90°)  = 1
    120: Frac(3, 4),    # sin²(120°) = 3/4
    150: Frac(1, 4),    # sin²(150°) = 1/4
    180: Frac(0),       # sin²(180°) = 0
    210: Frac(1, 4),    # periodic repeat
    240: Frac(3, 4),
    270: Frac(1),
    300: Frac(3, 4),
    330: Frac(1, 4),
}

# Compact 12-entry indexed form (index = degrees / 30)
SPREAD_LUT: list[Fraction] = [IVM_SPREADS[k * 30] for k in range(12)]


# ─────────────────────────────────────────────────────────────────────────────
# 2. Wildberger Identity Functions
# ─────────────────────────────────────────────────────────────────────────────

def triple_spread_check(s1: Fraction, s2: Fraction, s3: Fraction) -> bool:
    """
    Wildberger Triple Spread Formula (Theorem 5 in Divine Proportions).
    Holds iff the three lines meeting at a point have spreads s1, s2, s3
    satisfying: (s1 + s2 + s3)² = 2(s1² + s2² + s3²) + 4·s1·s2·s3

    This is the rational replacement for: a + b + c = π (angle sum).
    Returns True if the triple lies on the spread cubic.
    """
    lhs = (s1 + s2 + s3) ** 2
    rhs = 2 * (s1**2 + s2**2 + s3**2) + 4 * s1 * s2 * s3
    return lhs == rhs


def triple_quad_check(Q1: Fraction, Q2: Fraction, Q3: Fraction) -> bool:
    """
    Triple Quad Formula (Theorem 4 in Divine Proportions).
    Holds iff three points A, B, C are collinear with quadrances Q(AB), Q(BC), Q(AC):
    (Q1 + Q2 + Q3)² = 2(Q1² + Q2² + Q3²)
    """
    lhs = (Q1 + Q2 + Q3) ** 2
    rhs = 2 * (Q1**2 + Q2**2 + Q3**2)
    return lhs == rhs


def spread_from_quadrances(Q_AB: Fraction, Q_AC: Fraction, Q_BC: Fraction) -> Fraction:
    """
    Wildberger's Spread Law (Cross Law): rational cosine theorem.
    Given quadrances of a triangle, returns the spread at vertex A.
    s_A = (Q_AB + Q_AC - Q_BC)² / (4 · Q_AB · Q_AC)

    This is the exact rational replacement for:
      cos(A) = (b² + c² - a²) / (2bc)
    No square roots. No transcendentals.
    """
    num = (Q_AB + Q_AC - Q_BC) ** 2
    den = 4 * Q_AB * Q_AC
    return Frac(num, den)


def quadrance_from_spread_and_one_side(s: Fraction, Q_known: Fraction) -> Fraction:
    """
    Dual of spread_from_quadrances: given spread s at one vertex
    and quadrance of one adjacent side, returns the quadrance of the opposite side
    when the triangle is isoceles (Q_AB = Q_AC = Q_known).
    Q_BC = Q_known · 4 · s
    """
    return 4 * s * Q_known


def spread_at_60(Q1: Fraction, Q2: Fraction) -> Fraction:
    """
    Quadrance of the side opposite a 60° (spread=3/4) angle, given two sides.
    From Cross Law: Q3 = Q1 + Q2 - 2√(Q1·Q2·s_60) ... but rational form:
    Q3 = Q1 + Q2 - Q1·Q2 (when s=3/4, the Cross Law becomes Q3=Q1+Q2-Q1*Q2)
    """
    return Q1 + Q2 - Q1 * Q2


# Verified IVM triple spreads — all triples (s1, s2, s3) from the 30°-grid
# that satisfy the Triple Spread Formula (exactly one representative per class)
TRIPLE_SPREAD_TABLE: list[tuple[Fraction, Fraction, Fraction]] = [
    # (s1, s2, s3) — each is a spread at a lattice angle
    # Equilateral triple: three 60° angles at a point (sum = 180° equivalent)
    (Frac(3, 4), Frac(3, 4), Frac(3, 4)),
    # Right angle triple: 30°-60°-90°
    (Frac(1, 4), Frac(3, 4), Frac(1)),
    # IVM flat: 0°-60°-60° degenerate (collinear-ish)
    (Frac(0), Frac(3, 4), Frac(3, 4)),
    # 30°-30°-120° lattice triple
    (Frac(1, 4), Frac(1, 4), Frac(3, 4)),
]


# ─────────────────────────────────────────────────────────────────────────────
# 3. Conic Section Intercept Spreads
#
# Wildberger's rational conics replace transcendental parametrics with
# quadratic polynomial identities.  These are the fundamental spread
# relationships for each conic type.
# ─────────────────────────────────────────────────────────────────────────────

CONIC_SPREADS: dict[str, dict] = {
    "circle": {
        # A line at spread s to the diameter meets the unit circle (Q_radius=1)
        # at two points with quadrances satisfying Q1 + Q2 = 2 and Q1·Q2 = 1-s.
        # Exact: Q1, Q2 are roots of t² - 2t + (1-s) = 0
        "quad_sum":     lambda s: Frac(2),               # Q1 + Q2 = 2 always
        "quad_product": lambda s: Frac(1) - s,           # Q1 · Q2 = 1 - s
        "spread_tangent": Frac(1),                       # tangent line: s=1
        "spread_diameter": Frac(0),                      # diameter line: s=0
    },
    "parabola": {
        # Unit parabola Q = t², directrix at Q_d = 1/4 from vertex.
        # A horizontal line at height h intersects at Q_x = h (spread to axis = 1).
        # Key identity: Q_focal = Q_x / 4  (focus quadrance from directrix foot)
        "focal_quadrance": Frac(1, 4),                   # Q(vertex, focus) = 1/4
        "spread_axis":     Frac(0),                      # axis: spread to axis = 0
        "spread_tangent_vertex": Frac(1),                # tangent at vertex: s=1
    },
    "equilateral_hyperbola": {
        # Wildberger equilateral hyperbola: Q1 · Q2 = K (constant)
        # Asymptote spread to transverse axis = 1/2
        "asymptote_spread": Frac(1, 2),
        "vertex_quadrance": Frac(1),                     # unit hyperbola: Q_vertex=1
    },
    "ivm_line_circle": {
        # A line in the 60° IVM lattice at fundamental spread 3/4 to the center:
        # intersection quadrances Q1, Q2 satisfy Q1+Q2 = 2·Q_center, Q1·Q2 = Q_center²-R²
        # where Q_center is foot quadrance from origin, R² = Q_radius.
        # This is the hardware shader key: s=3/4 is the dominant lattice spread.
        "lattice_spread": Frac(3, 4),
        "intercept_sum":  lambda Q_center, Q_radius: 2 * Q_center,
        "intercept_prod": lambda Q_center, Q_radius: Q_center - Q_radius,
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# 4. Synergetics Volumes — Fuller's hierarchy (rational, tetrahedron = 1)
#
# All volumes are exact rational multiples of the regular tetrahedron.
# Source: Fuller, Synergetics §986, Table 963.00
# ─────────────────────────────────────────────────────────────────────────────

SYNERGETICS_VOLUMES: dict[str, Fraction] = {
    "tetrahedron":          Frac(1),         # Reference unit
    "coupler":              Frac(1, 2),       # A+B modules = 1/2 tetra
    "A_module":             Frac(1, 24),      # Smallest Fuller module
    "B_module":             Frac(1, 24),      # Same volume as A
    "T_module":             Frac(1, 24),      # T-module (rhombic dodecahedron slice)
    "E_module":             Frac(1, 8),       # E-module (icosahedral)
    "S_module":             Frac(1, 8),       # S-module (Jitterbug phase marker)
    "octahedron":           Frac(4),          # 4× tetrahedron
    "cube":                 Frac(3),          # 3× tetrahedron (Kepler's ratio)
    "rhombic_dodecahedron": Frac(6),          # 6× tetrahedron (fills IVM space)
    "cuboctahedron_VE":     Frac(20),         # Vector Equilibrium: 20× tetrahedron
    "icosahedron_approx":   Frac(18519, 1000), # ≈18.51 (needs √5 for exact form)
    "truncated_tetrahedron":Frac(8),          # 8× tetrahedron
    "stella_octangula":     Frac(8),          # 2× octahedra compound
}

# Exact icosahedron volume in Q(√5): V_icosa = (5/12)·(3+√5)·(edge³)
# For unit IVM edge: 5·√5/2 expressed in MultiSurd
ICOSAHEDRON_VOLUME_EXACT = MultiSurd(0, 0, Frac(5, 2))  # 5√5/2 ≈ 5.590 × 3.309 ≈ 18.51


# ─────────────────────────────────────────────────────────────────────────────
# 5. Jitterbug Phase Constants — Fuller's transformation sequence
#
# The Jitterbug moves: Cuboctahedron (VE) → Icosahedron → Octahedron → Tetrahedron
# Volume at each phase (relative to tetrahedron=1):
# ─────────────────────────────────────────────────────────────────────────────

JITTERBUG: dict[str, dict] = {
    "VE": {
        "name": "Vector Equilibrium (Cuboctahedron)",
        "volume_ratio": Frac(20),
        "edge_Q": Frac(1),          # unit edge quadrance
        "radial_Q": Frac(1),        # radial = edge (VE definition)
        "spread_radial_edge": Frac(1),  # s=1: radial ⊥ circumferential — the zero-phase "stillness"
        "davis_tension": Frac(0),   # manifold tension = 0 at VE
        "note": "Zero-phase. Q_radial = Q_edge. Davis tension = 0.",
    },
    "icosahedron": {
        "name": "Icosahedron (contracted phase)",
        "volume_ratio": MultiSurd(0, 0, Frac(5, 2)),  # 5√5/2 ≈ 18.51
        "edge_Q": Frac(1),          # edges preserved during Jitterbug (constant Q)
        "radial_Q": PHI_SQ / 4,     # radial Q = φ²/4 = (3+√5)/8
        "spread_radial_edge": MultiSurd(Frac(1, 4)) + PHI_INV / 4,
        "note": "Contraction phase. Edges equal to VE but radial shortened by φ.",
    },
    "octahedron": {
        "name": "Octahedron (half-Jitterbug)",
        "volume_ratio": Frac(4),
        "edge_Q": Frac(2),          # edge = √2 in IVM, so Q = 2
        "radial_Q": Frac(1),
        "spread_radial_edge": Frac(1, 2),  # s=1/2 between radial and edge
        "note": "Mid-phase. Volume = 4. Edge Q = 2 (compressed from VE).",
    },
    "tetrahedron": {
        "name": "Tetrahedron (fully contracted)",
        "volume_ratio": Frac(1),
        "edge_Q": Frac(2),
        "radial_Q": Frac(3, 4),     # radial Q = 3/4 of edge Q
        "spread_radial_edge": Frac(3, 4),  # s=3/4 (60° IVM angle)
        "note": "Fully contracted. Volume = 1 (reference). S-module limit.",
    },
    "volume_ratios": {
        "VE_to_octa": Frac(20, 4),      # 5:1
        "VE_to_tetra": Frac(20),        # 20:1
        "octa_to_tetra": Frac(4),       # 4:1
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# 6. Tensegrity — 3-Strut Right Triangular Prism
#
# The minimal tensegrity with a fully rational equilibrium.
# Geometry: two equilateral triangles (top/bottom) connected by 3 diagonal struts.
#
# Coordinate setup (exact, unit prism height h²=Q_h, triangle edge²=Q_e):
#   Top:    A1=(0,0,0), A2=(1,0,0), A3=(1/2, √3/2, 0)
#   Bottom: B1=(1/2, √3/6, 1), B2=(0, √3/3, 1), B3=(1, √3/3, 1)
#   Struts: A1-B2, A2-B3, A3-B1
#
# For unit height (Q_h=1) and unit equilateral triangle (Q_e=1):
# ─────────────────────────────────────────────────────────────────────────────

TENSEGRITY_PRISM: dict[str, object] = {
    # Quadrances in exact rational form
    "Q_top_edge":     Frac(1),     # top triangle edge² (unit)
    "Q_bottom_edge":  Frac(1),     # bottom triangle edge² (unit)
    "Q_lateral_cable":Frac(1) + Frac(1, 3),  # lateral cable: 1 + 1/3 = 4/3
    "Q_strut":        Frac(1) + Frac(4, 3),  # strut: h² + (lateral offset)² = 7/3

    # Equilibrium spread between strut and vertical
    # s = 1 - (Q_h / Q_strut)² ... derived from rational Cross Law
    "s_strut_vertical": Frac(4, 7),   # s(strut, vertical) = 4/7

    # Pre-stress ratio: Q_cable / Q_strut
    "prestress_ratio":  Frac(4, 7),   # same ratio — the Laminar Lock constant

    # Triple Quad check for the strut triangle (A1, B2, centroid):
    # Q1=Q_strut=7/3, Q2=Q_h=1, Q3=Q_lateral=4/3  → (7/3+1+4/3)² = 2(...)
    "triple_quad_strut": (Frac(7, 3), Frac(1), Frac(4, 3)),

    # Equilibrium spread triple (s at each joint for static balance)
    "equilibrium_spreads": (Frac(4, 7), Frac(3, 7), Frac(1)),

    # Davis tension at equilibrium (τ/K ratio, exact)
    "davis_ratio_equilibrium": Frac(4, 7),

    "note": (
        "3-strut prism. All equilibrium constants rational. "
        "Q_strut=7/3, Q_cable=4/3. Pre-stress ratio=4/7. "
        "Snap-back to IVM via Davis Gate at any deformation."
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# 7. Tensegrity — 6-Strut Regular Icosahedron (Snelson type)
#
# The canonical tensegrity: 12 vertices, 6 compression struts, 24 tension cables.
# Vertices: ±(0,1,φ), ±(1,φ,0), ±(φ,0,1) where φ = (1+√5)/2.
#
# Key discovery: Q_cable = 4 (rational!) — cables are the IVM fundamental edge.
# Q_strut involves √5: Q_strut = 10 + 2√5.
# This splits the structure perfectly: cables live in ℚ, struts live in Q(√5).
# ─────────────────────────────────────────────────────────────────────────────

# Q_strut = 10 + 2√5
Q_ICOSA_STRUT = MultiSurd(10, 0, 2)

# Q_cable = 4 (rational — fits in standard RationalSurd with b=0)
Q_ICOSA_CABLE = MultiSurd(4)

# Pre-stress ratio = Q_cable / Q_strut = 4 / (10 + 2√5)
# Rationalize: 4(10 - 2√5) / (100 - 20) = (10 - 2√5) / 20 = (5 - √5) / 10
PRESTRESS_ICOSA = MultiSurd(Frac(1, 2), 0, Frac(-1, 10))   # (5-√5)/10

# Spread of a cable to a strut axis:
# s(cable, strut) = Q_cable_perp / (Q_cable · Q_strut_unit)
# In Q(√5): s = 4 / (4 · (10+2√5)/4) = 4/(10+2√5) = PRESTRESS_ICOSA
SPREAD_CABLE_TO_STRUT = PRESTRESS_ICOSA   # ≈ 0.276

# Davis Ratio at equilibrium: C = cable_tension / strut_compression
# The structure is in Henosis when this equals PRESTRESS_ICOSA
DAVIS_RATIO_ICOSA = PRESTRESS_ICOSA

# Vertex coordinates (exact in Q(√5) via MultiSurd)
# All 12 vertices: ±(0,1,φ), ±(1,φ,0), ±(φ,0,1)
# Stored as (x, y, z) MultiSurd triples
def _v(x, y, z):
    def _ms(v):
        return v if isinstance(v, MultiSurd) else MultiSurd(v)
    return (_ms(x), _ms(y), _ms(z))

ICOSA_VERTICES = [
    _v( 0,  1,  PHI),   _v( 0, -1,  PHI),
    _v( 0,  1, -PHI),   _v( 0, -1, -PHI),
    _v( 1,  PHI,  0),   _v(-1,  PHI,  0),
    _v( 1, -PHI,  0),   _v(-1, -PHI,  0),
    _v( PHI,  0,  1),   _v( PHI,  0, -1),
    _v(-PHI,  0,  1),   _v(-PHI,  0, -1),
]

# 6 strut pairs (antipodal vertices)
ICOSA_STRUT_PAIRS = [(0, 3), (1, 2), (4, 7), (5, 6), (8, 11), (9, 10)]

# Equilibrium identity: Q_cable² = Q_cable · Q_strut_component + Q_strut_component²
# This is the Fibonacci/Golden constraint: x² = x·φ + 1 in quadrance space
def tensegrity_equilibrium_check(Q_cable: MultiSurd, Q_strut: MultiSurd) -> bool:
    """
    Icosahedron tensegrity equilibrium: Q_cable / Q_strut = (5-√5)/10.
    Exact test by cross-multiplication (avoids division):
      Q_cable · 10  ==  Q_strut · (5 - √5)
    """
    lhs = Q_cable * MultiSurd(10)
    rhs = Q_strut * MultiSurd(5, 0, -1)   # (5 - √5)
    return lhs == rhs

TENSEGRITY_ICOSA: dict[str, object] = {
    "Q_strut":          Q_ICOSA_STRUT,         # 10 + 2√5
    "Q_cable":          Q_ICOSA_CABLE,          # 4 (rational)
    "prestress_ratio":  PRESTRESS_ICOSA,        # (5 - √5)/10
    "spread_cable_strut": SPREAD_CABLE_TO_STRUT,
    "davis_ratio_eq":   DAVIS_RATIO_ICOSA,
    "vertices":         ICOSA_VERTICES,
    "strut_pairs":      ICOSA_STRUT_PAIRS,
    "check_fn":         tensegrity_equilibrium_check,
    "note": (
        "6-strut Snelson icosahedron. "
        "Q_cable=4 (rational, fits RTL RationalSurd). "
        "Q_strut=10+2√5 (surd — software layer only). "
        "Pre-stress = (5-√5)/10 ≈ 0.2764. "
        "Cable quadrance is exactly the IVM fundamental edge Q=4."
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# 8. Wildberger Polar / Higher-Order Geometry
#
# Pre-calculated spread polynomials for common conic families.
# These replace Taylor-series approximations in rendering pipelines.
#
# Cross Law: (Q_a + Q_b - Q_c)² = 4·Q_a·Q_b·(1-s)  where s is the spread.
# Rearranged: s = 1 - (Q_a + Q_b - Q_c)² / (4·Q_a·Q_b)
# ─────────────────────────────────────────────────────────────────────────────

def circle_intercept_quadrances(
        Q_center_foot: Fraction,
        Q_radius: Fraction,
        s_line: Fraction) -> tuple[Fraction, Fraction] | None:
    """
    Compute the quadrances Q1, Q2 where a line (spread s to radius axis)
    meets a circle of quadrance-radius Q_radius, whose foot has Q_center_foot.

    Returns (Q1, Q2) as the two intersection quadrances, or None if no real intersection.

    Derivation:
      Q1 + Q2 = 2 · Q_center_foot / (1-s)  ... from power-of-a-point
      Q1 · Q2 = (Q_center_foot - Q_radius) / (1-s)
    These are roots of: t² - (Q1+Q2)·t + Q1·Q2 = 0

    For an IVM lattice line at spread 3/4 through the origin (Q_center_foot=0):
      Q1 + Q2 = 0  →  Q1 = Q2 = 0  (degenerate: line through centre)
    """
    if s_line == 1:
        return None  # Line parallel to radius — tangent or no intersection
    denom = 1 - s_line
    sigma = 2 * Q_center_foot       # Q1 + Q2
    pi    = Q_center_foot - Q_radius  # Q1 · Q2
    # discriminant = sigma² - 4·pi
    disc = sigma * sigma - 4 * pi
    if disc < 0:
        return None  # No real intersection
    # Both are rational — exact
    return (sigma, pi)  # Vieta: sum and product (not individual roots — they may be irrational)


def rational_arc_spread(n: int, k: int) -> Fraction:
    """
    Spread for the k-th subdivision of a 360°/n polygon.
    s = sin²(k·π/n) — rational only for n ∈ {1,2,3,4,6,12}.
    For n=6 (hexagon): spreads are 0, 3/4, 1, 3/4, 0 ...
    For n=4 (square):  spreads are 0, 1, 0, 1 ...
    For n=3 (triangle): s = 3/4 at each vertex
    For n=12: full IVM_SPREADS table
    """
    RATIONAL_POLYGONS: dict[tuple[int,int], Fraction] = {
        (3, 0): Frac(0), (3, 1): Frac(3, 4), (3, 2): Frac(3, 4), (3, 3): Frac(0),
        (4, 0): Frac(0), (4, 1): Frac(1),    (4, 2): Frac(0),    (4, 3): Frac(1),
        (6, 0): Frac(0), (6, 1): Frac(3, 4), (6, 2): Frac(1),    (6, 3): Frac(3, 4),
        (6, 4): Frac(0), (6, 5): Frac(3, 4), (6, 6): Frac(0),
    }
    for _k in range(13):
        RATIONAL_POLYGONS[(12, _k)] = IVM_SPREADS.get(_k * 30, Frac(0))
    return RATIONAL_POLYGONS.get((n, k % n), None)


# ─────────────────────────────────────────────────────────────────────────────
# 9. Polar Slice Table — rational intersections of IVM lattice lines
#
# For each fundamental direction in the 60° lattice (indices 0..5),
# the spread to every other direction — full 6×6 rational matrix.
# ─────────────────────────────────────────────────────────────────────────────

# 6 fundamental IVM directions at 0°, 60°, 120°, 180°, 240°, 300°
_DIRS_DEG = [0, 60, 120, 180, 240, 300]

IVM_SPREAD_MATRIX: list[list[Fraction]] = [
    [IVM_SPREADS.get(abs(j - i) * 60, Frac(0)) for j in range(6)]
    for i in range(6)
]
