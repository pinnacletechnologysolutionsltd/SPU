"""Measured instrumentation for the fixed REL-1 programs. Run: python3 -B -I research/rel1/report.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import backends as B   # noqa: E402
import machine as Mc   # noqa: E402
import program as P    # noqa: E402

RUNS = (("P1 mixed (30 cmds, d=1)", P.P1, {}), ("P3 chain (32 cmds, d=1, lemma)", P.P3, {"lemma": True}),
        ("P2 gap (8 cmds, d=1)", P.P2, {}), ("P2 gap (8 cmds, d=3)", P.P2, {"d": 3}))
for title, prog, kw in RUNS:
    print(title)
    for be in (B.Relational, B.Conventional):
        m = Mc.Machine(be, **kw)
        out = P.execute(m, prog)
        by = {k: v.total() for k, v in m.cost.items()}
        sizes = m.sizes()
        print(f"  {be.name:12s} materialise={m.count['materialise']} ops_total={sum(by.values())} by_op={by} "
              f"states={len(m.states)} state_scalars={[s[0] for s in sizes]} state_bits={sum(s[1] for s in sizes)} "
              f"certs={len(m.certs)} obs={len(m.obs)} refused={sum(o['status'] == 'REFUSED' for o in out)}")
