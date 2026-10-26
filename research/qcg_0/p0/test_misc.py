"""Writer cap contract, capability tasks, gates, class gates and the mutant suite. Collected by test_p0.py."""
import os
import tempfile
import classes, gates, joins, mutants, mutants2
from test_lu import test
from writer import CapBreach, Out


@test
def writer_caps_and_exclusive_create():
    with tempfile.TemporaryDirectory() as d:
        o = Out(d, file_cap=10, total_cap=15)
        o.write("a", b"0123456789")
        try:
            o.write("b", b"0123456")                          # total 17 > 15
            raise AssertionError("total cap not enforced")
        except CapBreach:
            pass
        try:
            Out(d, 10, 100).write("a", b"x")                  # exclusive create: never overwrites
            raise AssertionError("overwrite allowed")
        except FileExistsError:
            pass
        try:
            Out(d, 3, 100).write("c", b"toolong")             # per-file cap
            raise AssertionError("file cap not enforced")
        except CapBreach:
            pass
        assert o.breach() == 90 and os.path.exists(os.path.join(d, "CAP_BREACH")) and not os.path.exists(os.path.join(d, "RUNNER_DONE"))


@test
def capability_tasks_match_references():
    r = {n: getattr(joins, n)() for n in ("s4", "s5", "s6", "loops", "phi_bad")}
    assert all(v["mismatches"] == [] for v in r.values()), {k: v["mismatches"] for k, v in r.items()}
    assert r["s4"]["checks"] == 897 and r["phi_bad"]["ACCUMULATED_LENGTH"] == "REFUSED(OUT_OF_DOMAIN)"


@test
def comparator_guard_trigger_rules():
    tot = lambda **k: dict({c: 10 for c in gates.GUARD}, **k)                                # noqa: E731
    arms = {"B-b": {"role": "conventional", "all_ok": True, "total": tot(M=5)},
            "B-a": {"role": "conventional", "all_ok": True, "total": tot(M=5)},          # tie: ASCII order picks B-a
            "B-x": {"role": "conventional", "all_ok": False, "total": tot(M=1)},         # ineligible
            "C": {"role": "candidate", "all_ok": True, "total": tot(M=5, T_ret_peak=5, A=11)}}
    assert gates.comparator(arms) == "B-a"
    e = gates.evaluate(arms, "C")
    assert e["trigger"]["T_ret_peak"] and not e["trigger"]["M"] and e["tradeoff"] and not e["signal"] and e["verdict"] == "TRADE-OFF"
    arms["C"]["total"] = tot(M=4, T_ret_peak=5)               # M exactly -20% also triggers (5*4 <= 4*5)
    assert gates.evaluate(arms, "C")["verdict"] == "SIGNAL"


@test
def class_gates():
    assert classes.retiming_class([(0, 1), (1, 1)], [(1, 1), (1, 1)])["code"] == "OUT_OF_DOMAIN"
    assert classes.retiming_class([(1, 1), (-1, 1)], None, "primitive")["status"] == "OK"
    assert classes.retiming_class([(0, 1), (0, 1), (1, 1)], None, "primitive")["code"] == "NOT_PRIMITIVE_RETIMING"
    assert classes.jet_exact(3, 3)["code"] == "APPROX_NOT_EXACT"


@test
def every_mutant_is_killed():
    res = {k: f()[0] for k, f in list(mutants.MUTANTS.items()) + list(mutants2.MUTANTS2.items())}
    assert len(res) == 24 and all(res.values()), [k for k, v in res.items() if not v]
