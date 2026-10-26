"""REL-1 tests. Run: timeout 120 bash -c 'ulimit -v 1048576; python3 -B -I research/rel1/test_rel1.py'"""
from __future__ import annotations

import os
import sys
from fractions import Fraction as Fr

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "phy_r3"))
import backends as B       # noqa: E402
import machine as Mc       # noqa: E402
import program as P        # noqa: E402
import review_phy_r3 as RV  # noqa: E402
from field import QF       # noqa: E402

BACKENDS = (B.Relational, B.Conventional)
P1_STATUS = (
    "UNRESOLVED VALID EXACT EXACT COMMITTED UNRESOLVED REUSED REUSED REUSED REFUSED EXACT VALID EXACT "
    "COMMITTED EXACT UNRESOLVED REFUSED REFUSED REUSED REFUSED COMMITTED REUSED COMMITTED REUSED REUSED "
    "REUSED REUSED EXACT REFUSED REFUSED").split()
P1_ERRORS = {9: "DEPENDENCIES_CHANGED", 16: "INVALID_STATE", 17: "DEPENDENCIES_CHANGED", 19: "STALE_STATE",
             28: "INADMISSIBLE_EDIT", 29: "INADMISSIBLE_EDIT"}


def run(backend, prog, **kw):
    m = Mc.Machine(backend, **kw)
    return m, P.execute(m, prog)


def test_phy_r3_review_passes_before_use():
    r = RV.review()
    assert r["formula_exact_squared"] and r["mutant_s_equals_kappa_killed"] and r["hooke_numeric_corroboration"]
    assert all(s["penalised_rank"] == 30 and s["penalised_psd"] and s["nullity_ldl"] == 6 for s in r["states"])


def test_p1_matches_expected_semantics_and_backends_agree():
    outs = []
    for be in BACKENDS:
        m, out = run(be, P.P1)
        assert [o["status"] for o in out] == P1_STATUS, be.name
        assert {i: o["error"] for i, o in enumerate(out) if "error" in o} == P1_ERRORS
        assert out[2]["value"] is True and out[10]["value"] is True and out[14]["value"] is False
        outs.append((out, m.snapshot()))
    assert outs[0] == outs[1], "relational and conventional differ"


def test_atomicity_and_immutable_handles():
    for be in BACKENDS:
        m = Mc.Machine(be)
        seen = []
        for c in P.P1:
            before, states = m.snapshot(), m.states
            r = m.step(c)
            if r["status"] in ("REFUSED", "UNRESOLVED") or c[0] == "QUERY":
                assert m.snapshot() == before, (be.name, c[0], r)
            assert all(a is b for a, b in zip(states, m.states)), "state replaced"
            seen.append(len(m.states))
        assert seen == sorted(seen) and m.states[4].gid == m.states[0].gid      # restoration: new handle, same content
        assert len({id(s) for s in m.states}) == 5


def test_independent_oracles_agree():
    import test_phy_r3 as T3                                   # PHY-R3 (reviewed above) and PHY-R1/R2 oracles
    A, fixture = T3.A, T3.Hs.fixture
    m, out = run(B.Conventional, P.P1)
    for h, Mt in ((0, P.M()), (1, P.MA)):
        pts = [tuple(QF.of(Fr(c), 1) for c in p) for p in m.states[h].x]
        assert A.coordinate_equilibrium(pts, A.target_densities(T3.MACH), T3.E, 1)
        assert fixture.oracle_verdict(pts, T3.E, 1) == "BALANCED"
        assert T3.certify(tuple(tuple(Fr(v) for v in r) for r in Mt), "squared")["verdict"] == "STRICT_STABLE"
    moved = [tuple(QF.of(Fr(c), 1) for c in p) for p in m.states[2].x]
    assert not A.coordinate_equilibrium(moved, A.target_densities(T3.MACH), T3.E, 1)
    rec = out[27]["receipt"][1]                                 # observed restored state == reference points
    assert [tuple(Fr(c) for c in p) for p in rec] == [tuple(Fr(c) for c in p) for p in m.states[0].x]


def test_representation_gap_is_explicit_not_silent():
    (mr, r), (mc, c) = run(B.Relational, P.P2), run(B.Conventional, P.P2)
    assert [o["status"] for o in r] == "COMMITTED VALID EXACT REFUSED COMMITTED EXACT EXACT UNRESOLVED".split()
    assert r[3]["error"] == "OUT_OF_FIELD" and r[2]["value"] is True and r[6]["value"] is True
    assert c[0] == {"status": "REFUSED", "error": "OUT_OF_FIELD"} and c[4] == c[0]
    assert all(o["error"] == "BAD_HANDLE" for i, o in enumerate(c) if i not in (0, 4))
    assert mr.count["materialise"] == 1 and not any(mr.states[h].kind == "coords" for h in range(3))
    # with d=3 the half-metric materialises in Q(sqrt3): both agree exactly, QF receipts included
    (mr3, r3), (mc3, c3) = run(B.Relational, P.P2, d=3), run(B.Conventional, P.P2, d=3)
    assert r3[:4] == c3[:4] and r3[3]["status"] == "EXACT" and r3[3]["receipt"][1][0][0][2] == 3
    assert r3[4]["status"] == "COMMITTED" and c3[4] == {"status": "REFUSED", "error": "OUT_OF_FIELD"}


