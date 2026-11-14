#!/usr/bin/env python3
"""SPU v0.3 RTL-0B gate B2: psurd_link (H0-UART-1B v2 parser / response builder) through the B1 UART primitives.
usage: b2_link.py OUT_DIR [--mutants] [--bit N]      (OUT_DIR must not exist; default N = 217 cycles/bit, 25 MHz)
The host side is a bit-banged serial driver and a psurd_uart_rx monitor; the backend is a bench mock (fixed
status / length / payload per command, synchronous payload read, completion delayed by 25 bit-times for LOAD_WORD). Expected commands,
response bytes and error counts come from this script, never from RTL output. Every case is followed by a
STATUS probe sent as soon as the previous response's last byte has arrived, so each error class is checked
for bounded recovery (plan correction D); error-response latency is checked against explicit cycle bounds.
--mutants: planted link defects must fail (run at 16 cycles/bit, where the full case list is also re-run).
Exit 0 only on PASS."""
import hashlib, json, random, subprocess, sys, traceback
from functools import reduce
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
LINK, RX = ROOT / 'hardware/rtl/core/psurd/psurd_link.v', ROOT / 'hardware/rtl/core/psurd/psurd_uart_rx.v'
TX = ROOT / 'hardware/rtl/peripherals/whisper/spu_uart_tx.v'
OK, REFUSED, BUSY, BAD, TMO = 0x00, 0x20, 0x22, 0x01, 0x04
PLEN = {1: 12, 2: 10, 3: 0, 4: 4, 5: 0, 6: 0}
MOCK = {1: (OK, 0), 2: (OK, 0), 3: (REFUSED, 1), 4: (BUSY, 0), 5: (OK, 9), 6: (OK, 213)}   # backend mock: status, length
mock_byte = lambda c, a: (a * 37 + 11 * c) & 0xFF
xor = lambda bs: reduce(lambda a, b: a ^ b, bs, 0)
def frame(c, pay=b'', ver=2, ln=None, bad=0):
    ln = len(pay) if ln is None else ln
    b = [0xA5, ver, c, ln & 0xFF, ln >> 8, *pay]
    return b + [xor(b) ^ bad]
def resp(c, st, pay=()):
    b = [0xA5, 2, c | 0x80, st, len(pay), 0, *pay]
    return b + [xor(b)]
def good(c): return resp(c, MOCK[c][0], [mock_byte(c, a) for a in range(MOCK[c][1])])
PROBE = frame(5)

