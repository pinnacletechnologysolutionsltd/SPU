#!/usr/bin/env python3
"""SPU v0.3 RTL-0C gate C2: behavioural simulation of the board top psurd_board_top (50 MHz in, KEY0 reset pad,
UART at the real 217 cycles/bit of the 25 MHz CPU clock). usage: c2_board.py OUT_DIR [--mutants]  (OUT_DIR new)
Reuses the RTL-0B bench host, reference model and oracle; the host-side monitor runs on its own 25 MHz clock.
Checks: first contact after power-up; programs loaded, run and read back through the board top (records equal
the oracle); reset pad behaviour - held then released, re-asserted during a run, re-asserted inside a frame, a
60 ns pulse, a bouncing release - each must return the system to its reset state (STATUS flags 00, IDLE, cause
FF, run id 0; RESULT and START refused) and leave it loadable. Release timing: the internal reset must drop
between RELEASE_MIN and RELEASE_MAX 50 MHz cycles after the pad's last rising edge.
BEHAVIOURAL ONLY: simulation says nothing about metastability or synchronizer structure (gate C3 checks those).
--mutants: planted board-top defects must fail. Exit 0 only on PASS."""
import hashlib, json, shutil, subprocess, sys, traceback
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'hardware/tests/psurd_rtl0b')); sys.path.insert(0, str(ROOT / 'hardware/tests/psurd_rtl0a'))
import rtl0b_host as H
from rtl0b_host import OK, REFUSED, O
from run_rtl0a import programs
from psurd_oracle import SLIK, BR, HALT, image
BOARD = ROOT / 'hardware/boards/artix7/psurd_board_top.v'
RELEASE_MIN, RELEASE_MAX = 257, 266          # 2 synchronizer + 255 count + 2 CPU-clock (4 x 50 MHz) stages, with phase slack
REF = lambda r: (REFUSED, bytes([r])); CLEARED = (OK, bytes([0, 0, 0xFF, 0, 0, 0, 0]))
A = [SLIK(0, 7), HALT]

def board_tb():
    t = H.TB
    def sub(a, b):
        nonlocal t
        assert t.count(a) == 1, a[:50]; t = t.replace(a, b)
    sub('''  psurd_sys_top #(.CLK_HZ(BIT), .BAUD(1), .TIMEOUT(BIT * 80)) dut (.clk(clk), .rst(rst), .uart_rx(drv), .uart_tx(txl),
    .busy(busy), .image_valid(iv), .record_valid(rv));''',
        '''  reg sys_clk = 0; always #10 sys_clk = ~sys_clk;                      // 50 MHz board oscillator
  psurd_board_top dut (.sys_clk(sys_clk), .rst_n(!rst), .uart_rx(drv), .uart_tx(txl));
  assign iv = dut.u_sys.image_valid; assign rv = dut.u_sys.record_valid; assign busy = dut.u_sys.busy;
  integer since = 0; reg padq = 0, irq = 1;                              // release timing, in 50 MHz cycles
  always @(posedge sys_clk) begin padq <= !rst; irq <= dut.u_sys.rst;
    since <= (!rst && padq) ? since + 1 : 0;
    if (irq && !dut.u_sys.rst) $display("Q %0d", since); end
  always @(posedge dut.cpu_clk) if (dut.u_sys.cmd_valid)
    $display("S %0d %0d %0d %0d %0d", dut.u_sys.cmd, dut.u_sys.runctl.state, iv, dut.u_sys.load_open, rv);''')
    sub('''    if (dut.cmd_valid) $display("S %0d %0d %0d %0d %0d", dut.cmd, dut.runctl.state, iv, dut.load_open, rv);\n''', '')
    sub("        default: ;\n      endcase", '''        4'd8: begin rst = 1; #60; rst = 0; #(BT * 3); end                 // 60 ns pulse (three 50 MHz cycles)
        4'd9: begin rst = 1; #(BT); for (k = 0; k < 12; k = k + 1) begin rst = 0; #(700 + 90 * k); rst = 1; #(300 + 50 * k); end
                    rst = 0; #(BT * 3); end                               // bouncing release
        default: ;
      endcase''')
    return t

def build(mutant_set):
    s = H.Session(217); P = {n: (w, b) for n, w, b in programs()}; runs = []
    def cleared():
        s.do(5, want=CLEARED); s.do(6, want=REF(10)); s.start(5, REF(8), poll=False)
    def prog(name):
        w, b = P[name]; s.load(image(w), True); s.start(b, (OK, b'')); runs.append(s.do(6, want=(OK, b'\xa5\x03\x01')))
    def raw_reset(op):
        s.stim.ops.append(op << 28); s.ops.append(('reset',))
    s.ops.append(('reset',)); s.case = 'first contact after power-up'; cleared()
    s.case = 'program 1 (SLIK 0,7; HALT)'; s.load(image(A), True); s.start(1000, (OK, b'')); s.do(6, want=(OK, b'\xa5\x03\x01\x00'))
    for n in (['B K=33'] if mutant_set else ['A-A', 'A-F', 'B K=33', 'B K=34', 'neg OVERFLOW alias d=a=b', 'neg uninit read']):
        s.case = f'program {n}'; prog(n)
    s.case = 'reset held and released with an image and a record present'; s.reset(); cleared()
    s.load(image(A), True); s.start(1000, (OK, b'')); s.do(6, want=(OK, b'\xa5\x03\x01\x00'))
    s.case = 'reset re-asserted during a run'; s.load(image([BR('AL', 0)]), True); s.start(1_000_000, (OK, b''), poll=False)
    s.do(5, during=True); s.reset(); cleared()                           # STATUS first: must report RUNNING (checked in evaluate)
    if not mutant_set:
        s.case = 'reset re-asserted inside a frame'; s.load(image(A), True); s.start(1000, (OK, b'')); s.do(6)
        s.raw(H.frame(1, image(A)[:12])[:9], b'')
        s.stim.ops[-1] = 1 << 28 | 1; s.reset(); cleared()                # no wait for a response: reset arrives mid-frame
        s.case = '60 ns reset pulse is a full reset'; s.load(image(A), True); s.start(1000, (OK, b'')); s.do(6); raw_reset(8); cleared()
        s.case = 'bouncing release is one clean reset'; s.load(image(A), True); s.start(1000, (OK, b'')); s.do(6); raw_reset(9); cleared()
        s.case = 'loadable after the reset cases'; prog('B K=33')
    return s

