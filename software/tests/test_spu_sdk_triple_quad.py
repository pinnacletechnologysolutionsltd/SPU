#!/usr/bin/env python3
"""SPU-ECO-3: the triple-quad identity (Q1+Q2+Q3)^2 - 2(Q1^2+Q2^2+Q3^2) = 4 D^2 compiled as two independent programs
with the existing IR and v0.3 backend. Software verification only; no hardware run is claimed.
Three layers are kept apart: EXACT equality (unbounded mathematics, Program.exact), PREDICTED finite-width execution
(backend replay), ACTUAL execution (oracle and C++ simulator). A refusal is never counted as a numerical result.
Constants are re-materialized by hand where they are used (v0.3 has no data memory; the backend does not do it).
Run: python3 software/tests/test_spu_sdk_triple_quad.py"""
import random, subprocess, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'software/sdk'), str(ROOT / 'software/tests')]
import spu as CLI, spu_record as REC
from spu_ir import Program
import spu_v03_backend as B

fails = []
def check(name, cond):
    print(('PASS ' if cond else 'FAIL ') + name)
    if not cond: fails.append(name)

def quad(p, A, Bp):                                              # Q(A, B), constants created here (re-materialized)
    ax, ay, bx, by = (p.const(*t) for t in (A[0], A[1], Bp[0], Bp[1]))
    dx, dy = p.sub(bx, ax), p.sub(by, ay)
    return p.add(p.square(dx), p.square(dy))
def lhs(P3, k=2):                                                # (Q1+Q2+Q3)^2 - k (Q1^2+Q2^2+Q3^2), k = 2 is the identity
    p = Program(); A, Bp, C = P3
    q1, q2, q3 = quad(p, A, Bp), quad(p, Bp, C), quad(p, C, A)
    s = p.add(p.add(q1, q2), q3); kk = p.const(k)
    t = p.add(p.add(p.square(q1), p.square(q2)), p.square(q3))
    p.result(p.sub(p.square(s), p.mul(kk, t))); return p
def rhs(P3, k=4):                                                # k D^2 with D = (B-A) x (C-A), k = 4 is the identity
    p = Program(); A, Bp, C = P3
    ax, ay, bx, by, cx, cy = (p.const(*t) for t in (A[0], A[1], Bp[0], Bp[1], C[0], C[1]))
    u, v, w, z = p.sub(bx, ax), p.sub(cy, ay), p.sub(by, ay), p.sub(cx, ax)
    D = p.sub(p.mul(u, v), p.mul(w, z)); kk = p.const(k)
    p.result(p.mul(kk, p.square(D))); return p
def ipts(*c): return tuple(((c[i], 0, 1), (c[i + 1], 0, 1)) for i in (0, 2, 4))
def spts(*c): return tuple(((c[i], c[i + 1], 1), (c[i + 2], c[i + 3], 1)) for i in (0, 4, 8))

def agree(pred, rec):                                            # prediction vs an actual record: refusal status AND value
    r, f = rec['registers'], rec['flags']
    return (rec['cause'] == 'HALT' and bool(f['RS']) == pred.rs and (r[7]['a'], r[7]['b'], r[7]['d']) == (pred.s7, 0, 1)
            and (r[pred.rout]['a'], r[pred.rout]['b'], r[pred.rout]['d']) == pred.result)