TB = r'''`timescale 1ns/1ps
module b2_tb;
  localparam BIT = @BIT@; localparam real BT = BIT * 40.0;
  reg clk = 0, rst = 1, drv = 1; integer cyc = 0, nrx = 0, k, w0;
  wire [7:0] rxd, txd, hd, radr; wire rxv, rxe, txs, txl, txb, txdn, hv, hf, cv, xe; wire [2:0] cmd; wire [95:0] pay;
  reg rv = 0; reg [7:0] rs = 0, rlen = 0, rdat = 0; reg [2:0] pc = 0; integer dly = -1;
  psurd_uart_rx #(BIT, 1) urx (.clk(clk), .rst_n(!rst), .rx(drv), .data(rxd), .valid(rxv), .frame_err(rxe));
  spu_uart_tx #(BIT, 1) utx (.clk(clk), .rst_n(!rst), .data(txd), .send(txs), .tx(txl), .busy(txb), .done(txdn));
  psurd_link #(.TIMEOUT(BIT * 80)) dut (.clk(clk), .rst(rst), .rx_data(rxd), .rx_valid(rxv), .rx_err(rxe), .tx_data(txd),
    .tx_send(txs), .tx_done(txdn), .cmd_valid(cv), .cmd(cmd), .payload(pay), .rsp_valid(rv), .rsp_status(rs),
    .rsp_len(rlen), .rsp_addr(radr), .rsp_data(rdat), .xerr(xe));
  psurd_uart_rx #(BIT, 1) hrx (.clk(clk), .rst_n(!rst), .rx(txl), .data(hd), .valid(hv), .frame_err(hf));
  always #20 clk = ~clk;
  reg txq = 1;
  always @(posedge clk) begin cyc <= cyc + 1; txq <= txl;
    if (txq && !txl) $display("W %0d", cyc);
    if (cv) $display("C %0d %0d %024x", cyc, cmd, pay);
    if (xe) $display("X %0d", cyc);
    if (hv) begin $display("R %0d %02x", cyc, hd); nrx <= nrx + 1; end
    if (hf) $display("RF %0d", cyc);
    rdat <= (radr * 37 + 11 * pc);                                   // synchronous payload read
    rv <= 0;
    if (cv) begin pc <= cmd; dly <= cmd == 2 ? BIT * 25 : cmd == 6 ? 3 : 0; end
    else if (dly == 0) begin rv <= 1; dly <= -1;
      case (pc) 3: begin rs <= 8'h20; rlen <= 1; end 4: begin rs <= 8'h22; rlen <= 0; end
        5: begin rs <= 8'h00; rlen <= 9; end 6: begin rs <= 8'h00; rlen <= 213; end
        default: begin rs <= 8'h00; rlen <= 0; end endcase
    end else if (dly > 0) dly <= dly - 1;
  end
  task sb(input [7:0] v, input stopv); begin
    drv = 0; #(BT); for (k = 0; k < 8; k = k + 1) begin drv = v[k]; #(BT); end drv = stopv; #(BT); drv = 1; end endtask
  task wresp(input integer nb, input integer maxc); begin                // wait for nb more response bytes
    w0 = cyc; while (nrx < nb && cyc - w0 < maxc) @(posedge clk); #7; end endtask
  task mark(input integer id); begin $display("M %0d %0d", id, cyc); end endtask
  initial begin
    #107 rst = 0; #(BT * 3);
@STIM@
    #(BT * 4); $display("END"); $finish;
  end
endmodule
'''

