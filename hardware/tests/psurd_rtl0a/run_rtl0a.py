#!/usr/bin/env python3
"""SPU v0.3 RTL-0A gates G2-G6: psurd RTL (simulation) vs the frozen contract. usage: run_rtl0a.py OUT_DIR [--mutants]
G2 sign unit vs oracle; G3 decoder (256 opcodes + per-field malformed words); G4 programs (Program A/B, negative
controls, OVERFLOW aliasing) as full 213-byte records vs the oracle AND the C++ simulator; G5 (--mutants) planted
RTL defects must fail; G6 shared Gen-1 sources match the recorded baseline. Records are assembled from RTL state by
this runner (simulation-only serializer; it does not qualify RTL-0B record/UART hardware). Exit 0 only on PASS."""
import hashlib, json, random, shutil, subprocess, sys, traceback, zlib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'software/tests'))
import psurd_oracle as O
from psurd_oracle import SLI, SLD, SMUL, SADD, SSUB, SNORM, SLIK, STST, BR, HALT, LOAD
from test_psurd_sim0 import prog_A, prog_B, X33
SHARED = ['hardware/rtl/core/spu13/spu13_surd_bank.v', 'hardware/rtl/core/spu13/spu13_surd_load.v',
          'hardware/rtl/core/spu13/spu13_surd_arith.v', 'hardware/rtl/math/surd_cpu_products.v',
          'hardware/rtl/math/surd_normalize_unit.v', 'hardware/rtl/math/surd_binary_gcd3.v', 'hardware/rtl/math/surd_exact_quotient.v']
BASE = ROOT / 'hardware/tests/spu13/gen1_integration/fixtures/source_hashes.sha256'
M64, WD = 1 << 64, 400000
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def sh(a, **k): return subprocess.run(a, capture_output=True, text=True, **k)
I = lambda k: (k, 0, 1); Z0 = (0, 0, 1)

def programs():
    P = []
    for k, pts in {'A': ((Z0, Z0), (I(2), (0, 1, 1)), (I(1), (0, 2, 1))), 'B': ((Z0, Z0), (I(1), (0, 1, 1)), (I(2), (0, 2, 1))),
                   'C': ((Z0, Z0), (I(1), (0, 2, 1)), (I(2), (0, 1, 1))), 'D': ((Z0, Z0), (I(1), (0, 1, 1)), (I(2), (1, 2000, 1000))),
                   'E': ((Z0, Z0), (I(2**40), Z0), (Z0, I(2**40))), 'F': ((Z0, (0, 0, 5)), ((2, 0, 2), (0, 2, 2)), ((6, 0, 3), (0, 4, 2)))}.items():
        P.append((f'A-{k}', prog_A(*pts), 10000))
    P += [(f'B K={K}', prog_B(K), 10000) for K in (-1, 0, 1, 2, 33, 34, 50)]
    m = 2**31 - 1
    neg = {'uninit read': [SADD(0, 1, 2), HALT], 'incomplete staging': [SLI(0, s, 1) for s in range(5)] + [SLD(0), HALT],
           'staging other target': [SLI(0, 0, 1), SLI(1, 0, 1), HALT], 'SLD d=0': LOAD(0, (1, 0, 0)) + [HALT],
           'BR NE before STST': [BR('NE', 0), HALT], 'BR RS no CV': [BR('RS', 1), HALT], 'BAD_TARGET taken': [BR('AL', 2), HALT],
           'BAD_TARGET not taken': [BR('RF', 9), HALT], 'PC_OVERRUN': [SLIK(0, 1)], 'PC_OVERRUN 256': [SLIK(0, 1)] * 256,
           'BUDGET loop': [BR('AL', 0)], 'BUDGET PC=L': [SLIK(0, 1)], 'HALT B-th': [SLIK(0, 1), HALT],
           'R clears RS sticky': [SLIK(0, m), SMUL(0, 0, 0), SMUL(0, 0, 0), SMUL(0, 0, 0), SLIK(1, 1), SADD(2, 1, 1), HALT],
           'OVERFLOW alias d=a=b': [SLIK(0, m), SMUL(0, 0, 0), SMUL(0, 0, 0), STST(0), HALT],
           'OVERFLOW alias d=a': [SLIK(0, m), SMUL(0, 0, 0), SLIK(1, m), SMUL(1, 1, 0), SMUL(1, 1, 0), HALT],
           'SNORM noncanonical': LOAD(3, (6, -4, 10)) + [SNORM(4, 3), SNORM(5, 5), HALT],
           'SLIK not SLI': [SLIK(0, 5), SLD(0), HALT], 'staging keeps value': [SLIK(0, 5), SLI(0, 0, 123), STST(0), HALT]}
    bud = {'BUDGET loop': 5, 'BUDGET PC=L': 1, 'HALT B-th': 2}
    P += [(f'neg {k}', w, bud.get(k, 10000)) for k, w in neg.items()]
    P += [(f'op {o:02x}', [o << 56, HALT], 10) for o in range(256)]
    forms = {'SLI': (SLI(1, 2, 0xA5A5A5A5), 0xFF), 'SLD': (SLD(1), (1 << 48) - 1), 'SMUL': (SMUL(1, 2, 3), 0xFF << 32 | 0xFFFFFF),
             'SADD': (SADD(1, 2, 3), 0xFF << 32 | 0xFFFFFF), 'SSUB': (SSUB(1, 2, 3), 0xFF << 32 | 0xFFFFFF), 'SNORM': (SNORM(1, 2), (1 << 40) - 1),
             'SLIK': (SLIK(1, -5), 0xFF << 40 | 0xFF), 'STST': (STST(2), 0xFF << 48 | (1 << 40) - 1), 'BR': (BR('AL', 0), 0xFF << 40 | 0xFFFFFF),
             'HALT': (HALT, (1 << 56) - 1)}
    idx = {'SLI': [(48, 8), (48, 255), (40, 6), (40, 255)], 'SLD': [(48, 8), (48, 255)], 'SMUL': [(48, 8), (40, 8), (24, 8), (24, 255)],
           'SNORM': [(48, 8), (40, 255)], 'SLIK': [(48, 8)], 'STST': [(40, 8), (40, 255)], 'BR': [(48, 10), (48, 255)]}
    for n, (w0, mask) in forms.items():
        ws = [w0 ^ (1 << b) for b in range(64) if mask >> b & 1] + [(w0 & ~(0xFF << s)) | v << s for s, v in idx.get(n, [])]
        P += [(f'field {n} {w:016x}', [w, HALT], 10) for w in ws]
    return P

