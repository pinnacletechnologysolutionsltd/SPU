#!/usr/bin/env python3
"""Lucas MAC oracle-to-RTL trace equivalence.

The Python arithmetic in test_lucas_mac_oracle.py is the reference model.  This
test drives the standalone RTL with the same deterministic vector set and
compares the accepted operation's completion/error outcome and result state.
"""

from __future__ import annotations

import random
import re
import subprocess
import tempfile
from pathlib import Path

from test_lucas_mac_oracle import (
    DEFAULT_MODULUS,
    phi_conj,
    phi_inv,
    phi_mul,
    phi_mul_full,
    phi_phslk,
)


ROOT = Path(__file__).resolve().parents[2]
RTL = ROOT / "hardware/rtl/core/spu13/spu13_lucas_mac.v"
MOD = DEFAULT_MODULUS


def make_vectors():
    rng = random.Random(0x4C55434153)
    vectors = []

    def add(op, a, b, c=0, d=0, n2a=0, n2b=0, d2a=0, d2b=0,
            exp_a=0, exp_b=0, exp_error=0, coherent=0, zero_divisor=0):
        vectors.append((op, a % MOD, b % MOD, c % MOD, d % MOD,
                        n2a % MOD, n2b % MOD, d2a % MOD, d2b % MOD,
                        exp_a % MOD, exp_b % MOD, exp_error,
                        coherent, zero_divisor))

    add(0, 3, 5, exp_a=5, exp_b=8)
    add(0, 0, 1, exp_a=1, exp_b=1)
    add(1, 3, 5, exp_a=8, exp_b=MOD - 5)
    add(2, 3, 5, 2, 7, exp_a=41, exp_b=66)
    add(3, 1, 0, exp_a=1, exp_b=0)
    add(3, 3, 5, exp_a=513, exp_b=5)
    add(3, 0, 0, exp_error=1)
    add(7, 3, 5, exp_error=1)

    coherent_cases = [
        ((3, 5), (2, 7), (6, 10), (4, 14)),
        ((3, 5), (2, 7), (6, 11), (4, 14)),
        ((3, 5), (1, 100), (6, 10), (4, 14)),
    ]
    for n1, d1, n2, d2 in coherent_cases:
        coherent, zd, _, _ = phi_phslk(n1, d1, n2, d2, MOD)
        add(4, n1[0], n1[1], d1[0], d1[1], n2[0], n2[1], d2[0], d2[1],
            exp_a=int(coherent), exp_b=int(zd), coherent=int(coherent),
            zero_divisor=int(zd))

    for _ in range(48):
        a, b, c, d = (rng.randrange(MOD) for _ in range(4))
        op = rng.randrange(4)
        if op == 0:
            ea, eb = phi_mul(a, b, MOD)
        elif op == 1:
            ea, eb = phi_conj(a, b, MOD)
        elif op == 2:
            ea, eb = phi_mul_full(a, b, c, d, MOD)
        else:
            try:
                ea, eb = phi_inv(a, b, MOD)
                add(op, a, b, c, d, exp_a=ea, exp_b=eb)
            except ValueError:
                add(op, a, b, c, d, exp_error=1)
            continue
        add(op, a, b, c, d, exp_a=ea, exp_b=eb)

    return vectors


