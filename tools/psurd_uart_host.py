#!/usr/bin/env python3
"""Host client for the SPU v0.3 programmable-surd system over UART (protocol H0-UART-1B v2; RTL-0B plan §3, §7).

usage:
  psurd_uart_host.py PORT status
  psurd_uart_host.py PORT load IMAGE.spui
  psurd_uart_host.py PORT start BUDGET
  psurd_uart_host.py PORT result [OUT.bin]
  psurd_uart_host.py PORT session SCRIPT.json OUT_DIR        (OUT_DIR must not exist)

Stop-and-wait: one frame, then the complete response or a LinkError. A missing, short or corrupt response is
an error; nothing is retried silently (the protocol has no sequence number, so a retry could repeat a START).
This tool never computes an expected result: a session script carries expected payloads (hex or a file written
beforehand by the oracle) and the tool only compares bytes. Raw termios, 115200 8N1, no extra dependency.
Session steps (JSON list of objects; "expect" is optional on every command step):
  {"op": "status" | "result" | "load_end"}, {"op": "start", "budget": N},
  {"op": "load_begin", "header_hex": H}, {"op": "load_word", "index": I, "word_hex": W},
  {"op": "load", "image": FILE}                     every frame of an image; expects OK for each unless "expect"
  {"op": "wait"}                                     poll STATUS until no run is in flight (TIMING poll values)
  {"op": "raw", "hex": H}                            bytes sent as they are (malformed-frame cases)
  {"op": "pause", "prompt": TEXT}                    operator action; waits for Enter on stdin
  expect: {"status": S, "payload_hex": H | "payload_file": F | "payload_prefix_hex": H, "none": true}
The first step whose expectation fails ends the session (exit 1). Every byte sent and received is logged with
a monotonic timestamp to OUT_DIR/traffic.jsonl; OUT_DIR/summary.json holds the per-step outcome."""
import json, os, select, sys, termios, time
from functools import reduce
from pathlib import Path

OK, REFUSED, BUSY, BAD_FRAME, TIMEOUT = 0x00, 0x20, 0x22, 0x01, 0x04
CMD = dict(load_begin=1, load_word=2, load_end=3, start=4, status=5, result=6)
# Host timing. A session script may override these under "timing"; the values used are written to summary.json.
TIMING = dict(startup_delay_s=0.5,      # after opening the port, before the first byte (stale input is drained)
              response_timeout_s=1.0,   # whole response; the longest (RESULT, 220 bytes) takes about 21 ms on the wire
              poll_interval_s=0.02,     # between STATUS polls while a run is in flight
              max_polls=3000)           # then the wait fails

class LinkError(Exception): pass
xor = lambda bs: reduce(lambda a, b: a ^ b, bs, 0)

def frame(cmd, payload=b''):
    b = bytes([0xA5, 0x02, cmd, len(payload) & 0xFF, len(payload) >> 8]) + bytes(payload)
    return b + bytes([xor(b)])

class Port:
    """Raw 8N1 serial port (or any file descriptor when fd is given, for tests)."""
    def __init__(self, path=None, fd=None, baud=termios.B115200, log=None):
        self.fd = os.open(path, os.O_RDWR | os.O_NOCTTY) if fd is None else fd; self.log = log
        if path is not None:
            a = termios.tcgetattr(self.fd)
            a[0] = 0; a[1] = 0; a[3] = 0                                   # raw input, output and local modes
            a[2] = termios.CS8 | termios.CREAD | termios.CLOCAL             # 8N1, no flow control
            a[4] = a[5] = baud; a[6][termios.VMIN] = 0; a[6][termios.VTIME] = 0
            termios.tcsetattr(self.fd, termios.TCSANOW, a)
    def _note(self, d, data):
        if self.log and data: self.log.write(json.dumps(dict(t=round(time.monotonic(), 6), dir=d, hex=data.hex())) + '\n'); self.log.flush()
    def write(self, data): self._note('tx', data); os.write(self.fd, data)
    def read(self, n, deadline):
        buf = b''
        while len(buf) < n:
            left = deadline - time.monotonic()
            if left <= 0 or not select.select([self.fd], [], [], left)[0]: break
            got = os.read(self.fd, n - len(buf)); self._note('rx', got); buf += got
        return buf
    def drain(self): return self.read(4096, time.monotonic() + 0.05)