def cases(bit, rnd):
    """Each case: name, steps, expected commands [(cmd, payload bytes)], expected response bytes, expected xerr
    count, and latency bound in cycles from the mark (after the last stimulus byte) to the response start bit."""
    T = bit * 80; C = []
    rb = lambda n: bytes(rnd.randrange(256) for _ in range(n))
    snd = lambda bs: [('b', v, 1) for v in bs]
    FAST, SLOW = 2 * bit + 8, T + 2 * bit + 8              # error is known at the last byte / only after the timeout
    def add(name, steps, cmds, rsp, x, bound=None, lo=0): C.append((name, steps, cmds, rsp, x, bound, lo))
    for c in PLEN:                                           # 1 valid frames
        for _ in range(3):
            p = rb(PLEN[c]); add(f'valid cmd {c}', snd(frame(c, p)), [(c, p)], good(c), 0)
    for c in PLEN:                                           # 2 checksum
        for bad in (0x01, 0x80, 0xFF):
            add(f'bad checksum cmd {c} ^{bad:02x}', snd(frame(c, rb(PLEN[c]), bad=bad)), [], resp(c, BAD), 1, FAST)
    emb = bytes(PROBE) + bytes(6)                            # a complete valid STATUS frame inside a payload
    for v in (0, 1, 3, 0xA5):                                # 3 version
        add(f'bad version {v:02x} with embedded valid frame', snd(frame(1, emb, ver=v)), [], resp(1, BAD), 1, FAST)
    for c in (0, 7, 8, 0x85, 0xFF):                          # 4 unknown command
        add(f'unknown cmd {c:02x}', snd(frame(c)), [], resp(c, BAD), 1, FAST)
    for c in PLEN:                                           # 5 length
        for ln in {PLEN[c] + 1, max(PLEN[c] - 1, 0), 0, 12} - {PLEN[c]}:
            add(f'length {ln} for cmd {c}', snd(frame(c, rb(ln))), [], resp(c, BAD), 1, FAST)
    add('length 0x0100 for STATUS, wrong high byte only, nothing follows', snd([0xA5, 2, 5, 0, 1]), [], resp(5, BAD), 1, SLOW, T - 8)
    add('length 65535: drain stops after 12 + 1 bytes', snd([0xA5, 2, 5, 0xFF, 0xFF] + list(emb) + [0]), [], resp(5, BAD), 1, FAST)
    add('length 300 for LOAD_BEGIN: drain stops after 12 + 1 bytes', snd([0xA5, 2, 1, 44, 1] + list(emb) + [0]), [], resp(1, BAD), 1, FAST)
    add('length 12 for STATUS, only the checksum sent', snd(frame(5, ln=12)), [], resp(5, BAD), 1, SLOW, T - 8)
    full = frame(1, rb(12))                                  # 6 truncation at every position
    for cut in range(1, len(full)):
        add(f'truncated after {cut} bytes', snd(full[:cut]), [], resp(1 if cut > 2 else 0, TMO), 1, SLOW, T - 8)
    p = rb(12); f = frame(1, p)                              # 7 inter-byte timeout edges
    under, over = T - 12 * bit, T - 8 * bit                  # gap after a byte; valid-to-valid = gap + 10 bits
    add('every gap just under the timeout (frame far longer than one timeout)',
        [s for v in f[:-1] for s in (('b', v, 1), ('g', under))] + [('b', f[-1], 1)], [(1, p)], good(1), 0)
    for pos in (1, 5, 9, 17):
        add(f'gap over the timeout after byte {pos}', snd(f[:pos]) + [('m',), ('g', over)] + snd(f[pos:]),
            [], resp(1 if pos > 2 else 0, TMO), 1, SLOW, T - 8)
    for pos in (1, 2, 4, 5, 10, 17):                         # 8 UART framing error inside a frame
        steps = [('b', v, 0 if i == pos else 1) for i, v in enumerate(frame(1, emb))]
        add(f'UART framing error at byte {pos}, embedded valid frame after it', steps, [], resp(1 if pos > 2 else 0, BAD), 1, SLOW, T - 8)
    add('noise outside a frame: bytes and a framing error', snd([0, 0x5A, 2, 5, 0xFF]) + [('b', 0x33, 0), ('g', 3 * bit)] + snd([1, 2]), [], [], 0)
    add('START sent during a RESULT response is ignored', snd(frame(6)) + [('g', 40 * bit)] + snd(frame(4, rb(4))), [(6, b'')], good(6), 0)
    add('LOAD_END sent while LOAD_WORD is pending in the backend', snd(frame(2, p[:10]) + frame(3)), [(2, p[:10])], good(2), 0)
    add('reset inside a payload', snd(f[:9]) + [('r',)], [], [], 0)
    return C

def build(C, bit):
    L, n = [], 0
    for i, (name, steps, cmds, rsp, x, bound, lo) in enumerate(C):
        L.append(f'    mark({2 * i});'); marked = False
        for s in steps:
            if s[0] == 'b': L.append(f"    sb(8'h{s[1]:02x}, {s[2]});")
            elif s[0] == 'g': L.append(f'    #({s[1]} * 40.0);')
            elif s[0] == 'm': L.append(f'    mark({2 * i + 1});'); marked = True
            elif s[0] == 'r': L.append('    rst = 1; #(BT * 2); rst = 0; #(BT * 2);')
        if not marked: L.append(f'    mark({2 * i + 1});')
        n += len(rsp); L.append(f'    wresp({n}, {bit * 80 * 3 + len(rsp) * bit * 12 + 400});')
        if not rsp: L.append(f'    #(BT * 100);')                    # no response expected: longer than a timeout
        L.append(''.join(f"    sb(8'h{v:02x}, 1);" for v in PROBE))
        n += len(good(5)); L.append(f'    wresp({n}, {bit * 400});')
    return '\n'.join(L)

