"""A31 field oracle — split-biquadratic algebra over M31, with batch inversion.

Python behavioral model of the RTL A31 arithmetic chain:

  spu13_m31_multiplier.v   — a31_mul (cross-product table, basis [1,√3,√5,√15])
  spu13_fp4_inverter.v     — a31_tower_inv (Conjugate Reduction Tower,
                             FLAGS.V on zero norm)
  rplu_thimble_pade.v      — pade_eval (Horner numerator/denominator,
                             one tower inversion, final multiply)

On top of the bit-exact primitives this module adds the Montgomery batch
inversion prototype (task: batched thimble/Padé runs): k tower inversions
become 1 tower inversion + 3(k-1) multiplies, and the zero-divisor check
defers to a single norm test on the accumulated denominator product —
valid because the norm is multiplicative into the field F_p, so the
product norm is zero iff at least one factor norm is zero.

Every function takes an optional OpCount so callers can measure the
MAC-vs-tower tradeoff with real workload mixes before any RTL is written.

Usage:
    from lib.a31_field import a31_mul, a31_tower_inv, batch_tower_inv
"""

P = 2147483647  # M31 = 2^31 - 1

# Cycle costs, from RTL comments (see module headers cited above):
#   tower: spu13_fp4_inverter.v  "Total latency: ~76 cycles, deterministic"
#   mult:  spu13_m31_multiplier.v is a 2-stage pipeline; through the shared
#          launch/wait FSM one multiply costs ~3 cycles (spu13_jet_inv.v:
#          "6 multiplies = ~18 cycles")
TOWER_CYCLES = 76
MULT_CYCLES = 3


def m31(x):
    """Reduce to [0, P-1]."""
    x %= P
    return x if x >= 0 else x + P


class OpCount:
    """Counts shared-multiplier ops and tower invocations."""

    def __init__(self):
        self.mults = 0
        self.towers = 0

    def cycles(self, mult_cycles=MULT_CYCLES, tower_cycles=TOWER_CYCLES):
        return self.mults * mult_cycles + self.towers * tower_cycles


# ── A31 element: (c0, c1, c2, c3) = c0 + c1·√3 + c2·√5 + c3·√15 ──────────

A31_ZERO = (0, 0, 0, 0)
A31_ONE = (1, 0, 0, 0)


def a31_add(a, b):
    return tuple(m31(x + y) for x, y in zip(a, b))


def a31_sub(a, b):
    return tuple(m31(x - y) for x, y in zip(a, b))


def a31_neg(a):
    return tuple(m31(-x) for x in a)


def a31_mul(a, b, ctr=None):
    """Cross-product table, identical to spu13_m31_multiplier.v."""
    if ctr is not None:
        ctr.mults += 1
    c0, c1, c2, c3 = a
    d0, d1, d2, d3 = b
    return (
        m31(c0 * d0 + 3 * c1 * d1 + 5 * c2 * d2 + 15 * c3 * d3),
        m31(c0 * d1 + c1 * d0 + 5 * c2 * d3 + 5 * c3 * d2),
        m31(c0 * d2 + c2 * d0 + 3 * c1 * d3 + 3 * c3 * d1),
        m31(c0 * d3 + c1 * d2 + c2 * d1 + c3 * d0),
    )


def a31_conj_5_15(z):
    """Conjugate w.r.t. √5, √15 (fp4_inverter Stage A input)."""
    return (z[0], z[1], m31(-z[2]), m31(-z[3]))


def a31_norm(z, ctr=None):
    """Scalar norm N in F_p: Stage A + Stage B of the tower, no Fermat.

    N = 0 iff z is zero or a zero divisor. Costs 2 shared-multiplier ops —
    this is the cheap per-element singularity probe used by the batch
    fallback path.
    """
    w = a31_mul(z, a31_conj_5_15(z), ctr)
    w_conj = (w[0], m31(-w[1]), 0, 0)
    return a31_mul(w, w_conj, ctr)[0]


