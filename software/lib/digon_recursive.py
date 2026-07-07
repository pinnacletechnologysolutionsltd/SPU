"""Digon-recursive series evaluator — cost model at parameterized jet depth.

Three evaluation strategies + Newton, with a fourth "sparse jet" model that
tracks nilpotency orders through the lattice traversal, exploiting the
digon structure to avoid full (N+1)(N+2)/2 Cauchy products.

Key insight: c₀ is O(ε) (Taylor-shifted to root), so c₀^p is O(ε^p).
Face coefficients (c₂, c₃, ...) are A31 scalars — order-0 sparse jets
(only ε⁰ component non-zero). c₁⁻¹ from jet_inv is a dense order-0 jet
(all ε channels populated). The sparse model exploits this mixed sparsity.

Run:  PYTHONPATH=software python3 software/lib/digon_recursive.py
"""

from lib.a31_field import MULT_CYCLES, TOWER_CYCLES
from lib.hyper_catalan import enumerate_types


# ── Jet ring costs ────────────────────────────────────────────────────────

def jet_mul_cost(N):
    """Base A31 mults for one full jet_mul at order N: (N+1)(N+2)/2."""
    return (N + 1) * (N + 2) // 2


def jet_mul_cost_sparse(N, order):
    """Sparse jet_mul where one operand is order-0-sparse (only ε⁰).
    Cost is just the ε⁰ row of the Cauchy product: (order+1) base mults.
    
    More generally: multiplying a jet at order k (dominant term ε^k)
    by a jet at order j costs sum_{t=0}^{min(N, k+j)} ... but for the
    practical case where one operand has only ε⁰ non-zero, the cost
    is (order+1) — copy each component through a scalar multiply.
    """
    return order + 1


def jet_inv_cost(N):
    """Jet inverse: 1 tower + systematic reassembly into h_1..h_N.

    RTL pattern (extends spu13_jet_inv.v to general N):
      c0^-1 via tower
      c0^-2 ... c0^-(N+1): N base mults
      Reassembly: ~N(N+1)/2 base mults (Bell-polynomial terms of the c_i)
    """
    return 1, N + N * (N + 1) // 2


def newton_iterations(N):
    """Newton doubles precision each step."""
    target = N + 1
    iters, prec = 0, 1
    while prec < target:
        prec *= 2
        iters += 1
    return iters


# ── Type enumeration ──────────────────────────────────────────────────────

def vertices(m):
    return 2 + sum((i + 1) * mi for i, mi in enumerate(m))


def edges(m):
    return 1 + sum((i + 2) * mi for i, mi in enumerate(m))


def surviving_types(num_vars, N):
    """Types with V-1 <= N (survive at nilpotency depth N)."""
    return enumerate_types(num_vars, N, lambda m: vertices(m) - 1)


# ── Cost models ───────────────────────────────────────────────────────────

def series_naive_cost(types, N):
    """Per-type power() from scratch. 1 tower shared."""
    towers = 0
    mults = 0
    jmc = jet_mul_cost(N)
    c1_inv_done = False
    for m in types:
        if not c1_inv_done:
            t, m_ = jet_inv_cost(N)
            towers += t
            mults += m_
            c1_inv_done = True
        v1 = vertices(m) - 1
        e = edges(m)
        faces = sum(m)
        mults += v1 * jmc          # power(c0, v1)
        mults += e * jmc           # power(c1_inv, e)
        mults += faces * jmc       # per-face powers
        nz = sum(1 for mi in m if mi > 0)
        mults += (2 + nz) * jmc    # combine: Cm * c0 * ci * faces
    return towers, mults


def series_shared_cost(types, N):
    """Precompute all powers; O(V) per-term for face powers."""
    towers = 0
    mults = 0
    jmc = jet_mul_cost(N)
    if not types:
        return 0, 0

    c1_inv_done = False
    for m in types:
        if not c1_inv_done:
            t, m_ = jet_inv_cost(N)
            towers += t
            mults += m_
            c1_inv_done = True
            break

    max_v1 = max(vertices(m) - 1 for m in types)
    max_e = max(edges(m) for m in types)
    num_vars = len(types[0])

    mults += max_v1 * jmc      # precompute c0 powers
    mults += max_e * jmc       # precompute c1_inv powers
    for i in range(num_vars):
        max_mi = max((m[i] for m in types), default=0)
        if max_mi > 0:
            mults += max_mi * jmc  # precompute face powers

    for m in types:
        nz = sum(1 for mi in m if mi > 0)
        mults += (3 + nz) * jmc    # combine: Cm * c0 * ci * faces
    return towers, mults


