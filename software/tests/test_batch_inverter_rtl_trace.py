#!/usr/bin/env python3
"""Regenerate batch-inverter expectations with the Python oracle and run RTL.

The committed .mem file supplies deterministic denominator cases, but expected
inverse and singular values are recomputed here with the independent A31 tower
oracle. This prevents a stale golden artifact from making the RTL test pass.
"""

from __future__ import annotations

import contextlib
import io
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEM = ROOT / "hardware/tests/spu13/spu13_batch_inv_golden.mem"


def oracle_api():
    import sys
    sys.path.insert(0, str(ROOT / "software"))
    with contextlib.redirect_stdout(io.StringIO()):
        from lib.a31_field import a31_tower_inv
    return a31_tower_inv


def read_denominator_cases():
    words = []
    for line in MEM.read_text(encoding="utf-8").splitlines():
        line = line.split("//", 1)[0].strip()
        if line:
            words.append(int(line, 16))
    n_cases = words[0]
    pos = 1
    cases = []
    for _ in range(n_cases):
        k = words[pos]
        pos += 1
        dens = []
        for _ in range(k):
            dens.append(tuple(words[pos:pos + 4]))
            pos += 9
        cases.append(dens)
    return cases


def render_mem(cases, a31_tower_inv):
    out = [f"{len(cases):08X}"]
    for dens in cases:
        out.append(f"{len(dens):08X}")
        for d in dens:
            inv, singular = a31_tower_inv(d)
            if singular:
                inv = (0, 0, 0, 0)
            out.extend(f"{x:08X}" for x in d)
            out.extend(f"{x:08X}" for x in inv)
            out.append(f"{int(singular):08X}")
    return "\n".join(out) + "\n"


def render_tb(mem_path: Path):
    return f'''`timescale 1ns/1ps
module batch_trace_tb;
  reg clk=0, rst_n=0, start=0, d_valid=0, d_last=0;
  reg [4:0] batch_size; reg [31:0] d0,d1,d2,d3;
  wire [31:0] inv0,inv1,inv2,inv3; wire inv_valid,inv_singular,done,busy;
  wire [3:0] debug_state; integer golden[0:600]; integer ptr, cases, ci, k, li;
  reg [31:0] e0[0:15],e1[0:15],e2[0:15],e3[0:15]; reg es[0:15];
  reg [31:0] c0[0:15],c1[0:15],c2[0:15],c3[0:15]; reg cs[0:15];
  integer cap, errors, timeout;
  always #5 clk=~clk;
  spu13_batch_inverter #(.MAX_BATCH(16),.USE_STRUCTURED_INVERTER(0),.STRUCTURED_INVERTER_SEQUENTIAL(0)) dut(
    .clk(clk),.rst_n(rst_n),.start(start),.batch_size(batch_size),
    .d0(d0),.d1(d1),.d2(d2),.d3(d3),.d_valid(d_valid),.d_last(d_last),
    .inv0(inv0),.inv1(inv1),.inv2(inv2),.inv3(inv3),.inv_valid(inv_valid),
    .inv_singular(inv_singular),.done(done),.busy(busy),.debug_state(debug_state));
  always @(posedge clk) if (inv_valid) begin
    c0[cap]<=inv0;c1[cap]<=inv1;c2[cap]<=inv2;c3[cap]<=inv3;cs[cap]<=inv_singular;cap<=cap+1;
  end
  initial begin
    $readmemh("{mem_path}", golden); cases=golden[0]; ptr=1; errors=0; cap=0;
    if ((^golden[0])===1'bx || cases==0) begin $display("BATCH_TRACE: FAIL empty"); $finish; end
    #20 rst_n=1; #20;
    for (ci=0;ci<cases;ci=ci+1) begin
      k=golden[ptr];ptr=ptr+1;cap=0;batch_size=k;start=1;#10;start=0;
      for (li=0;li<k;li=li+1) begin
        d0=golden[ptr];d1=golden[ptr+1];d2=golden[ptr+2];d3=golden[ptr+3];
        e0[li]=golden[ptr+4];e1[li]=golden[ptr+5];e2[li]=golden[ptr+6];e3[li]=golden[ptr+7];es[li]=golden[ptr+8];ptr=ptr+9;
        d_valid=1;d_last=(li==k-1);#10;d_valid=0;d_last=0;
      end
      timeout=0;while(!done && timeout<50000) begin @(posedge clk);timeout=timeout+1;end
      if(timeout>=50000) begin $display("TRACE_FAIL case=%0d timeout state=%0d",ci,debug_state);errors=errors+1;end
      else begin
        repeat(2) @(posedge clk);
        for(li=0;li<k;li=li+1) if(cs[li]!==es[li] || (!es[li] && (c0[li]!==e0[li] || c1[li]!==e1[li] || c2[li]!==e2[li] || c3[li]!==e3[li]))) begin
          $display("TRACE_FAIL case=%0d lane=%0d singular=%b/%b",ci,li,cs[li],es[li]);errors=errors+1;
        end
        if (errors == 0) $display("TRACE_PASS case=%0d lanes=%0d",ci,k);
      end
      #20;
    end
    if(errors==0)$display("BATCH_TRACE: PASS cases=%0d",cases);else $display("BATCH_TRACE: FAIL errors=%0d",errors);
    $finish;
  end
endmodule
'''


def main():
    a31_tower_inv = oracle_api()
    if not MEM.exists():
        print(f"missing denominator fixture: {MEM}")
        return 1
    cases = read_denominator_cases()
    with tempfile.TemporaryDirectory(prefix="batch_trace_") as td:
        td = Path(td)
        mem = td / "batch.mem"
        tb = td / "batch_trace_tb.v"
        vvp = td / "batch_trace_tb.vvp"
        mem.write_text(render_mem(cases, a31_tower_inv), encoding="utf-8")
        tb.write_text(render_tb(mem), encoding="utf-8")
        build = subprocess.run([
            "iverilog", "-g2012", "-y", "hardware/rtl/core/spu13",
            "-y", "hardware/rtl/core/shared", "-y", "hardware/rtl/math",
            "-y", "hardware/rtl/common", "-I", "hardware/rtl/arch",
            "-o", str(vvp), "hardware/rtl/core/spu13/spu13_batch_inverter.v",
            str(tb)], cwd=ROOT, text=True, capture_output=True, check=False)
        if build.returncode:
            print(build.stdout, end=""); print(build.stderr, end=""); return 1
        run = subprocess.run(["vvp", str(vvp)], cwd=ROOT, text=True,
                             capture_output=True, check=False)
        print(run.stdout, end=""); print(run.stderr, end="")
        return 0 if run.returncode == 0 and "BATCH_TRACE: PASS" in run.stdout else 1


if __name__ == "__main__":
    raise SystemExit(main())
