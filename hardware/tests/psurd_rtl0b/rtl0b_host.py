"""Shared bench host for SPU v0.3 RTL-0B gates B3 and B4: drives psurd_sys_top over its simulated UART.
Not a test by itself. Provides H0-UART-1B v2 framing, a stimulus interpreter testbench (bit-banged serial
driver, psurd_uart_rx monitor, protocol-aware wait for each response, STATUS polling after START), and Model:
a reference model of the plan's state rules (RTL-0B plan §2, §3; contract §9-§11) written from the documents,
not from the RTL. Run results in the model come from psurd_oracle. Bench-only observation: at each cmd_valid
the testbench logs the run state, which classifies samples taken while a run is in flight (BUSY rules)."""
import subprocess, sys, zlib
from functools import reduce
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'software/tests'))
import psurd_oracle as O
SHARED = ['hardware/rtl/core/spu13/spu13_surd_load.v', 'hardware/rtl/core/spu13/spu13_surd_arith.v',
          'hardware/rtl/math/surd_cpu_products.v', 'hardware/rtl/math/surd_normalize_unit.v', 'hardware/rtl/math/surd_binary_gcd3.v',
          'hardware/rtl/math/surd_exact_quotient.v', 'hardware/rtl/peripherals/whisper/spu_uart_tx.v']
PSURD = ['psurd_sys_top.v', 'psurd_link.v', 'psurd_loader.v', 'psurd_runctl.v', 'psurd_record.v', 'psurd_uart_rx.v', 'psurd_core.v',
         'psurd_decode.v', 'psurd_exec.v', 'psurd_imem.v', 'psurd_sign.v', 'psurd_bank_lutram.v']
OK, REFUSED, BUSY, BAD, TMO = 0x00, 0x20, 0x22, 0x01, 0x04
POLL = (1 << 28) - 1
xor = lambda bs: reduce(lambda a, b: a ^ b, bs, 0)
def frame(c, pay=b'', bad=0):
    b = [0xA5, 2, c, len(pay) & 0xFF, len(pay) >> 8, *pay]
    return bytes(b + [xor(b) ^ bad])
def resp(c, st, pay=b''):
    b = [0xA5, 2, c | 0x80, st, len(pay), 0, *pay]
    return bytes(b + [xor(b)])
def load_frames(raw):
    """Host view of an SPUI file: header, then every complete 8-byte word present, then LOAD_END."""
    n = (len(raw) - 12) // 8
    return [frame(1, raw[:12])] + [frame(2, i.to_bytes(2, 'little') + raw[12 + 8 * i:20 + 8 * i]) for i in range(n)] + [frame(3)]

class Model:
    def __init__(s): s.iv = s.lo = False; s.rec = None; s.run_id = 0; s.image = []; s.buf = []; s.L = 0; s.crc = 0
    def xerr(s): s.lo = False
    def refuse(s, r): s.iv = s.lo = False; return REFUSED, bytes([r])
    def status(s, state=None):
        rv = s.rec is not None and state is None
        return bytes([s.iv | s.lo << 1 | rv << 2, (3 if rv else 0) if state is None else state, s.rec[3] if rv else 0xFF]) + s.run_id.to_bytes(4, 'little')
    def cmd(s, c, p):
        if c == 1:
            L = int.from_bytes(p[6:8], 'little')
            if p[:4] != b'SPUI': return s.refuse(1)
            if p[4:6] != b'\x01\x03': return s.refuse(2)
            if not 1 <= L <= 256: return s.refuse(3)
            s.iv, s.lo, s.L, s.crc, s.buf = False, True, L, int.from_bytes(p[8:12], 'little'), []
            return OK, b''
        if c == 2:
            if not s.lo: return s.refuse(7)
            if int.from_bytes(p[:2], 'little') != len(s.buf) or len(s.buf) == s.L: return s.refuse(5)
            s.buf.append(p[2:10]); return OK, b''
        if c == 3:
            if not s.lo: return s.refuse(7)
            if len(s.buf) != s.L: return s.refuse(6)
            if zlib.crc32(b''.join(s.buf)) != s.crc: return s.refuse(4)
            s.iv, s.lo, s.image = True, False, [int.from_bytes(w, 'big') for w in s.buf]
            return OK, b''
        if c == 4:
            B = int.from_bytes(p, 'little')
            if not s.iv: return REFUSED, b'\x08'
            if B == 0: return REFUSED, b'\x09'
            s.rec = O.record(O.run(s.image, B)); s.run_id += 1; return OK, b''
        if c == 5: return OK, s.status()
        return (OK, s.rec) if s.rec is not None else (REFUSED, b'\x0a')