class Client:
    def __init__(self, port, timing=None): self.port, self.t = port, dict(TIMING, **(timing or {}))
    def response(self, cmd=None):
        """One response: (status, payload). cmd = expected command echo, or None to accept any (raw frames)."""
        dl = time.monotonic() + self.t['response_timeout_s']; h = self.port.read(6, dl)
        if len(h) < 6: raise LinkError(f'no or short response header ({h.hex()})')
        if h[0] != 0xA5 or h[1] != 0x02 or not h[2] & 0x80: raise LinkError(f'bad response header {h.hex()}')
        n = h[4] | h[5] << 8; rest = self.port.read(n + 1, dl)
        if len(rest) < n + 1: raise LinkError(f'short response: {len(rest)} of {n + 1} bytes after header {h.hex()}')
        if xor(h + rest) != 0: raise LinkError(f'response checksum mismatch {(h + rest).hex()}')
        if cmd is not None and h[2] != cmd | 0x80: raise LinkError(f'response for command {h[2] & 0x7F:#x}, sent {cmd:#x}')
        return h[3], rest[:-1]
    def xfer(self, cmd, payload=b''): self.port.write(frame(cmd, payload)); return self.response(cmd)
    def status(self):
        st, p = self.xfer(CMD['status'])
        if st != OK or len(p) != 7: raise LinkError(f'STATUS answered {st:#x} {p.hex()}')
        return dict(image_valid=p[0] & 1, load_open=p[0] >> 1 & 1, record_valid=p[0] >> 2 & 1, state=p[1], cause=p[2],
                    run_id=int.from_bytes(p[3:7], 'little'), raw=p.hex())
    def load_frames(self, image):
        if len(image) < 12: raise ValueError('an SPUI image has at least a 12-byte header')
        yield CMD['load_begin'], image[:12]
        for i in range((len(image) - 12) // 8): yield CMD['load_word'], i.to_bytes(2, 'little') + image[12 + 8 * i:20 + 8 * i]
        yield CMD['load_end'], b''
    def load(self, image):
        """Send every frame; stop at the first that is not OK. Returns (status, payload, frames sent)."""
        n = 0
        for cmd, p in self.load_frames(image):
            st, pl = self.xfer(cmd, p); n += 1
            if st != OK: return st, pl, n
        return OK, b'', n
    def start(self, budget): return self.xfer(CMD['start'], int(budget).to_bytes(4, 'little'))
    def result(self): return self.xfer(CMD['result'])
    def wait(self):
        for k in range(self.t['max_polls']):
            s = self.status()
            if s['state'] not in (1, 2): return s, k + 1
            time.sleep(self.t['poll_interval_s'])
        raise LinkError(f"run still in flight after {self.t['max_polls']} polls")

def check(exp, st, pl, base):
    if exp is None: return None
    if exp.get('none'): return None if st is None else f'expected no response, got status {st:#x}'
    if st is None: return 'no response'
    if 'status' in exp and st != exp['status']: return f"status {st:#04x}, expected {exp['status']:#04x} (payload {pl.hex()[:40]})"
    want = bytes.fromhex(exp['payload_hex']) if 'payload_hex' in exp else (base / exp['payload_file']).read_bytes() if 'payload_file' in exp else None
    if want is not None and pl != want: return f'payload {pl.hex()[:80]} != expected {want.hex()[:80]}'
    if 'payload_prefix_hex' in exp and not pl.startswith(bytes.fromhex(exp['payload_prefix_hex'])): return f"payload {pl.hex()[:40]} does not start with {exp['payload_prefix_hex']}"
    return None

def session(port_path, script_path, out, fd=None, ask=input):
    script_path = Path(script_path); script = json.loads(script_path.read_text()); base = script_path.parent
    out = Path(out); out.mkdir(parents=True); log = open(out / 'traffic.jsonl', 'w')
    port = Port(port_path, fd=fd, log=log); c = Client(port, script.get('timing')); rows = []; fail = None
    time.sleep(c.t['startup_delay_s']); stale = port.drain()
    for i, step in enumerate(script['steps']):
        op, exp, st, pl, note = step['op'], step.get('expect'), None, b'', ''
        try:
            if op == 'pause': ask(step.get('prompt', 'press Enter to continue') + ' '); note = 'operator confirmed'; exp = None
            elif op == 'wait': s, n = c.wait(); st, pl, note = OK, bytes.fromhex(s['raw']), f'{n} polls'
            elif op == 'load':
                st, pl, n = c.load((base / step['image']).read_bytes()); note = f'{n} frames'
                exp = exp or dict(status=OK)
            elif op == 'raw':
                port.write(bytes.fromhex(step['hex']))
                try: st, pl = c.response(None)
                except LinkError as e:
                    note = str(e)
                    if not (exp or {}).get('none') or 'no or short response header ()' not in note: raise
            elif op == 'start': st, pl = c.start(step['budget'])
            elif op == 'load_begin': st, pl = c.xfer(CMD[op], bytes.fromhex(step['header_hex']))
            elif op == 'load_word': st, pl = c.xfer(CMD[op], int(step['index']).to_bytes(2, 'little') + bytes.fromhex(step['word_hex']))
            elif op in CMD: st, pl = c.xfer(CMD[op])
            else: raise ValueError(f'unknown step op {op!r}')
            err = check(exp, st, pl, base)
        except (LinkError, OSError, ValueError) as e:
            err = f'{type(e).__name__}: {e}'
        rows.append(dict(step=i, op=op, name=step.get('name', ''), status=st, payload_hex=pl.hex(), note=note, ok=err is None, error=err))
        if err: fail = i; break
    res = dict(result='PASS' if fail is None else 'FAIL', failed_step=fail, steps_run=len(rows), steps_total=len(script['steps']),
               timing=c.t, stale_bytes_drained=stale.hex(), script=str(script_path), rows=rows)
    (out / 'summary.json').write_text(json.dumps(res, indent=1) + '\n'); log.close()
    return res

def main(a):
    if len(a) < 2: print(__doc__); return 2
    path, op = a[0], a[1]
    if op == 'session':
        r = session(path, a[2], a[3]); print(f"session {r['result']}: {r['steps_run']} of {r['steps_total']} steps" + (f"; failed at step {r['failed_step']}: {r['rows'][-1]['error']}" if r['failed_step'] is not None else ''))
        return 0 if r['result'] == 'PASS' else 1
    c = Client(Port(path)); time.sleep(c.t['startup_delay_s']); c.port.drain()
    if op == 'status': print(json.dumps(c.status())); return 0
    if op == 'load': st, pl, n = c.load(Path(a[2]).read_bytes()); print(f'load: status {st:#04x} payload {pl.hex()} after {n} frames'); return 0 if st == OK else 1
    if op == 'start': st, pl = c.start(int(a[2], 0)); print(f'start: status {st:#04x} payload {pl.hex()}'); return 0 if st == OK else 1
    if op == 'result':
        st, pl = c.result(); print(f'result: status {st:#04x}, {len(pl)} bytes'); print(pl.hex())
        if st == OK and len(a) > 2: Path(a[2]).write_bytes(pl)
        return 0 if st == OK else 1
    print(__doc__); return 2

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
