"""GEN1-ISA-COVERAGE-2 oracle: expected ROM images and UART frames, derived without any DUT output.

Sources: ROM words from the tracked encoder (software/tools/surd_cpu_encoding.encode_surd); arithmetic from the
host model (software/experiments/surd_cpu_stream.canonical/fits); acceptance rules from the frozen Gen-1 subset
(SLI S0 slice<6, SLD S0, SMUL S0,S0,S0, SRD S0 slice<6, all reserved bits zero); frame layout from the packetizer
protocol: a5 01 status(01 ok / 02 fault) mask pc | 6 x u32le result slices (zero where mask bit clear) | CRC-32 LE
over bytes 0..28 (zlib.crc32). Run directly to freeze expected_records.json.
"""
import json, sys, zlib, hashlib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[4]; sys.path.insert(0, str(ROOT))
from software.tools.surd_cpu_encoding import encode_surd
from software.experiments.surd_cpu_stream import canonical, fits
import parse_record as PR

M64, M32 = (1 << 64) - 1, (1 << 32) - 1
def slices(a, b, d): return [(a & M64) & M32, (a & M64) >> 32, (b & M64) & M32, (b & M64) >> 32, d & M32, d >> 32]
def program(a, b, d):
    p = [encode_surd('SLI', ['S0', str(i), str(v)]) for i, v in enumerate(slices(a, b, d))]
    p += [encode_surd('SLD', ['S0']), encode_surd('SMUL', ['S0', 'S0', 'S0'])]
    p += [encode_surd('SRD', ['S0', str(i)]) for i in range(6)]
    return p + [0, 0]
GOLDEN = program(1, 2, 3)
CASES = {  # id: (name, operands, extra word edits {index: word})
    0: ('G', (1, 2, 3), {}),
    1: ('N1', (1, -2, 3), {}),
    2: ('N2', (1 << 32, -(1 << 32), 1 << 32), {}),
    3: ('O', ((1 << 63) - 1, (1 << 63) - 1, 1), {}),
    4: ('I', (1, 2, 0), {}),
    5: ('M1', (1, 2, 3), {1: GOLDEN[1] | 0x01}),
    6: ('M2', (1, 2, 3), {7: 0x7400000000000000}),
}
def accepted(w):
    op, dst, sa = w >> 56, (w >> 48) & 255, (w >> 40) & 255
    if op == 0x70: return dst == 0 and sa < 6 and w & 255 == 0
    if op == 0x72: return dst == 0 and sa < 6 and w & ((1 << 40) - 1) == 0
    return w in (0x7100000000000000, 0x7300000000000000)
def s64(lo, hi):
    v = lo | hi << 32; return v - (1 << 64) if v >> 63 else v
def execute(rom):
    """Returns (fault, pc, mask, result_slices, retires[(pc,status)], cause) for the fixed 14-instruction flow.
    Status codes from the ISA: OK=0, INVALID=1, OVERFLOW=2. cause: None, 'fetch_reject' or 'retire_status'."""
    st, s0, res, mask, ret = [None] * 6, None, [0] * 6, 0, []
    for pc in range(14):
        w = rom[pc]
        if not accepted(w): return True, pc, mask, [0] * 6, ret, 'fetch_reject'
        op, sl, pay = w >> 56, (w >> 40) & 255, (w >> 8) & M32
        if op == 0x70: st[sl] = pay
        elif op == 0x71:
            if None in st or (st[4] | st[5] << 32) == 0:                                       # SLD INVALID
                return True, pc, mask, [0] * 6, ret + [(pc, 1)], 'retire_status'
            s0 = (s64(st[0], st[1]), s64(st[2], st[3]), st[4] | st[5] << 32)
        elif op == 0x73:
            a, b, d = s0; raw = (a * a + 3 * b * b, 2 * a * b, d * d)
            if fits(raw): s0 = raw
            elif fits(canonical(raw)): s0 = canonical(raw)
            else: return True, pc, mask, [0] * 6, ret + [(pc, 2)], 'retire_status'              # OVERFLOW
        elif op == 0x72: res[sl] = slices(*s0)[sl]; mask |= 1 << sl
        ret.append((pc, 0))
    return False, 14, mask, res, ret, None
def frame(fault, pc, mask, res):
    body = bytes([0xA5, 0x01, 0x02 if fault else 0x01, mask, pc]) + b''.join(
        (r if mask >> (i) & 1 else 0).to_bytes(4, 'little') for i, r in enumerate(res))
    return body + zlib.crc32(body).to_bytes(4, 'little')
def build():
    out = {}
    for cid, (name, ops, edits) in CASES.items():
        rom = program(*ops)
        for k, w in edits.items(): rom[k] = w
        f, pc, mask, res, ret, cause = execute(rom)
        out[str(cid)] = {'name': name, 'operands': [str(x) for x in ops], 'rom': ['%016x' % w for w in rom],
                         'fault': f, 'pc': pc, 'mask': mask, 'retires': ret, 'cause': cause,
                         'frame': frame(f, pc, mask, res).hex()}
    assert bytes.fromhex(out['0']['frame']) == PR.EXPECTED, 'G oracle frame != frozen 3.40 EXPECTED'
    return out
if __name__ == '__main__':
    exp = build(); p = Path(sys.argv[1]); p.write_text(json.dumps(exp, indent=1) + '\n')
    for c in exp.values(): print(c['name'], 'fault' if c['fault'] else 'ok', 'pc', c['pc'], 'mask %02x' % c['mask'], c['cause'], c['retires'][-1:], len(c['retires']), c['frame'])
    print('sha256', hashlib.sha256(p.read_bytes()).hexdigest())