TB_CORE = r'''`timescale 1ns/1ps
module rtl0a_tb;
  reg clk=0, rst=1, start=0; reg [31:0] budget=0; reg [8:0] img_len=1;
  wire done; wire [2:0] cause; wire [8:0] pc; wire [31:0] retired; wire Z,N,P,CV,R,RS; wire [1:0] status;
  psurd_core core(.clk(clk),.rst(rst),.start(start),.budget(budget),.img_len(img_len),.imem_we(1'b0),.imem_waddr(8'd0),
    .imem_wdata(64'd0),.dump_ra(3'd0),.dump_q(),.dump_valid(),.done(done),.cause(cause),
    .pc(pc),.retired(retired),.Z(Z),.N(N),.P(P),.CV(CV),.R(R),.RS(RS),.status(status));
  always #5 clk = ~clk;
  reg [63:0] PROG[0:NPROG*256-1]; reg [31:0] LEN[0:NPROG-1]; reg [31:0] BUD[0:NPROG-1];
  integer k, i, c;
  initial begin
    $readmemh("prog.hex", PROG); $readmemh("len.hex", LEN); $readmemh("bud.hex", BUD);
    repeat(3) @(posedge clk); rst = 0;
    for (k=0;k<NPROG;k=k+1) begin
      for (i=0;i<256;i=i+1) core.imem.mem[i] = PROG[k*256+i];
      img_len = LEN[k]; budget = BUD[k];
      @(negedge clk); start = 1; @(negedge clk); start = 0;
      c = 0; while (!done && c < WDC) begin @(posedge clk); #1; c = c + 1; end
      if (!done) begin $display("T %0d", k); rst = 1; repeat(3) @(negedge clk); rst = 0; end
      else begin
        $display("P %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %h", k, cause, pc, retired, Z, N, P, CV, R, RS, status, c, core.exu.bank.initialized);
        for (i=0;i<8;i=i+1) $display("G %0d %0d %h", k, i, core.exu.bank.tuples[i]);
      end
    end
    $display("END"); $finish;
  end
endmodule
'''
TB_SIGN = r'''module sign_tb; reg [191:0] V[0:NV-1]; reg [191:0] t; wire z,n,p; integer i;
  psurd_sign s(.t(t),.zero(z),.neg(n),.pos(p));
  initial begin $readmemh("sign.hex", V); for (i=0;i<NV;i=i+1) begin t=V[i]; #1; $display("S %0d %0d %0d %0d", i, z, n, p); end $finish; end
endmodule
'''
def pack(t): return '%048x' % ((t[2] % M64) << 128 | (t[1] % M64) << 64 | (t[0] % M64))
def rtl_record(f, regs, mask, budget):    # simulation-only serializer (contract §11), independent of O.record
    cause, pc, ret, z, n, p, cv, r, rs, st, _ = f
    b = bytes([0xA5, 3, 1, cause, pc & 255, pc >> 8, z | n << 1 | p << 2 | cv << 3 | r << 4 | rs << 5, st])
    b += ret.to_bytes(4, 'little') + budget.to_bytes(4, 'little') + bytes([mask])
    for i in range(8):                     # uninitialized storage is unspecified (may be X): never parsed (§2, §11)
        if not mask >> i & 1: b += bytes(24); continue
        v = int(regs[i], 16)
        b += b''.join((v >> (64 * j) & (M64 - 1)).to_bytes(8, 'little') for j in range(3))
    return b + zlib.crc32(b).to_bytes(4, 'little')