def a31_tower_inv(z, ctr=None):
    """Conjugate Reduction Tower, step-for-step spu13_fp4_inverter.v.

    Returns (inverse, flags_v). flags_v mirrors FLAGS.V: set when the
    norm is zero (z is zero or a zero divisor), inverse is None.
    The tower's internal multiplies and Fermat chain are costed as one
    TOWER_CYCLES unit, matching the RTL's deterministic ~76 cycles.
    """
    if ctr is not None:
        ctr.towers += 1
    z_conj = a31_conj_5_15(z)
    w = a31_mul(z, z_conj)                      # Stage A
    w_conj = (w[0], m31(-w[1]), 0, 0)
    n = a31_mul(w, w_conj)[0]                   # Stage B: scalar norm
    if n == 0:
        return None, True                        # S_EXCEPTION, FLAGS.V
    n_inv = pow(n, P - 2, P)                     # Fermat chain
    temp = a31_mul(z_conj, w_conj)               # Stage D1
    return tuple(m31(t * n_inv) for t in temp), False  # Stage D2


# ── Montgomery batch inversion ────────────────────────────────────────────

def batch_tower_inv(dens, ctr=None):
    """Invert k A31 elements with one tower run: 1 tower + 3(k-1) mults.

    Returns (inverses, singular_indices). The zero-divisor check is
    deferred: one tower on the accumulated product detects "some factor
    is singular" for free (its norm stage); only then does the fallback
    probe each element's norm (2 mults each) to isolate the offenders
    and re-batch the unit subset. Unit entries always get bit-exact
    inverses (ring inverses are unique, so the unwound values equal the
    per-element tower results).
    """
    k = len(dens)
    if k == 0:
        return [], []

    prefix = [dens[0]]                           # prefix[i] = d0·…·di
    for d in dens[1:]:
        prefix.append(a31_mul(prefix[-1], d, ctr))

    total_inv, flags_v = a31_tower_inv(prefix[-1], ctr)

    if flags_v:
        # At least one singular factor: isolate by per-element norm probe,
        # then batch-invert the unit subset (second tower, no recursion).
        singular = [i for i, d in enumerate(dens) if a31_norm(d, ctr) == 0]
        units = [i for i in range(k) if a31_norm(dens[i]) != 0]
        inverses = [None] * k
        if units:
            unit_invs, _ = batch_tower_inv([dens[i] for i in units], ctr)
            for i, inv in zip(units, unit_invs):
                inverses[i] = inv
        return inverses, singular

    # Unwind: inv_i = (d0·…·dk-1)^-1 · (d0·…·di-1) · (di+1·…·dk-1)
    inverses = [None] * k
    acc = total_inv
    for i in range(k - 1, 0, -1):
        inverses[i] = a31_mul(acc, prefix[i - 1], ctr)
        acc = a31_mul(acc, dens[i], ctr)
    inverses[0] = acc
    return inverses, []


# ── Padé evaluation (rplu_thimble_pade.v behavior) ────────────────────────

def horner(coeffs, x, ctr=None):
    """Evaluate sum coeffs[i]·x^i by Horner. coeffs[0] is the constant."""
    val = coeffs[-1]
    for c in reversed(coeffs[:-1]):
        val = a31_add(a31_mul(val, x, ctr), c)
    return val


def pade_eval(num_coeffs, den_coeffs, x, ctr=None):
    """Baseline single eval: Horner both, one tower, final multiply.

    Returns (result, flags_v) — matches rplu_thimble_pade.v.
    """
    n_val = horner(num_coeffs, x, ctr)
    d_val = horner(den_coeffs, x, ctr)
    d_inv, flags_v = a31_tower_inv(d_val, ctr)
    if flags_v:
        return None, True
    return a31_mul(n_val, d_inv, ctr), False


def pade_eval_batch(num_coeffs, den_coeffs, xs, ctr=None):
    """Batched evals sharing one tower run via Montgomery batch inversion.

    Returns (results, singular_indices). results[i] is None for lanes
    whose denominator was a zero divisor (per-lane FLAGS.V equivalent).
    """
    n_vals = [horner(num_coeffs, x, ctr) for x in xs]
    d_vals = [horner(den_coeffs, x, ctr) for x in xs]
    d_invs, singular = batch_tower_inv(d_vals, ctr)
    results = [
        a31_mul(n, inv, ctr) if inv is not None else None
        for n, inv in zip(n_vals, d_invs)
    ]
    return results, singular
