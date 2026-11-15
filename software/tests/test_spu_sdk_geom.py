#!/usr/bin/env python3
"""SPU-ECO-5: geometry layer (spu_geom.py) over the IR and the v0.3 backend. Software verification only.
Generated images go through the existing assembler, oracle and C++ simulator; successful results are compared with the
a self-contained exact reference defined in this file (Python fractions, written from the definitions); refusals are never counted as values.
Run: python3 software/tests/test_spu_sdk_geom.py"""
import hashlib, json, random, subprocess, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'software/sdk'), str(ROOT / 'software/tests')]
import spu as CLI, spu_asm as A, spu_record as REC
from fractions import Fraction as F
from math import gcd, lcm
import spu_geom as G
from spu_ir import IRError


class R:
    """Self-contained exact reference over Q(sqrt3): a value is a pair (p, q) of Fractions meaning p + q*sqrt3. Written from the definitions; it shares
    no code with spu_geom, spu_ir or spu_v03_backend, and no MATHLIB-0 file is used."""
    val = staticmethod(lambda t: (F(t[0], t[2]), F(t[1], t[2])))
    add = staticmethod(lambda x, y: (x[0] + y[0], x[1] + y[1]))
    sub = staticmethod(lambda x, y: (x[0] - y[0], x[1] - y[1]))
    mul = staticmethod(lambda x, y: (x[0] * y[0] + 3 * x[1] * y[1], x[0] * y[1] + x[1] * y[0]))
    @staticmethod
    def tup(v):                                                  # canonical (a, b, d): gcd(|a|, |b|, d) = 1, d > 0, zero is (0, 0, 1)
        d = lcm(v[0].denominator, v[1].denominator); a, b = int(v[0] * d), int(v[1] * d)
        if a == 0 and b == 0: return (0, 0, 1)
        g = gcd(gcd(a, b), d); return (a // g, b // g, d // g)
    @staticmethod
    def quadrance(p, q):
        dx, dy = R.sub(q[0], p[0]), R.sub(q[1], p[1]); return R.add(R.mul(dx, dx), R.mul(dy, dy))
    @staticmethod
    def orientation(a, b, c):
        ux, uy, vx, vy = R.sub(b[0], a[0]), R.sub(b[1], a[1]), R.sub(c[0], a[0]), R.sub(c[1], a[1]); return R.sub(R.mul(ux, vy), R.mul(uy, vx))
    @staticmethod
    def triple_quad(q1, q2, q3):
        s = R.add(R.add(q1, q2), q3); t = R.add(R.add(R.mul(q1, q1), R.mul(q2, q2)), R.mul(q3, q3)); return R.sub(R.mul(s, s), R.mul((F(2), F(0)), t))

fails = []
def check(name, cond):
    print(('PASS ' if cond else 'FAIL ') + name)
    if not cond: fails.append(name)
def raises(exc, f):
    try: f(); return False
    except exc: return True
EX = ROOT / 'software/sdk/examples'
val = lambda t: R.val(t if isinstance(t, tuple) else (t, 0, 1))
rpt = lambda p: (val(p[0]), val(p[1]))                         # reference point from raw coordinates

def build(fn, *pts):                                           # pts: raw coordinates, created in the order given
    g = G.Geometry(); P = [g.point(*p) for p in pts]; g.result(fn(*P)); return g.compile()

with tempfile.TemporaryDirectory() as t:
    vm = Path(t) / 'spu_vm'
    check('C++ simulator builds', subprocess.run(['make', '-s', '-C', str(ROOT / 'software/vm'), f'BIN={vm}'], capture_output=True).returncode == 0)
    def actual(c):
        return {'oracle': REC.decode(CLI.run_oracle(c.image, 10000)), 'sim': REC.decode(CLI.run_sim(c.image, 10000, str(vm)))}
    def agree(c, recs):                                        # prediction (refusal status, S7, S0) equals every actual record
        pr = c.prediction
        return all(r['cause'] == 'HALT' and bool(r['flags']['RS']) == pr.rs and r['registers'][7]['a'] == pr.s7
                   and (r['registers'][0]['a'], r['registers'][0]['b'], r['registers'][0]['d']) == pr.result for r in recs.values())
    def s0(r): g = r['registers'][0]; return (g['a'], g['b'], g['d'])

    # 1. quadrance: byte-identical to both committed examples
    for name, pts in (('quadrance', (((0, 1, 1), 1), (2, (0, 2, 1)))), ('quadrance_refusal', ((0, 0), (4000000000, 0)))):
        c = build(G.quadrance, *pts); exp = json.loads((EX / name / 'expected.json').read_text()); recs = actual(c)
        check(f'{name}: library image is byte-identical to the committed example ({c.words} words)', hashlib.sha256(c.image).hexdigest() == exp['image_sha256'])
        img = Path(t) / f'{name}.spui'; img.write_bytes(c.image)
        check(f'{name}: spu verify against the committed expectation', CLI.main(['verify', str(img), '--expect', str(EX / name / 'expected.json'), '--spu-vm', str(vm)]) == 0)
        check(f'{name}: prediction equals oracle and simulator', agree(c, recs))
    c = build(G.quadrance, ((0, 1, 1), 1), (2, (0, 2, 1))); ref = R.tup(R.quadrance(rpt(((0, 1, 1), 1)), rpt((2, (0, 2, 1)))))
    check('quadrance: exact value equals the independent reference (20 - 8 sqrt3)', ref == (20, -8, 1) and s0(actual(c)['sim']) == ref)

    # 2. orientation against the existing frozen orientation example
    pts = ((0, 0), ((2, 0, 1), (0, 1, 1)), (1, (0, 2, 1))); c = build(G.orientation, *pts); recs = actual(c)
    ex = json.loads((EX / 'orientation/expected.json').read_text())['registers']['S0']
    check('orientation: determinant S0 equals the existing orientation example (3 sqrt3)', all(s0(r) == tuple(ex) for r in recs.values()) and agree(c, recs))
    check('orientation: equals the independent reference', R.tup(R.orientation(*[rpt(p) for p in pts])) == (0, 3, 1))
    words, _ = A.assemble((EX / 'orientation/orientation.spu').read_text(), A.PROFILE)
    frozen = [d[0] for d in (A.decode(w, len(words)) for w in words) if d and d[0] in ('SADD', 'SSUB', 'SMUL')][:7]
    check('orientation: arithmetic sequence equals the first 7 arithmetic instructions of the frozen example', [x[0] for x in c.instructions if x[0] in ('SADD', 'SSUB', 'SMUL')] == frozen)

    # 3. triple-quad and the orientation relation, including the ECO-3 refusal witness
    for name, pts, want in (('standard triangle', ((0, 0), (4, 1), (1, 3)), 484),
                            ('integer witness', ((39798, 37420), (-89693, 36555), (30454, 25765)), 9013625693308608100)):
        tq = build(G.triple_quad_points, *pts); fo = build(lambda a, b, c: 4 * G.orientation(a, b, c) ** 2, *pts)
        rt, rf = actual(tq), actual(fo); refv = R.tup(R.triple_quad(*[R.quadrance(rpt(p), rpt(q)) for p, q in ((pts[0], pts[1]), (pts[1], pts[2]), (pts[2], pts[0]))]))
        check(f'{name}: prediction equals oracle and simulator for both programs', agree(tq, rt) and agree(fo, rf))
        check(f'{name}: the independent reference gives {want} for triple-quad, and 4D^2 returns it', refv == (want, 0, 1) and not fo.prediction.rs and s0(rf['sim']) == refv)
        if name == 'standard triangle': check(f'{name}: triple-quad also returns {want} (no refusal)', not tq.prediction.rs and s0(rt['sim']) == refv)
        else: check(f'{name}: triple-quad refuses (RS = 1, S7 = 2) and its S0 is not the value', tq.prediction.rs and rt['sim']['flags']['RS'] == 1 and s0(rt['sim']) != refv)

    # 4. deterministic sweep against the independent reference; refusals are excluded from value checks
    rnd = random.Random(20261115); ok = n_ref = n_val = 0
    for _ in range(20):
        sq = rnd.random() < 0.5; m = rnd.choice((10 ** 3, 10 ** 5)); mk = lambda: (rnd.randint(-m, m), rnd.randint(-m, m), 1) if sq else rnd.randint(-m, m)
        pts = [(mk(), mk()) for _ in range(3)]
        for fn, rf in ((lambda a, b, c: G.quadrance(a, b), lambda a, b, c: R.quadrance(a, b)), (G.orientation, R.orientation),
                       (G.triple_quad_points, lambda a, b, c: R.triple_quad(R.quadrance(a, b), R.quadrance(b, c), R.quadrance(c, a)))):
            c = build(fn, *pts); want = R.tup(rf(*[rpt(p) for p in pts])); recs = actual(c) if rnd.random() < 0.3 else {'oracle': REC.decode(CLI.run_oracle(c.image, 10000))}
            ok += agree(c, recs) and R.tup((c.exact[0], c.exact[1])) == want
            if c.prediction.rs: n_ref += 1
            else: n_val += 1; ok += s0(recs['oracle']) == want
    print(f'sweep: {n_val} successful runs checked against the reference, {n_ref} refusals excluded from value checks')
    check('sweep: exact mode equals the reference, prediction equals execution, successful values equal the reference', ok == 60 + n_val)

# 5. operator semantics: one IR operation each, in evaluation order, nothing simplified
g = G.Geometry(); x, y = g.const(5), g.const(7); r = (x + y) - y
check('no simplification: (x + y) - y is two operations', [s[0] for s in g.prog.stmts] == ['const', 'const', 'add', 'sub'])
g = G.Geometry(); x = g.const(3); r = x ** 2
check('x**2 is one multiplication of x by itself', g.prog.stmts[1] == ('mul', 0, 0))
g = G.Geometry(); x = g.const(3); r = -x
check('-x is const 0 minus x (one constant, one subtraction)', g.prog.stmts[1:] == [('const', (0, 0, 1)), ('sub', 1, 0)])
g = G.Geometry(); x = g.const(3); r = 2 * x + 1
check('integers are coerced at the point of use', [s[0] for s in g.prog.stmts] == ['const', 'const', 'mul', 'const', 'add'])
check('rejected: **3, mixed programs, float, bool', raises(IRError, lambda: G.Geometry().const(1) ** 3) and raises(IRError, lambda: G.Geometry().const(1) + G.Geometry().const(2))
      and raises(IRError, lambda: G.Geometry().const(1) + 1.5) and raises(IRError, lambda: G.Geometry().const(1) + True))
# 6. negative controls
c = build(G.quadrance, ((0, 1, 1), 1), (2, (0, 2, 1)))
check('negative control: a wrong expected quadrance is detected', R.tup((c.exact[0], c.exact[1])) != (20, -7, 1))
cr = build(G.quadrance, (0, 0), (4000000000, 0))
check('negative control: a refused run is not accepted as the exact value', cr.prediction.rs and cr.prediction.result != R.tup((cr.exact[0], cr.exact[1])))
print(f'\n{"FAIL" if fails else "PASS"}: {len(fails)} failure(s)')
sys.exit(1 if fails else 0)
