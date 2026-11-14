"""Loader-session, boundary and per-field decoder fixtures for the programmable-surd harness.

Contract: docs/design/SPU_V03_CONTRACT_CANDIDATE.md §3 (fields), §7 (BUDGET at PC = L), §9-§10 (image validity).
Called from test_psurd_sim0.py; expected records come from psurd_oracle.py, never from the simulator.
"""
import psurd_oracle as O
from psurd_oracle import SLI, SLD, SMUL, SADD, SSUB, SNORM, SLIK, STST, BR, HALT, image


def run_fixtures(exe, out, sh, check):
    def session(*steps, budget=1000):
        args = [str(exe), '--profile', 'programmable-surd', '--budget', str(budget)]
        for s in steps: args += ['--do', s]
        r = sh(args); return r.returncode, r.stdout.split('\n')[:-1]
    def put(name, raw):
        p = out / f'fx_{name}.spui'; p.write_bytes(raw); return f'load:{p}'
    A = [SLIK(0, 7), HALT]; recA = O.record(O.run(A, 1000)).hex()
    a = put('A', image(A))
    bad = {'framing': b'SPUX' + image(A)[4:], 'identity rev 0x02': image(A, rev=0x02),
           'length': image(A)[:-8], 'CRC': image(A, crc_delta=1)}
    rc, lines = session('start')
    check('session: START with no image refused', rc == 0 and lines == ['START REFUSED: no valid image'], lines)
    rc, lines = session(a, 'start')
    check('session: LOAD then START runs', lines == ['LOAD OK', recA], lines)
    for k, raw in bad.items():                                    # contract §10: refused LOAD invalidates
        b = put(k.replace(' ', '_'), raw)
        rc, lines = session(a, b, 'start')
        check(f'session: refused LOAD ({k}) invalidates old image', rc == 0 and len(lines) == 3 and lines[0] == 'LOAD OK'
              and lines[1].startswith('LOAD REFUSED') and lines[2] == 'START REFUSED: no valid image', lines)
        rc, lines = session(b, a, 'start')
        check(f'session: valid LOAD after refused ({k}) runs', lines[1:] == ['LOAD OK', recA], lines)
    P1 = [SLIK(i, 100 + i) for i in range(8)] + [HALT]; P2 = [STST(3), HALT]
    rc, lines = session(put('P1', image(P1)), 'start', put('P2', image(P2)), 'start')
    want2 = O.record(O.run(P2, 1000)).hex()
    check('session: stale register bits never observable after reload', len(lines) == 4 and lines[3] == want2
          and want2[6:8] == '02' and bytes.fromhex(want2)[16] == 0, lines[3:])
    rc, lines = session(a, 'start', 'start')
    check('session: repeated START on one image identical', lines == ['LOAD OK', recA, recA], lines)
    # §7: BUDGET exhausted when the next PC equals L -> BUDGET with PC = L (precedence over PC_OVERRUN)
    rc, lines = session(put('BL', image([SLIK(0, 1)])), 'start', budget=1)
    st = O.run([SLIK(0, 1)], 1)
    check('boundary: BUDGET with PC = L', lines[1:] == [O.record(st).hex()] and st['cause'] == 'BUDGET' and st['pc'] == 1, lines)
    # §3 per-field decoder fixtures: every must-be-zero bit, and out-of-range index fields
    forms = {'SLI': (SLI(1, 2, 0xA5A5A5A5), 0xFF), 'SLD': (SLD(1), (1 << 48) - 1),
             'SMUL': (SMUL(1, 2, 3), 0xFF << 32 | 0xFFFFFF), 'SADD': (SADD(1, 2, 3), 0xFF << 32 | 0xFFFFFF),
             'SSUB': (SSUB(1, 2, 3), 0xFF << 32 | 0xFFFFFF), 'SNORM': (SNORM(1, 2), (1 << 40) - 1),
             'SLIK': (SLIK(1, -5), 0xFF << 40 | 0xFF), 'STST': (STST(2), 0xFF << 48 | (1 << 40) - 1),
             'BR': (BR('AL', 0), 0xFF << 40 | 0xFFFFFF), 'HALT': (HALT, (1 << 56) - 1)}
    idx = {'SLI': [(48, 8), (48, 255), (40, 6), (40, 255)], 'SLD': [(48, 8), (48, 255)],
           'SMUL': [(48, 8), (40, 8), (24, 8), (24, 255)], 'SNORM': [(48, 8), (40, 255)], 'SLIK': [(48, 8)],
           'STST': [(40, 8), (40, 255)], 'BR': [(48, 10), (48, 255)]}
    for name, (w0, mask) in forms.items():
        words = [w0 ^ (1 << b) for b in range(64) if mask >> b & 1]
        words += [(w0 & ~(0xFF << sh_)) | v << sh_ for sh_, v in idx.get(name, [])]
        fails = []
        for w in words:
            p = out / 'fx_dec.spui'; p.write_bytes(image([w, HALT]))
            r = sh([str(exe), '--profile', 'programmable-surd', str(p), '--budget', '10'])
            st = O.run([w, HALT], 10)
            if st['cause'] != 'BAD_ENCODING' or st['pc'] != 0 or r.stdout.strip() != O.record(st).hex(): fails.append(hex(w))
        check(f'decoder fields: {name} ({len(words)} malformed words) -> BAD_ENCODING, no state change', not fails, fails[:4])
