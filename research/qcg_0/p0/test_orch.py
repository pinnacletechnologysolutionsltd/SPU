"""Budget, sequential refusal rule, orchestration, role matching and frontier reporting tests. Collected by test_p0.py."""
import os
import gates
from test_lu import test


@test
def op_budget_stops_before_the_operation():
    from account import Ledger
    from events import OpBudget, P4096
    from ledger import lit
    old = Ledger.GRAND[0], Ledger.LIMIT
    try:
        L = Ledger(P4096, "T")
        L.begin("Q", 0)
        Ledger.GRAND[0], Ledger.LIMIT = 0, 3
        a = lit(3, L)
        with L.enter("a1"):
            a * a, a + a, a - a                          # exactly 3 counted operations: allowed
            try:
                a * a
                raise AssertionError("fourth operation executed")
            except OpBudget as e:
                assert e.event == "T.Q.q00.a1.4", e.event
        assert L.c["M"] == 1 and Ledger.GRAND[0] == 3    # the refused operation left no count behind
        Ledger.GRAND[0], Ledger.LIMIT = 0, 1
        try:
            lit(1, L) / lit(0, L)                         # DIV_ZERO is administrative: not a counted operation
        except Exception as e:  # noqa: BLE001
            assert e.code == "DIV_ZERO"
        assert Ledger.GRAND[0] == 0
    finally:
        Ledger.GRAND[0], Ledger.LIMIT = old


@test
def sequential_refusal_rule():
    import arms_seq, arms_seq2, refs
    from events import W31, Profile
    for cls in (arms_seq.SeqH, arms_seq.SeqF, arms_seq2.SeqC2, arms_seq2.SeqPH):         # PH5 S3: sample 1 refuses, S3 reads Sprev
        a = cls(W31, refs.source("PH5"), "S3")
        a.prepare()
        sts = [r["status"] for r in a.run_tape()]
        assert sts[:2] == ["OK", "REFUSED"] and sts[2:] == ["NOT_ISSUED"] * 15, (cls.name, sts)
    tight = Profile("T", 23, 46)                                        # forces mid-tape refusals on S1 (no Sprev dependence)
    h = arms_seq.SeqH(tight, refs.source("PH5"), "S1")
    f = arms_seq.SeqF(tight, refs.source("PH5"), "S1")
    for a in (h, f):
        assert a.prepare() is None
    sh, sf = [r["status"] for r in h.run_tape()], [r["status"] for r in f.run_tape()]
    assert "REFUSED" in sh and "NOT_ISSUED" not in sh and len(sh) == 17        # stateless arm: every request still gets a status
    assert "REFUSED" in sf and "NOT_ISSUED" in sf                             # stepped tables: later samples would be off-grid


@test
def orchestration_and_serialization():
    import json
    import run
    import tempfile
    import artifact
    import campaign
    from events import P4096
    rows, _ = campaign.cell_a(P4096)
    fake = {"stage6_mutants": {"X": {"killed": True}}, "counted_operations": 1, "rows": rows}
    assert artifact.dumps(fake) == artifact.dumps(json.loads(artifact.dumps(fake)))        # canonical round trip

    def go(build, verdict=lambda R: True):
        d = tempfile.mkdtemp()
        return run.main(["--out", d], build, verdict), sorted(os.listdir(d))
    rc, files = go(lambda: fake)
    assert rc == 0 and "RUNNER_DONE" in files, (rc, files)
    assert {"results.json", "results.sha256", "readback.txt"} <= set(files)
    rc, files = go(lambda: fake, lambda R: False)
    assert rc == 1 and "RUNNER_DONE" not in files and "results.json" in files
    from events import OpBudget
    def boom_budget():
        raise OpBudget("x.Q.q00.a1.1")
    rc, files = go(boom_budget)
    assert rc == 92 and "RUNNER_DONE" not in files
    def boom():
        raise ValueError("x")
    rc, files = go(boom)
    assert rc == 2 and "RUNNER_DONE" not in files


@test
def role_matching_is_exact_for_sequential_arms():
    import stages
    assert stages.is_conv("PH", stages.CONV_S) and not stages.is_conv("PHFD", stages.CONV_S) and not stages.is_conv("C1", stages.CONV_S)
    assert stages.is_conv("B-PH", stages.CONV_A) and stages.is_conv("E-TS", stages.CONV_B) and not stages.is_conv("C2", stages.CONV_A)


@test
def conventional_frontier_is_reporting_only():
    tot = lambda **k: dict({c: 10 for c in gates.GUARD}, **k)                                # noqa: E731
    arms = {"A": {"role": "conventional", "all_ok": True, "total": tot(M=5, A=9)},
            "B": {"role": "conventional", "all_ok": True, "total": tot(M=6, A=9)},          # dominated by A
            "C": {"role": "conventional", "all_ok": True, "total": tot(M=7, A=2)},          # trade-off with A: kept
            "D": {"role": "conventional", "all_ok": True, "total": tot(M=5, A=9)},          # equal to A: both kept
            "E": {"role": "conventional", "all_ok": False, "total": tot(M=1, A=1)},         # ineligible: ignored
            "X": {"role": "candidate", "all_ok": True, "total": tot(M=1, A=1)}}              # candidate: ignored
    assert gates.frontier(arms) == ["A", "C", "D"]
    before = (gates.comparator(arms), gates.virtual_best(arms), gates.evaluate(arms, "X"))
    gates.frontier(arms)
    assert before == (gates.comparator(arms), gates.virtual_best(arms), gates.evaluate(arms, "X"))   # no side effects
    assert gates.comparator(arms) == "A" and gates.dominates(arms["A"]["total"], arms["B"]["total"])
    assert not gates.dominates(arms["A"]["total"], arms["D"]["total"])
