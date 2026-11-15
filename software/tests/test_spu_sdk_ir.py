#!/usr/bin/env python3
"""SPU-ECO-2 tests: IR -> v0.3 backend for the two committed quadrance examples. Software verification only.
Generated images are compared byte for byte with the hand-written examples, run on the oracle and the C++ simulator,
and the compile-time refusal PREDICTION is compared with the actual run. Run: python3 software/tests/test_spu_sdk_ir.py"""
import hashlib, json, subprocess, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'software/sdk'), str(ROOT / 'software/tests')]
import spu as CLI, spu_asm as A, spu_record as REC
from spu_ir import Program, IRError
import spu_v03_backend as B

fails = []
def check(name, cond):
    print(('PASS ' if cond else 'FAIL ') + name)
    if not cond: fails.append(name)
def raises(exc, f):
    try: f(); return False
    except exc: return True

def quadrance(ax, ay, bx, by):                                  # q = (bx - ax)^2 + (by - ay)^2, operation order as written
    p = Program(); a, b, c, d = (p.const(*t) for t in (ax, ay, bx, by))
    dx, dy = p.sub(c, a), p.sub(d, b); p.result(p.add(p.square(dx), p.square(dy))); return p
NORMAL = quadrance((0, 1, 1), (1, 0, 1), (2, 0, 1), (0, 2, 1))              # A = (sqrt3, 1), B = (2, 2 sqrt3)
REFUSAL = quadrance((0, 0, 1), (0, 0, 1), (4000000000, 0, 1), (0, 0, 1))    # B = (4e9, 0)

def agree(pred, rec):                                           # does the prediction match an actual record?
    r = rec['registers']; f = rec['flags']
    return (rec['cause'] == 'HALT' and bool(f['RS']) == pred.rs and (r[7]['a'], r[7]['b'], r[7]['d']) == (pred.s7, 0, 1)
            and (r[pred.rout]['a'], r[pred.rout]['b'], r[pred.rout]['d']) == pred.result)

with tempfile.TemporaryDirectory() as t:
    t = Path(t); vm = t / 'spu_vm'
    check('C++ simulator builds', subprocess.run(['make', '-s', '-C', str(ROOT / 'software/vm'), f'BIN={vm}'], capture_output=True).returncode == 0)
    recs, preds = {}, {}
    for name, prog in (('quadrance', NORMAL), ('quadrance_refusal', REFUSAL)):
        d = ROOT / 'software/sdk/examples' / name
        asm, img, words, ins, rout = B.compile_v03(prog)
        ref = t / f'{name}_ref.spui'; CLI.main(['assemble', str(d / f'{name}.spu'), '-o', str(ref), '--profile', 'programmable-surd'])
        check(f'{name}: generated image is byte-identical to the hand-written example ({len(words)} words)', img == ref.read_bytes())
        exp = json.loads((d / 'expected.json').read_text())
        check(f'{name}: image hash equals the committed expectation', hashlib.sha256(img).hexdigest() == exp['image_sha256'])
        spui = t / f'{name}.spui'; spui.write_bytes(img)
        check(f'{name}: spu verify (oracle, simulator, expectation) on the generated image', CLI.main(['verify', str(spui), '--expect', str(d / 'expected.json'), '--spu-vm', str(vm)]) == 0)
        preds[name] = B.predict(ins, rout)
        recs[name] = {b: REC.decode(f(img)) for b, f in (('oracle', lambda i: CLI.run_oracle(i, 10000)), ('sim', lambda i: CLI.run_sim(i, 10000, str(vm))))}
        check(f'{name}: prediction agrees with the actual oracle and simulator records', all(agree(preds[name], r) for r in recs[name].values()))
    check('normal: exact value 20 - 8 sqrt3, no refusal predicted, S7 = 0', NORMAL.exact() == (20, -8) and preds['quadrance'].refusals == [] and preds['quadrance'].s7 == 0)
    pr = preds['quadrance_refusal']
    check('refusal: first SMUL (instruction 6) predicted to refuse, RS = 1, S7 = 2', pr.refusals == [(6, 'SMUL')] and pr.rs and pr.s7 == 2)
    check('refusal: stale destination preserved (S0 = 4000000000, not the exact quadrance)', pr.result == (4000000000, 0, 1) and REFUSAL.exact() == (16 * 10 ** 18, 0))
    # negative controls: a wrong classification or a wrong expected result must be detected
    check('negative control: refusal prediction is rejected against the normal record', not agree(preds['quadrance_refusal'], recs['quadrance']['sim']))
    check('negative control: no-refusal prediction is rejected against the refusal record', not agree(preds['quadrance'], recs['quadrance_refusal']['sim']))
    check('negative control: a wrong expected exact value is detected', NORMAL.exact() != (20, -7))

