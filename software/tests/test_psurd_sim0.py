#!/usr/bin/env python3
"""SPU-V03-SIM-0: EXPERIMENTAL programmable-surd profile vs an independent oracle. Usage: OUT_DIR [--skip-gen1].
References: ISA draft rev 2 / contract candidate tables (expected values) and psurd_oracle.py (full records); image rev 0x03.
run_all_tests.py passes --skip-gen1 (it runs Gen-1 conformance separately). Software only: no RTL or hardware claim. results.json written; exit 0 only on PASS."""
import hashlib, json, math, subprocess, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import psurd_oracle as O
from psurd_fixtures import run_fixtures
from psurd_oracle import SLI, SLD, SRD, SMUL, SADD, SSUB, SNORM, SLIK, STST, BR, HALT, LOAD, image

ROOT = Path(__file__).resolve().parents[2]
CHECKS = []
def check(name, ok, obs=''): CHECKS.append(dict(name=name, ok=bool(ok), observed=repr(obs)[:600]))
def sh(args, **kw): return subprocess.run(args, capture_output=True, text=True, timeout=300, **kw)
X = (1 << 63) - 1
Z0 = (0, 0, 1); I = lambda k: (k, 0, 1)

def prog_A(A, B, C):
    L = 42
    return sum((LOAD(i, t) for i, t in enumerate((*A, *B, *C))), []) + [
        SSUB(2, 2, 0), SSUB(4, 4, 0), SSUB(3, 3, 1), SSUB(5, 5, 1), SMUL(0, 2, 5), SMUL(1, 3, 4), SSUB(0, 0, 1),
        BR('RS', L + 17), STST(0), BR('GT', L + 13), BR('LT', L + 15), SLIK(7, 0), HALT, SLIK(7, 1), HALT,
        SLIK(7, -1), HALT, SLIK(7, 2), HALT]
def prog_B(K):
    return LOAD(1, (2, 1, 1)) + [SLIK(0, 1), SLIK(3, 1), SLIK(4, K), STST(4), BR('LT', 22), BR('EQ', 18),
        SMUL(0, 0, 1), BR('RF', 20), SSUB(4, 4, 3), STST(4), BR('GT', 13), SLIK(7, 0), HALT, SLIK(7, 1), HALT,
        SLIK(7, -1), HALT]
X33 = (3743165875258953026, 2161117825702177665, 1)

