#!/usr/bin/env python3
"""SDK-0 tests: v0.3 assembler/disassembler/record decoder against the independent oracle and the frozen RTL-0C
session images, negative cases, and the end-to-end orientation example (oracle and C++ simulator).
Not part of run_all_tests.py; run directly: python3 software/tests/test_spu_sdk.py"""
import json, random, subprocess, sys, tempfile, zlib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'software/sdk'), str(ROOT / 'software/tests')]
import spu_asm as A, spu_record as REC, psurd_oracle as O, spu as CLI
from test_psurd_sim0 import prog_A, prog_B

SESSION = ROOT / 'hardware/tests/psurd_rtl0c/session_v1'
EX = ROOT / 'software/sdk/examples/orientation'
fails = []
def check(name, cond):
    print(('PASS ' if cond else 'FAIL ') + name)
    if not cond: fails.append(name)
def rejects(name, src, profile='programmable-surd'):
    try: A.assemble(src, profile); check(f'rejects {name}', False)
    except A.AsmError: check(f'rejects {name}', True)

r = random.Random(20261112)
# 1. independent encoder == oracle encoder, every form
ok = True
for _ in range(2000):
    d, a, b, s = (r.randrange(8) for _ in range(4))
    u = r.randrange(2 ** 32); ok &= A.enc('SLI', [d, s % 6, u]) == O.SLI(d, s % 6, u)
    ok &= A.enc('SLD', [d]) == O.SLD(d) and A.enc('SNORM', [d, a]) == O.SNORM(d, a) and A.enc('STST', [a]) == O.STST(a)
    ok &= all(A.enc(m, [d, a, b]) == f(d, a, b) for m, f in (('SMUL', O.SMUL), ('SADD', O.SADD), ('SSUB', O.SSUB)))
    i = r.randrange(-2 ** 31, 2 ** 31); ok &= A.enc('SLIK', [d, i]) == O.SLIK(d, i)
    cc = r.choice(list(A.CC)); t = r.randrange(256); ok &= A.enc('BR', [A.CC[cc], t]) == O.BR(cc, t)
    t3 = (r.randrange(-2 ** 63, 2 ** 63), r.randrange(-2 ** 63, 2 ** 63), r.randrange(1, 2 ** 64))
    ok &= A.loadt(d, *t3) == O.LOAD(d, t3)
check('encoder agrees with the oracle encoder for every form (2,000 random cases each)', ok and A.enc('HALT', []) == O.HALT)

# 2. decode rules == oracle field rules (fuzz biased to the opcode block)
ok = True
for _ in range(50000):
    w = r.randrange(2 ** 64)
    if r.random() < 0.9: w = (0x70 + r.randrange(16)) << 56 | (w & ((1 << 56) - 1)) & r.choice([(1 << 56) - 1, 0x0F0F_FFFF_FFFF_FF00, 0x0F0F_00FF_0000_00])
    ok &= (A.decode(w, 256) is not None) == O.fields_ok(w)
check('decoder accepts exactly the words the oracle accepts (50,000 fuzzed words)', ok)

# 3. round trips: every frozen session image and the reference programs
imgs = sorted(SESSION.glob('*.spui')); n_rt = 0
for p in imgs:
    b = p.read_bytes()
    if p.name == 'bad_crc.spui':
        try: A.parse_image(b); check('bad_crc.spui refused', False)
        except ValueError: check('bad_crc.spui refused', True)
        continue
    words = A.parse_image(b)
    for macros in (True, False):
        back, _ = A.assemble(A.disassemble(words, macros), 'programmable-surd'); n_rt += back == words
check(f'disassemble -> assemble reproduces all {len(imgs) - 1} session images (with and without LOADT macros)', n_rt == 2 * (len(imgs) - 1))
for name, w in (('Program A', prog_A(((0, 0, 1), (0, 0, 5)), ((2, 0, 2), (0, 2, 2)), ((6, 0, 3), (0, 4, 2)))), ('Program B K=34', prog_B(34))):
    check(f'{name} round trip', A.assemble(A.disassemble(w), 'programmable-surd')[0] == w)

# 4. negative cases: nothing is skipped or inferred
rejects('missing profile', 'HALT', profile=None)
rejects('another profile', 'HALT', profile='gen1-surd')
rejects('.profile mismatch', '.profile spu13\nHALT')
rejects('SPU-13 Sovereign assembly (.sas)', (ROOT / 'examples/01_scalar_fibonacci/fibonacci.sas').read_text())
for m in ('SRD S0, 0', 'SMOV S0, S1', 'SSTAT', 'MFOLD S0', 'LD R0, 1, 0', 'NOP'): rejects(m, m + '\nHALT')
for bad in ('SLIK S8, 1', 'SLI S0, 6, 0', 'SLIK S0, 2147483648', 'SLI S0, 0, -1', 'SMUL S0, S1', 'SMUL S0, S1, S2, S3',
            'SLIK S0, 1.5', 'SLIK S0, 12abc', 'BR XX, 0', 'BR AL, nowhere', 'BR AL, 5', 'LOADT S0, 1, 0, 0', 'STST R0'):
    rejects(bad, bad + '\nHALT')
rejects('duplicate label', 'x: HALT\nx: HALT'); rejects('empty program', '; nothing'); rejects('257 words', 'HALT\n' * 257)
check('256 words accepted', len(A.assemble('HALT\n' * 256, 'programmable-surd')[0]) == 256)

# 5. record decoder
s = O.run(prog_B(33), 1000); rec = O.record(s); d = REC.decode(rec)
check('record decoder matches the oracle state', d['cause'] == s['cause'] and d['retired'] == s['retired']
      and all((g['a'], g['b'], g['d']) == (s['reg'][i] or (0, 0, 0)) for i, g in enumerate(d['registers'])))
bad = bytearray(rec); bad[20] ^= 1
try: REC.decode(bytes(bad)); check('corrupted record refused', False)
except ValueError: check('corrupted record refused', True)
check('value formatting', [REC.value_str(*t) for t in ((0, 3, 1), (-1, 1, 2), (7, 0, 2), (0, 0, 5))] == ['3√3', '-1/2 + √3/2', '7/2', '0'])

# 6. end to end: source -> image (== silicon-session image) -> oracle and C++ simulator -> frozen record
with tempfile.TemporaryDirectory() as t:
    t = Path(t); img = t / 'orientation.spui'; vm = t / 'spu_vm'
    check('example assembles', CLI.main(['assemble', str(EX / 'orientation.spu'), '-o', str(img), '--profile', 'programmable-surd']) == 0)
    check('example image is byte-identical to session_v1/A-A.spui', img.read_bytes() == (SESSION / 'A-A.spui').read_bytes())
    b = subprocess.run(['make', '-s', '-C', str(ROOT / 'software/vm'), f'BIN={vm}'], capture_output=True, text=True)
    check('C++ simulator builds', b.returncode == 0)
    exp = json.loads((EX / 'expected.json').read_text())
    check('expected record is the frozen session record',
          __import__('hashlib').sha256((SESSION / 'record_01_4150ac7bbcbc.rec').read_bytes()).hexdigest() == exp['record_sha256'])
    check('spu verify: oracle and simulator agree with the expectations', CLI.main(['verify', str(img), '--expect', str(EX / 'expected.json'),
                                                                                    '--spu-vm', str(vm)]) == 0)
print(f'\n{"FAIL" if fails else "PASS"}: {len(fails)} failure(s)')
sys.exit(1 if fails else 0)