MUTANTS = {
    'reset polarity inverted': ('rst_sync <= {rst_sync[0], rst_n};', 'rst_sync <= {rst_sync[0], ~rst_n};'),
    'release counter removed': ("wire rst_n_int = (rst_count == 8'hff);", 'wire rst_n_int = rst_sync[1];'),
    'release counter 8 cycles': ("wire rst_n_int = (rst_count == 8'hff);", "wire rst_n_int = (rst_count[2:0] == 3'h7);"),
    'divide by four': [('    reg cpu_clk_div = 1\'b0;\n', '    reg cpu_clk_div = 1\'b0;\n    reg div_ph = 1\'b0;\n    always @(posedge sys_clk) div_ph <= rst_n_int ? ~div_ph : 1\'b0;\n'),
                       ('cpu_clk_div <= ~cpu_clk_div;', 'cpu_clk_div <= div_ph ? ~cpu_clk_div : cpu_clk_div;')],
    'release synchronizer removed (reset never clocked in)': ('wire cpu_rst_n = cpu_rst_sync[1];', 'wire cpu_rst_n = rst_n_int;'),
    'system reset tied off': ('.rst(!cpu_rst_n)', ".rst(1'b0)"),
}

def evaluate(out, s, board):
    got, ended = H.run(out, s.stim, timeout=40000, tb=board_tb(), extra=[board]); q = [int(x.split()[1]) for x in got.pop('log')]
    fails, seen, pay = s.check(got)
    if seen.get(5) != {1}: fails['run in flight at reset'] = [f'STATUS before the mid-run reset saw run states {seen.get(5)}']
    if not ended: fails['run'] = ['did not end']
    nres = 1 + sum(o[0] == 'reset' for o in s.ops[1:])
    if len(q) != nres or not all(RELEASE_MIN <= x <= RELEASE_MAX for x in q): fails['release timing'] = [f'{len(q)} releases (want {nres}), cycles {q}']
    return fails, q

def main(out, mutants):
    out = Path(out).resolve(); out.mkdir(parents=True); res = dict(status='ERROR', gate='C2', scope='behavioural simulation only'); chk = {}
    try:
        res['sources'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [BOARD] + [ROOT / 'hardware/rtl/core/psurd' / n for n in H.PSURD]}
        res['tool'] = subprocess.run(['iverilog', '-V'], capture_output=True, text=True).stdout.splitlines()[0]
        s = build(False); cases = list(dict.fromkeys(o[2] for o in s.ops if o[0] != 'reset'))
        fails, q = evaluate(out / 'dut', s, BOARD); res['failures'] = {k: v[:4] for k, v in fails.items()}; res['release_cycles'] = q
        chk[f'{len(cases)} board cases, {s.stim.n} frames at 217 cycles/bit: responses and records equal the reference model and oracle'] = not [k for k in fails if k != 'release timing']
        chk[f'{len(q)} reset releases, each {RELEASE_MIN}-{RELEASE_MAX} cycles of 50 MHz after the pad'] = 'release timing' not in fails
        if mutants:
            ms = build(True); src = BOARD.read_text(); res['mutants'] = {}
            for name, subs in MUTANTS.items():
                md = out / ('mut_' + ''.join(ch if ch.isalnum() else '_' for ch in name)); md.mkdir(); t = src
                for a, b in (subs if isinstance(subs, list) else [subs]):
                    assert t.count(a) == 1, name; t = t.replace(a, b)
                (md / BOARD.name).write_text(t)
                f, _ = evaluate(md / 'run', ms, md / BOARD.name); chk[f'mutant detected: {name}'] = bool(f); res['mutants'][name] = sorted(f)[:3]
        res['status'] = 'PASS' if all(chk.values()) else 'FAIL'
    except Exception:
        res['traceback'] = traceback.format_exc()
    finally:
        res['checks'] = chk; (out / 'results.json').write_text(json.dumps(res, indent=1) + '\n')
    print('C2', res['status'], json.dumps(chk, indent=1), res.get('traceback', ''))
    for k, v in list(res.get('failures', {}).items())[:10]: print(' ', k, v[:2])
    return 0 if res['status'] == 'PASS' else 1

if __name__ == '__main__':
    sys.exit(main(sys.argv[1], '--mutants' in sys.argv[2:]))
