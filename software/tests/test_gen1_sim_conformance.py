#!/usr/bin/env python3
"""gen1-surd C++ profile conformance (SPU-GEN1-SIM-IMPL-0). Standalone; NOT part of run_all_tests.py.

Usage: python3 software/tests/test_gen1_sim_conformance.py OUT_DIR   (OUT_DIR must not exist)
Pure Python: shares no code with the C++ model. References: the frozen GEN1-ISA-COVERAGE-2 fixture
(RTL simulation), the hardware evidence ledger text (silicon success frames) and an expected-state
model written here from docs/GEN1_ARCHITECTURAL_CONTRACT.md §7. Writes results.json (PASS/FAIL/ERROR)
in every case; every check keeps its boolean and observed value. Exit 0 only on PASS.
"""
import hashlib, json, math, subprocess, sys, traceback, zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / 'hardware/tests/spu13/gen1_integration/fixtures/expected_records.json'
FIXTURE_SHA = '3268eed2b374c5fdea7e3ac9ca78ac119fad059c8d1d0c98b4f8dfdefa01b832'
CONTRACT = ROOT / 'docs/GEN1_ARCHITECTURAL_CONTRACT.md'
CONTRACT_SHA = '0e1c1566a52e24a9124165a19c4b1ac0a272cc8932a84a7e45d64782d08f2a2e'
LEDGER = ROOT / 'docs/hardware_evidence.md'
FA = ROOT / 'hardware/tests/spu13/gen1_integration/fixtures/fault_after_srd.json'   # RTL-derived directed case
FA_SHA = 'faf52b7ae790550adc61fc4ffb8145b888783ba58d98af9935f1e26ff616d1cf'
LEGACY_REV = '5948d8d5189602cfdca42023aa7e99e3fd0763e5'   # last revision before the gen1-surd profile (14ab48a6)
G340 = 'a5 01 01 3f 0e | 0d000000 00000000 04000000 00000000 09000000 00000000 | 422b6b75'
CHECKS = []

def check(name, ok, observed):
    CHECKS.append(dict(name=name, ok=bool(ok), observed=repr(observed)[:2000]))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(args, **kw): return subprocess.run(args, capture_output=True, text=True, timeout=60, **kw)

