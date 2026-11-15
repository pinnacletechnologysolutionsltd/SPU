#!/usr/bin/env python3
"""SDK quadrance examples: oracle and C++ simulator agree with each other, with the expectation files, and with an
independent exact computation (Python fractions, no psurd_* code). Software only; no hardware run is claimed.
Not part of run_all_tests.py; run directly: python3 software/tests/test_spu_sdk_quadrance.py"""
import hashlib, json, subprocess, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'software/sdk')]
import spu as CLI

fails = []
def check(name, cond):
    print(('PASS ' if cond else 'FAIL ') + name)
    if not cond: fails.append(name)

def mul(x, y): return (x[0] * y[0] + 3 * x[1] * y[1], x[0] * y[1] + x[1] * y[0])   # (a + b sqrt3), integers
def quadrance(p, q):
    dx = (q[0][0] - p[0][0], q[0][1] - p[0][1]); dy = (q[1][0] - p[1][0], q[1][1] - p[1][1])
    a, b = mul(dx, dx), mul(dy, dy); return (a[0] + b[0], a[1] + b[1])
fits = lambda v: all(-2 ** 63 <= c < 2 ** 63 for c in v)

# independent exact expectations: points as ((x_a, x_b), (y_a, y_b)) meaning x_a + x_b sqrt3
q1 = quadrance(((0, 1), (1, 0)), ((2, 0), (0, 2)))                    # A = (sqrt3, 1), B = (2, 2 sqrt3)
q2 = quadrance(((0, 0), (0, 0)), ((4000000000, 0), (0, 0)))           # A = (0, 0), B = (4e9, 0)
check('independent quadrance of the normal case is 20 - 8 sqrt3', q1 == (20, -8))
check('independent dx^2 of the refusal case does not fit 64-bit fields', q2 == (16 * 10 ** 18, 0) and not fits(q2))

with tempfile.TemporaryDirectory() as t:
    t = Path(t); vm = t / 'spu_vm'
    b = subprocess.run(['make', '-s', '-C', str(ROOT / 'software/vm'), f'BIN={vm}'], capture_output=True, text=True)
    check('C++ simulator builds', b.returncode == 0)
    for name in ('quadrance', 'quadrance_refusal'):
        d = ROOT / 'software/sdk/examples' / name; img = t / f'{name}.spui'
        check(f'{name} assembles', CLI.main(['assemble', str(d / f'{name}.spu'), '-o', str(img), '--profile', 'programmable-surd']) == 0)
        exp = json.loads((d / 'expected.json').read_text())
        check(f'{name} image hash matches the expectation', hashlib.sha256(img.read_bytes()).hexdigest() == exp['image_sha256'])
        check(f'{name}: spu verify (oracle, simulator, expectation)', CLI.main(['verify', str(img), '--expect', str(d / 'expected.json'), '--spu-vm', str(vm)]) == 0)
    e1 = json.loads((ROOT / 'software/sdk/examples/quadrance/expected.json').read_text())['registers']
    check('normal expectation S0 equals the independent exact result', tuple(e1['S0'][:2]) == q1 and e1['S0'][2] == 1 and e1['S7'] == [0, 0, 1])
    e2 = json.loads((ROOT / 'software/sdk/examples/quadrance_refusal/expected.json').read_text())['registers']
    check('refusal expectation reports S7 = 2 and a stale S0 (not the quadrance)', e2['S7'] == [2, 0, 1] and tuple(e2['S0'][:2]) != q2)
print(f'\n{"FAIL" if fails else "PASS"}: {len(fails)} failure(s)')
sys.exit(1 if fails else 0)
