#!/usr/bin/env python3
"""SPU v0.3 RTL-0B gate B1: qualify the existing UART primitives spu_uart_rx / spu_uart_tx for v0.3.
usage: b1_uart.py OUT_DIR [--mutants] [--legacy-rx]      (OUT_DIR must not exist)
Default RX is psurd_uart_rx (v0.3, D2); --legacy-rx runs the shared spu_uart_rx, which fails T4-T6.
25 MHz clock, 115200 baud (217 cycles/bit, as Gen-1). Testbench generated into OUT_DIR. Sections:
T1 TX->RX loopback, all 256 byte values; T2 TX waveform (start/data LSB-first/stop, 217-cycle bits);
T3 RX from an asynchronous bit-banged driver at nominal and +-2 % baud with non-clock-aligned phases;
T4 bad stop bit -> frame_err, no byte, then recovery; T5 idle-line glitch shorter than half a bit -> no byte;
T6 20-bit break -> no spurious byte, then recovery. Expected values come from this script, not RTL output.
--mutants: planted defects (RX samples at bit start; TX wrong bit time) must fail. Exit 0 only on PASS."""
import json, random, shutil, subprocess, sys, traceback
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
LEGACY_RX, TX = ROOT / 'hardware/rtl/peripherals/whisper/spu_uart_rx.v', ROOT / 'hardware/rtl/peripherals/whisper/spu_uart_tx.v'
RX = ROOT / 'hardware/rtl/core/psurd/psurd_uart_rx.v'
BIT = 217; NS = BIT * 40
TB = r'''`timescale 1ns/1ps
module b1_tb;
  reg clk = 0, rst_n = 0, send = 0, drv = 0; reg [7:0] d = 0; integer cyc = 0, i, k;
  wire txl, busy, done, lv, lf, dv, df; wire [7:0] ld, dd;
  spu_uart_tx #(25000000, 115200) tx (.clk(clk), .rst_n(rst_n), .data(d), .send(send), .tx(txl), .busy(busy), .done(done));
  RXMOD #(25000000, 115200) rl (.clk(clk), .rst_n(rst_n), .rx(txl), .data(ld), .valid(lv), .frame_err(lf));
  RXMOD #(25000000, 115200) rd (.clk(clk), .rst_n(rst_n), .rx(drv), .data(dd), .valid(dv), .frame_err(df));
  always #20 clk = ~clk;
  always @(posedge clk) begin cyc <= cyc + 1;
    if (lv) $display("L %0d %02x", cyc, ld); if (lf) $display("LF %0d", cyc);
    if (dv) $display("D %0d %02x", cyc, dd); if (df) $display("DF %0d", cyc); end
  reg txq = 1; always @(posedge clk) begin txq <= txl; if (txq !== txl) $display("W %0d %0d", cyc, txl); end
  task tsend(input [7:0] v); begin @(negedge clk); while (busy) @(negedge clk); d = v; send = 1; @(negedge clk); send = 0;
    while (!done) @(negedge clk); end endtask
  task dbyte(input [7:0] v, input real bt, input stopv); begin
    drv = 0; #(bt); for (k = 0; k < 8; k = k + 1) begin drv = v[k]; #(bt); end drv = stopv; #(bt); drv = 1; #(bt * 2); end endtask
  initial begin
    $display("M T0"); #100 rst_n = 1; #(NSB * 5); drv = 1; #(NSB * 12);   // > one frame: a false start would complete here
    $display("M T1"); for (i = 0; i < 256; i = i + 1) tsend(i);
    #(NSB * 3); $display("M T3");
@@T3@@
    #(NSB * 30); $display("M T4"); dbyte(8'hA5, NSB, 0); #(NSB * 2); dbyte(8'h3C, NSB, 1);
    #(NSB * 30); $display("M T5"); drv = 0; #(NSB / 3); drv = 1; #(NSB * 12); dbyte(8'h5A, NSB, 1);
    #(NSB * 30); $display("M T6"); drv = 0; #(NSB * 20); drv = 1; #(NSB * 3); dbyte(8'hC3, NSB, 1);
    #(NSB * 4); $display("END"); $finish;
  end
endmodule
'''

def t3_stimulus(rnd):
    cases, lines = [], []
    for scale in (1.0, 0.98, 1.02):
        for _ in range(64):
            v, ph = rnd.randrange(256), rnd.randrange(1, 997)
            cases.append(v); lines.append(f'    #({ph} + 0.37); dbyte(8\'h{v:02x}, {NS * scale:.2f}, 1);')
    return cases, '\n'.join(lines)