def expected_s0(a, b, d):
    """Contract §7 written independently: SLD needs d != 0; SMUL raw-fit else gcd-normalize else refuse."""
    if d == 0: return None                                   # SLD INVALID: S0 stays uninitialized
    A, B, D = a * a + 3 * b * b, 2 * a * b, d * d
    fit = lambda x, y, z: -2**63 <= x < 2**63 and -2**63 <= y < 2**63 and 0 < z < 2**64
    if fit(A, B, D): return (A, B, D)
    g = math.gcd(math.gcd(A, B), D)
    A, B, D = (0, 0, 1) if A == B == 0 else (A // g, B // g, D // g)
    return (A, B, D) if fit(A, B, D) else (a, b, d)          # OVERFLOW preserves S0

def rom_bytes(words): return b''.join(int(w, 16).to_bytes(8, 'big') for w in words)
def frame_of(t, ok=True):
    a, b, d = (x % 2**64 for x in t)
    body = bytes([0xA5, 1, 1 if ok else 2, 0x3F, 14]) + b''.join(
        v.to_bytes(4, 'little') for v in (a & 0xffffffff, a >> 32, b & 0xffffffff, b >> 32, d & 0xffffffff, d >> 32))
    return body + zlib.crc32(body).to_bytes(4, 'little')

def gen1(exe, out, rom, *extra):
    p = out / 'roms' / (hashlib.sha256(rom).hexdigest()[:16] + '.bin'); p.parent.mkdir(exist_ok=True); p.write_bytes(rom)
    diag = p.with_suffix('.diag.json'); raw = p.with_suffix('.frame')
    r = run([str(exe), '--profile', 'gen1-surd', str(p), '--frame-out', str(raw), '--diag-out', str(diag), *extra])
    return r, (raw.read_bytes() if raw.exists() else b''), (json.loads(diag.read_text()) if diag.exists() else {})

def main(out):
    out = Path(out).resolve(); out.mkdir(parents=True)       # refuses an existing directory
    res = dict(status='ERROR', harness_sha256=sha(__file__), fixture_sha256=sha(FIXTURE),
               fa_fixture_sha256=sha(FA), contract_sha256=sha(CONTRACT), legacy_baseline_revision=LEGACY_REV)
    try:
        check('fixture identity', res['fixture_sha256'] == FIXTURE_SHA, res['fixture_sha256'])
        check('contract identity', res['contract_sha256'] == CONTRACT_SHA, res['contract_sha256'])
        check('FA fixture identity', res['fa_fixture_sha256'] == FA_SHA, res['fa_fixture_sha256'])
        exe, base = out / 'spu_vm', out / 'baseline' / 'vm'
        b = run(['make', '-s', '-B', '-C', str(ROOT / 'software/vm'), 'spu_vm', f'BIN={exe}'])
        check('build', b.returncode == 0, b.stderr[-500:])
        base.mkdir(parents=True)                                  # HEAD legacy VM; ../common/include as in-tree
        (base.parent / 'common').symlink_to(ROOT / 'software/common', target_is_directory=True)
        for n in ('spu_vm.cpp', 'checked_math.h', 'assembly_operands.h'):   # legacy baseline pinned before gen1-surd
            (base / n).write_text(run(['git', '-C', str(ROOT), 'show', f'{LEGACY_REV}:software/vm/{n}']).stdout)
        bb = run(['c++', '-std=c++17', '-O2', '-Wall', '-o', str(base / 'spu_vm'), str(base / 'spu_vm.cpp')])
        check('baseline build (HEAD legacy VM)', bb.returncode == 0, bb.stderr[-500:])
        res.update(executable_sha256=sha(exe), compiler=run(['c++', '--version']).stdout.splitlines()[0],
                   sources={n: sha(ROOT / 'software/vm' / n) for n in
                            ('Makefile', 'spu_vm.cpp', 'gen1_wide.hpp', 'gen1_surd.hpp', 'gen1_cli.hpp')})
        fx = json.loads(FIXTURE.read_text())
        fa = json.loads(FA.read_text())                       # fault after SRD: reference is the frozen RTL
        r, raw, dg = gen1(exe, out, rom_bytes(fa['rom']))
        check('FA frame equals RTL', r.stdout.strip() == fa['frame'] and raw.hex() == fa['frame'], r.stdout.strip())
        check('FA diag pc/cause/retires', (dg.get('pc'), dg.get('cause'), dg.get('retires'), dg.get('fault'))
              == (fa['pc'], fa['cause'], fa['retires'], fa['fault']), dg)
        check('FA internal state S0', dg.get('s0') == {'initialized': True, 'a': '13', 'b': '4', 'd': '9'}, dg.get('s0'))
        for c in fx.values():                                 # gates 1 and 2: frames and diagnostics
            rom = rom_bytes(c['rom']); r, raw, dg = gen1(exe, out, rom)
            want = bytes.fromhex(c['frame'])
            check(f"{c['name']} frame (stdout)", r.returncode == 0 and r.stdout.strip() == c['frame'], r.stdout.strip())
            check(f"{c['name']} frame (raw)", raw == want, raw.hex())
            check(f"{c['name']} crc", zlib.crc32(raw[:29]).to_bytes(4, 'little') == raw[29:], raw[29:].hex())
            check(f"{c['name']} diag pc/cause/retires", (dg.get('pc'), dg.get('cause'), dg.get('retires'), dg.get('fault'))
                  == (c['pc'], c['cause'], c['retires'], c['fault']), dg)
            check(f"{c['name']} diag not hardware-observable", dg.get('hardware_observable') is False, dg.get('hardware_observable'))
            a, bb_, d = (int(x) for x in c['operands'])
            exp = None if c['name'] == 'M1' else expected_s0(a, bb_, d)   # M1 faults before SLD
            if c['name'] == 'M2': exp = (a, bb_, d)                         # SADD rejected after SLD
            got = dg.get('s0', {}); gt = (int(got.get('a', 0)), int(got.get('b', 0)), int(got.get('d', 0)))
            check(f"{c['name']} internal state S0", (got.get('initialized'), gt) == ((exp is not None), exp or (0, 0, 1)), got)
        led = LEDGER.read_text()
        words = [int(w, 16) for w in fx['0']['rom']]
        def variant(edits):                                   # low-half ROM edits as recorded in the ledger
            w = list(words)
            for i, (old, new) in edits.items(): assert (w[i] & 0xffffffff) == old; w[i] = (w[i] & ~0xffffffff) | new
            return b''.join(x.to_bytes(8, 'big') for x in w)
        sil = [('3.40/3.47/3.51 golden', {}, (13, 4, 9), G340, None),
               ('3.41 (2,2,3)', {0: (0x100, 0x200)}, (16, 8, 9), '(16,8,9)', None),
               ('3.43 (2,1,5)', {0: (0x100, 0x200), 2: (0x200, 0x100), 4: (0x300, 0x500)}, (7, 4, 25), '(7,4,25)', None),
               ('3.49 (2,1,3)', {0: (0x100, 0x200), 2: (0x200, 0x100)}, (7, 4, 9), '(7,4,9)', '7e5ddbf3')]
        for name, ed, t, text, crc in sil:
            _, raw, _ = gen1(exe, out, variant(ed))
            check(f'silicon {name}: ledger records it', text in led and (crc is None or crc in led), text)
            ok = raw == frame_of(t) and (name[:4] != '3.40' or raw == bytes.fromhex(G340.replace(' ', '').replace('|', '')))
            check(f'silicon {name}: frame', ok and (crc is None or '%08x' % zlib.crc32(raw[:29]) == crc), raw.hex())
        groot = out / 'roms' / 'golden.bin'; groot.write_bytes(rom_bytes(fx['0']['rom']))   # gate 3: isolation
        for args in (['--bin', str(groot), '--quiet'], [str(ROOT / 'software/programs/isa_test.sas'), '--quiet'],
                     [str(ROOT / 'software/programs/equilibrium_test.sas'), '--quiet']):
            new, old = run([str(exe), *args]), run([str(base / 'spu_vm'), *args])
            check(f'legacy unchanged {args[0][-20:]}', (new.returncode, new.stdout, new.stderr) == (old.returncode, old.stdout, old.stderr),
                  (new.returncode, old.returncode))
            alias = run([str(exe), '--profile', 'legacy', *args])
            check(f'--profile legacy == default {args[0][-20:]}', (alias.returncode, alias.stdout) == (old.returncode, old.stdout), alias.returncode)
        check('legacy still rejects Gen-1 ROM', 'unsupported canonical opcode' in run([str(exe), '--bin', str(groot)]).stderr, '')
        bad = {'unknown profile': ['--profile', 'gen2', str(groot)], 'duplicate': ['--profile', 'gen1-surd', '--profile=gen1-surd', str(groot)],
               'missing value': [str(groot), '--profile'], 'legacy option': ['--profile', 'gen1-surd', '--steps', '5', str(groot)],
               'source text': ['--profile', 'gen1-surd', str(ROOT / 'software/programs/isa_test.sas')]}
        for name, args in bad.items():
            r = run([str(exe), *args]); check(f'refused: {name}', r.returncode == 1 and r.stdout == '', (r.returncode, r.stdout[:80]))
        late = run([str(exe), str(groot), '--profile', 'gen1-surd'])
        check('profile honoured when not first', late.stdout.strip() == fx['0']['frame'], late.stdout.strip())
        m = json.loads(run([str(exe), '--profile', 'gen1-surd', '--capabilities']).stdout)   # gate 4: manifest
        caps = m['capabilities']
        check('manifest identity', m['profile'] == 'gen1-surd' and m['implementation'] == 'spu-vm-cpp' and
              len(m['build_id']) == 64 and m['source_revision'] != 'unversioned', {k: m[k] for k in ('profile', 'source_revision', 'build_id')})
        check('manifest certifies nothing', all(c['conformance'] == 'not_run' and c['evidence'] is None for c in caps.values()), caps.keys())
        check('manifest contract hash', CONTRACT_SHA in caps['cpu.gen1-surd.fixed-rom-v1']['semantic_contract'], '')
        check('flash boot not applicable', 'board.flash-boot' in m['not_applicable'] and not any('flash' in k for k in caps), m['not_applicable'])
        res['manifest'] = m
        good = bytes.fromhex(fx['0']['frame']); _, graw, _ = gen1(exe, out, rom_bytes(fx['0']['rom']))   # negative controls
        flip = lambda x, i: x[:i] + bytes([x[i] ^ 1]) + x[i + 1:]
        controls = {'crc byte flipped': flip(good, 30) != graw, 'slice byte flipped': flip(good, 5) != graw,
                    'payload altered': gen1(exe, out, variant({0: (0x100, 0x300)}))[1] != good,
                    'expectations shifted': bytes.fromhex(fx['1']['frame']) != graw}
        for name, fired in controls.items(): check(f'negative control fires: {name}', fired, fired)
        res['status'] = 'PASS' if all(c['ok'] for c in CHECKS) else 'FAIL'
    except Exception:
        res['traceback'] = traceback.format_exc()
    finally:
        res.update(checks=CHECKS, checks_total=len(CHECKS), failed=[c for c in CHECKS if not c['ok']])
        (out / 'results.json').write_text(json.dumps(res, indent=1) + '\n')
    print(res['status'], len(CHECKS), 'checks;', len(res['failed']), 'failed')
    return 0 if res['status'] == 'PASS' else 1

if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))
