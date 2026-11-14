#!/usr/bin/env python3
"""SPU v0.3 RTL-0A gate G1 (hard stop): the UNCHANGED shared spu13_surd_arith vs the frozen v0.3 contract.

usage: g1_arith.py OUT_DIR [--vectors N] [--seed S]     (OUT_DIR must not exist)
Ops 4 SADD, 5 SSUB, 6 SNORM (3 SMUL as control). Expected STORED tuples and status come from the
independent oracle software/tests/psurd_oracle.py, never from RTL output. The testbench is generated into
OUT_DIR (no .v enters the tree). Shared sources are checked against the recorded Gen-1 baseline
hardware/tests/spu13/gen1_integration/fixtures/source_hashes.sha256 before anything runs. Handshake checks:
one done per start, result/status stable after done, operands latched at start, start while busy ignored,
reset mid-operation gives no stale done. Watchdog per operation; a timeout is its own outcome.
Exit 0 only on PASS; results.json is always written."""
import hashlib, json, random, subprocess, sys, traceback
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'software/tests'))
import psurd_oracle as O
SRC = ['hardware/rtl/core/spu13/spu13_surd_arith.v', 'hardware/rtl/math/surd_cpu_products.v',
       'hardware/rtl/math/surd_normalize_unit.v', 'hardware/rtl/math/surd_binary_gcd3.v',
       'hardware/rtl/math/surd_exact_quotient.v']
BASE = ROOT / 'hardware/tests/spu13/gen1_integration/fixtures/source_hashes.sha256'
WD = 20000
M64 = 1 << 64
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pack(t): return '%048x' % ((t[2] % M64) << 128 | (t[1] % M64) << 64 | (t[0] % M64))
def unpack(h):
    v = int(h, 16); s = lambda x: x - M64 if x >> 63 else x
    return (s(v & (M64 - 1)), s(v >> 64 & (M64 - 1)), v >> 128)
def expect(op, x, y):
    r = {3: lambda: O.mul(x, y), 4: lambda: O.addsub(x, y, 1), 5: lambda: O.addsub(x, y, -1), 6: lambda: O.norm(x)}[op]()
    return (2, None) if r is None else (0, r)
def raw_class(op, x, y):
    if op == 6: return 'norm'
    if op == 3: A, B, D = x[0] * y[0] + 3 * x[1] * y[1], x[0] * y[1] + x[1] * y[0], x[2] * y[2]
    else:
        import math; g = math.gcd(x[2], y[2]); u, v = y[2] // g, x[2] // g; s = 1 if op == 4 else -1
        A, B, D = x[0] * u + s * y[0] * v, x[1] * u + s * y[1] * v, x[2] * u
    fits = O.I64(A) and O.I64(B) and 0 < D < M64
    return 'raw_fit' if fits else ('normalized' if expect(op, x, y)[0] == 0 else 'overflow')

