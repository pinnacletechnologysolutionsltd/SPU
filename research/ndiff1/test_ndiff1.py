"""Controls for NDIFF-1: detectors accept good cases and reject mutants."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ndiff1 as N
import rep, cost
from rep import *
from curve import sample_curve

base = sample_curve()
chain = N.CHAINS["H rot30,scale r3,t2"]
r = rep.from_ph(base, "GEN")
for op, nm in chain:
    r = rep.step(r, op, N.arg(op, nm))
out = cost.ph_eval(r, N.T0)
N.check(out, chain, base)                     # good case accepted
bad = dict(out); bad["Q"] = out["Q"] + ONE
try:
    N.check(bad, chain, base); raise SystemExit("FAIL mutant accepted")
except AssertionError:
    pass
# a different chain (rot60 instead of rot30) must disagree with the oracle
other = [("rot", "r60")] + chain[1:]
try:
    N.check(out, other, base); raise SystemExit("FAIL wrong chain accepted")
except AssertionError:
    pass
# the transforms commute as maps (reversed chain is the same curve): oracle agrees, documenting why order is not a control
N.check(out, list(reversed(chain)), base)
# representability: r60/scale3 yes; r30, sqrt3-scale, t2 no
for ch, ok in (("A rot60", True), ("C scale3", True), ("B rot30", False), ("D scale r3", False), ("E t2", False)):
    res = N.run_chain(N.CHAINS[ch], base)
    assert ("unrepresentable" not in res["PRIM"]) == ok, ch
    assert "unrepresentable" not in res["GEN"]
# composed-at-evaluation has zero maintenance and matches oracle (checked inside run_chain)
assert N.run_chain(N.CHAINS["E t2"], base)["COMP_PH"]["maint"] == 0
print("PASS test_ndiff1")
