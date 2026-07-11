#!/usr/bin/env python3
"""Exact tensegrity-balancer oracle tests."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.tensegrity_balancer import (
    Edge,
    EdgeType,
    Fraction,
    GridState,
    ONE,
    Phi,
    PHI_ONE,
    PHI_ZERO,
    RationalSurd,
    TensegrityFault,
    TensegrityState,
    TensegritySystem,
    Vec3Phi,
    ZERO,
    make_tensegrity_antipodal_counterexample,
    make_tensegrity_six_strut,
    segments_contact_closed,
    segments_intersect_interior,
    solve_equilibrium,
)


passed = 0
failed = 0


def check(cond, msg):
    global passed, failed
    if cond:
        passed += 1
        print(f"  PASS  {msg}")
    else:
        failed += 1
        print(f"  FAIL  {msg}")


def run_case(fn):
    try:
        fn()
    except Exception as exc:
        check(False, f"{fn.__name__}: unexpected exception {exc}")


def test_exact_surd_sign_cases():
    check(not RationalSurd(Fraction(0), Fraction(0)).is_positive(),
          "Q(sqrt3) sign: zero is not positive")
    check(RationalSurd(Fraction(2), Fraction(1)).is_positive(),
          "Q(sqrt3) sign: positive same-sign components")
    check(not RationalSurd(Fraction(-2), Fraction(-1)).is_positive(),
          "Q(sqrt3) sign: negative same-sign components")
    check(not RationalSurd(Fraction(1), Fraction(-1)).is_positive(),
          "Q(sqrt3) sign: 1 - sqrt3 < 0 by exact square compare")
    check(RationalSurd(Fraction(2), Fraction(-1)).is_positive(),
          "Q(sqrt3) sign: 2 - sqrt3 > 0 by exact square compare")
    check(RationalSurd(Fraction(-1), Fraction(1)).is_positive(),
          "Q(sqrt3) sign: -1 + sqrt3 > 0 by exact square compare")
    check(not RationalSurd(Fraction(-2), Fraction(1)).is_positive(),
          "Q(sqrt3) sign: -2 + sqrt3 < 0 by exact square compare")


def _p(a=0, b=0) -> Phi:
    return Phi(Fraction(a), Fraction(b))


def _point(x: Phi, y: Phi, z: Phi = PHI_ZERO) -> Vec3Phi:
    return Vec3Phi(x, y, z)


def test_segment_predicates_over_qphi():
    half_phi = Phi(ZERO, Fraction(1, 2))
    phi = Phi(ZERO, ONE)
    p0 = _point(PHI_ZERO, PHI_ZERO)
    p1 = _point(phi, PHI_ZERO)
    q0 = _point(half_phi, _p(-1))
    q1 = _point(half_phi, _p(1))
    check(segments_intersect_interior(p0, p1, q0, q1),
          "Q(phi) segment intersection returns a verdict instead of crashing")
    check(segments_contact_closed(p0, p1, q0, q1),
          "Q(phi) segment contact accepts the same interior crossing")

    p0 = _point(_p(0), PHI_ZERO)
    p1 = _point(_p(3), PHI_ZERO)
    q0 = _point(_p(1), PHI_ZERO)
    q1 = _point(_p(4), PHI_ZERO)
    check(segments_intersect_interior(p0, p1, q0, q1),
          "collinear overlapping interiors are detected")
    check(segments_contact_closed(p0, p1, q0, q1),
          "closed contact detects the same collinear overlap")

    p0 = _point(_p(0), PHI_ZERO)
    p1 = _point(_p(2), PHI_ZERO)
    q0 = _point(_p(1), PHI_ZERO)
    q1 = _point(_p(1), _p(1))
    check(not segments_intersect_interior(p0, p1, q0, q1),
          "T-junction endpoint-on-interior is not an open-interval intersection")
    check(segments_contact_closed(p0, p1, q0, q1),
          "T-junction endpoint-on-interior is closed-interval contact")

    p0 = _point(_p(0), PHI_ZERO)
    p1 = _point(_p(2), PHI_ZERO)
    q0 = _point(_p(0), _p(1))
    q1 = _point(_p(2), _p(1))
    check(not segments_intersect_interior(p0, p1, q0, q1),
          "non-touching parallel struts have no open-interval intersection")
    check(not segments_contact_closed(p0, p1, q0, q1),
          "non-touching parallel struts have no closed-interval contact")


def test_canonical_six_strut_balances():
    sys = make_tensegrity_six_strut()
    sys.configure()
    check(sys.state == TensegrityState.CONFIGURING,
          "canonical six-strut fixture enters CONFIGURING")
    sys.verify_balance()
    check(sys.state == TensegrityState.BALANCED,
          f"canonical expanded-octahedron fixture reaches BALANCED ({sys.fault_detail})")
    check(len(sys.equilibrium_densities) == len(sys.edges),
          "canonical equilibrium density assigned to every edge")
    check(all((e.edge_type == EdgeType.STRUT and (-q).is_positive()) or
              (e.edge_type != EdgeType.STRUT and q.is_positive())
              for e, q in zip(sys.edges, sys.equilibrium_densities)),
          "canonical equilibrium densities have cable/GAP positive and strut negative signs")


def test_canonical_fixture_geometry_and_ratio():
    sys = make_tensegrity_six_strut()
    cables = [e for e in sys.edges if e.edge_type == EdgeType.CABLE]
    struts = [e for e in sys.edges if e.edge_type == EdgeType.STRUT]
    check(len(cables) == 24, "canonical fixture has 24 inter-rectangle cables")
    check(len(struts) == 6, "canonical fixture has six struts")
    check(all(sys.nodes[e.node_a].quadrance_to(sys.nodes[e.node_b]) == Phi.from_int(6)
              for e in cables),
          "canonical cables all have quadrance 6")
    check(all(sys.nodes[e.node_a].quadrance_to(sys.nodes[e.node_b]) == Phi.from_int(16)
              for e in struts),
          "canonical struts all have quadrance 16")

    result = solve_equilibrium(sys.nodes, sys.edges)
    cable_density = next(q for e, q in zip(sys.edges, result.densities)
                         if e.edge_type == EdgeType.CABLE)
    strut_density = next(q for e, q in zip(sys.edges, result.densities)
                         if e.edge_type == EdgeType.STRUT)
    check(result.ok and cable_density * 3 == (-strut_density) * 2,
          "solver derives exact q_cable:q_strut = 2:-3 ratio")


def test_strut_collision_detected():
    sys = make_tensegrity_six_strut()
    strut_idxs = [i for i, e in enumerate(sys.edges) if e.edge_type == EdgeType.STRUT]
    sys.edges[strut_idxs[1]] = Edge(0, 9, EdgeType.STRUT)
    sys.configure()
    sys.verify_balance()
    check(sys.state == TensegrityState.FAULT_STRUT_COLLISION,
          "shared strut endpoint faults STRUT_COLLISION")


def test_cable_slack_detected():
    sys = make_tensegrity_six_strut()
    for e in sys.edges:
        if e.edge_type == EdgeType.CABLE:
            sys.nodes[e.node_b] = sys.nodes[e.node_a]
            break
    sys.configure()
    sys.verify_balance()
    check(sys.state == TensegrityState.FAULT_CABLE_SLACK,
          "zero-length cable faults CABLE_SLACK")


def test_grid_mismatch_detected():
    sys = make_tensegrity_six_strut()
    sys.grid_states[0] = GridState.CONJ
    sys.configure()
    sys.verify_balance()
    check(sys.state == TensegrityState.FAULT_GRID_MISMATCH,
          "cross-grid non-GAP edge faults GRID_MISMATCH")


def test_gap_edge_allows_crossing_guard():
    sys = make_tensegrity_six_strut()
    sys.grid_states[0] = GridState.CONJ
    for i, e in enumerate(sys.edges):
        if e.node_a == 0 or e.node_b == 0:
            sys.edges[i] = Edge(e.node_a, e.node_b, EdgeType.GAP, e.rest_quadrance)
    check(sys.guard_grid_consistency(),
          "GAP-marked cross-grid edges pass grid-consistency guard")


def test_fault_is_terminal():
    sys = make_tensegrity_six_strut()
    for e in sys.edges:
        if e.edge_type == EdgeType.CABLE:
            sys.nodes[e.node_b] = sys.nodes[e.node_a]
            break
    sys.configure()
    sys.verify_balance()
    check(sys.state == TensegrityState.FAULT_CABLE_SLACK,
          "fault setup reaches CABLE_SLACK")
    fault_state = sys.state
    try:
        sys.verify_balance()
        check(False, "verify_balance from a fault state must assert")
    except AssertionError:
        check(sys.state == fault_state, "fault state is terminal until reset")


def test_disconnected_topology_detected():
    sys = TensegritySystem(
        nodes=[Vec3Phi.origin() for _ in range(6)],
        grid_states=[GridState.MAIN] * 6,
        edges=[
            Edge(0, 1, EdgeType.STRUT),
            Edge(0, 2, EdgeType.STRUT),
            Edge(1, 2, EdgeType.STRUT),
            Edge(3, 4, EdgeType.STRUT),
            Edge(3, 5, EdgeType.STRUT),
            Edge(4, 5, EdgeType.STRUT),
        ],
    )
    sys.configure()
    check(sys.state == TensegrityState.FAULT_TOPOLOGY,
          "disconnected topology faults at configure")


def test_equilibrium_derivation_and_breakage():
    sys = make_tensegrity_six_strut()
    result = solve_equilibrium(sys.nodes, sys.edges)
    check(result.ok, "exact force-density solver finds canonical self-stress")
    cable_density = next(q for e, q in zip(sys.edges, result.densities)
                         if e.edge_type == EdgeType.CABLE)
    strut_density = next(q for e, q in zip(sys.edges, result.densities)
                         if e.edge_type == EdgeType.STRUT)
    check(cable_density.is_positive() and (-strut_density).is_positive(),
          "derived equilibrium ratio has cable positive and strut negative signs")

    perturbed = make_tensegrity_six_strut()
    v = perturbed.nodes[0]
    perturbed.nodes[0] = Vec3Phi(v.x + PHI_ONE, v.y, v.z)
    perturbed.configure()
    perturbed.verify_balance()
    check(perturbed.state == TensegrityState.FAULT_NOT_IN_EQUILIBRIUM,
          "perturbing one vertex breaks equilibrium")

    flipped = make_tensegrity_six_strut()
    for i, e in enumerate(flipped.edges):
        if e.edge_type == EdgeType.CABLE:
            flipped.edges[i] = Edge(e.node_a, e.node_b, EdgeType.STRUT, e.rest_quadrance)
            break
    flipped.configure()
    flipped.verify_balance()
    check(flipped.fault in (TensegrityFault.STRUT_COLLISION,
                            TensegrityFault.NOT_IN_EQUILIBRIUM),
          "flipping one cable to strut breaks structural/equilibrium guards")


def test_antipodal_counterexample_fails_only_interior_guard():
    sys = make_tensegrity_antipodal_counterexample()
    check(sys.guard_valid_topology(), "antipodal counterexample passes topology guard")
    check(sys.guard_struts_separated(), "antipodal counterexample passes endpoint-separation guard")
    check(sys.guard_cables_taut(), "antipodal counterexample passes tautness guard")
    check(sys.guard_grid_consistency(), "antipodal counterexample passes grid-consistency guard")
    check(sys.guard_equilibrium(), "antipodal counterexample passes equilibrium guard")
    check(not sys.guard_struts_disjoint_interior(),
          "antipodal counterexample fails exactly strut interior-intersection guard")

    balanced = make_tensegrity_antipodal_counterexample()
    balanced.configure()
    balanced.verify_balance()
    check(balanced.state == TensegrityState.FAULT_STRUT_INTERSECTION,
          "antipodal counterexample reaches STRUT_INTERSECTION terminal fault")


def test_regular_icosahedron_24_cable_net_has_no_self_stress():
    regular = make_tensegrity_antipodal_counterexample()
    short_rectangle_edges = {
        (0, 2), (1, 3),
        (4, 6), (5, 7),
        (8, 9), (10, 11),
    }
    edges = []
    for i in range(len(regular.nodes)):
        for j in range(i + 1, len(regular.nodes)):
            if ((i, j) not in short_rectangle_edges and
                    regular.nodes[i].quadrance_to(regular.nodes[j]) == Phi.from_int(4)):
                edges.append(Edge(i, j, EdgeType.CABLE, Phi.from_int(4)))
    for a, b in [(0, 1), (2, 3), (4, 5), (6, 7), (8, 10), (9, 11)]:
        edges.append(Edge(a, b, EdgeType.STRUT,
                          regular.nodes[a].quadrance_to(regular.nodes[b])))

    result = solve_equilibrium(regular.nodes, edges)
    check(len([e for e in edges if e.edge_type == EdgeType.CABLE]) == 24,
          "regular-icosahedron comparison uses the 24-cable net")
    check(not result.ok,
          "regular-icosahedron vertex set has no 24-cable-net self-stress")


if __name__ == "__main__":
    print("=== Tensegrity balancer exact oracle tests ===")
    for case in (
        test_exact_surd_sign_cases,
        test_segment_predicates_over_qphi,
        test_canonical_six_strut_balances,
        test_canonical_fixture_geometry_and_ratio,
        test_strut_collision_detected,
        test_cable_slack_detected,
        test_grid_mismatch_detected,
        test_gap_edge_allows_crossing_guard,
        test_fault_is_terminal,
        test_disconnected_topology_detected,
        test_equilibrium_derivation_and_breakage,
        test_antipodal_counterexample_fails_only_interior_guard,
        test_regular_icosahedron_24_cable_net_has_no_self_stress,
    ):
        run_case(case)

    print(f"\n{passed} passed, {failed} failed")
    if failed:
        print("FAIL")
        sys.exit(1)
    print("PASS")