def render_tb(vectors):
    calls = []
    for i, v in enumerate(vectors):
        op, a, b, c, d, n2a, n2b, d2a, d2b, ea, eb, err, coh, zd = v
        calls.append(
            f"        run_case({i}, 3'd{op}, 10'd{a}, 10'd{b}, 10'd{c}, 10'd{d}, "
            f"10'd{n2a}, 10'd{n2b}, 10'd{d2a}, 10'd{d2b}, "
            f"10'd{ea}, 10'd{eb}, 1'b{err}, 1'b{coh}, 1'b{zd});"
        )
    return f'''`timescale 1ns/1ps
module lucas_trace_tb;
  reg clk = 0; always #5 clk = ~clk;
  reg rst_n = 0, ce = 1, start = 0;
  reg [2:0] opcode; reg [9:0] op_a, op_b, op_c, op_d;
  reg [9:0] n2a, n2b, d2a, d2b;
  wire busy, done, error; wire [9:0] result_a, result_b;
  wire coherent, zero_divisor, norm_violation;
  integer failures = 0;
  spu13_lucas_mac #(.L_P(521), .L_P_BITS(10)) dut (
    .clk(clk), .rst_n(rst_n), .ce(ce), .start(start), .opcode(opcode),
    .op_a(op_a), .op_b(op_b), .op_c(op_c), .op_d(op_d),
    .phslk_n2_a(n2a), .phslk_n2_b(n2b),
    .phslk_d2_a(d2a), .phslk_d2_b(d2b),
    .busy(busy), .done(done), .error(error),
    .result_a(result_a), .result_b(result_b),
    .phslk_coherent(coherent), .phslk_zero_divisor(zero_divisor),
    .norm_violation(norm_violation));

  task run_case;
    input integer idx; input [2:0] op; input [9:0] a,b,c,d,nn_a,nn_b,dd_a,dd_b;
    input [9:0] exp_a, exp_b; input exp_error, exp_coherent, exp_zero;
    integer cycles;
    begin
      @(negedge clk);
      opcode=op; op_a=a; op_b=b; op_c=c; op_d=d;
      n2a=nn_a; n2b=nn_b; d2a=dd_a; d2b=dd_b; start=1;
      @(negedge clk); start=0; cycles=0;
      while (!done && !error && cycles < 200) begin @(negedge clk); cycles=cycles+1; end
      if ((error !== exp_error) || (!exp_error &&
          (result_a !== exp_a || result_b !== exp_b || norm_violation !== 1'b0)) ||
          (op == 3'd4 && (coherent !== exp_coherent || zero_divisor !== exp_zero))) begin
        $display("TRACE_FAIL idx=%0d op=%0d done=%b error=%b result=(%0d,%0d) coherent=%b zd=%b norm=%b cycles=%0d",
                 idx, op, done, error, result_a, result_b, coherent,
                 zero_divisor, norm_violation, cycles);
        failures=failures+1;
      end else begin
        $display("TRACE_PASS idx=%0d op=%0d done=%b error=%b cycles=%0d", idx, op, done, error, cycles);
      end
    end
  endtask

  initial begin
    opcode=0; op_a=0; op_b=0; op_c=0; op_d=0; n2a=0; n2b=0; d2a=0; d2b=0;
    #2; rst_n=0; #12; rst_n=1;
{chr(10).join(calls)}
    if (failures == 0) $display("LUCAS_TRACE: PASS cases={len(vectors)}");
    else $display("LUCAS_TRACE: FAIL cases={len(vectors)} failures=%0d", failures);
    $finish;
  end
endmodule
'''


def main():
    vectors = make_vectors()
    with tempfile.TemporaryDirectory(prefix="lucas_trace_") as td:
        td_path = Path(td)
        tb = td_path / "lucas_trace_tb.v"
        vvp = td_path / "lucas_trace_tb.vvp"
        tb.write_text(render_tb(vectors), encoding="utf-8")
        build = subprocess.run(
            ["iverilog", "-g2012", "-o", str(vvp), str(RTL), str(tb)],
            cwd=ROOT, text=True, capture_output=True, check=False)
        if build.returncode:
            print(build.stdout, end="")
            print(build.stderr, end="")
            return 1
        run = subprocess.run(["vvp", str(vvp)], cwd=ROOT,
                             text=True, capture_output=True, check=False)
        print(run.stdout, end="")
        print(run.stderr, end="")
        if run.returncode or "LUCAS_TRACE: PASS" not in run.stdout:
            return 1
        observed = len(re.findall(r"TRACE_PASS idx=", run.stdout))
        if observed != len(vectors):
            print(f"trace record count mismatch: {observed} != {len(vectors)}")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