def run_core(out, src, P, tag):
    d = out / tag; d.mkdir(); NP = len(P)
    (d / 'prog.hex').write_text(''.join('%016x\n' % (w[i] if i < len(w) else 0) for _, w, _ in P for i in range(256)))
    (d / 'len.hex').write_text(''.join('%08x\n' % len(w) for _, w, _ in P)); (d / 'bud.hex').write_text(''.join('%08x\n' % b for _, _, b in P))
    (d / 'tb.v').write_text(TB_CORE.replace('NPROG', str(NP)).replace('WDC', str(WD)))
    c = sh(['iverilog', '-g2012', '-s', 'rtl0a_tb', '-o', str(d / 'sim'), str(d / 'tb.v')] + [str(s) for s in src], timeout=300)   # -s: RTL-0B tops in the same directory are not elaborated
    if c.returncode: raise RuntimeError(f'{tag} compile: ' + c.stderr[-800:])
    r = sh(['vvp', '-n', str(d / 'sim')], cwd=d, timeout=3000); (d / 'sim.log').write_text(r.stdout); (d / 'sim').unlink()
    L = r.stdout.split('\n'); recs, regs = {}, {}
    for x in L:
        t = x.split()
        if t[:1] == ['P']: recs[int(t[1])] = ([int(v) for v in t[2:13]], int(t[13], 16))
        if t[:1] == ['G']: regs.setdefault(int(t[1]), {})[int(t[2])] = t[3]
    out_recs = {k: rtl_record(f, regs[k], m, P[k][2]).hex() for k, (f, m) in recs.items()}
    return out_recs, [int(x.split()[1]) for x in L if x.startswith('T ')], 'END' in L