TB = r'''`timescale 1ns/1ps
module sys_tb;
  localparam BIT = @BIT@; localparam real BT = BIT * 40.0;
  reg clk = 0, rst = 1, drv = 1; integer cyc = 0, nrx = 0, n0 = 0, ip = 0, k, w0, go, np;
  wire txl, hv, hf, busy, iv, rv; wire [7:0] hd;
  reg hrst_n = 0; initial #50 hrst_n = 1;                               // the host monitor is not reset with the DUT
  reg [31:0] stim [0:@N@]; reg [31:0] op; reg [7:0] last [0:255];
  psurd_sys_top #(.CLK_HZ(BIT), .BAUD(1), .TIMEOUT(BIT * 80)) dut (.clk(clk), .rst(rst), .uart_rx(drv), .uart_tx(txl),
    .busy(busy), .image_valid(iv), .record_valid(rv));
  psurd_uart_rx #(BIT, 1) hrx (.clk(clk), .rst_n(hrst_n), .rx(txl), .data(hd), .valid(hv), .frame_err(hf));
  always #20 clk = ~clk;
  always @(posedge clk) begin cyc <= cyc + 1;
    if (hv) begin $display("R %02x", hd); if (nrx - n0 < 256) last[nrx - n0] <= hd; nrx <= nrx + 1; end
    if (hf) $display("RF");
    if (dut.cmd_valid) $display("S %0d %0d %0d %0d %0d", dut.cmd, dut.runctl.state, iv, dut.load_open, rv);
  end
  task sb(input [7:0] v, input stopv); begin
    drv = 0; #(BT); for (k = 0; k < 8; k = k + 1) begin drv = v[k]; #(BT); end drv = stopv; #(BT); drv = 1; end endtask
  task await(input integer maxc); begin w0 = cyc;                        // complete response (length-aware), or give up
    while (!(nrx - n0 >= 7 && nrx - n0 >= 7 + last[4]) && cyc - w0 < maxc) begin   // after maxc cycles with no byte
      @(posedge clk); if (hv) w0 = cyc; end
    #7; end endtask
  initial begin
    $readmemh("stim.hex", stim); #107 rst = 0; #(BT * 3);
    while (stim[ip][31:28] != 4'd5) begin
      op = stim[ip]; ip = ip + 1;
      case (op[31:28])
        4'd0: sb(op[7:0], 1'b1);
        4'd7: sb(op[7:0], 1'b0);                                         // byte with a bad stop bit
        4'd2: begin $display("F %0d", op[27:0]); n0 = nrx; end
        4'd1: await(op[27:0]);
        4'd3: #(op[27:0] * 40.0);
        4'd4: begin go = 1; np = 0;                                      // poll STATUS until no run is in flight
          while (go) begin
            $display("F %0d", 28'hFFFFFFF); n0 = nrx;
            sb(8'hA5, 1); sb(8'h02, 1); sb(8'h05, 1); sb(8'h00, 1); sb(8'h00, 1); sb(8'hA2, 1); await(BIT * 400);
            np = np + 1; go = (last[7] == 1 || last[7] == 2) && nrx - n0 >= 14;
            if (np >= 3000) begin $display("DEAD"); $finish; end        // a run that never ends: stop without END (a failure)
          end end
        4'd6: begin rst = 1; #(BT * 2); rst = 0; #(BT * 3); end
        default: ;
      endcase
    end
    #(BT * 4); $display("END"); $finish;
  end
endmodule
'''

class Stim:
    """Builds the stimulus program. Each frame gets an id; run() returns {id: (response bytes, [state logs])}."""
    def __init__(s, bit): s.bit, s.ops, s.n = bit, [], 0
    def send(s, data, bad_stop_at=None, wait=None):
        s.ops.append(2 << 28 | s.n)
        s.ops += [(7 if i == bad_stop_at else 0) << 28 | v for i, v in enumerate(data)]
        s.ops.append(1 << 28 | (s.bit * 400 if wait is None else wait)); s.n += 1; return s.n - 1
    def gap(s, cycles): s.ops.append(3 << 28 | cycles)
    def poll(s): s.ops.append(4 << 28)
    def reset(s): s.ops.append(6 << 28)