def test_p3_lemma_reuse_agrees_with_fresh_validation_and_defers_materialisation():
    res = {}
    for be in BACKENDS:
        m, out = run(be, P.P3, lemma=True)
        assert [o["status"] for o in out][-1] == "EXACT" and all(o["status"] != "REFUSED" for o in out)
        for h in range(1, 7):
            c = m.certs[(h, "stability")]
            assert c.basis.startswith("reused_lemma") and c.value is True
            fresh = m.b.compute(m.states[h], "stability", Mc.X.Ops())
            assert fresh is True, "lemma-reused certificate disagrees with fresh exact test"
        res[be.name] = (out, m.count["materialise"])
    assert res["relational"][0] == res["conventional"][0]
    assert res["relational"][1] == 1 and res["conventional"][1] == 7
    for be in BACKENDS:                                           # lemma off: stability must be recomputed
        m, out = run(be, P.P3, lemma=False)
        assert out[5]["status"] == "REFUSED" and out[5]["error"] == "DEPENDENCIES_CHANGED"


def test_negative_controls():
    bad = [P.M(v) for v in (Fr(1), Fr(6, 5))] + [P.M(Fr(3, 5), diag=(Fr(9, 8), 1, 1)),
                                                 ((1, Fr(3, 5), 0), (Fr(1, 5), 1, 0), (0, 0, 1)),
                                                 P.M(Fr(2 ** 40, 2 ** 41 + 1))]
    for be in BACKENDS:
        m = Mc.Machine(be)
        for M_ in bad:
            before = m.snapshot()
            assert m.step(("TRANSFORM", M_)) == {"status": "REFUSED", "error": "INADMISSIBLE_EDIT"}
            assert m.snapshot() == before
        for c in (("TRANSFORM", True), ("MOVE", (0, 1, 2), (0, 0, 1)), ("MOVE", (0,), (0, 0, 0)),
                  ("QUERY", 0, "nope"), ("OBSERVE", True), ("OBSERVE", 7), ("JUMP", 1), "x"):
            assert m.step(c)["status"] == "REFUSED"
        assert m.states == m.states[:1] and m.transitions == 0
        m2 = Mc.Machine(be, state_capacity=2)                  # capacities
        assert m2.step(("TRANSFORM", P.MA))["status"] == "COMMITTED"
        assert m2.step(("TRANSFORM", P.MB))["error"] == "STATE_CAPACITY"
        m3 = Mc.Machine(be, certificate_capacity=3)
        assert m3.step(("VALIDATE", 0))["error"] == "CERTIFICATE_CAPACITY" and not m3.certs
        m4 = Mc.Machine(be)
        for _ in range(8):
            assert m4.step(("TRANSFORM", P.M(Fr(3, 5))))["status"] == "COMMITTED"
        assert m4.step(("TRANSFORM", P.MA))["error"] in ("TRANSITION_LIMIT", "STATE_CAPACITY")
        m5 = Mc.Machine(be)
        for _ in range(32):
            m5.step(("QUERY", 0, "equilibrium"))
        assert m5.step(("QUERY", 0, "equilibrium")) == {"status": "REFUSED", "error": "COMMAND_LIMIT"}
    # stale-certificate mutant: skipping the dependency check wrongly carries equilibrium to a moved state
    for be in BACKENDS:
        m, out = run(be, P.P1[:17] + (("REUSE", 1, "equilibrium"),), skip_dependency_check=True)
        assert out[17]["status"] == "REUSED"                   # mutant accepts ...
        fresh = Mc.Machine(B.Conventional)
        fresh.step(("TRANSFORM", P.MA)), fresh.step(("MOVE", (0, 1), (0, 0, 1)))
        assert fresh.step(("QUERY", 2, "equilibrium"))["value"] is False     # ... independent check rejects it


def test_determinism_and_instrumentation():
    for be in BACKENDS:
        (m1, o1), (m2, o2) = run(be, P.P1), run(be, P.P1)
        assert o1 == o2 and m1.snapshot() == m2.snapshot()
        assert {k: dict(v) for k, v in m1.cost.items()} == {k: dict(v) for k, v in m2.cost.items()}
        assert dict(m1.count) == dict(m2.count) and sum(v.total() for v in m1.cost.values()) > 0
    rel, conv = Mc.Machine(B.Relational), Mc.Machine(B.Conventional)
    assert rel.sizes()[0][0] == 6 and conv.sizes()[0][0] == 36


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    for t in TESTS:
        t()
        print("PASS", t.__name__)
    print(f"PASS all {len(TESTS)} REL-1 test groups")