def series_digon_cost(types, N):
    """Lattice traversal: sorted by V, lexicographic. Incremental power updates."""
    towers = 0
    mults = 0
    jmc = jet_mul_cost(N)
    if not types:
        return 0, 0

    c1_inv_done = False
    for m in types:
        if not c1_inv_done:
            t, m_ = jet_inv_cost(N)
            towers += t
            mults += m_
            c1_inv_done = True
            break

    num_vars = len(types[0])
    sorted_m = sorted(types, key=lambda m: (vertices(m), m))

    prev_v1 = -1
    prev_e = -1
    prev_faces = None

    for m in sorted_m:
        v1 = vertices(m) - 1
        e = edges(m)
        faces = tuple(m)

        if prev_v1 < 0:
            if v1 > 0:
                mults += v1 * jmc
            if e > 0:
                mults += e * jmc
            mults += sum(m) * jmc
            nz = sum(1 for mi in m if mi > 0)
            mults += (3 + nz) * jmc
        else:
            dv = v1 - prev_v1
            de = e - prev_e
            df = [faces[i] - prev_faces[i] for i in range(num_vars)]
            added = sum(max(0, d) for d in df)
            if dv > 0:
                mults += dv * jmc
            if de > 0:
                mults += de * jmc
            mults += added * jmc
            nz = sum(1 for mi in m if mi > 0)
            mults += (3 + nz) * jmc

        prev_v1, prev_e, prev_faces = v1, e, faces

    return towers, mults


def series_sparse_cost(types, N):
    """Digon lattice + mixed-sparsity jet arithmetic.

    Sparsity model:
      c₀:      O(ε)      → c₀^p is O(ε^p), sparse (orders p..N populated)
      c₁⁻¹:    dense      → all ε channels populated (from jet_inv reassembly)
      c₂,c₃,..: ε⁰-only   → scalar A31 elements (sparse order-0 jets)

    Lattice walk: types sorted by V, lexicographic. Incremental power
    updates using sparse multiplies where operands permit.

    Factoring: x = c₀·c₁⁻¹ · Σ C_m·c₀^{V-2}·c₁^{-(E-1)}·c₂^{m₂}·...
    The c₀·c₁⁻¹ prefix is one dense jet_mul. The inner sum's terms have
    only sparse c₀ powers and scalar face coefficients.
    """
    towers = 0
    mults = 0
    if not types:
        return 0, 0

    jmc = jet_mul_cost(N)
    c1_inv_done = False
    for m in types:
        if not c1_inv_done:
            t, m_ = jet_inv_cost(N)
            towers += t
            mults += m_
            c1_inv_done = True
            break

    num_vars = len(types[0])
    sorted_m = sorted(types, key=lambda m: (vertices(m), m))

    # ── Precompute c₁⁻¹ powers (dense, full jet_muls) ─────────────────
    max_e = max(edges(m) for m in types)
    if max_e > 0:
        mults += max_e * jmc

    # ── Precompute face-coefficient powers (sparse: ε⁰-only → scalar mults) ─
    for i in range(num_vars):
        max_mi = max((m[i] for m in types), default=0)
        if max_mi > 0:
            mults += max_mi  # one base mult per face-power step

    # ── Per-type evaluation with sparse c₀ chain ──────────────────────
    prev_v1 = -1
    prev_e = -1
    prev_faces = None
    prev_c0_acc_cost = 0  # cumulative mult cost of building c0^v1

    for m in sorted_m:
        v1 = vertices(m) - 1
        e = edges(m)
        faces = tuple(m)

        # c₀ power chain: build c₀^{v1} from c₀^{prev_v1} via sparse muls.
        # Each step: result (order p) * c₀ (order 1) → sparse mul.
        # Dominant order after multiply = p+1, so cost = (p+1)+1 = p+2.
        if prev_v1 < 0:
            c0_chain_cost = 0
            for p in range(1, v1):
                c0_chain_cost += (p + 2)  # sparse: order p * order 1 → order p+1
        else:
            c0_chain_cost = 0
            for p in range(prev_v1, v1):
                c0_chain_cost += (p + 2)

        mults += c0_chain_cost

        # ── Term assembly ──────────────────────────────────────────────
        # term = C_m · c₀^{V-1} · c₁^{-E} · c₂^{m₂} · c₃^{m₃} · ...
        # C_m: integer → free (constant assignment)
        # × c₀^{V-1}: sparse mul at order v1 (result * dense order-v1 jet)
        #   → cost = v1 + 1 (scalar multiply across v1+1 components)
        # × c₁^{-E}: dense lookup (free), but the multiply is ONE dense
        #   jet_mul. This is the bottleneck.
        # × each face power: sparse (ε⁰-only) → scalar mult per factor.
        mults += jet_mul_cost_sparse(N, v1)   # Cm * c0_part
        mults += jmc                          # * c1_inv_part (dense!)

        nz = sum(1 for mi in m if mi > 0)
        mults += nz                           # * each face (scalar mults)

        prev_v1, prev_e, prev_faces = v1, e, faces

    return towers, mults


