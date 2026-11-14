#!/usr/bin/env python3
"""SPU v0.3 RTL-0B gate B3: SPUI loader and image validity, on psurd_sys_top over its simulated UART.
usage: b3_loader.py OUT_DIR [--mutants] [--bit N]     (OUT_DIR must not exist; default N = 4 cycles/bit;
the UART bit timing itself is qualified at 217 cycles/bit by B1 and B2)
Every refusal kind starts from a loaded, run image A (image-valid = 1, record present) and must leave
image-valid = 0 (STATUS, and START refused 'no image'), the retained record readable, and a following valid
load runnable. Also: LOAD_END is the only commit point; a malformed non-load frame leaves a valid image intact;
load commands during a run or finalizing answer BUSY and change nothing; L = 256; the SIM-0 session
sequences mirrored and compared response for response with `spu_vm --do`. Expected responses come from the
reference model in rtl0b_host.py and from psurd_oracle. --mutants: planted loader defects must fail."""
import hashlib, json, random, shutil, subprocess, sys, traceback
from pathlib import Path
import rtl0b_host as H
from rtl0b_host import OK, REFUSED, BUSY, BAD, TMO, ROOT, O, frame, resp
from psurd_oracle import SLIK, SADD, STST, BR, HALT, image
A = [SLIK(0, 7), HALT]
B = [SLIK(1, 9), SLIK(2, -3), SADD(3, 1, 2), STST(3), HALT]
C = [SLIK(i, 100 + i) for i in range(6)] + [HALT]
LOOP = [BR('AL', 0)]
REF = lambda r: (REFUSED, bytes([r]))
word = lambda img, i, idx=None: (i if idx is None else idx).to_bytes(2, 'little') + img[12 + 8 * i:20 + 8 * i]

