#!/usr/bin/env python3
"""SPU v0.3 RTL-0B gate B4: the complete system, psurd_sys_top, driven only through its simulated UART.
usage: b4_system.py OUT_DIR [--mutants | --control] [--quick] [--bit N]   (OUT_DIR must not exist; default N = 4 cycles/bit;
UART bit timing is qualified at 217 cycles/bit by B1/B2; `--quick --bit 217` runs a subset at the real rate)
The full RTL-0A program set (run_rtl0a.programs) is loaded as SPUI images over the UART, started and read back:
every 213-byte record must equal the oracle (through the reference model) and the C++ simulator. Directed
cases: RESULT before any run; repeated START; a refused START keeps the old record; a failed LOAD after a
completed run invalidates the image but leaves the record readable; a new run replaces the record; stale
register contents are never observable. START / RESULT / STATUS are sent at swept delays into a run so each is
sampled in RUNNING, FINALIZING and READY. --quick: a program subset. --mutants: planted defects in run control,
record builder and the register-dump path must fail (run on the quick set). --control: only the two mutants
in CONTROL, as the negative control of the repository regression gate (run_all_tests.py)."""
import hashlib, json, shutil, subprocess, sys, traceback
from pathlib import Path
import rtl0b_host as H
from rtl0b_host import OK, REFUSED, ROOT, O
sys.path.insert(0, str(ROOT / 'hardware/tests/psurd_rtl0a'))
from run_rtl0a import programs
from psurd_oracle import SLIK, SADD, STST, BR, HALT, image
A = [SLIK(0, 7), HALT]; B = [SLIK(1, 9), SLIK(2, -3), SADD(3, 1, 2), STST(3), HALT]; LOOP = [BR('AL', 0)]
REF = lambda r: (REFUSED, bytes([r]))

def build(bit, quick):
    s = H.Session(bit); P = programs(); runs = []
    if quick: P = [p for p in P if p[0].startswith(('A-', 'B K', 'neg '))][::3] + [p for p in P if p[0].startswith(('op ', 'field '))][::60]
    s.reset(); s.case = 'RESULT before any run'; s.do(6, want=REF(10)); s.do(5, want=(OK, bytes([0, 0, 0xFF, 0, 0, 0, 0])))
    s.start(5, REF(8), poll=False)
    for name, w, bud in P:
        s.case = f'program {name}'; s.load(image(w), True); s.start(bud, (OK, b'')); runs.append((name, w, bud, s.do(6, want=(OK, b'\xa5\x03\x01'))))
    s.case = 'repeated START gives identical records'; s.load(image(B), True); same = []
    for _ in range(3): s.start(100, (OK, b'')); same.append(s.do(6, want=(OK, b'\xa5\x03\x01'))); s.do(5)
    s.case = 'refused START (B = 0) keeps the old record'; s.start(0, REF(9), poll=False); s.do(6, want=(OK, b'\xa5\x03\x01')); s.do(5, want=(OK, bytes([5, 3])))
    s.case = 'failed LOAD after a completed run: image invalid, record intact and readable'
    s.load(image(A, crc_delta=1)); s.do(5, want=(OK, bytes([4, 3]))); s.do(6, want=(OK, b'\xa5\x03\x01'))
    s.start(100, REF(8), poll=False); s.do(6, want=(OK, b'\xa5\x03\x01'))
    s.case = 'a new run replaces the record'; s.load(image(A), True); s.do(6, want=(OK, b'\xa5\x03\x01')); s.start(100, (OK, b'')); s.do(6, want=(OK, b'\xa5\x03\x01'))
    s.case = 'stale register contents never observable after a reload'
    s.load(image([SLIK(i, 100 + i) for i in range(8)] + [HALT]), True); s.start(100, (OK, b'')); s.do(6)
    s.load(image([STST(3), HALT]), True); s.start(100, (OK, b'')); s.do(6, want=(OK, b'\xa5\x03\x01\x02'))    # cause 2 INVALID, mask 0
    for c, p, nb in [(4, (7).to_bytes(4, 'little'), 10), (6, b'', 6), (5, b'', 6)]:
        budget = ((77 + 10 * nb) * bit + 400) // 3                 # the run ends about when the frame does
        for g in range(0, 840 + 2 * bit, 40):                      # + 2 bit-times: response and stop-bit slack
            s.case = f'command {c} sent {g} cycles into a run'; s.load(image(LOOP), True); s.start(budget, (OK, b''), poll=False)
            s.stim.gap(g); s.do(c, p, during=True); s.stim.poll(); s.do(6, want=(OK, b'\xa5\x03\x01\x06')); s.do(5)
    return s, runs, same

