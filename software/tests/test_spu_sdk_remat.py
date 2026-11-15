#!/usr/bin/env python3
"""SPU-ECO-4: automatic constant rematerialization in the v0.3 backend. Software verification only.
The triple-quad left side is built with ONE shared set of coordinate constants (ECO-3 needed manual re-creation) and must
now compile, with the same arithmetic order, refusal behaviour and results as the hand-re-materialized program.
Run: python3 software/tests/test_spu_sdk_remat.py"""
import subprocess, sys, tempfile
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
def ipts(*c): return tuple(((c[i], 0, 1), (c[i + 1], 0, 1)) for i in (0, 2, 4))
def spts(*c): return tuple(((c[i], c[i + 1], 1), (c[i + 2], c[i + 3], 1)) for i in (0, 4, 8))

def lhs(P3, shared):                                             # (Q1+Q2+Q3)^2 - 2(Q1^2+Q2^2+Q3^2); arithmetic order identical either way
    p = Program(); A, Bp, C = P3
    if shared: v = [p.const(*t) for t in (A[0], A[1], Bp[0], Bp[1], C[0], C[1])]; pts = ((v[0], v[1]), (v[2], v[3]), (v[4], v[5]))
    def pt(k, raw):
        return pts[k] if shared else (p.const(*raw[0]), p.const(*raw[1]))
    def quad(a, b):
        dx, dy = p.sub(b[0], a[0]), p.sub(b[1], a[1]); return p.add(p.square(dx), p.square(dy))
    q1 = quad(pt(0, A), pt(1, Bp)); q2 = quad(pt(1, Bp), pt(2, C)); q3 = quad(pt(2, C), pt(0, A))
    s = p.add(p.add(q1, q2), q3); two = p.const(2)
    t = p.add(p.add(p.square(q1), p.square(q2)), p.square(q3)); p.result(p.sub(p.square(s), p.mul(two, t))); return p
ARITH = ('SADD', 'SSUB', 'SMUL')
def arith_shape(ins):                                            # the arithmetic sequence with registers replaced by value roles is order-only here
    return [x[0] for x in ins if x[0] in ARITH]
def value(r): g = r['registers'][0]; return (g['a'], g['b'], g['d'])

with tempfile.TemporaryDirectory() as t:
    vm = Path(t) / 'spu_vm'
    check('C++ simulator builds', subprocess.run(['make', '-s', '-C', str(ROOT / 'software/vm'), f'BIN={vm}'], capture_output=True).returncode == 0)
    cases = {'standard triangle': (ipts(0, 0, 4, 1, 1, 3), 484),
             'integer witness (manual lhs refuses)': (ipts(39798, 37420, -89693, 36555, 30454, 25765), None),
             'sqrt3 witness': (spts(-4245, -3149, -4267, -8702, -2702, 9525, 7694, -9328, 4472, -6685, -9652, 9360), None)}
    for name, (P3, want) in cases.items():
        man, sh = lhs(P3, False), lhs(P3, True)
        ins_s, rout_s, ws_s = B.lower(sh); ins_m, rout_m, _ = B.lower(man)
        nconst = sum(1 for x in sh.stmts if x[0] == 'const'); loads = sum(1 for x in ins_s if x[0] in ('SLIK', 'LOADT'))
        check(f'{name}: shared-constant program compiles ({ws_s} words, {loads} loads for {nconst} constants; manual version {B.lower(man)[2]} words)', loads > nconst)
        check(f'{name}: arithmetic sequence (order and count) identical to the manual version', arith_shape(ins_s) == arith_shape(ins_m) and len(arith_shape(ins_s)) > 0)
        asm, img, words, ins, rout = B.compile_v03(sh); pr = B.predict(ins, rout); pm = B.predict(ins_m, rout_m)
        check(f'{name}: predicted refusal behaviour equals the manual version (RS, S7, refused operation count)', (pr.rs, pr.s7, len(pr.refusals)) == (pm.rs, pm.s7, len(pm.refusals)))
        recs = {'oracle': REC.decode(CLI.run_oracle(img, 10000)), 'sim': REC.decode(CLI.run_sim(img, 10000, str(vm)))}
        ok = all(r['cause'] == 'HALT' and bool(r['flags']['RS']) == pr.rs and r['registers'][7]['a'] == pr.s7 and value(r) == pr.result for r in recs.values())
        check(f'{name}: prediction equals oracle and simulator actual execution', ok)
        if not pr.rs: check(f'{name}: no refusal, S0 equals the exact value', value(recs['sim']) == tuple(map(int, sh.exact())) + (1,) and (want is None or value(recs['sim'])[0] == want))
        else: check(f'{name}: refusal observed; S0 is a stale intermediate, not the exact value', value(recs['sim']) != tuple(map(int, sh.exact())) + (1,))
    # regression: programs that never need rematerialization are unchanged (ECO-2 byte-identity is covered by test_spu_sdk_ir.py)
    p = Program(); a, b = p.const(2), p.const(3); p.result(p.mul(a, b)); ins = B.lower(p)[0]
    check('no pressure: no extra loads', [x[0] for x in ins] == ['SLIK', 'SLIK', 'SMUL'])
    # limits that remain
    live = Program(); vs = [live.add(live.const(i), live.const(i)) for i in range(8)]; acc = vs[0]
    for c in vs[1:]: acc = live.add(acc, c)
    live.result(acc)
    try: B.lower(live); msg = ''
    except B.CompileError as e: msg = str(e)
    check('8 live COMPUTED values still fail (they cannot be rematerialized)', 'live values' in msg)
    # negative control: the reloads are needed. Dropping one makes the replay fail
    ins_s, rout = B.lower(lhs(cases['standard triangle'][0], True))[:2]; ref = B.predict(ins_s, rout).result
    first = next(i for i, x in enumerate(ins_s) if x[0] in ARITH); late = [i for i, x in enumerate(ins_s) if x[0] in ('SLIK', 'LOADT') and i > first]
    def changed(k):
        try: return B.predict(ins_s[:k] + ins_s[k + 1:], rout).result != ref
        except KeyError: return True
    check(f'negative control: dropping any of the {len(late)} loads issued after the first arithmetic instruction is detected by the replay', len(late) >= 1 and all(changed(k) for k in late))
print(f'\n{"FAIL" if fails else "PASS"}: {len(fails)} failure(s)')
sys.exit(1 if fails else 0)