def run(out, link, bit, C, stim):
    out.mkdir(parents=True)
    (out / 'tb.v').write_text(TB.replace('@BIT@', str(bit)).replace('@STIM@', stim))
    c = subprocess.run(['iverilog', '-g2012', '-o', str(out / 'sim'), str(out / 'tb.v'), str(link), str(RX), str(TX)], capture_output=True, text=True)
    if c.returncode: raise RuntimeError('compile: ' + c.stderr[-800:])
    r = subprocess.run(['vvp', '-n', str(out / 'sim')], capture_output=True, text=True, timeout=3000)
    (out / 'sim.log').write_text(r.stdout); (out / 'sim').unlink()
    ev, cur, mk = {}, None, {}
    for t in (x.split() for x in r.stdout.split('\n')):
        if t[:1] == ['M']:
            mk[int(t[1])] = int(t[2])
            if int(t[1]) % 2 == 0: cur = int(t[1]) // 2; ev[cur] = []
        elif t and cur is not None: ev[cur].append(t)
    fails, probe = [], good(5)
    for i, (name, steps, cmds, rsp, x, bound, lo) in enumerate(C):
        e = ev.get(i, [])
        gc = [(int(t[2]), bytes.fromhex(t[3])[::-1]) for t in e if t[0] == 'C']
        want = [(c, p + bytes(12 - len(p))) for c, p in cmds] + [(5, None)]
        ok_c = len(gc) == len(want) and all(g[0] == w[0] and (w[1] is None or g[1][:len(cmds[j][1])] == cmds[j][1]) for j, (g, w) in enumerate(zip(gc, want)))
        ok_r = [int(t[2], 16) for t in e if t[0] == 'R'] == rsp + probe and not any(t[0] == 'RF' for t in e)
        ok_x = sum(t[0] == 'X' for t in e) == x
        ok_t = True
        if bound is not None:
            w = [int(t[1]) for t in e if t[0] == 'W' and int(t[1]) >= mk.get(2 * i + 1, 1 << 60)]
            ok_t = bool(w) and lo <= w[0] - mk[2 * i + 1] <= bound
        if not (ok_c and ok_r and ok_x and ok_t): fails.append(f'{name}: cmd={ok_c} resp={ok_r} xerr={ok_x} latency={ok_t}')
    if 'END' not in r.stdout: fails.append('run did not end')
    return fails

