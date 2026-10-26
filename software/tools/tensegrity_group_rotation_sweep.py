#!/usr/bin/env python3
"""Option A: does a COORDINATED group rotation reach new balanced geometry?

CONTEXT. spu_strategy/contract_tensegrity_active_control_2026-09-04.md
FALSIFIED the single-strut primitive: of all 144 single octahedral rotations
from the balanced canonical state, 24 stayed balanced and ALL 24 were the C4
stabiliser of the rotated strut's own axis -- they map the strut onto itself
pointwise and do not move the structure. "100% recovery" was recovery by not
moving.

An external analysis (reviewed 2026-09-06) proposed Option A: actuate the
three orthogonal strut pairs together rather than one strut alone, on the
argument that a symmetric group motion preserves cable uniformity and reaches
a continuum of new equilibria. That argument is ASSERTED, not tested, and it
has the same shape as the claim falsified on 09-04.

THE GATE, and it is the whole point (handover 2026-09-06 section 11):
    the test is "GENUINELY NEW GEOMETRY", not "the guard returned BALANCED".
The falsified primitive returned BALANCED twenty-four times. Any Option A
test that stops at the guard's verdict reproduces the 09-04 mistake exactly.

WHAT IS ENUMERATED. Each strut is rotated about ITS OWN MIDPOINT -- which is
not a global rotation of the structure, and is what makes a new shape
possible at all. Schemes:

  all      the same rotation R applied to all six struts
  opposed  R to pair 0, R^-1 to pair 1, identity to pair 2 (and the two
           other assignments of which pair is held) -- "symmetric opposition"

Rotations are the 24 signed axis permutations with det = +1: the octahedral
rotation group, and the same catalogue the 09-04 sweep used, being the subset
of exact rotations unambiguously representable in the RTL's integer Z[phi]
ABI.

Usage:
    python3 software/tools/tensegrity_group_rotation_sweep.py

CC0 1.0 Universal.
"""
import itertools
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

from tensegrity_balancer import (  # noqa: E402
    EdgeType, Phi, TensegrityState, Vec3Phi,
    make_tensegrity_six_strut,
)

STRUT_PAIRS = [((0, 1), (2, 3)), ((4, 5), (6, 7)), ((8, 10), (9, 11))]


def octahedral_rotations():
    """The 24 signed axis permutations with determinant +1."""
    out = []
    for perm in itertools.permutations(range(3)):
        for signs in itertools.product((1, -1), repeat=3):
            m = [[0, 0, 0] for _ in range(3)]
            for row, col in enumerate(perm):
                m[row][col] = signs[row]
            det = (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
                   - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
                   + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))
            if det == 1:
                out.append(tuple(tuple(r) for r in m))
    return out


def inverse(m):
    return tuple(tuple(m[j][i] for j in range(3)) for i in range(3))


def apply_about(m, p, c):
    """Rotate point p about centre c by integer matrix m, exactly."""
    d = (p.x - c.x, p.y - c.y, p.z - c.z)
    out = []
    for row in m:
        acc = Phi.from_int(0)
        for k in range(3):
            if row[k] == 1:
                acc = acc + d[k]
            elif row[k] == -1:
                acc = acc - d[k]
        out.append(acc)
    return Vec3Phi(c.x + out[0], c.y + out[1], c.z + out[2])


def midpoint_doubled(nodes, a, b):
    """2*midpoint, so the centre stays in Z[phi] with no division."""
    return Vec3Phi(nodes[a].x + nodes[b].x,
                   nodes[a].y + nodes[b].y,
                   nodes[a].z + nodes[b].z)


TWO = Phi.from_int(2)


def rotate_strut(nodes, a, b, m):
    """Rotate strut (a,b) about its own midpoint, exactly, with no rounding.

    Work in the doubled frame: with c2 = p_a + p_b,
        2*p_new = c2 + m . (2*p - c2)
    and for p = p_a the inner term is exactly (p_a - p_b). The sum
    c2 + m.(p_a - p_b) is even componentwise, because (p_a + p_b) and
    (p_a - p_b) have equal parity and m only permutes and negates
    components -- so the halving is exact, not rounded."""
    c2 = midpoint_doubled(nodes, a, b)
    updated = {}
    for idx, other in ((a, b), (b, a)):
        d = (nodes[idx].x - nodes[other].x,
             nodes[idx].y - nodes[other].y,
             nodes[idx].z - nodes[other].z)
        comps = []
        for row in m:
            acc = Phi.from_int(0)
            for k in range(3):
                if row[k] == 1:
                    acc = acc + d[k]
                elif row[k] == -1:
                    acc = acc - d[k]
            comps.append(acc)
        updated[idx] = Vec3Phi((c2.x + comps[0]) / TWO,
                               (c2.y + comps[1]) / TWO,
                               (c2.z + comps[2]) / TWO)
    nodes[a], nodes[b] = updated[a], updated[b]


def geometry_key(sys_):
    """Position multiset -- invariant to node relabelling."""
    from tensegrity_balancer import _vec_to_frac3
    return tuple(sorted(_vec_to_frac3(n) for n in sys_.nodes))


def labelled_key(sys_):
    from tensegrity_balancer import _vec_to_frac3
    return tuple(_vec_to_frac3(n) for n in sys_.nodes)