def build(bit, rnd):
    s = H.Session(bit); iA, iB, iC = image(A), image(B), image(C)
    def before(name):                                            # image A valid, run, record present
        s.case = name; s.load(iA, True); s.start(5, (OK, b'')); s.do(6)
    def after(valid=False, flags=None):
        s.do(5, want=(OK, bytes([flags or (5 if valid else 4)])))       # STATUS flags: record-valid, image-valid as required
        s.start(5, (OK, b'') if valid else REF(8)); s.do(6)      # the record stays readable either way
        s.load(iB, True); s.start(50, (OK, b'')); s.do(6); s.do(5, want=(OK, bytes([5])))
    hdr = lambda **k: image(C, **k)[:12]
    for name, h, r in [('framing: magic SPUX', b'SPUX' + iC[4:12], 1), ('framing: magic lower case', b'spui' + iC[4:12], 1),
                       ('identity: profile 0x02', hdr(profile=2), 2), ('identity: revision 0x02 (SIM-0, SRD)', hdr(rev=2), 2),
                       ('identity: revision 0x04', hdr(rev=4), 2), ('length: L = 0', hdr(length=0), 3),
                       ('length: L = 257', hdr(length=257), 3), ('length: L = 65535', hdr(length=65535), 3)]:
        before(name); s.do(1, h, want=REF(r)); s.do(2, word(iC, 0), want=REF(7)); after()
    before('CRC: header CRC off by one'); s.load(image(C, crc_delta=1)); s.ops[-1] = s.ops[-1][:5] + (REF(4), False); after()
    for _ in range(4):
        bitpos = rnd.randrange(64 * len(C)); raw = bytearray(iC); raw[12 + bitpos // 8] ^= 1 << bitpos % 8
        before(f'CRC: image bit {bitpos} flipped'); s.load(bytes(raw)); s.ops[-1] = s.ops[-1][:5] + (REF(4), False); after()
    before('order: index 1 skipped'); s.do(1, iC[:12], want=(OK, b'')); s.do(2, word(iC, 0), want=(OK, b''))
    s.do(2, word(iC, 2), want=REF(5)); s.do(2, word(iC, 1), want=REF(7)); s.do(3, want=REF(7)); after()
    before('order: duplicate index'); s.do(1, iC[:12]); s.do(2, word(iC, 0)); s.do(2, word(iC, 0), want=REF(5)); s.do(3, want=REF(7)); after()
    before('order: index high byte ignored would accept 0x0100'); s.do(1, iC[:12]); s.do(2, word(iC, 0, 0x100), want=REF(5)); after()
    before('order: word index L after a complete image'); s.do(1, iC[:12])
    for i in range(len(C)): s.do(2, word(iC, i), want=(OK, b''))
    s.do(2, word(iC, 0, len(C)), want=REF(5)); s.do(3, want=REF(7)); after()
    before('truncated: LOAD_END one word early'); s.do(1, iC[:12])
    for i in range(len(C) - 1): s.do(2, word(iC, i))
    s.do(3, want=REF(6)); after()
    before('truncated: LOAD_END with no words'); s.do(1, iC[:12]); s.do(3, want=REF(6)); after()
    f1 = frame(2, word(iC, 1))
    before('timeout inside a LOAD_WORD frame'); s.do(1, iC[:12]); s.do(2, word(iC, 0))
    s.raw(f1[:9], resp(2, TMO)); s.do(5, want=(OK, bytes([4]))); s.do(2, word(iC, 1), want=REF(7)); after()
    before('bad checksum on a LOAD_WORD frame'); s.do(1, iC[:12]); s.do(2, word(iC, 0))
    s.raw(frame(2, word(iC, 1), bad=4), resp(2, BAD)); s.do(2, word(iC, 1), want=REF(7)); after()
    before('bad checksum on a STATUS frame during a load'); s.do(1, iC[:12]); s.do(2, word(iC, 0))
    s.raw(frame(5, bad=1), resp(5, BAD)); s.do(3, want=REF(7)); after()
    before('UART framing error during a load'); s.do(1, iC[:12]); s.do(2, word(iC, 0))
    s.raw(f1, resp(2, BAD), bad_stop_at=7); s.do(2, word(iC, 1), want=REF(7)); after()
    before('new LOAD_BEGIN (bad header) during a load'); s.do(1, iC[:12]); s.do(2, word(iC, 0))
    s.do(1, hdr(rev=2), want=REF(2)); s.do(2, word(iC, 1), want=REF(7)); after()
    before('LOAD_WORD with no load open'); s.do(2, word(iC, 0), want=REF(7)); after()
    before('LOAD_END with no load open'); s.do(3, want=REF(7)); after()
    before('LOAD_BEGIN alone (transfer never completed)'); s.do(1, iC[:12], want=(OK, b'')); s.do(5, want=(OK, bytes([6]))); after(flags=6)
    # --- cases that end with a valid image
    before('new LOAD_BEGIN (valid) during a load: old one aborted, new one loads'); s.do(1, iC[:12]); s.do(2, word(iC, 0)); s.do(2, word(iC, 1))
    s.load(iB, True); s.start(50, (OK, b'')); s.do(6)
    s.case = 'LOAD_END is the only commit point'; s.do(1, iC[:12], want=(OK, b''))
    for i in range(len(C)): s.do(2, word(iC, i), want=(OK, b''))
    s.do(5, want=(OK, bytes([6]))); s.start(50, REF(8)); s.do(6)       # complete but not executable; old record intact
    s.do(3, want=(OK, b'')); s.do(5, want=(OK, bytes([5]))); s.start(50, (OK, b'')); s.do(6)
    for name, data, rsp, bs in [('bad checksum STATUS', frame(5, bad=8), resp(5, BAD), None), ('bad checksum LOAD_BEGIN', frame(1, hdr(rev=2), bad=1), resp(1, BAD), None),
                                ('bad checksum LOAD_END', frame(3, bad=2), resp(3, BAD), None), ('truncated LOAD_BEGIN', frame(1, iB[:12])[:8], resp(1, TMO), None),
                                ('wrong length LOAD_END', bytes([0xA5, 2, 3, 1, 0, 0, 0xA5 ^ 2 ^ 3 ^ 1]), resp(3, BAD), None),
                                ('UART framing error in START', frame(4, bytes(4)), resp(4, BAD), 6)]:
        before(f'malformed frame with no load open leaves the image valid: {name}'); s.raw(data, rsp, bs); after(valid=True)
    before('START with B = 0 is refused and changes nothing'); s.start(0, REF(9), poll=False); after(valid=True)
    s.case = 'L = 256 image'; big = [SLIK(i % 8, i) for i in range(255)] + [HALT]
    s.load(image(big), True); s.start(1000, (OK, b'')); s.do(6)
    # --- load commands while a run is in flight or finalizing: BUSY, no state change
    during = {}
    for c, p, nb in [(1, iB[:12], 18), (2, word(iC, 0), 16), (3, b'', 6)]:
        budget = ((77 + 10 * nb) * bit + 400) // 3
        for g in range(0, 840, 40):
            s.case = f'load command {c} during a run (gap {g})'; s.load(image(LOOP), True); s.start(budget, (OK, b''), poll=False)
            s.stim.gap(g); i = s.do(c, p, during=True); during.setdefault(c, []).append(i); s.stim.poll(); s.do(6); s.do(5)
            s.start(7, poll=True); s.do(6)                             # image still valid only if the command was BUSY
    return s

def sim0_sessions():
    a = image(A); bad = {'framing': b'SPUX' + a[4:], 'identity rev 0x02': image(A, rev=2), 'length': a[:-8], 'CRC': image(A, crc_delta=1)}
    P1, P2 = image([SLIK(i, 100 + i) for i in range(8)] + [HALT]), image([STST(3), HALT])
    S = [('start',), (a, 'start'), (P1, 'start', P2, 'start'), (a, 'start', 'start')]
    for b in bad.values(): S += [(a, b, 'start'), (b, a, 'start')]
    return S

def mirror(out, exe, bit):
    """SIM-0 sessions: the same LOAD/START sequences through the C++ simulator and through the RTL."""
    S = sim0_sessions(); s = H.Session(bit); ids = []
    for sess in S:
        s.reset(); row = []
        for st in sess:
            if st == 'start': row.append(('start', s.start(1000), s.do(6)))
            else: row.append(('load', s.load(st)))
        ids.append(row)
    got, ended = H.run(out / 'mirror', s.stim); fails = [] if ended else ['mirror run did not end']
    why = {1: 'bad framing', 2: 'architecture identity mismatch', 3: 'bad length', 5: 'bad length', 6: 'bad length', 4: 'CRC mismatch'}
    for k, (sess, row) in enumerate(zip(S, ids)):
        args, rtl = [str(exe), '--profile', 'programmable-surd', '--budget', '1000'], []
        for j, st in enumerate(sess):
            if st != 'start': p = out / f'm{k}_{j}.spui'; p.write_bytes(st)
            args += ['--do', 'start' if st == 'start' else f'load:{p}']
        for r in row:
            if r[0] == 'load':
                rs = [bytes(got[i][0]) for i in r[1]]; nok = [x for x in rs if len(x) < 7 or x[3] != OK]
                rtl.append('LOAD OK' if not nok else 'LOAD REFUSED: ' + (why.get(nok[0][6], '?') if len(nok[0]) > 7 and nok[0][3] == REFUSED else '?'))
            else:
                a, b = bytes(got[r[1]][0]), bytes(got[r[2]][0])
                rtl.append(b[6:-1].hex() if a == resp(4, OK) and len(b) == 220 else 'START REFUSED: no valid image' if a == resp(4, REFUSED, b'\x08') else '?')
        cpp = subprocess.run(args, capture_output=True, text=True).stdout.split('\n')[:-1]
        if cpp != rtl or not cpp: fails.append(f'session {k}: simulator {[x[:40] for x in cpp]} != RTL {[x[:40] for x in rtl]}')
    return fails, len(S)

MUTANTS = {
    'refused LOAD keeps image-valid': ("answer(REFUSED, r); image_valid <= 1'b0; load_open <= 1'b0;", "answer(REFUSED, r); load_open <= 1'b0;"),
    'accepted LOAD_BEGIN keeps image-valid': ("image_valid <= 1'b0; load_open <= 1'b1; cnt <= 9'd0;", "load_open <= 1'b1; cnt <= 9'd0;"),
    'refusal leaves the load open': ("answer(REFUSED, r); image_valid <= 1'b0; load_open <= 1'b0;", "answer(REFUSED, r); image_valid <= 1'b0;"),
    'word count not checked at LOAD_END': ("else if (cnt != img_len) refuse(8'd6);", "else if (1'b0) refuse(8'd6);"),
    'CRC not checked': ("else if (~crc != crc_exp) refuse(8'd4);", "else if (1'b0) refuse(8'd4);"),
    'CRC covers 56 of 64 bits': ("sr <= payload[79:16]; bits <= 7'd64;", "sr <= payload[79:16]; bits <= 7'd56;"),
    'order not checked': ("else if (payload[15:0] != {7'd0, cnt} || cnt == img_len) refuse(8'd5);", "else if (cnt == img_len) refuse(8'd5);"),
    'index high byte ignored': ("payload[15:0] != {7'd0, cnt}", "payload[7:0] != cnt[7:0]"),
    'word index L accepted': ("else if (payload[15:0] != {7'd0, cnt} || cnt == img_len) refuse(8'd5);", "else if (payload[15:0] != {7'd0, cnt}) refuse(8'd5);"),
    'commit at the last word': ("if (bits == 7'd1) begin imem_we <= 1'b1; cnt <= cnt + 9'd1; answer(OK, 8'd0); end", "if (bits == 7'd1) begin imem_we <= 1'b1; cnt <= cnt + 9'd1; answer(OK, 8'd0); if (cnt + 9'd1 == img_len) image_valid <= 1'b1; end"),
    'malformed frame does not abort the load': ("end else if (xerr) load_open <= 1'b0;", "end else if (1'b0) load_open <= 1'b0;"),
    'malformed frame clears image-valid': ("end else if (xerr) load_open <= 1'b0;", "end else if (xerr) begin load_open <= 1'b0; image_valid <= 1'b0; end"),
    'BUSY ignored by the loader': ("if (busy) answer(BUSY, 8'd0);\n            else case (cmd)", "case (cmd)"),
    'revision not checked': ("payload[47:32] != 16'h0301 ? 3'd2 :", "payload[39:32] != 8'h01 ? 3'd2 :"),
    'L = 256 refused': ("hdr_len > 16'd256", "hdr_len > 16'd255"),
    'L = 257 accepted': ("hdr_len > 16'd256", "hdr_len > 16'd257"),
    'words stored little-endian': ("assign word[8 * (7 - g) +: 8] = payload[16 + 8 * g +: 8];", "assign word[8 * g +: 8] = payload[16 + 8 * g +: 8];"),
    'write address off by one': ("imem_waddr <= cnt[7:0]; imem_wdata <= word;", "imem_waddr <= cnt[7:0] + 8'd1; imem_wdata <= word;"),
    'LOAD_WORD without a load does not invalidate': ("3'd2: if (!load_open) refuse(8'd7);", "3'd2: if (!load_open) answer(REFUSED, 8'd7);"),
}

def evaluate(out, s, psurd_dir=None):
    got, ended = H.run(out, s.stim, psurd_dir); fails, seen, _ = s.check(got)
    if not ended: fails['run'] = ['did not end']
    for c in (1, 2, 3):                                                # the sweep must have sampled each state
        if not {1, 2, 3} <= seen.get(c, set()): fails[f'sweep cmd {c}'] = [f'run states sampled: {sorted(x for x in seen.get(c, set()) if x is not None)}']
    return fails

def main(out, mutants, bit):
    out = Path(out).resolve(); out.mkdir(parents=True); res = dict(status='ERROR', gate='B3', bit_cycles=bit); chk = {}
    try:
        res['sources'] = {n: hashlib.sha256((ROOT / 'hardware/rtl/core/psurd' / n).read_bytes()).hexdigest() for n in H.PSURD}
        res['tool'] = subprocess.run(['iverilog', '-V'], capture_output=True, text=True).stdout.splitlines()[0]
        s = build(bit, random.Random(20261112)); cases = list(dict.fromkeys(o[2] for o in s.ops if o[0] != 'reset'))
        fails = evaluate(out / 'dut', s); res['failures'] = {k: v[:4] for k, v in fails.items()}
        chk[f'{len(cases)} loader cases, {s.stim.n} frames: every response equals the reference model'] = not fails
        exe = out / 'spu_vm'; subprocess.run(['make', '-s', '-B', '-C', str(ROOT / 'software/vm'), 'spu_vm', f'BIN={exe}'], check=True)
        mf, n = mirror(out, exe, bit); res['mirror_failures'] = mf
        chk[f'{n} SIM-0 sessions: RTL responses equal spu_vm --do, response for response'] = not mf
        if mutants:
            res['mutants'] = {}; src = (ROOT / 'hardware/rtl/core/psurd/psurd_loader.v').read_text()
            for name, (a, b) in MUTANTS.items():
                md = out / ('mut_' + ''.join(ch if ch.isalnum() else '_' for ch in name)); md.mkdir()
                for n_ in H.PSURD: shutil.copy(ROOT / 'hardware/rtl/core/psurd' / n_, md / n_)
                assert src.count(a) == 1, name; (md / 'psurd_loader.v').write_text(src.replace(a, b))
                f = evaluate(md / 'run', s, md); chk[f'mutant detected: {name}'] = bool(f); res['mutants'][name] = sorted(f)[:3]
        res['status'] = 'PASS' if all(chk.values()) else 'FAIL'
    except Exception:
        res['traceback'] = traceback.format_exc()
    finally:
        res['checks'] = chk; (out / 'results.json').write_text(json.dumps(res, indent=1) + '\n')
    print('B3', res['status'], json.dumps(chk, indent=1), res.get('traceback', ''))
    for k, v in list(res.get('failures', {}).items())[:12]: print(' ', k, v[:2])
    for v in res.get('mirror_failures', [])[:6]: print(' ', v)
    return 0 if res['status'] == 'PASS' else 1

if __name__ == '__main__':
    a = sys.argv[2:]
    sys.exit(main(sys.argv[1], '--mutants' in a, int(a[a.index('--bit') + 1]) if '--bit' in a else 4))
