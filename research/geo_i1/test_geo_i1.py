"""GEO-I1 tests. Run: timeout 120 bash -c 'ulimit -v 1048576; python3 -B -I research/geo_i1/test_geo_i1.py'"""
from __future__ import annotations

import os
import sys
from collections import Counter
from fractions import Fraction as Fr

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gi_baseline as B    # noqa: E402
import gi_engine as E      # noqa: E402
import gi_metric as GM     # noqa: E402
import gi_scene as S       # noqa: E402
import gi_session as G     # noqa: E402
import hier as H           # noqa: E402

PTS = H.gbt.domain(S.K)
SHAPES = {s.sid: s for s in S.scene()}
M0, M12, M13 = G.M3(), G.M3(Fr(3, 5)), G.M3(Fr(3, 5), Fr(1, 2))


def tests_of(eng, sid, M):
    before = Counter(eng.ctr)
    cover = eng.query(SHAPES[sid], M, "refine")
    d = {k: eng.ctr[k] - before[k] for k in ("bound", "point", "reused")}
    return d["bound"] + d["point"], d["reused"], cover


def run_program(**kw):
    s = G.Session(**kw)
    steps = []
    for label, cmd in G.PROGRAM:
        r = s.command(cmd) if cmd else None
        steps.append((label, r, s.query_all(label)))
    return s, steps


def wrongs(row, name):
    return sum(rec[name].get("wrong", 0) for rec in row["shapes"].values() if name in rec)


def test_bounds_exact_conservative_and_scaled():
    full = H.Hierarchy(S.K, lambda c: True)
    for m in (Fr(0), Fr(3, 5), Fr(1, 2), Fr(-1, 2), Fr(4, 5), Fr(1, 3), Fr(-7, 10)):
        ex, sc = GM.table_exact(m, S.K, Counter()), GM.table_scaled(m, S.K, Counter())
        for c in full.nodes:                                    # every node, every descendant
            assert max(GM.Q(m, x) for x in H.offsets(c[2])) == ex[c[2]]
        assert all(a <= b for a, b in zip(ex, sc))              # scaled certificate is conservative
        assert all(GM.Q(m, x) <= sc[4] for x in PTS)
        assert any(GM.Q(m, x) == ex[4] for x in PTS)            # exact bound is attained (tight)


def test_integrated_program_is_exact_in_every_engine():
    s, steps = run_program()
    assert [(st[1] or {}).get("status") for st in steps] == [None, "COMMITTED", "COMMITTED", "COMMITTED",
                                                              "REFUSED", "COMMITTED", "COMMITTED", "COMMITTED"]
    assert steps[4][1]["error"] == "INADMISSIBLE_EDIT"
    assert steps[5][2] == {"step": "MOVE strut (non-affine)", "status": "REFUSED", "error": "NOT_A_METRIC_STATE"}
    refused_at = {}
    for label, _, row in steps:
        if row["status"] != "OK":
            continue
        for name in list(s.engines) + ["flat", "exh", "coord"]:
            assert wrongs(row, name) == 0, (label, name)
        for sid, rec in row["shapes"].items():
            for n in s.engines:
                assert rec[n]["partition_ok"]
                if n != "H_exact_static":
                    assert rec[n]["unres"] == 0                  # refine mode resolves everything
            assert rec["H_exact_refine"]["unres"] == 0
            if "refused" in rec["coord"]:
                refused_at.setdefault(label, []).append(sid)
    assert refused_at == {"T m13=1/2 (m12 kept)": ["md13"], "T relational-only M2": ["md12", "md13", "md23"]}
    assert any(rec["H_exact_static"]["unres"] for _, _, row in steps if row["status"] == "OK"
               for rec in row["shapes"].values())            # static mode reports UNRESOLVED explicitly
    assert s.rel.count["materialise"] == 1                     # only REL-1's MOVE needed coordinates


def test_selective_invalidation_by_dependency_content():
    eng = E.Engine()
    for sid in SHAPES:
        tests_of(eng, sid, M0)
    for sid in SHAPES:                                          # repeated query: nothing recomputed
        t, r, _ = tests_of(eng, sid, M0)
        assert t == 0 and r > 0
    expect_changed = {"md12": True, "md13": False, "md23": False, "nat_disk": False, "nat_halfplane": False}
    for sid in SHAPES:                                          # only m12 changes
        t, r, _ = tests_of(eng, sid, M12)
        assert (t > 0) == expect_changed[sid], sid
    for sid in SHAPES:                                          # only m13 changes
        t, r, _ = tests_of(eng, sid, M13)
        assert (t > 0) == (sid == "md13"), sid
    M2 = G.M3(Fr(1, 3), Fr(1, 4), Fr(1, 5))                     # all three change; natives untouched
    for sid in SHAPES:
        assert (tests_of(eng, sid, M2)[0] > 0) == (SHAPES[sid].native is None), sid
    single, content = E.Engine(), E.Engine(slots="content")      # restoration: content slots reuse, single does not
    for eng2 in (single, content):
        for M in (M0, M12, M0):
            for sid in ("md12",):
                last = tests_of(eng2, sid, M)[0]
        assert (last == 0) == (eng2 is content)