def run(out, rx, tx, cases, stim):
    out.mkdir(parents=True)
    mod = 'spu_uart_rx' if rx.name == 'spu_uart_rx.v' else 'psurd_uart_rx'
    (out / 'tb.v').write_text(TB.replace('NSB', str(NS)).replace('@@T3@@', stim).replace('RXMOD', mod))
    c = subprocess.run(['iverilog', '-g2012', '-o', str(out / 'sim'), str(out / 'tb.v'), str(rx), str(tx)], capture_output=True, text=True)
    if c.returncode: raise RuntimeError('compile: ' + c.stderr[-600:])
    r = subprocess.run(['vvp', '-n', str(out / 'sim')], capture_output=True, text=True, timeout=1200)
    (out / 'sim.log').write_text(r.stdout); (out / 'sim').unlink()
    sec, ev = None, {}
    for t in (x.split() for x in r.stdout.split('\n')):
        if t[:1] == ['M']: sec = t[1]; ev[sec] = []
        elif t and t[0] in ('L', 'LF', 'D', 'DF', 'W') and sec: ev[sec].append(t)
    chk = {}
    chk['T0 line low through reset: no spurious byte or error'] = not [e for e in ev.get('T0', []) if e[0] in ('D', 'DF')]
    t1 = ev.get('T1', [])
    chk['T1 loopback 256 values, no frame error'] = [int(e[2], 16) for e in t1 if e[0] == 'L'] == list(range(256)) and not any(e[0] == 'LF' for e in t1)
    w = [(int(e[1]), int(e[2])) for e in t1 if e[0] == 'W']
    first = w[:20]                                   # byte 0x00: start(0) + 8 x 0 + stop(1): one fall, one rise 9 bits later
    rel, start = [], None                            # transitions relative to each frame's start edge (within 10 bits)
    for t, v in w:
        if start is None or t - start >= 10 * BIT:
            start = t if v == 0 else None; continue
        rel.append(t - start)
    chk['T2 TX bit time 217 cycles (every in-frame transition on the 217-cycle grid from its start edge)'] = len(rel) > 500 and all(x % BIT == 0 for x in rel)
    chk['T2 TX byte 0x00 is start + 8 zeros + stop (9 bit-times low)'] = len(first) >= 2 and first[0][1] == 0 and first[1][0] - first[0][0] == 9 * BIT
    t3 = ev.get('T3', [])
    chk['T3 async driver, nominal and +-2 % baud, 192 bytes'] = [int(e[2], 16) for e in t3 if e[0] == 'D'] == cases and not any(e[0] == 'DF' for e in t3)
    t4 = ev.get('T4', [])
    chk['T4 bad stop: frame_err, no byte, then recovery'] = [e[0] for e in t4 if e[0] in ('D', 'DF')][:1] == ['DF'] and [e[2] for e in t4 if e[0] == 'D'] == ['3c']
    t5 = ev.get('T5', [])
    chk['T5 idle glitch < half bit: no spurious byte or error; next byte ok'] = [(e[0], e[2] if len(e) > 2 else '') for e in t5 if e[0] in ('D', 'DF')] == [('D', '5a')]
    t6 = ev.get('T6', [])
    chk['T6 break: no spurious byte; recovery byte ok'] = [e[2] for e in t6 if e[0] == 'D'] == ['c3']
    chk['run ended'] = 'END' in r.stdout
    return chk, {k: v[:12] for k, v in ev.items() if k in ('T4', 'T5', 'T6')}

def main(out, mutants, legacy):
    global RX
    if legacy: RX = LEGACY_RX
    out = Path(out).resolve(); out.mkdir(parents=True); res = dict(status='ERROR', gate='B1')
    try:
        import hashlib
        res['sources'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (RX, TX)}; res['rx'] = RX.name
        res['tool'] = subprocess.run(['iverilog', '-V'], capture_output=True, text=True).stdout.splitlines()[0]
        cases, stim = t3_stimulus(random.Random(20261111))
        chk, ev = run(out / 'dut', RX, TX, cases, stim); res['checks'] = chk; res['events'] = ev
        if mutants:
            muts = {'RX samples at bit start': (RX, 'HALF_BIT    = BIT_CYCLES / 2', 'HALF_BIT    = 1'),
                    'TX bit time 216 cycles': (TX, 'cycle_cnt < BIT_CYCLES - 1', 'cycle_cnt < BIT_CYCLES - 2')}
            if not legacy:
                muts['RX no start-bit re-check'] = (RX, 'if (rx_s2) state <= S_IDLE;', "if (1'b0) state <= S_IDLE;")
                muts['RX starts on low level, not falling edge'] = (RX, 'else if (armed && rx_prev) begin', 'else if (armed) begin')
                muts['RX armed at reset'] = (RX, "rx_prev <= 1'b1; armed <= 1'b0;", "rx_prev <= 1'b1; armed <= 1'b1;")
            for name, (src, a, b) in muts.items():
                md = out / ('mut_' + name.replace(' ', '_')); md.mkdir()
                t = src.read_text(); assert t.count(a) == 1, name; (md / src.name).write_text(t.replace(a, b))
                rx = md / RX.name if src == RX else RX; tx = md / TX.name if src == TX else TX
                mc, _ = run(md / 'run', rx, tx, cases, stim)
                res['checks'][f'mutant detected: {name}'] = not all(v for k, v in mc.items() if k != 'run ended')
        res['status'] = 'PASS' if all(res['checks'].values()) else 'FAIL'
    except Exception:
        res['traceback'] = traceback.format_exc()
    finally:
        (out / 'results.json').write_text(json.dumps(res, indent=1) + '\n')
    print('B1', res['status'], json.dumps(res.get('checks'), indent=1))
    return 0 if res['status'] == 'PASS' else 1

if __name__ == '__main__':
    sys.exit(main(sys.argv[1], '--mutants' in sys.argv[2:], '--legacy-rx' in sys.argv[2:]))