with tempfile.TemporaryDirectory() as t:
    vm = Path(t) / 'spu_vm'
    check('C++ simulator builds', subprocess.run(['make', '-s', '-C', str(ROOT / 'software/vm'), f'BIN={vm}'], capture_output=True).returncode == 0)
    def build(prog):                                             # -> (image, words, prediction)
        asm, img, words, ins, rout = B.compile_v03(prog); return img, len(words), B.predict(ins, rout)
    def actual(img, sim=True):                                   # oracle always, simulator on request
        recs = {'oracle': REC.decode(CLI.run_oracle(img, 10000))}
        if sim: recs['sim'] = REC.decode(CLI.run_sim(img, 10000, str(vm)))
        return recs
    def value(rec): g = rec['registers'][0]; return (g['a'], g['b'], g['d'])

    # 1. standard integer triangle (0,0), (4,1), (1,3): D = 11, both sides 484
    T = ipts(0, 0, 4, 1, 1, 3); res = {}
    for nm, f in (('lhs', lhs), ('rhs', rhs)):
        p = f(T); img, w, pr = build(p); recs = actual(img)
        res[nm] = (p, w, pr, recs)
        check(f'standard triangle {nm}: {w} words, exact 484, predicted no refusal, S0 = 484 on oracle and simulator',
              p.exact() == (484, 0) and not pr.rs and all(agree(pr, r) and value(r) == (484, 0, 1) and r['flags']['RS'] == 0 for r in recs.values()))
    check('standard triangle: both sides identical in exact mode and on the machine', res['lhs'][0].exact() == res['rhs'][0].exact() and res['lhs'][2].result == res['rhs'][2].result)
    check('standard triangle sizes: lhs 43 words, rhs 21 words', (res['lhs'][1], res['rhs'][1]) == (43, 21))

    # 2. recorded integer divergence witness: exact value fits 64 bits, yet the lhs refuses and the rhs does not
    W = ipts(39798, 37420, -89693, 36555, 30454, 25765); EXACT = 9013625693308608100
    pl, pr_ = lhs(W), rhs(W); il, wl, prl = build(pl); ir, wr, prr = build(pr_); rl, rr = actual(il), actual(ir)
    check('witness: exact mode equal on both sides, value 9013625693308608100 fits int64', pl.exact() == pr_.exact() == (EXACT, 0) and EXACT < 2 ** 63)
    check(f'witness lhs ({wl} words): refusal predicted and observed (RS = 1, S7 = 2) on oracle and simulator',
          prl.rs and prl.s7 == 2 and all(agree(prl, r) and r['flags']['RS'] == 1 and r['registers'][7]['a'] == 2 for r in rl.values()))
    check(f'witness rhs ({wr} words): no refusal, S0 = 9013625693308608100, S7 = 0 on oracle and simulator',
          not prr.rs and all(agree(prr, r) and value(r) == (EXACT, 0, 1) and r['registers'][7]['a'] == 0 for r in rr.values()))
    check('witness: the refused lhs S0 is a stale intermediate, not the identity value', value(rl['sim']) != (EXACT, 0, 1) and value(rl['sim']) == prl.result)

    # 3. sqrt3 divergence witness (inputs preserved from the ECO-3 feasibility scratch run)
    S = spts(-4245, -3149, -4267, -8702, -2702, 9525, 7694, -9328, 4472, -6685, -9652, 9360); SE = (1289057080712143536, 33467196502925568)
    pl, pr_ = lhs(S), rhs(S); il, wl, prl = build(pl); ir, wr, prr = build(pr_); rl, rr = actual(il), actual(ir)
    check(f'sqrt3 witness ({wl}/{wr} words): exact equal, lhs refuses, rhs returns the exact value',
          pl.exact() == pr_.exact() == SE and prl.rs and not prr.rs and all(agree(prl, r) and r['flags']['RS'] == 1 for r in rl.values())
          and all(agree(prr, r) and value(r) == (SE[0], SE[1], 1) for r in rr.values()))

    # 4. deterministic sweep: 50 triangles; oracle on every program, simulator on every 5th case
    rnd = random.Random(20261115); cnt = dict(both_ok=0, lhs_only=0, rhs_only=0, both_ref=0); bad = []
    plan = [('i', 10 ** 2)] * 5 + [('i', 10 ** 4)] * 5 + [('i', 10 ** 5)] * 25 + [('s', 10 ** 4)] * 15
    for n, (kind, mag) in enumerate(plan):
        c = [rnd.randint(-mag, mag) for _ in range(6 if kind == 'i' else 12)]
        P3 = ipts(*c) if kind == 'i' else spts(*c); out = []
        for f in (lhs, rhs):
            p = f(P3); img, w, pr = build(p); recs = actual(img, sim=(n % 5 == 0))
            if not all(agree(pr, r) for r in recs.values()): bad.append((n, f.__name__, 'prediction != actual'))
            out.append((p, pr))
        (pl, a), (pr_, b) = out
        if pl.exact() != pr_.exact(): bad.append((n, 'exact', 'identity fails mathematically'))
        if not a.rs and not b.rs:
            cnt['both_ok'] += 1
            if a.result != b.result: bad.append((n, 'machine', 'both succeeded with different values'))
        elif a.rs and b.rs: cnt['both_ref'] += 1
        elif a.rs: cnt['lhs_only'] += 1
        else: cnt['rhs_only'] += 1
    print('sweep:', len(plan), 'cases', cnt)
    check('sweep: exact equality holds in all 50 cases, and prediction equals actual execution on every executed program', not bad)
    check('sweep: sum of categories is 50; no case where both sides succeed with different values', sum(cnt.values()) == 50)
    check('sweep: the divergence class is present (lhs refuses while rhs succeeds in at least one case)', cnt['lhs_only'] >= 1)

    # 5. negative controls
    wrong_l, wrong_r = lhs(T, k=3), rhs(T, k=4)
    check('negative control: a wrong identity (factor 3 instead of 2) is detected in exact mode', wrong_l.exact() != wrong_r.exact())
    il2, _, pw = build(wrong_l); rw = actual(il2)['oracle']
    check('negative control: the wrong identity is detected on the machine (484 expected, not returned)', value(rw) != (484, 0, 1) and agree(pw, rw))
    check('negative control: a refused run is not accepted as the identity value', value(rl['sim']) != (SE[0], SE[1], 1) and rl['sim']['flags']['RS'] == 1)
print(f'\n{"FAIL" if fails else "PASS"}: {len(fails)} failure(s)')
sys.exit(1 if fails else 0)