def test_rel1_refusals_are_atomic_for_certificates():
    s = G.Session()
    s.query_all("start")
    snap = (dict((n, len(e.certs)) for n, (e, _) in s.engines.items()), s.metric())
    for bad in (G.M3(Fr(1)), G.M3(Fr(6, 5)), ((Fr(9, 8), 0, 0), (0, 1, 0), (0, 0, 1)),
                ((1, Fr(1, 2), 0), (Fr(1, 3), 1, 0), (0, 0, 1))):
        assert s.command(("TRANSFORM", bad))["status"] == "REFUSED"
    assert snap == (dict((n, len(e.certs)) for n, (e, _) in s.engines.items()), s.metric())
    row = s.query_all("after refusals")
    assert all(c["bound"] == 0 and c["point"] == 0 for k, c in row["delta"].items() if k.startswith("H_"))


def test_mutants_are_detected_and_controls_stay_exact():
    cases = {"stale": dict(check_dep=False), "wrong_entry": dict(dep_mode="wrong_entry"), "false_bound": dict(wrong_bound=True)}
    engines = {k: (E.Engine(**v), "refine") for k, v in cases.items()}
    engines["declared"] = (E.Engine(), "refine")
    s, steps = run_program(engines=engines, flat_check_dep=False)
    for k in cases:
        assert sum(wrongs(row, k) for _, _, row in steps if row["status"] == "OK") > 0, k
    assert sum(wrongs(row, "declared") for _, _, row in steps if row["status"] == "OK") == 0
    assert sum(wrongs(row, "flat") for _, _, row in steps if row["status"] == "OK") > 0     # flat stale mutant
    s2, st2 = run_program(engines={"all": (E.Engine(dep_mode="all"), "refine"), "declared": (E.Engine(), "refine")})
    tot = lambda n: sum(sum(r["delta"][n][c] for c in ("bound", "point")) for _, _, r in st2 if r["status"] == "OK")  # noqa: E731
    assert sum(wrongs(row, "all") for _, _, row in st2 if row["status"] == "OK") == 0
    assert tot("all") > tot("declared")                        # over-broad dependency: exact but wasteful


def test_representation_gap_and_selective_observation():
    s = G.Session()
    s.command(("TRANSFORM", M12))
    assert s.query_all("m12=3/5")["shapes"]["md12"]["coord"] == {"wrong": 0}
    obs = s.observe([(3, 1), (1, 2), (-2, 0)])
    assert obs["status"] == "EXACT" and s.obs_ctr["materialise"] == 1 and s.obs_ctr["points"] == 3
    for (a, b), (x, y) in zip([(3, 1), (1, 2), (-2, 0)], obs["coords"]):
        assert x * x + y * y == GM.Q(Fr(3, 5), (a, b))             # coordinates reproduce the metric exactly
    s.command(("TRANSFORM", G.M3(Fr(1, 3))))
    row = s.query_all("m12=1/3")
    assert row["shapes"]["md12"]["coord"] == {"refused": "OUT_OF_FIELD"}
    assert wrongs(row, "H_exact_refine") == 0 and wrongs(row, "flat") == 0
    assert s.observe([(3, 1)]) == {"status": "REFUSED", "error": "OUT_OF_FIELD"} and s.obs_ctr["materialise"] == 1


def test_scaled_bounds_are_exact_and_trade_table_work_for_tests():
    s, steps = run_program()
    ok = [r for _, _, r in steps if r["status"] == "OK"]
    tests = lambda n: sum(r["delta"][n][c] for r in ok for c in ("bound", "point"))   # noqa: E731
    assert wrongs(ok[0], "H_scaled_refine") == 0 and all(wrongs(r, "H_scaled_refine") == 0 for r in ok)
    assert tests("H_scaled_refine") >= tests("H_exact_refine")
    assert sum(r["delta"]["H_scaled_refine"]["table_evals"] for r in ok) == 0
    assert sum(r["delta"]["H_exact_refine"]["table_evals"] for r in ok) >= 2801 * 5


def test_determinism_and_measurements_present():
    (s1, a), (s2, b) = run_program(), run_program()
    assert [r for _, _, r in a] == [r for _, _, r in b] and s1.footprint() == s2.footprint()
    assert all("delta" in r and r["delta"]["flat"] is not None for _, _, r in a if r["status"] == "OK")
    assert s1.oracle_ctr["oracle_point"] > 0 and s1.coord_ctr["materialise"] > 0


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    for t in TESTS:
        t()
        print("PASS", t.__name__)
    print(f"PASS all {len(TESTS)} GEO-I1 test groups")