def main(out, mutants):
    out = Path(out).resolve(); out.mkdir(parents=True); res = dict(status='ERROR', harness_sha256=sha(__file__)); checks = {}
    try:
        base = dict(l.split()[::-1] for l in BASE.read_text().splitlines() if l.strip())
        res['shared'] = {s: sha(ROOT / s) for s in SHARED}; res['new_rtl'] = {p.name: sha(p) for p in sorted((ROOT / 'hardware/rtl/core/psurd').glob('*.v'))}
        checks['G6 shared sources == recorded Gen-1 baseline'] = all(base.get(s) == h for s, h in res['shared'].items())
        if not checks['G6 shared sources == recorded Gen-1 baseline']: raise RuntimeError('shared source drift; refusing to run')
        res['tool'] = sh(['iverilog', '-V']).stdout.splitlines()[0]
        rnd = random.Random(7); E = [0, 1, -1, (1 << 63) - 1, -(1 << 63), 1 << 62]
        sv = [(a, b, 1) for a in E for b in E]; pell = [(2, 1), (7, 4), (26, 15), (97, 56), (362, 209)]
        a, b = 1, 0
        for _ in range(33): a, b = 2 * a + 3 * b, a + 2 * b; pell.append((a, b))
        sv += [(x, -y, 1) for x, y in pell] + [(-x, y, 1) for x, y in pell] + [(rnd.randrange(-M64 // 2, M64 // 2), rnd.randrange(-M64 // 2, M64 // 2), 1) for _ in range(3000)]
        sd = out / 'g2'; sd.mkdir(); (sd / 'sign.hex').write_text(''.join(pack(t) + '\n' for t in sv)); (sd / 'tb.v').write_text(TB_SIGN.replace('NV', str(len(sv))))
        c = sh(['iverilog', '-g2012', '-o', str(sd / 'sim'), str(sd / 'tb.v'), str(ROOT / 'hardware/rtl/core/psurd/psurd_sign.v')]); r = sh(['vvp', '-n', str(sd / 'sim')], cwd=sd); (sd / 'sim').unlink()
        got = {int(t[1]): (int(t[2]), int(t[3]), int(t[4])) for t in (x.split() for x in r.stdout.split('\n')) if t[:1] == ['S']}
        bad = [i for i, t in enumerate(sv) if got.get(i) != (O.sign(t) == 0, O.sign(t) < 0, O.sign(t) > 0)]
        checks[f'G2 sign unit: {len(sv)} tuples (boundary, {2 * len(pell)} near-cancelling Pell, random)'] = c.returncode == 0 and not bad
        src = [ROOT / 'hardware/rtl/core/psurd' / n for n in res['new_rtl']] + [ROOT / s for s in SHARED]
        P = programs(); res['programs'] = len(P)
        recs, tos, ended = run_core(out, src, P, 'core')
        exe = out / 'spu_vm'; sh(['make', '-s', '-B', '-C', str(ROOT / 'software/vm'), 'spu_vm', f'BIN={exe}'])
        fails = {'oracle': [], 'cpp': []}
        for k, (name, w, B) in enumerate(P):
            want = O.record(O.run(w, B)).hex(); img = out / 'img.spui'; img.write_bytes(O.image(w))
            cpp = sh([str(exe), '--profile', 'programmable-surd', str(img), '--budget', str(B)]).stdout.strip()
            if recs.get(k) != want: fails['oracle'].append(name)
            if recs.get(k) != cpp: fails['cpp'].append(name)
        g3 = [n for n in fails['oracle'] if n.startswith(('op ', 'field '))]
        checks[f'G3 decoder: 256 opcodes + {sum(n.startswith("field ") for n, _, _ in P)} malformed words == oracle'] = not g3 and ended and not tos
        checks[f'G4 programs/controls: {sum(not n.startswith(("op ", "field ")) for n, _, _ in P)} records == oracle'] = not fails['oracle'] and ended and not tos
        checks['G4 all records == C++ simulator'] = not fails['cpp']
        res.update(failures={k: v[:15] for k, v in fails.items()}, timeouts=tos, sign_mismatch=bad[:10])
        if mutants:
            muts = {'BR without CV check': ('psurd_core.v', "else if (sign_cc && !CV) finish(3'd2);", "else if (1'b0) finish(3'd2);"),
                    'refusal writes destination': ('psurd_exec.v', "arith_done && busy && arith_status == 4'd0;", "arith_done && busy;"),
                    'decoder ignores bit 59': ('psurd_decode.v', 'case (op)', "case ({op[7:4], 1'b0, op[2:0]})")}
            for mn, (fn, a_, b_) in muts.items():
                md = out / ('mut_src_' + mn.replace(' ', '_')); md.mkdir()
                for p in src[:len(res['new_rtl'])]: shutil.copy(p, md / p.name)
                t = (md / fn).read_text(); assert t.count(a_) == 1, mn; (md / fn).write_text(t.replace(a_, b_))
                mr, mt, _ = run_core(out, [md / n for n in res['new_rtl']] + src[len(res['new_rtl']):], P, 'run_' + mn.replace(' ', '_'))
                checks[f'G5 mutant fails: {mn}'] = bool(mt) or any(mr.get(k) != O.record(O.run(w, B)).hex() for k, (_, w, B) in enumerate(P))
        res['status'] = 'PASS' if all(checks.values()) else 'FAIL'
    except Exception:
        res['traceback'] = traceback.format_exc()
    finally:
        res['checks'] = checks; (out / 'results.json').write_text(json.dumps(res, indent=1, default=str) + '\n')
    print('RTL-0A', res['status'], {k: v for k, v in checks.items()})
    return 0 if res['status'] == 'PASS' else 1

if __name__ == '__main__':
    sys.exit(main(sys.argv[1], '--mutants' in sys.argv[2:]))
