#!/usr/bin/env python3
"""RTL-0C gate C1: tools/psurd_uart_host.py against the RTL-0B reference model over a pseudo-terminal.
The device side uses the bench framing and Model from hardware/tests/psurd_rtl0b/rtl0b_host.py (written from the
plan and contract); the client has its own framing, so the two are cross-checked. Covers: every command; a full
load / start / wait / result equal to the oracle record; refusals; session mode with expectations (pass, and
stop at the first failing step); and link faults - a lost response, a short response, a bad response checksum
and a wrong command echo must each raise an error, never a silent success or a retry. Exit 0 only on PASS."""
import json, os, pty, sys, tempfile, threading, tty
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools')); sys.path.insert(0, str(ROOT / 'hardware/tests/psurd_rtl0b'))
import psurd_uart_host as C
import rtl0b_host as H
from psurd_oracle import SLIK, SADD, STST, HALT, image
O = H.O

class Device(threading.Thread):
    """Reference-model device on the pty master. fault: 'silent' | 'short' | 'corrupt' | 'echo' for the next frame."""
    def __init__(s, fd): super().__init__(daemon=True); s.fd, s.m, s.fault, s.frames, s.buf = fd, H.Model(), None, [], b''
    def run(s):
        while True:
            try: d = os.read(s.fd, 4096)
            except OSError: return
            if not d: return
            s.buf += d
            while len(s.buf) >= 6 and len(s.buf) >= 6 + (s.buf[3] | s.buf[4] << 8):
                n = 6 + (s.buf[3] | s.buf[4] << 8); f, s.buf = s.buf[:n], s.buf[n:]; s.frames.append(f)
                if H.xor(f): r = H.resp(f[2], H.BAD); s.m.xerr()
                else: st, pl = s.m.cmd(f[2], f[5:-1]); r = H.resp(f[2], st, pl)
                fault, s.fault = s.fault, None
                if fault == 'silent': continue
                if fault == 'short': r = r[:-2]
                if fault == 'corrupt': r = r[:-1] + bytes([r[-1] ^ 1])
                if fault == 'echo': r = H.resp((f[2] % 6) + 1, r[3], r[6:-1])
                os.write(s.fd, r)

def main():
    master, slave = pty.openpty(); tty.setraw(slave); tty.setraw(master)
    dev = Device(master); dev.start(); fast = dict(startup_delay_s=0.0, response_timeout_s=0.3, poll_interval_s=0.0, max_polls=5)
    c = C.Client(C.Port(fd=slave), fast); fails = []
    def check(name, ok, detail=''):
        print(('ok   ' if ok else 'FAIL ') + name + ('' if ok else f'  {detail}'))
        if not ok: fails.append(name)
    A = [SLIK(1, 9), SLIK(2, -3), SADD(3, 1, 2), STST(3), HALT]; recA = O.record(O.run(A, 100))
    s = c.status(); check('STATUS before anything: flags 0, IDLE, cause FF, run id 0', (s['image_valid'], s['state'], s['cause'], s['run_id']) == (0, 0, 0xFF, 0), s)
    check('RESULT before a run: REFUSED reason 10', c.result() == (C.REFUSED, b'\x0a'))
    check('START with no image: REFUSED reason 8', c.start(5) == (C.REFUSED, b'\x08'))
    check('client frame bytes equal the bench framing', dev.frames[-1] == H.frame(4, (5).to_bytes(4, 'little')) and C.frame(2, bytes(10)) == H.frame(2, bytes(10)))
    st, pl, n = c.load(image(A)); check('load: every frame OK, L + 2 frames', (st, n) == (C.OK, len(A) + 2), (st, pl, n))
    check('START accepted', c.start(100) == (C.OK, b''))
    s, polls = c.wait(); check('wait: READY, record valid, run id 1', (s['state'], s['record_valid'], s['run_id']) == (3, 1, 1), s)
    st, pl = c.result(); check('RESULT: 213 bytes equal to the oracle record', st == C.OK and pl == recA, pl.hex()[:40])
    st, pl, n = c.load(image(A, crc_delta=1)); check('bad CRC: stops at LOAD_END with REFUSED reason 4', (st, pl, n) == (C.REFUSED, b'\x04', len(A) + 2), (st, pl, n))
    st, pl, n = c.load(image(A, rev=2)); check('revision 0x02: stops at the first frame with REFUSED reason 2', (st, pl, n) == (C.REFUSED, b'\x02', 1), (st, pl, n))
    check('START with B = 0 after a failed load: REFUSED reason 8', c.start(0) == (C.REFUSED, b'\x08'))
    check('record still readable after the failed loads', c.result() == (C.OK, recA))
    for fault, word in [('silent', 'no or short response header'), ('short', 'short response'), ('corrupt', 'checksum'), ('echo', 'response for command')]:
        dev.fault = fault; before = len(dev.frames)
        try: c.xfer(C.CMD['status']); err = None
        except C.LinkError as e: err = str(e)
        c.port.drain()
        check(f'link fault "{fault}": LinkError, exactly one frame sent (no retry)', err is not None and word in err and len(dev.frames) == before + 1, err)
    check('link usable after the faults', c.status()['record_valid'] == 1)
    with tempfile.TemporaryDirectory() as td:
        td = Path(td); (td / 'a.spui').write_bytes(image(A)); (td / 'a.rec').write_bytes(recA)
        steps = [dict(op='status'), dict(op='load', image='a.spui'), dict(op='start', budget=100, expect=dict(status=0)), dict(op='wait'),
                 dict(op='result', expect=dict(status=0, payload_file='a.rec')),
                 dict(op='raw', hex=(H.frame(5)[:-1] + b'\x00').hex(), expect=dict(status=1)),
                 dict(op='load_begin', header_hex=image(A, rev=2)[:12].hex(), expect=dict(status=0x20, payload_hex='02')),
                 dict(op='pause', prompt='test pause'), dict(op='status', expect=dict(payload_prefix_hex='04'))]
        (td / 's.json').write_text(json.dumps(dict(timing=fast, steps=steps)))
        r = C.session(None, td / 's.json', td / 'out', fd=slave, ask=lambda p: '')
        check('session: all steps pass, traffic and summary written', r['result'] == 'PASS' and r['steps_run'] == len(steps) and (td / 'out/traffic.jsonl').stat().st_size > 0, r['rows'][-1])
        steps2 = [dict(op='status'), dict(op='result', expect=dict(status=0, payload_hex='00')), dict(op='start', budget=5)]
        (td / 's2.json').write_text(json.dumps(dict(timing=fast, steps=steps2))); before = len(dev.frames)
        r = C.session(None, td / 's2.json', td / 'out2', fd=slave, ask=lambda p: '')
        check('session: stops at the first failing step and sends nothing after it', r['result'] == 'FAIL' and r['failed_step'] == 1 and len(dev.frames) == before + 2, r)
        dev.fault = 'silent'; (td / 's3.json').write_text(json.dumps(dict(timing=fast, steps=[dict(op='status'), dict(op='status')])))
        r = C.session(None, td / 's3.json', td / 'out3', fd=slave, ask=lambda p: '')
        check('session: a lost response is a FAIL at that step', r['result'] == 'FAIL' and r['failed_step'] == 0, r)
    print(f"psurd_uart_host: {'PASS' if not fails else 'FAIL'} ({len(fails)} failed)")
    return 1 if fails else 0

if __name__ == '__main__':
    sys.exit(main())