MUTANTS = {
    'FINALIZING is not busy': ('psurd_runctl.v', "assign busy = state == RUNNING || state == FINALIZING;", "assign busy = state == RUNNING;"),
    'START accepted without an image': ('psurd_runctl.v', "else if (!image_valid) answer(REFUSED, 8'd8, 8'd1);", "else if (1'b0) answer(REFUSED, 8'd8, 8'd1);"),
    'START with B = 0 accepted': ('psurd_runctl.v', "else if (budget_in == 32'd0) answer(REFUSED, 8'd9, 8'd1);", "else if (1'b0) answer(REFUSED, 8'd9, 8'd1);"),
    'refused START clears the record': ('psurd_runctl.v', "else if (budget_in == 32'd0) answer(REFUSED, 8'd9, 8'd1);", "else if (budget_in == 32'd0) begin answer(REFUSED, 8'd9, 8'd1); state <= IDLE; end"),
    'stale done ends the next run at once': ('psurd_runctl.v', "else if (armed) begin state <= FINALIZING;", "else begin state <= FINALIZING;"),
    'RESULT answered while running': ('psurd_runctl.v', "3'd6: if (busy) answer(BUSY, 8'd0, 8'd0);", "3'd6: if (1'b0) answer(BUSY, 8'd0, 8'd0);"),
    'START answered OK while running': ('psurd_runctl.v', "3'd4: if (busy) answer(BUSY, 8'd0, 8'd0);", "3'd4: if (busy) answer(OK, 8'd0, 8'd0);"),
    'run id not incremented': ('psurd_runctl.v', "run_id <= run_id + 32'd1; answer(OK, 8'd0, 8'd0);", "answer(OK, 8'd0, 8'd0);"),
    'record published before it is built': ('psurd_runctl.v', "if (state == FINALIZING && rec_done) state <= READY;", "if (state == FINALIZING) state <= READY;"),
    'uninitialized register not zero-filled': ('psurd_record.v', "(mask[r] ? dump_q[8 * j +: 8] : 8'd0)", "dump_q[8 * j +: 8]"),
    'record CRC omits byte 208': ('psurd_record.v', "crc <= crc8(crc, wbyte); idx <= idx + 8'd1;", "if (idx != 8'd208) crc <= crc8(crc, wbyte); idx <= idx + 8'd1;"),
    'mask from one register': ('psurd_record.v', "mask[r] <= dump_valid; r <= r + 3'd1;", "mask <= {8{dump_valid}}; r <= r + 3'd1;"),
    'register bytes reversed': ('psurd_record.v', "(mask[r] ? dump_q[8 * j +: 8] : 8'd0)", "(mask[r] ? dump_q[8 * (5'd23 - j) +: 8] : 8'd0)"),
    'budget field holds the retired count': ('psurd_record.v', "{mask, budget, retired,", "{mask, retired, retired,"),
    'registers advance every 23 bytes': ('psurd_record.v', "if (j == 5'd23) begin", "if (j == 5'd22) begin"),
    'dump port not connected to bank port A': ('psurd_core.v', ".ra(done ? dump_ra : ra)", ".ra(ra)"),
    'STATUS sends the reason byte': ('psurd_sys_top.v', "cmd == 3'd5 ? status_bytes[8 * rsp_addr[2:0] +: 8] :", "cmd == 3'd7 ? status_bytes[8 * rsp_addr[2:0] +: 8] :"),
    'record read not selected for RESULT': ('psurd_sys_top.v', "wire sel_record = cmd == 3'd6 && r_status == 8'h00;", "wire sel_record = 1'b0;"),
}
CONTROL = ('FINALIZING is not busy', 'uninitialized register not zero-filled')