def run(out, stim, psurd_dir=None, timeout=3000, tb=None, extra=()):
    """tb / extra: another testbench text (module sys_tb) and extra sources, used by the RTL-0C board bench."""
    out.mkdir(parents=True)
    src = [(Path(psurd_dir) if psurd_dir else ROOT / 'hardware/rtl/core/psurd') / n for n in PSURD] + [ROOT / x for x in SHARED] + list(extra)
    (out / 'stim.hex').write_text(''.join('%08x\n' % o for o in stim.ops + [5 << 28]))
    (out / 'tb.v').write_text((tb or TB).replace('@BIT@', str(stim.bit)).replace('@N@', str(len(stim.ops))))
    c = subprocess.run(['iverilog', '-g2012', '-s', 'sys_tb', '-o', str(out / 'sim'), str(out / 'tb.v')] + [str(x) for x in src], capture_output=True, text=True)
    if c.returncode: raise RuntimeError('compile: ' + c.stderr[-1200:])
    r = subprocess.run(['vvp', '-n', str(out / 'sim')], cwd=out, capture_output=True, text=True, timeout=timeout)
    (out / 'sim.log').write_text(r.stdout); (out / 'sim').unlink()
    got, cur = {'log': [x for x in r.stdout.split('\n') if x.startswith('Q ')]}, None
    for t in (x.split() for x in r.stdout.split('\n')):
        if t[:1] == ['F']: cur = int(t[1]); got[cur] = (bytearray(), [])
        elif cur is None or not t: continue
        elif t[0] == 'R': got[cur][0].extend(bytes([int(t[1], 16)]) if all(ch in '0123456789abcdef' for ch in t[1]) else b'<X>')   # a byte with X/Z bits (any case) is a mismatch
        elif t[0] == 'S': got[cur][1].append(tuple(int(v) if v.isdigit() else -1 for v in t[1:]))   # X/Z state: -1, a mismatch
        elif t[0] == 'RF': got[cur][0].extend(b'<RF>')
    return got, 'END' in r.stdout

class Session:
    """Stimulus plus the expectation list. Expected responses are computed by replaying Model after the run
    (check), because a frame sent while a run is in flight ('during') is judged against the run state the
    bench logged at its cmd_valid: RUNNING/FINALIZING -> BUSY and no state change; otherwise the normal rule."""
    def __init__(s, bit): s.stim, s.ops, s.case = Stim(bit), [], ''
    def do(s, c, p=b'', want=None, during=False):                    # want: (status, payload) the model must give
        i = s.stim.send(frame(c, p)); s.ops.append(('cmd', i, s.case, c, bytes(p), want, during)); return i
    def raw(s, data, expect, bad_stop_at=None):                        # transport-level error: explicit expected bytes
        i = s.stim.send(data, bad_stop_at); s.ops.append(('raw', i, s.case, bytes(expect))); return i
    def load(s, raw_image, want_ok=None):
        fs = load_frames(raw_image)
        return [s.do(f[2], f[5:-1], want=(OK, b'') if want_ok else None) for f in fs]
    def start(s, B, want=None, poll=True):
        i = s.do(4, B.to_bytes(4, 'little'), want)
        if poll: s.stim.poll()
        return i
    def reset(s): s.stim.reset(); s.ops.append(('reset',))
    def check(s, got):
        m, fails, seen, payloads = Model(), {}, {}, {}
        def bad(case, msg): fails.setdefault(case, []).append(msg)
        for op in s.ops:
            if op[0] == 'reset': m = Model(); continue
            i, case = op[1], op[2]; g, logs = got.get(i, (b'', [])); g = bytes(g)
            if op[0] == 'raw':
                m.xerr()
                if g != op[3]: bad(case, f'frame {i}: transport response {g.hex()} != {op[3].hex()}')
                if logs: bad(case, f'frame {i}: a command was issued for a malformed frame')
                continue
            _, _, _, c, p, want, during = op
            state = logs[0][1] if logs else None
            if during: seen.setdefault(c, set()).add(state)
            if during and state in (1, 2): st, pl = (OK, m.status(state)) if c == 5 else (BUSY, b'')
            else: st, pl = m.cmd(c, p)
            if want is not None and not during and not (st == want[0] and pl.startswith(want[1])):
                bad(case, f'frame {i}: reference model gave {st:02x} {pl.hex()[:20]}, the case requires {want[0]:02x} {want[1].hex()}')
            if g != resp(c, st, pl): bad(case, f'frame {i} cmd {c}: got {g.hex()[:60]} want {resp(c, st, pl).hex()[:60]}')
            if len(logs) != 1 or logs[0][0] != c: bad(case, f'frame {i}: command log {logs}')
            payloads[i] = g[6:-1]
        return fails, seen, payloads