def evaluate(nodes):
    sys_ = make_tensegrity_six_strut()
    sys_.nodes = nodes
    sys_.configure()
    if sys_.state != TensegrityState.CONFIGURING:
        return sys_, False
    sys_.verify_balance()
    return sys_, sys_.state == TensegrityState.BALANCED


def main():
    rots = octahedral_rotations()
    assert len(rots) == 24, len(rots)

    base = make_tensegrity_six_strut()
    base.configure()
    base.verify_balance()
    base_geo, base_lab = geometry_key(base), labelled_key(base)

    print("CONTROL 1 -- canonical fixture is BALANCED:",
          "PASS" if base.state == TensegrityState.BALANCED else f"FAIL ({base.fault_detail})")
    if base.state != TensegrityState.BALANCED:
        return 1

    # CONTROL 2. Without this the whole sweep is vacuous: a broken rotation
    # would fail every candidate and produce exactly the same "0 new
    # geometry" answer as a genuine falsification. A rotation about a strut's
    # own midpoint MUST preserve that strut's quadrance.
    strut_q = {}
    for pair in STRUT_PAIRS:
        for (a, b) in pair:
            strut_q[(a, b)] = base.nodes[a].quadrance_to(base.nodes[b])
    bad = 0
    for R in rots:
        nodes = list(make_tensegrity_six_strut().nodes)
        for pair in STRUT_PAIRS:
            for (a, b) in pair:
                rotate_strut(nodes, a, b, R)
        for (a, b), q in strut_q.items():
            if nodes[a].quadrance_to(nodes[b]) != q:
                bad += 1
    print(f"CONTROL 2 -- rotation preserves every strut quadrance:",
          "PASS" if bad == 0 else f"FAIL ({bad} violations)")
    if bad:
        print("   The transform is wrong. Any negative result below would be")
        print("   an artifact of a broken rotation, not a property of the")
        print("   structure. HALT.")
        return 1

    # CONTROL 3. The perturbations must genuinely break balance for real
    # reasons -- a distribution of faults, not a single degenerate mode.
    from collections import Counter
    faults = Counter()
    for R in rots:
        nodes = list(make_tensegrity_six_strut().nodes)
        for pair in STRUT_PAIRS:
            for (a, b) in pair:
                rotate_strut(nodes, a, b, R)
        sys_, ok = evaluate(nodes)
        faults[sys_.state.name if not ok else 'BALANCED'] += 1
    print(f"CONTROL 3 -- outcome distribution over scheme 'all': {dict(faults)}")

    schemes = {'all': [lambda R, i: R for _ in range(1)]}
    results = {}

    def run(name, assign):
        balanced = new_geo = same_lab = relabel = 0
        examples = []
        for R in rots:
            nodes = list(make_tensegrity_six_strut().nodes)
            for pi, pair in enumerate(STRUT_PAIRS):
                M = assign(R, pi)
                if M is None:
                    continue
                for (a, b) in pair:
                    rotate_strut(nodes, a, b, M)
            sys_, ok = evaluate(nodes)
            if not ok:
                continue
            balanced += 1
            g, l = geometry_key(sys_), labelled_key(sys_)
            if g != base_geo:
                new_geo += 1
                if len(examples) < 3:
                    examples.append(R)
            elif l == base_lab:
                same_lab += 1
            else:
                relabel += 1
        results[name] = (balanced, new_geo, same_lab, relabel)
        print(f"\n== scheme '{name}' over {len(rots)} rotations ==")
        print(f"   balanced                          {balanced:>3} / {len(rots)}")
        print(f"   -- identical geometry AND labels  {same_lab:>3}")
        print(f"   -- identical geometry, relabelled {relabel:>3}")
        print(f"   -- GENUINELY NEW GEOMETRY         {new_geo:>3}   <-- the gate")
        if examples:
            print(f"   example rotations producing new geometry: {examples}")

    run('all', lambda R, pi: R)
    for held in range(3):
        run(f'opposed(hold pair {held})',
            lambda R, pi, h=held: None if pi == h else (R if pi == (h + 1) % 3 else inverse(R)))

    total_new = sum(v[1] for v in results.values())
    print("\n" + "=" * 66)
    if total_new == 0:
        print("RESULT: no scheme reached any new balanced geometry.")
        print("Option A is FALSIFIED ON THIS CATALOGUE, for the same reason the")
        print("single-strut primitive was: the reachable balanced set is the")
        print("canonical configuration and nothing else.")
        print()
        print("SCOPE LIMIT -- state this wherever the result is quoted.")
        print("What is falsified is coordinated group rotation drawn from the")
        print("24 DISCRETE octahedral rotations. The Fuller Jitterbug is a")
        print("CONTINUOUS motion, and its intermediate states are generally not")
        print("representable in the RTL's integer Z[phi] ABI at all. So this")
        print("result does not say the Jitterbug mechanism is wrong; it says")
        print("the exact catalogue the hardware can express does not contain")
        print("it. That is a statement about the REPRESENTATION, and it is the")
        print("more useful half of the finding: the obstacle to active control")
        print("here may be the ABI rather than the mechanics.")
    else:
        print(f"RESULT: {total_new} genuinely new balanced configurations found.")
        print("Option A is VIABLE on this catalogue. Inspect the examples before")
        print("drafting RTL -- confirm they are not a relabelling the geometry")
        print("key failed to canonicalise.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