def vectors(n, seed):
    rnd = random.Random(seed)
    E = [0, 1, -1, 2, 3, (1 << 62), -(1 << 62), (1 << 63) - 1, -(1 << 63), (1 << 31) - 1]
    Ds = [1, 2, 3, 4, 6, 12, 1000, 1 << 32, 1 << 63, M64 - 1]
    def val(): return rnd.choice(E) if rnd.random() < .3 else rnd.randrange(-(1 << rnd.choice([8, 31, 62, 63])), 1 << rnd.choice([8, 31, 62, 63]))
    def den(): return rnd.choice(Ds) if rnd.random() < .5 else rnd.randrange(1, 1 << rnd.choice([4, 20, 40, 64]))
    def tup():
        if rnd.random() < .25:                         # scaled (non-canonical) representations
            k = rnd.choice([2, 3, 6, 1000]); a, b, d = rnd.randrange(-999, 1000), rnd.randrange(-999, 1000), rnd.randrange(1, 1000)
            return (a * k, b * k, d * k)
        return (val(), val(), den())
    out = [(op, (a, b, d), (c, e, f)) for op in (3, 4, 5, 6) for a in E[:9:2] for b in E[1:9:2] for d in (1, 1 << 63, M64 - 1)
           for (c, e, f) in [(E[7], E[8], 1), (1, 0, 1), (-3, 5, M64 - 1)]]
    def big():                                         # large common factor K: raw overflows, gcd reduction fits
        K = rnd.randrange(1 << 58, 1 << 60); m = lambda: rnd.randrange(-8, 9)
        return (m() * K, m() * K, rnd.randrange(1, 9) * K)
    small = lambda: (rnd.randrange(-16, 17), rnd.randrange(-16, 17), rnd.randrange(1, 17))
    for op in (4, 5, 6): out += [(op, tup(), tup()) for _ in range(n)]
    out += [(3, tup(), tup()) for _ in range(max(1, n // 4))]
    for op in (3, 4, 5): out += [(op, big(), small() if op == 3 else big()) for _ in range(max(1, n // 4))]
    return out

TB = r'''`timescale 1ns/1ps
module g1_tb;
  reg clk=0, rst=1, start=0; reg [2:0] op=0; reg [191:0] lhs=0, rhs=0;
  wire done, rr, ns; wire [3:0] status, phase; wire [191:0] result;
  spu13_surd_arith dut(.clk(clk),.rst(rst),.start(start),.op(op),.lhs(lhs),.rhs(rhs),.done(done),.status(status),
                       .result(result),.phase(phase),.rescue_request(rr),.normalization_start(ns));
  always #5 clk = ~clk;
  reg [7:0] OPS[0:NV-1]; reg [191:0] LS[0:NV-1]; reg [191:0] RS[0:NV-1];
  integer i, c, nd, k, bad; reg [3:0] st; reg [191:0] res;
  task fire(input [2:0] o, input [191:0] l, input [191:0] r);
    begin @(negedge clk); op=o; lhs=l; rhs=r; start=1; @(negedge clk); start=0; lhs=~l; rhs=~r; end
  endtask
  task waitdone(output integer cc, output integer n);
    begin cc=0; n=0;
      while (n==0 && cc<WDC) begin @(posedge clk); #1; cc=cc+1; if (done) begin n=1; st=status; res=result; end end
      bad=0; for (k=0;k<6;k=k+1) begin @(posedge clk); #1; if (done) n=n+1; if (status!==st || result!==res) bad=1; end
    end
  endtask
  initial begin
    $readmemh("ops.hex", OPS); $readmemh("lhs.hex", LS); $readmemh("rhs.hex", RS);
    repeat(3) @(posedge clk); rst=0;
    for (i=0;i<NV;i=i+1) begin fire(OPS[i][2:0], LS[i], RS[i]); waitdone(c, nd);
      if (nd==0) $display("T %0d", i); else $display("R %0d %0d %h %0d %0d %0d", i, st, res, c, nd, bad); end
    // H1: start while busy is ignored (vector 0 = long op, vector 1 = a different op)
    fire(OPS[HL][2:0], LS[HL], RS[HL]); repeat(2) @(negedge clk);
    if (phase!=0) begin op=OPS[HO][2:0]; lhs=LS[HO]; rhs=RS[HO]; start=1; @(negedge clk); start=0; end
    waitdone(c, nd); $display("H1 %0d %h %0d %0d", st, res, nd, phase);
    // H2: reset mid-operation -> no stale done; next op correct
    fire(OPS[HL][2:0], LS[HL], RS[HL]); repeat(2) @(negedge clk); $display("H2busy %0d", phase); rst=1; repeat(2) @(negedge clk); rst=0;
    nd=0; for (k=0;k<WDC;k=k+1) begin @(posedge clk); #1; if (done) nd=nd+1; end $display("H2stale %0d", nd);
    fire(OPS[HO][2:0], LS[HO], RS[HO]); waitdone(c, nd); $display("H2next %0d %h %0d", st, res, nd);
    $display("END"); $finish;
  end
endmodule
'''

def main(out, n, seed):
    out = Path(out).resolve(); out.mkdir(parents=True)
    res = dict(gate='G1', status='ERROR', seed=seed, vectors_per_op=n, harness_sha256=sha(__file__),
               oracle_sha256=sha(ROOT / 'software/tests/psurd_oracle.py'), watchdog_cycles=WD)
    try:
        base = dict(l.split()[::-1] for l in BASE.read_text().splitlines() if l.strip())
        res['sources'] = {s: sha(ROOT / s) for s in SRC}
        res['baseline_match'] = all(base.get(s) == h for s, h in res['sources'].items())
        if not res['baseline_match']: raise RuntimeError('shared source differs from recorded Gen-1 baseline; refusing to run')
        V = vectors(n, seed)
        (out / 'ops.hex').write_text(''.join('%02x\n' % op for op, _, _ in V))
        (out / 'lhs.hex').write_text(''.join(pack(x) + '\n' for _, x, _ in V))
        (out / 'rhs.hex').write_text(''.join(pack(y) + '\n' for _, _, y in V))
        res['vectors_sha256'] = hashlib.sha256((out / 'lhs.hex').read_bytes() + (out / 'rhs.hex').read_bytes() + (out / 'ops.hex').read_bytes()).hexdigest()
        HL = next(i for i, (op, x, y) in enumerate(V) if op == 4 and raw_class(op, x, y) == 'normalized')
        HO = next(i for i, (op, x, y) in enumerate(V) if op == 3 and expect(op, x, y)[0] == 0)
        (out / 'g1_tb.v').write_text(TB.replace('NV', str(len(V))).replace('WDC', str(WD)).replace('HL', str(HL)).replace('HO', str(HO)))
        tools = subprocess.run(['iverilog', '-V'], capture_output=True, text=True).stdout.splitlines()[:1]
        res['tool'] = tools[0] if tools else 'unknown'
        c = subprocess.run(['iverilog', '-g2012', '-o', str(out / 'sim'), str(out / 'g1_tb.v')] + [str(ROOT / s) for s in SRC],
                           capture_output=True, text=True, timeout=300)
        if c.returncode: raise RuntimeError('compile failed: ' + c.stderr[-1000:])
        try: r = subprocess.run(['vvp', '-n', str(out / 'sim')], cwd=out, capture_output=True, text=True, timeout=3000)
        except subprocess.TimeoutExpired: res['status'] = 'TIMEOUT'; raise
        (out / 'sim.log').write_text(r.stdout)
        L = r.stdout.split('\n'); rows = {int(x.split()[1]): x.split() for x in L if x.startswith('R ')}
        res['timeouts'] = [int(x.split()[1]) for x in L if x.startswith('T ')]
        mism, cls, cycles = [], {}, {}
        for i, (op, x, y) in enumerate(V):
            k = (op, raw_class(op, x, y)); cls[str(k)] = cls.get(str(k), 0) + 1
            if i not in rows: continue
            _, _, st, h, cc, nd, bad = rows[i]; est, et = expect(op, x, y)
            ok = int(st) == est and int(nd) == 1 and bad == '0' and (est != 0 or unpack(h) == et)
            cycles[op] = max(cycles.get(op, 0), int(cc))
            if not ok: mism.append(dict(i=i, op=op, lhs=x, rhs=y, rtl_status=int(st), rtl=unpack(h), exp_status=est, exp=et, dones=nd, unstable=bad))
        h1 = next(x.split() for x in L if x.startswith('H1 ')); h2s = next(x.split() for x in L if x.startswith('H2stale'))
        h2n = next(x.split() for x in L if x.startswith('H2next')); h2b = next(x.split() for x in L if x.startswith('H2busy'))
        eHL, eHO = expect(*V[HL]), expect(*V[HO])
        hs = {'H1 start while busy ignored': int(h1[1]) == eHL[0] and unpack(h1[2]) == eHL[1] and h1[3] == '1',
              'H2 operation was in flight at reset': h2b[1] != '0', 'H2 no stale done after reset': h2s[1] == '0',
              'H2 next operation correct': int(h2n[1]) == eHO[0] and unpack(h2n[2]) == eHO[1] and h2n[3] == '1'}
        canon = sum(1 for i, (op, x, y) in enumerate(V) if i in rows and expect(op, x, y)[0] == 0
                    and unpack(rows[i][3]) != O.norm(expect(op, x, y)[1]))   # RTL tuple differs from canonical form
        res.update(vectors=len(V), classes=cls, max_cycles=cycles, mismatches=mism[:20], mismatch_count=len(mism), handshake=hs,
                   ended='END' in L, control_canonical_expectation_would_mismatch=canon)
        ok = res['ended'] and not res['timeouts'] and not mism and len(rows) == len(V) and all(hs.values()) and canon > 0
        res['status'] = 'PASS' if ok else ('TIMEOUT' if res['timeouts'] else 'FAIL')
    except Exception:
        res['traceback'] = traceback.format_exc()
    finally:
        (out / 'results.json').write_text(json.dumps(res, indent=1, default=str) + '\n')
    print('G1', res['status'], res.get('vectors'), 'vectors;', res.get('mismatch_count'), 'mismatches;', len(res.get('timeouts', [])), 'timeouts')
    return 0 if res['status'] == 'PASS' else 1

if __name__ == '__main__':
    a = sys.argv[1:]; n = int(a[a.index('--vectors') + 1]) if '--vectors' in a else 2000
    s = int(a[a.index('--seed') + 1]) if '--seed' in a else 20261111
    sys.exit(main(a[0], n, s))
