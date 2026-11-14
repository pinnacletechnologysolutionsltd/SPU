#!/usr/bin/env python3
"""SPU v0.3 RTL-0C gate C5: generate the frozen physical-session package (plan §6, refinements R2 and R3).
usage: c5_session.py OUT_DIR      (OUT_DIR must not exist; needs iverilog and a C++ compiler on PATH)
Writes: script.json for tools/psurd_uart_host.py (steps P2-P8 with expected statuses and payloads, frozen host
timing), the SPUI images, the expected 213-byte records, DERIVATION.md (timing and P7 budget) and
MANIFEST.sha256. Expected responses come from the RTL-0B reference model (rtl0b_host.Model) and psurd_oracle;
every expected record is also produced by the C++ simulator spu_vm and must be byte-identical, or generation
fails. The cycles per `BR AL 0` iteration used for the P7 budget are measured on the RTL core simulation.
Nothing here touches a board. The package is reproducible: same inputs, same bytes."""
import hashlib, json, math, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'hardware/tests/psurd_rtl0b')); sys.path.insert(0, str(ROOT / 'hardware/tests/psurd_rtl0a')); sys.path.insert(0, str(ROOT / 'tools'))
import rtl0b_host as H
import run_rtl0a as R
import psurd_uart_host as C
from psurd_oracle import SLIK, BR, HALT, image
O = H.O
TIMING = dict(startup_delay_s=0.5, response_timeout_s=1.0, poll_interval_s=0.02, max_polls=3000)
HOST_ALLOWANCE_S, SAFETY, BAUD, CLK_HZ = 0.1, 4, 115200, 25_000_000

def measure_loop_cycles(tmp):
    """Cycles per BR AL 0 iteration, from two budgets on the RTL core (difference removes the fixed overhead)."""
    src = [ROOT / 'hardware/rtl/core/psurd' / n for n in ('psurd_core.v', 'psurd_decode.v', 'psurd_exec.v', 'psurd_imem.v', 'psurd_sign.v', 'psurd_bank_lutram.v')] + [ROOT / s for s in R.SHARED]
    d = tmp / 'loop_rtl'; d.mkdir(parents=True); P = [('a', [BR('AL', 0)], 1000), ('b', [BR('AL', 0)], 5000)]
    (d / 'prog.hex').write_text(''.join('%016x\n' % (w[i] if i < len(w) else 0) for _, w, _ in P for i in range(256)))
    (d / 'len.hex').write_text('00000001\n' * 2); (d / 'bud.hex').write_text(''.join('%08x\n' % b for _, _, b in P))
    (d / 'tb.v').write_text(R.TB_CORE.replace('NPROG', '2').replace('WDC', '400000'))
    c = subprocess.run(['iverilog', '-g2012', '-s', 'rtl0a_tb', '-o', str(d / 'sim'), str(d / 'tb.v')] + [str(s) for s in src], capture_output=True, text=True)
    if c.returncode: raise RuntimeError(c.stderr[-400:])
    r = subprocess.run(['vvp', '-n', str(d / 'sim')], cwd=d, capture_output=True, text=True); (d / 'sim').unlink()
    cyc = {int(t[1]): int(t[12]) for t in (x.split() for x in r.stdout.split('\n')) if t[:1] == ['P']}
    per = (cyc[1] - cyc[0]) / 4000
    if per != int(per): raise RuntimeError(f'non-integer cycles per iteration: {cyc}')
    return int(per), cyc