def newton_cost(types, N, degree=5):
    """Newton-Hensel at depth N for a degree-d polynomial."""
    iters = newton_iterations(N)
    jmc = jet_mul_cost(N)
    t_per_inv, m_per_inv = jet_inv_cost(N)
    per_iter_mults = (2 * degree - 1) * jmc  # f(y) + f'(y) Horner + final mul
    towers = iters * t_per_inv
    mults = iters * (per_iter_mults + m_per_inv)
    return towers, mults, iters


# ── Display ────────────────────────────────────────────────────────────────

def fmt_tm(towers, mults):
    return f"{towers}T + {mults:>5d}m = {towers * TOWER_CYCLES + mults * MULT_CYCLES:>6d}c"


def compare_depths(num_vars=4, max_depth=9, degree=5):
    print(f"Cost model: tower={TOWER_CYCLES}cyc, base-mult={MULT_CYCLES}cyc, "
          f"degree-{degree} polynomial")
    print(f"Sparse model: c₀=O(ε), c₁⁻¹=dense, c_{{{2}..{num_vars+1}}}=ε⁰-only")
    print()
    print(f"{'Depth':>5} │ {'Types':>5} │ {'Newton':>22} │ {'Series(n)':>22} │ "
          f"{'Series(s)':>22} │ {'Series(d)':>22} │ {'Sparse(d)':>22}")
    print(f"{'':->5}─┼{'':->5}─┼{'':->22}─┼{'':->22}─┼{'':->22}─┼{'':->22}─┼{'':->22}")

    for N in range(2, max_depth + 1, 2):
        types = surviving_types(num_vars, N)
        nt, nm, niters = newton_cost(types, N, degree)
        stn_t, stn_m = series_naive_cost(types, N)
        sts_t, sts_m = series_shared_cost(types, N)
        std_t, std_m = series_digon_cost(types, N)
        ssp_t, ssp_m = series_sparse_cost(types, N)

        print(f" ε{N+1}  │ {len(types):>5} │ {fmt_tm(nt, nm):>22} │ "
              f"{fmt_tm(stn_t, stn_m):>22} │ {fmt_tm(sts_t, sts_m):>22} │ "
              f"{fmt_tm(std_t, std_m):>22} │ {fmt_tm(ssp_t, ssp_m):>22}")

    print()
    print("(n)=naive  (s)=shared-powers  (d)=digon-recursive  Sparse(d)=digon+sparse-jet")
    print(f"Newton iterations: "
          f"{ {N: newton_iterations(N) for N in range(2, max_depth+1, 2)} }")
    print()

    print("Series(sparse) / Newton ratio:")
    print(f"{'Depth':>5} │ {'Ratio':>8} │ {'Winner':>10} │ {'Breakdown (Series)'}")
    print(f"{'':->5}─┼{'':->8}─┼{'':->10}─┼{'':->40}")
    for N in range(2, max_depth + 1, 2):
        types = surviving_types(num_vars, N)
        nt, nm, _ = newton_cost(types, N, degree)
        ssp_t, ssp_m = series_sparse_cost(types, N)
        nc = nt * TOWER_CYCLES + nm * MULT_CYCLES
        sc = ssp_t * TOWER_CYCLES + ssp_m * MULT_CYCLES
        ratio = sc / nc
        winner = "Newton" if nc <= sc else "Series"
        print(f" ε{N+1}  │ {ratio:>7.2f}x │ {winner:>10} │ "
              f"{ssp_t}T {ssp_m}m  vs  {nt}T {nm}m")


if __name__ == "__main__":
    compare_depths()