# order and refusal are preserved: no algebraic simplification, (x + y) - y stays two operations
p = Program(); x, y = p.const(5), p.const(7); p.result(p.sub(p.add(x, y), y))
ins, _, words = B.lower(p)
check('no optimization: (x + y) - y lowers to SADD then SSUB', [i[0] for i in ins] == ['SLIK', 'SLIK', 'SADD', 'SSUB'])
check('square is lowered through multiplication', [s[0] for s in (lambda q: (q.square(q.const(3)), q.stmts)[1])(Program())] == ['const', 'mul'])
# limits and rejections
big = Program(); big.result(big.const(0, 1, 1))
check('a result in S0 compiles', B.compile_v03(big)[2].__len__() > 0)
many = Program(); acc = many.const(0, 1, 1)
for _ in range(40): acc = many.add(acc, many.const(0, 1, 1))     # 2 live values, 8 words per step: only the word limit applies
many.result(acc)
try: B.lower(many); msg = ''
except B.CompileError as e: msg = str(e)
check('256-word image limit is enforced before assembly', 'words' in msg and '256' in msg)
live = Program(); vs = [live.add(live.const(i), live.const(i)) for i in range(8)]; acc = vs[0]    # 8 COMPUTED values, all live
for c in vs[1:]: acc = live.add(acc, c)
live.result(acc)
check('more than 7 live computed values is a compile error (no data memory; only constants can be rematerialized)', raises(B.CompileError, lambda: B.lower(live)))
busy = Program(); a0 = busy.const(1); b0 = busy.const(2); r0 = busy.add(b0, b0); busy.add(a0, a0); busy.result(r0)
check('result needing S0 while S0 is busy is a compile error (no move instruction)', raises(B.CompileError, lambda: B.lower(busy)))
dead = Program(); dead.const(9); dead.result(dead.const(1))
check('a never-used value does not hold its register (result still lands in S0)', B.lower(dead)[1] == 0)
check('IR rejects a foreign operand and a zero denominator', raises(IRError, lambda: Program().add(NORMAL.const(1), NORMAL.const(2))) and raises(IRError, lambda: Program().const(1, 0, 0)))
check('constants that do not fit 64-bit fields are a compile error', raises(B.CompileError, lambda: B.lower((lambda q: (q.result(q.const(2 ** 63)), q)[1])(Program()))))

# the prediction's per-operation results against the C++ SurdFixed64 adapter (MATHLIB-0, dev/next; skipped without Boost)
HDR = ROOT / 'software/math/include/spu/math/surd_fixed64.hpp'
if HDR.exists() and Path('/usr/include/boost/multiprecision/cpp_int.hpp').exists():
    with tempfile.TemporaryDirectory() as t:
        t = Path(t); (t / 'x.cpp').write_text('''#include "spu/math/surd_fixed64.hpp"
#include <iostream>
using namespace spu::math;
int main(){ std::string op; long long a,b,c,e; unsigned long long d,f;
  while (std::cin >> op >> a >> b >> d >> c >> e >> f) { auto x=*make_fixed(a,b,d), y=*make_fixed(c,e,f);
    FixedResult r = op=="SMUL"?smul(x,y):op=="SADD"?sadd(x,y):ssub(x,y);
    if (r.status==Commit::refused) std::cout<<"R\\n"; else std::cout<<r.value->a<<" "<<r.value->b<<" "<<r.value->d<<"\\n"; } }''')
        ok = subprocess.run(['g++', '-std=c++17', '-I', str(ROOT / 'software/math/include'), '-I', str(ROOT / 'software/vm'), str(t / 'x.cpp'), '-o', str(t / 'x')], capture_output=True).returncode == 0
        check('SurdFixed64 cross-check driver builds', ok)
        for name, pr in preds.items():
            tr = pr.trace; inp = ''.join(f'{o} {x[0]} {x[1]} {x[2]} {y[0]} {y[1]} {y[2]}\n' for o, x, y, _ in tr)
            out = subprocess.run([str(t / 'x')], input=inp, capture_output=True, text=True).stdout.split('\n')[:len(tr)]
            want = ['R' if r is None else '%d %d %d' % r for *_, r in tr]
            check(f'{name}: per-operation prediction equals SurdFixed64 smul/sadd/ssub ({len(tr)} operations)', out == want)
else: print('SKIP SurdFixed64 cross-check (MATHLIB headers or Boost not present)')
print(f'\n{"FAIL" if fails else "PASS"}: {len(fails)} failure(s)')
sys.exit(1 if fails else 0)