MUTANTS = {
    'checksum not checked': ('if (x == rx_data) begin', "if (1'b1) begin"),
    'version not checked': ("4'd1: ver_ok <= rx_data == 8'h02;", "4'd1: ver_ok <= 1'b1;"),
    'length high byte ignored': ("len == {12'd0, exp})", "len[7:0] == {4'd0, exp})"),
    'length not checked': ("exp != 4'd15 && len == {12'd0, exp})", "exp != 4'd15)"),
    'unknown command accepted': ("default: exp = 4'd15;", "default: exp = 4'd0;"),
    'no drain after a header error': ("n <= len > 16'd12 ? 4'd12 : len[3:0]; end", "n <= 4'd0; end"),
    'drain not clamped to 12': ("n <= len > 16'd12 ? 4'd12 : len[3:0]; end", "n <= len[3:0]; end"),
    'timeout disabled': ('wire expired = tcnt == TIMEOUT - 1;', "wire expired = 1'b0;"),
    'timeout is per frame, not per byte': ("tcnt <= (rx_valid || rx_err) ? 16'd0 : tcnt + 16'd1;", "tcnt <= (state == S_IDLE) ? 16'd0 : tcnt + 16'd1;"),
    'timeout twice as long': ('wire expired = tcnt == TIMEOUT - 1;', 'wire expired = tcnt == 2 * TIMEOUT - 1;'),
    'UART framing error ignored in payload': ('S_PAY: if (rx_err) state <= S_QUIET;', "S_PAY: if (1'b0) state <= S_QUIET;"),
    'no quiet wait after a framing error': ('S_QUIET: if (expired && !rx_valid && !rx_err) fail(ST_BAD_FRAME);', 'S_QUIET: fail(ST_BAD_FRAME);'),
    'xerr never raised': ("begin xerr <= 1'b1; respond(s, 8'd0); end", "begin respond(s, 8'd0); end"),
    'command issued before the checksum': ("if (n == exp - 4'd1) state <= S_CSUM;", "if (n == exp - 4'd1) begin state <= S_CSUM; cmd_valid <= 1'b1; end"),
    'payload bytes reversed': ('payload[8 * n +: 8] <= rx_data;', 'payload[8 * (4\'d11 - n) +: 8] <= rx_data;'),
    'response checksum omits the status': ('S_TLOAD: begin xs <= xs ^ tx_data;', "S_TLOAD: begin xs <= ti == 8'd3 ? xs : xs ^ tx_data;"),
    'response one payload byte short': ("wire [8:0] last = {1'b0, rl} + 9'd6;", "wire [8:0] last = {1'b0, rl} + 9'd5;"),
    'payload read not given a cycle to settle': ('S_TPREP: state <= S_TLOAD;', 'S_TPREP: state <= S_TLOAD;\n            // mutant\n'),
    'timeout answered as BAD_FRAME': ("S_CSUM: if (rx_err) state <= S_QUIET;\n                    else if (rx_valid) begin\n                        if (x == rx_data) begin cmd_valid <= 1'b1; state <= S_EXEC; end\n                        else fail(ST_BAD_FRAME);\n                    end else if (expired) fail(ST_TIMEOUT);",
                                      "S_CSUM: if (rx_err) state <= S_QUIET;\n                    else if (rx_valid) begin\n                        if (x == rx_data) begin cmd_valid <= 1'b1; state <= S_EXEC; end\n                        else fail(ST_BAD_FRAME);\n                    end else if (expired) fail(ST_BAD_FRAME);"),
    'bytes accepted while a request is pending': ('S_EXEC: if (rsp_valid) respond(rsp_status, rsp_len);', "S_EXEC: if (rsp_valid) respond(rsp_status, rsp_len); else if (rx_valid && rx_data == 8'hA5) state <= S_HDR;"),
}
del MUTANTS['payload read not given a cycle to settle']       # not expressible as a one-line substitution; covered by B4 record bytes

def main(out, mutants, bit):
    out = Path(out).resolve(); out.mkdir(parents=True); res = dict(status='ERROR', gate='B2', bit_cycles=bit, timeout_cycles=bit * 80)
    try:
        res['sources'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (LINK, RX, TX)}
        res['tool'] = subprocess.run(['iverilog', '-V'], capture_output=True, text=True).stdout.splitlines()[0]
        chk = {}
        for b in dict.fromkeys((bit, 16) if mutants else (bit,)):
            C = cases(b, random.Random(20261112)); stim = build(C, b)
            f = run(out / f'dut_bit{b}', LINK, b, C, stim)
            chk[f'{len(C)} cases at {b} cycles/bit'] = not f; res[f'failures_bit{b}'] = f
        if mutants:
            C = cases(16, random.Random(20261112)); stim = build(C, 16); src = LINK.read_text(); res['mutants'] = {}
            for name, (a, b) in MUTANTS.items():
                md = out / ('mut_' + ''.join(ch if ch.isalnum() else '_' for ch in name)); md.mkdir()
                assert src.count(a) == 1, name; (md / LINK.name).write_text(src.replace(a, b))
                f = run(md / 'run', md / LINK.name, 16, C, stim)
                chk[f'mutant detected: {name}'] = bool(f); res['mutants'][name] = f[:3]
        res['checks'] = chk; res['status'] = 'PASS' if all(chk.values()) else 'FAIL'
    except Exception:
        res['traceback'] = traceback.format_exc()
    finally:
        (out / 'results.json').write_text(json.dumps(res, indent=1) + '\n')
    print('B2', res['status'], json.dumps(res.get('checks', res.get('traceback')), indent=1))
    for k, v in res.items():
        if k.startswith('failures') and v: print(k, *v[:20], sep='\n  ')
    return 0 if res['status'] == 'PASS' else 1

if __name__ == '__main__':
    a = sys.argv[2:]
    sys.exit(main(sys.argv[1], '--mutants' in a, int(a[a.index('--bit') + 1]) if '--bit' in a else 217))