def main(out, skip_gen1=False):
    out = Path(out).resolve(); out.mkdir(parents=True)
    res = dict(status='ERROR', harness_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               oracle_sha256=hashlib.sha256((ROOT / 'software/tests/psurd_oracle.py').read_bytes()).hexdigest(),
               contract_sha256=hashlib.sha256((ROOT / 'docs/design/SPU_V03_CONTRACT_CANDIDATE.md').read_bytes()).hexdigest(),
               fixtures_sha256=hashlib.sha256((ROOT / 'software/tests/psurd_fixtures.py').read_bytes()).hexdigest())
    try:
        exe = out / 'spu_vm'
        b = sh(['make', '-s', '-B', '-C', str(ROOT / 'software/vm'), 'spu_vm', f'BIN={exe}'])
        check('build', b.returncode == 0, b.stderr[-400:])
        n = [0]
        def sim(words, budget=10000, raw=None, extra=()):
            n[0] += 1; p = out / f'img{n[0]:04d}.spui'; p.write_bytes(raw if raw is not None else image(words))
            return sh([str(exe), '--profile', 'programmable-surd', str(p), '--budget', str(budget), *extra])
        def agree(name, words, budget=10000):
            r = sim(words, budget); st = O.run(words, budget); want = O.record(st).hex()
            check(f'{name}: record == oracle', r.returncode == 0 and r.stdout.strip() == want, (r.returncode, r.stdout[:80], r.stderr[:200]))
            return st
        # Program A: draft §7.1 table
        Aexp = {'A': (((Z0, Z0), (I(2), (0, 1, 1)), (I(1), (0, 2, 1))), 1, (0, 3, 1)),
                'B': (((Z0, Z0), (I(1), (0, 1, 1)), (I(2), (0, 2, 1))), 0, (0, 0, 1)),
                'C': (((Z0, Z0), (I(1), (0, 2, 1)), (I(2), (0, 1, 1))), -1, (0, -3, 1)),
                'D': (((Z0, Z0), (I(1), (0, 1, 1)), (I(2), (1, 2000, 1000))), 1, (1, 0, 1000)),
                'E': (((Z0, Z0), (I(2**40), Z0), (Z0, I(2**40))), 2, None),
                'F': ((((0, 0, 1), (0, 0, 5)), ((2, 0, 2), (0, 2, 2)), ((6, 0, 3), (0, 4, 2))), 0, (0, 0, 60))}
        for k, (pts, s7, det) in Aexp.items():
            st = agree(f'A case {k}', prog_A(*pts))
            check(f'A case {k}: draft table', st['cause'] == 'HALT' and st['reg'][7] == I(s7) and
                  (det is None or st['reg'][0] == det) and st['flags']['RS'] == (k == 'E'), (st['reg'][7], st['reg'][0]))
        # Program B: draft §7.2 table
        for K, s7, x0 in ((-1, -1, I(1)), (0, 0, I(1)), (1, 0, (2, 1, 1)), (2, 0, (7, 4, 1)), (33, 0, X33),
                          (34, 1, X33), (50, 1, X33)):
            st = agree(f'B K={K}', prog_B(K))
            check(f'B K={K}: draft table', st['cause'] == 'HALT' and st['reg'][7] == I(s7) and st['reg'][0] == x0, st['reg'][0])
        check('B k=34 raw coefficient exceeds int64', 2 * X33[0] + 3 * X33[1] == 13969685227624439047 > X, '')
        # negative controls: record agreement plus the expected cause
        def neg(name, words, cause, budget=10000, pc=None):
            st = agree(name, words, budget)
            check(f'{name}: cause {cause}', st['cause'] == cause and (pc is None or st['pc'] == pc), (st['cause'], st['pc']))
        valid = {0x70, 0x71, 0x73, 0x74, 0x75, 0x76} | set(range(0x78, 0x7C))   # 0x72 SRD retired
        for op in range(256):                                     # every opcode, all other fields zero
            w = op << 56; st = O.run([w, HALT], 10)
            r = sim([w, HALT], 10)
            ok = r.stdout.strip() == O.record(st).hex() and (op in valid or st['cause'] == 'BAD_ENCODING')
            if not ok or op in (0x72, 0x77, 0x78, 0x7C, 0x7F, 0xF0): check(f'opcode sweep 0x{op:02x}', ok, (st['cause'], r.stdout[:20]))
        check('opcode sweep: 256 opcodes agree; unlisted are BAD_ENCODING', not [c for c in CHECKS if c['name'].startswith('opcode sweep') and not c['ok']])
        bad = {'SLI slice 6': SLI(0, 6, 1), 'SLI low byte': SLI(0, 0, 1) | 1, 'SLD reg 8': 0x71 << 56 | 8 << 48,
               'SMUL sb 8': SMUL(0, 0, 0) | 8 << 24, 'SADD bits39:32': SADD(0, 0, 0) | 1 << 32, 'SSUB low': SSUB(0, 0, 0) | 1 << 8,
               'SNORM payload': SNORM(0, 0) | 1 << 8, 'SLIK r2': SLIK(0, 1) | 1 << 40, 'STST r1': STST(0) | 1 << 48,
               'BR cc 10': 0x7A << 56 | 10 << 48, 'BR low': BR('AL', 0) | 1, 'HALT extra': HALT | 1, 'SRD (retired, well-formed)': SRD(0, 0)}
        for k, w in bad.items(): neg(f'malformed {k}', [SLIK(0, 1), w, HALT], 'BAD_ENCODING', pc=1)
        st = O.run([SLIK(0, 1), SRD(0, 0), HALT], 99)
        check('SRD retired: no state change', st['reg'][0] == I(1) and st['retired'] == 1 and st['flags']['CV'] == 0, st['reg'][0])
        neg('uninitialized read', [SADD(0, 1, 2), HALT], 'INVALID', pc=0)
        neg('incomplete staging', [SLI(0, s, 1) for s in range(5)] + [SLD(0), HALT], 'INVALID', pc=5)
        neg('staging other target', [SLI(0, 0, 1), SLI(1, 0, 1), HALT], 'INVALID', pc=1)
        neg('SLD d = 0', LOAD(0, (1, 0, 0)) + [HALT], 'INVALID', pc=6)
        for cc in ('EQ', 'NE', 'LT', 'GE', 'GT', 'LE'): neg(f'sign branch {cc} before STST', [BR(cc, 0), HALT], 'INVALID', pc=0)
        for cc in ('AL', 'RF', 'NR', 'RS'): neg(f'{cc} needs no CV', [BR(cc, 1), HALT], 'HALT')
        neg('branch outside image (taken)', [BR('AL', 2), HALT], 'BAD_TARGET', pc=0)
        neg('branch outside image (not taken)', [BR('RF', 9), HALT], 'BAD_TARGET', pc=0)
        neg('fall off end', [SLIK(0, 1)], 'PC_OVERRUN', pc=1)
        neg('fall off 256-word image, no wrap', [SLIK(0, 1)] * 256, 'PC_OVERRUN', budget=1000, pc=256)
        neg('budget exhausted', [BR('AL', 0)], 'BUDGET', budget=5, pc=0)
        neg('HALT as B-th retirement', [SLIK(0, 1), HALT], 'HALT', budget=2)
        st = O.run([SLIK(0, 2**31 - 1), SMUL(0, 0, 0), SMUL(0, 0, 0), SMUL(1, 0, 0), STST(0), HALT], 99)
        check('overflow recoverable, destination kept', st['reg'][0] == ((2**31 - 1)**2, 0, 1) and st['reg'][1] is None and st['flags']['R'] == 1 and st['flags']['RS'] == 1 and st['cause'] == 'HALT', st)
        agree('overflow recoverable', [SLIK(0, 2**31 - 1), SMUL(0, 0, 0), SMUL(0, 0, 0), SMUL(1, 0, 0), STST(0), HALT], 99)
        st = agree('R clears, RS sticky', [SLIK(0, 2**31 - 1), SMUL(0, 0, 0), SMUL(0, 0, 0), SMUL(0, 0, 0), SLIK(1, 1), SADD(2, 1, 1), HALT])
        check('R clears, RS sticky: flags', (st['flags']['R'], st['flags']['RS']) == (0, 1), st['flags'])
        st = agree('SLIK does not alias SLI', [SLIK(0, 5), SLD(0), HALT]); check('SLIK does not alias SLI: SLD faults', st['cause'] == 'INVALID' and st['pc'] == 1)
        st = agree('staging keeps committed value', [SLIK(0, 5), SLI(0, 0, 123), STST(0), HALT]); check('staging keeps committed value: S0 = 5', st['reg'][0] == I(5))
        run_fixtures(exe, out, sh, check)                         # sessions, BUDGET at PC = L, per-field decoder
        rp = [BR('RS', 6), SLIK(0, 2**31 - 1), SMUL(0, 0, 0), SMUL(0, 0, 0), STST(0), HALT, HALT]
        r = sim(rp, extra=('--repeat', '3')); lines = r.stdout.split()
        check('repeated START: clean state', len(lines) == 3 and len(set(lines)) == 1 and lines[0] == O.record(O.run(rp, 10000)).hex(), lines[:1])
        refused = {'bad magic': b'XPUI' + image([HALT])[4:], 'legacy identity': image([HALT], profile=0x00),
                   'wrong revision': image([HALT], rev=0x01), 'historical revision 0x02 (SIM-0, SRD)': image([HALT], rev=0x02),
                   'bad CRC': image([HALT], crc_delta=1),
                   'L = 0': image([], length=0), 'L = 257': image([HALT] * 257), 'truncated': image([HALT, HALT])[:-1]}
        for k, raw in refused.items():
            r = sim(None, raw=raw); check(f'image refused: {k}', r.returncode == 1 and r.stdout == '', (r.returncode, r.stderr[:80]))
        r = sim(None, raw=image([HALT])); check('revision 0x03 image executes', r.returncode == 0 and r.stdout.strip() == O.record(O.run([HALT], 10000)).hex(), r.stdout[:20])
        for k, bud in (('budget 0', '0'), ('budget missing', None)):
            p = out / 'h.spui'; p.write_bytes(image([HALT]))
            r = sh([str(exe), '--profile', 'programmable-surd', str(p)] + (['--budget', bud] if bud else []))
            check(f'START refused: {k}', r.returncode == 1 and r.stdout == '', r.stderr[:80])
        for k, args in {'unknown profile': ['--profile', 'gen2', str(p)], 'two profiles': ['--profile', 'programmable-surd', '--profile', 'gen1-surd', str(p)]}.items():
            r = sh([str(exe), *args]); check(f'dispatch refuses: {k}', r.returncode == 1 and r.stdout == '', r.stderr[:80])
        m = json.loads(sh([str(exe), '--profile', 'programmable-surd', '--capabilities']).stdout)
        check('manifest: ISA frozen; not Gen-1, not RTL qualified; FPGA demonstrated (§3.53); certifies nothing', m['status'] == 'experimental' and
              m['gen1_conformant'] is False and m['isa_frozen'] is True and m['rtl_qualified'] is False and m['fpga_demonstrated'] is True
              and '§3.53' in m['fpga_evidence'] and all(c['conformance'] == 'not_run' for c in m['capabilities'].values()), m['status'])
        phys = {k: c['physical'] for k, c in m['capabilities'].items()}
        check('manifest: physical evidence scoped per capability (partial where §3.53 did not exercise it)',
              all('§3.53' in v for v in phys.values()) and phys['cpu.psurd.arith-smul-sadd-ssub-snorm'].startswith('partial')
              and 'SADD and SNORM not executed' in phys['cpu.psurd.arith-smul-sadd-ssub-snorm']
              and phys['cpu.psurd.registers-s0-s7'].startswith('partial') and phys['cpu.psurd.sign-test-and-branch'].startswith('partial')
              and m['capabilities']['cpu.psurd.result-record-v0']['hardware_observable'] is True, phys)
        check('manifest: SRD unsupported, image revision 3', m['image_revision'] == 3 and any('SRD' in u for u in m['unsupported']), m['unsupported'])
        g = json.loads(sh([str(exe), '--profile', 'gen1-surd', '--capabilities']).stdout)
        check('gen1-surd manifest still gen1-surd', g['profile'] == 'gen1-surd' and 'cpu.gen1-surd.fixed-rom-v1' in g['capabilities'], g['profile'])
        # falsifiability: each planted oracle bug must make at least one registered program disagree with the simulator
        probe = [prog_A(*Aexp[k][0]) for k in 'ADEF'] + [prog_B(K) for K in (0, 34)] + [[BR('NE', 1), HALT]]
        sims = [sim(p).stdout.strip() for p in probe]
        real = dict(mul=O.mul, sign=O.sign, fit_or_norm=O.fit_or_norm, run=O.run)
        def always_norm(A, B, D):                                 # drops the raw-fit rule
            if A == B == 0: return (0, 0, 1)
            g = math.gcd(math.gcd(A, B), D); A, B, D = A // g, B // g, D // g
            return (A, B, D) if O.I64(A) and O.I64(B) and 0 < D < O.M64 else None
        mutants = {'always normalize (no raw-fit)': ('fit_or_norm', always_norm),
                   'sign ignores sqrt3 term': ('sign', lambda x: (x[0] > 0) - (x[0] < 0)),
                   'overflow overwrites with zero': ('mul', lambda x, y: real['mul'](x, y) or (0, 0, 1)),
                   'no CV requirement': ('run', lambda w, b: real['run']([BR('AL', 1) if x == BR('NE', 1) else x for x in w], b))}
        for k, (fn, impl) in mutants.items():
            setattr(O, fn, impl)
            try: fired = any(O.record(O.run(p, 10000)).hex() != s for p, s in zip(probe, sims))
            finally: setattr(O, fn, real[fn])
            check(f'mutation control fires: {k}', fired, fired)
        good = O.record(O.run(probe[0], 10000)).hex(); bad = good[:-2] + ('01' if good[-2:] == '00' else '00')
        check('control: corrupted expected record is detected', good == sims[0] and bad != sims[0], '')
        if skip_gen1: res['gen1_conformance'] = 'skipped: run separately by run_all_tests.py'
        else:
            c = sh([sys.executable, str(ROOT / 'software/tests/test_gen1_sim_conformance.py'), str(out / 'gen1_conformance')])
            check('Gen-1 conformance unchanged: PASS 80', c.returncode == 0 and c.stdout.strip().startswith('PASS 80 checks; 0 failed'), c.stdout.strip())
        res['status'] = 'PASS' if all(c['ok'] for c in CHECKS) else 'FAIL'
    except Exception:
        res['traceback'] = traceback.format_exc()
    finally:
        res.update(checks=CHECKS, checks_total=len(CHECKS), failed=[c for c in CHECKS if not c['ok']])
        (out / 'results.json').write_text(json.dumps(res, indent=1) + '\n')
    print(res['status'], len(CHECKS), 'checks;', len(res['failed']), 'failed')
    return 0 if res['status'] == 'PASS' else 1

if __name__ == '__main__':
    if len(sys.argv) not in (2, 3) or sys.argv[2:] not in ([], ['--skip-gen1']): sys.exit('usage: OUT_DIR [--skip-gen1]')
    sys.exit(main(sys.argv[1], sys.argv[2:] == ['--skip-gen1']))