def main(out):
    out = Path(out).resolve(); out.mkdir(parents=True); tmp = out / '_tmp'; tmp.mkdir()
    exe = tmp / 'spu_vm'; subprocess.run(['make', '-s', '-B', '-C', str(ROOT / 'software/vm'), 'spu_vm', f'BIN={exe}'], check=True)
    P = {n: (w, b) for n, w, b in R.programs()}; m = H.Model(); steps = []; files = {}; recs = {}
    def put(name, data): (out / name).write_bytes(data); files[name] = data; return name
    def img(tag, words, **k): return put(f'{tag}.spui', image(words, **k))
    def step(phase, name, op, exp=None, **k): steps.append(dict(phase=phase, name=name, op=op, **k, **({'expect': exp} if exp is not None else {})))
    def cmd(phase, name, op, c, p=b'', **k):                    # one protocol command; expectation from the reference model
        st, pl = m.cmd(c, p); step(phase, name, op, dict(status=st, payload_hex=pl.hex()) if len(pl) != 213 else dict(status=st, payload_file=rec_file(pl)), **k); return st, pl
    def rec_file(pl):
        h = hashlib.sha256(pl).hexdigest()[:12]
        if h not in recs: recs[h] = put(f'record_{len(recs):02d}_{h}.rec', pl)
        return recs[h]
    def status(phase, name): cmd(phase, name, 'status', 5)
    def start(phase, name, budget): return cmd(phase, name, 'start', 4, budget.to_bytes(4, 'little'), budget=budget)
    def result(phase, name): return cmd(phase, name, 'result', 6)
    def load(phase, name, tag, words, budget_for_check=None, **k):
        raw = image(words, **k); fn = img(tag, words, **k); st = pl = None
        for f in H.load_frames(raw):
            st, pl = m.cmd(f[2], f[5:-1])
            if st != H.OK: break
        step(phase, name, 'load', dict(status=st, payload_hex=pl.hex()), image=fn)
    def run(phase, tag, words, budget):
        load(phase, f'load {tag}', tag, words); start(phase, f'START {tag}', budget); step(phase, f'wait {tag}', 'wait')
        st, pl = result(phase, f'RESULT {tag}')
        cpp = subprocess.run([str(exe), '--profile', 'programmable-surd', str(out / f'{tag}.spui'), '--budget', str(budget)], capture_output=True, text=True).stdout.strip()
        if st != H.OK or cpp != pl.hex(): raise RuntimeError(f'{tag}: oracle record and spu_vm record differ, or the run was refused')
        return pl
    P1 = [SLIK(0, 7), HALT]
    status('P2', 'first STATUS'); result('P2', 'RESULT before any run'); start('P2', 'START with no image', 5)
    load('P3', 'load program 1', 'prog1', P1); status('P3', 'STATUS after load')
    start('P4', 'START program 1', 1000); step('P4', 'wait program 1', 'wait'); _, rec1 = result('P4', 'RESULT program 1'); status('P4', 'STATUS after run')
    cpp = subprocess.run([str(exe), '--profile', 'programmable-surd', str(out / 'prog1.spui'), '--budget', '1000'], capture_output=True, text=True).stdout.strip()
    if cpp != rec1.hex(): raise RuntimeError('program 1: oracle and spu_vm differ')
    for n in ('A-A', 'A-B', 'A-C', 'A-D', 'A-E', 'A-F', 'B K=33', 'B K=34'):
        run('P5', n.replace(' ', '_').replace('=', ''), *P[n])
    load('P6', 'load A-A for repetition', 'A-A', P['A-A'][0])
    for i in range(5):
        start('P6', f'repeat {i + 1}: START', P['A-A'][1]); step('P6', f'repeat {i + 1}: wait', 'wait'); result('P6', f'repeat {i + 1}: RESULT'); status('P6', f'repeat {i + 1}: STATUS')
    run('P6', 'prog1_again', P1, 1000)
    load('P7', 'image with a wrong CRC', 'bad_crc', P1, crc_delta=1); status('P7', 'STATUS: image invalid, record kept'); start('P7', 'START refused: no image', 5); result('P7', 'earlier record still readable')
    cmd('P7', 'header with revision 0x02', 'load_begin', 1, image(P1, rev=2)[:12], header_hex=image(P1, rev=2)[:12].hex())
    load('P7', 'reload program 1', 'prog1', P1); start('P7', 'START with B = 0', 0); result('P7', 'record unchanged after refused START')
    # long run: budget derived, not chosen (R3)
    per, cyc = measure_loop_cycles(tmp)
    during = [(6, 14), (10, 7), (18, 7), (6, 7), (6, 14)]           # STATUS, START, LOAD_BEGIN, RESULT, STATUS: host bytes, device bytes
    wire_s = sum(h * 10 + d * 11 for h, d in during) / BAUD; need_s = (wire_s + HOST_ALLOWANCE_S * len(during)) * SAFETY
    budget = math.ceil(need_s * CLK_HZ / per / 1_000_000) * 1_000_000
    LOOP = [BR('AL', 0)]; load('P7', 'load the long-running loop', 'loop', LOOP)
    st, _ = m.cmd(4, budget.to_bytes(4, 'little')); step('P7', 'START long run', 'start', dict(status=st, payload_hex=''), budget=budget)
    busy_status = m.status(1).hex()                                  # image valid, RUNNING, no record, cause FF, this run id
    step('P7', 'STATUS during the run: RUNNING', 'status', dict(status=0, payload_hex=busy_status))
    step('P7', 'START during the run: BUSY', 'start', dict(status=H.BUSY, payload_hex=''), budget=5)
    step('P7', 'LOAD_BEGIN during the run: BUSY', 'load_begin', dict(status=H.BUSY, payload_hex=''), header_hex=image(P1)[:12].hex())
    step('P7', 'RESULT during the run: BUSY', 'result', dict(status=H.BUSY, payload_hex=''))
    step('P7', 'STATUS still RUNNING (the run outlasted the commands)', 'status', dict(status=0, payload_hex=busy_status))
    step('P7', 'wait long run', 'wait'); _, recL = result('P7', 'RESULT long run: BUDGET record')
    cpp = subprocess.run([str(exe), '--profile', 'programmable-surd', str(out / 'loop.spui'), '--budget', str(budget)], capture_output=True, text=True).stdout.strip()
    if cpp != recL.hex() or recL[3] != 6: raise RuntimeError('long run: oracle and spu_vm differ, or the cause is not BUDGET')
    m.xerr(); step('P7', 'frame with a bad checksum: BAD_FRAME', 'raw', dict(status=H.BAD, payload_hex=''), hex=(C.frame(5)[:-1] + bytes([C.frame(5)[-1] ^ 0x10])).hex())
    status('P7', 'STATUS after BAD_FRAME')
    m.xerr(); step('P7', 'truncated frame: TIMEOUT', 'raw', dict(status=H.TMO, payload_hex=''), hex=C.frame(4, bytes(4))[:7].hex())
    status('P7', 'STATUS after TIMEOUT')
    step('P8', 'operator: press KEY0 once', 'pause', prompt='Press KEY0 (reset) once, release it, then press Enter.')
    m = H.Model(); status('P8', 'STATUS after reset'); result('P8', 'RESULT after reset'); start('P8', 'START after reset', 5)
    load('P8', 'reload program 1 after reset', 'prog1', P1); start('P8', 'START program 1 after reset', 1000); step('P8', 'wait after reset', 'wait')
    _, rec8 = result('P8', 'RESULT equals the P4 record')
    if rec8 != rec1: raise RuntimeError('P8 record differs from P4 in the reference model')
    put('script.json', (json.dumps(dict(package='SPU v0.3 RTL-0C physical session, version 1', protocol='H0-UART-1B v2', timing=TIMING, steps=steps), indent=1) + '\n').encode())
    put('DERIVATION.md', f'''# RTL-0C session package: frozen host timing and P7 budget (plan R2, R3)

Generated by `hardware/tests/psurd_rtl0c/c5_session.py`. {len(steps)} steps, {len(recs)} distinct expected records.

## Host timing (R2)

| Setting | Value | Derivation |
|---|---|---|
| Serial | 115,200 baud, 8N1, no flow control | `psurd_sys_top` defaults: 25 MHz / 115,200 = 217 cycles per bit |
| Delay between opening the port and the first byte | {TIMING['startup_delay_s']} s | The board releases reset 255 cycles of 50 MHz (5.1 us) after KEY0 or configuration; 0.5 s is for the operator and USB, and stale input is drained first |
| Per-response timeout | {TIMING['response_timeout_s']} s | The longest response (RESULT, 220 bytes at 11 bit-times) takes 21.0 ms; the device's own inter-byte timeout answers within 0.7 ms. 1.0 s leaves room for USB and host scheduling |
| STATUS polling interval | {TIMING['poll_interval_s']} s | One poll exchange is 20 bytes, about 1.9 ms on the wire |
| Maximum polls per wait | {TIMING['max_polls']} | {TIMING['max_polls'] * TIMING['poll_interval_s']:.0f} s at the interval above; the longest run in this session is {budget * per / CLK_HZ:.2f} s |

A missing or malformed response is a failure of that step. Nothing is retried.

## P7 budget (R3)

- Commands sent during the long run: STATUS, START, LOAD_BEGIN, RESULT, STATUS. Host bytes and device bytes
  per exchange: {during}. On the wire at 115,200 baud (10 bit-times per host byte, 11 per device byte):
  **{wire_s * 1000:.2f} ms**.
- Host allowance: {HOST_ALLOWANCE_S} s per exchange for USB and scheduling latency (an assumption; not measured) x {len(during)} = {HOST_ALLOWANCE_S * len(during):.1f} s.
- Safety factor {SAFETY}: required run time **{need_s:.3f} s**.
- Cycles per `BR AL 0` iteration: **{per}**, measured on the RTL core simulation (budgets 1,000 and 5,000 took {cyc[0]} and {cyc[1]} cycles).
- Budget = ceil({need_s:.3f} s x 25,000,000 / {per}), rounded up to a million: **{budget:,}** retired instructions.
- **Instructions are not clock cycles.** {budget:,} retired `BR AL 0` instructions x {per} cycles each =
  {budget * per:,} cycles of the 25 MHz clock = **{budget * per / CLK_HZ:.2f} s**. (At one cycle per instruction it would be {budget / CLK_HZ:.2f} s.)
- **Margin if the host is slower than assumed.** The five exchanges must finish inside the {budget * per / CLK_HZ:.2f} s run. With
  {wire_s * 1000:.2f} ms on the wire, the host may spend up to **{(budget * per / CLK_HZ - wire_s) / len(during):.3f} s per exchange** ({(budget * per / CLK_HZ - wire_s) / len(during) / HOST_ALLOWANCE_S:.1f} times the
  {HOST_ALLOWANCE_S} s allowance) before the last STATUS would fall after the end of the run.

## Sent during the run versus processed during the run

A BUSY answer shows that the command was processed while a run was in flight; the session does not rely on
that alone. The three BUSY commands (START, LOAD_BEGIN, RESULT) are bracketed by two STATUS commands whose
expected payload is flags `01` (image valid, no record), state `01` RUNNING, cause `FF`, and this run's id.
Because the link is stop-and-wait and the device answers in order, both STATUS answers reporting RUNNING
establish that everything between them was received and answered during the run. If the run ended early, the
second STATUS reports READY and that step fails; the BUSY answers are never assumed.

## Stop at the first failure; no retries

`tools/psurd_uart_host.py session` ends at the first step whose response is missing, malformed or different
from the expectation, and sends nothing afterwards. Every byte sent and received up to that point is already
in `traffic.jsonl` (flushed per write) and the per-step outcome is in `summary.json`. No LOAD, START or RESULT
is ever repeated after a timeout: the protocol has no sequence number, so a retry could act twice. This
behaviour is covered by the host-client tests (four link faults, each with exactly one frame sent; a failing
step followed by no further frames).
'''.encode())
    rows = ['| # | Phase | Step | Command | Expected status | Expected payload |', '|---|---|---|---|---|---|']
    names_st = {0: 'OK', 0x20: 'REFUSED', 0x22: 'BUSY', 1: 'BAD_FRAME', 4: 'TIMEOUT'}
    for i, s in enumerate(steps):
        e = s.get('expect', {}); extra = s.get('image') or (f"budget {s['budget']:,}" if 'budget' in s else '') or (s.get('hex', '') and 'raw ' + s['hex']) or ''
        pay = e.get('payload_file') or (e.get('payload_hex') or ('—' if e else ''))
        rows.append(f"| {i} | {s['phase']} | {s['name']} | {s['op']} {extra} | {names_st.get(e.get('status'), '(operator)' if s['op'] == 'pause' else 'OK, no run in flight' if s['op'] == 'wait' else '')} | {pay} |")
    put('SESSION.md', ('# RTL-0C session package v1: every step in order\n\nGenerated listing of `script.json` for review. Payloads are hex; a `.rec` file is a 213-byte expected record.\n'
        'A STATUS payload is: flags (bit 0 image-valid, bit 1 load-open, bit 2 record-valid), run state, cause or FF, run id (4 bytes, little-endian).\n\n' + '\n'.join(rows) + '\n').encode())
    import shutil; shutil.rmtree(tmp)
    names = sorted(p.name for p in out.iterdir())
    (out / 'MANIFEST.sha256').write_text(''.join(f'{hashlib.sha256((out / n).read_bytes()).hexdigest()}  {n}\n' for n in names))
    print(f'C5 package: {len(steps)} steps, {len(recs)} records, {len(names)} files, P7 budget {budget:,} ({per} cycles per iteration)')
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))