def evaluate(out, s, psurd_dir=None):
    got, ended = H.run(out, s.stim, psurd_dir, timeout=20000); fails, seen, pay = s.check(got)
    if not ended: fails['run'] = ['did not end']
    for c in (4, 5, 6):
        if not {1, 2, 3} <= seen.get(c, set()): fails[f'sweep cmd {c}'] = [f'run states sampled: {sorted(x for x in seen.get(c, set()) if x is not None)}']
    return fails, pay

def main(out, mutants, quick, bit, control=False):
    out = Path(out).resolve(); out.mkdir(parents=True); res = dict(status='ERROR', gate='B4', bit_cycles=bit, quick=quick); chk = {}
    try:
        res['sources'] = {n: hashlib.sha256((ROOT / 'hardware/rtl/core/psurd' / n).read_bytes()).hexdigest() for n in H.PSURD}
        res['tool'] = subprocess.run(['iverilog', '-V'], capture_output=True, text=True).stdout.splitlines()[0]
        s, runs, same = build(bit, quick); cases = list(dict.fromkeys(o[2] for o in s.ops if o[0] != 'reset'))
        fails, pay = evaluate(out / 'dut', s); res['failures'] = {k: v[:4] for k, v in fails.items()}
        nd = sum(not c.startswith('program ') for c in cases)
        chk[f'{len(runs)} programs loaded over UART: every 213-byte record equals the oracle'] = not any(k.startswith('program ') for k in fails)
        chk[f'{nd} directed and BUSY-sweep cases ({s.stim.n} frames in all) equal the reference model'] = not any(not k.startswith('program ') for k in fails)
        exe = out / 'spu_vm'; subprocess.run(['make', '-s', '-B', '-C', str(ROOT / 'software/vm'), 'spu_vm', f'BIN={exe}'], check=True)
        cpp_bad = []
        for name, w, bud, i in runs:
            img = out / 'img.spui'; img.write_bytes(image(w))
            c = subprocess.run([str(exe), '--profile', 'programmable-surd', str(img), '--budget', str(bud)], capture_output=True, text=True).stdout.strip()
            if len(c) != 426 or pay.get(i, b'').hex() != c: cpp_bad.append(name)
        res['cpp_mismatch'] = cpp_bad[:15]
        chk[f'{len(runs)} records equal the C++ simulator'] = not cpp_bad
        chk['repeated START: three identical records'] = len({bytes(pay.get(i, b'')) for i in same}) == 1 and len(pay.get(same[0], b'')) == 213
        if mutants or control:
            res['mutants'] = {}; qs, _, _ = (s, 0, 0) if quick else build(bit, True)
            for name, (fn, a, b) in ((k, v) for k, v in MUTANTS.items() if mutants or k in CONTROL):
                md = out / ('mut_' + ''.join(ch if ch.isalnum() else '_' for ch in name)); md.mkdir()
                for n_ in H.PSURD: shutil.copy(ROOT / 'hardware/rtl/core/psurd' / n_, md / n_)
                t = (md / fn).read_text(); assert t.count(a) == 1, name; (md / fn).write_text(t.replace(a, b))
                f, _ = evaluate(md / 'run', qs, md); chk[f'mutant detected: {name}'] = bool(f); res['mutants'][name] = sorted(f)[:3]
        res['status'] = 'PASS' if all(chk.values()) else 'FAIL'
    except Exception:
        res['traceback'] = traceback.format_exc()
    finally:
        res['checks'] = chk; (out / 'results.json').write_text(json.dumps(res, indent=1) + '\n')
    print('B4', res['status'], json.dumps(chk, indent=1), res.get('traceback', ''))
    for k, v in list(res.get('failures', {}).items())[:12]: print(' ', k, v[:2])
    return 0 if res['status'] == 'PASS' else 1

if __name__ == '__main__':
    a = sys.argv[2:]
    sys.exit(main(sys.argv[1], '--mutants' in a, '--quick' in a, int(a[a.index('--bit') + 1]) if '--bit' in a else 4, '--control' in a))
