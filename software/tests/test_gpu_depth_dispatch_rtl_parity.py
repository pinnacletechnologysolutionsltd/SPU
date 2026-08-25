#!/usr/bin/env python3
"""test_gpu_depth_dispatch_rtl_parity.py -- exercises spu_depth_dispatch.v's
pending queue and per-unit input latching against
gpu_depth_v2_oracle.py's depth_interp_setup(), for scenarios a single-
triangle oracle can't cover on its own:

1. unit0-only and unit1-only dispatch match the oracle.
2. Simultaneous depth_setup0+depth_setup1 pulses: unit0 gets fixed
   priority, unit1 is not dropped -- it completes on the very next pass.
3. THE correctness property spu_depth_dispatch.v exists to guarantee:
   if depth_setup1 pulses while unit0's job is still running, and the
   raw a/b/c/z input wires for unit1 then CHANGE before unit1's
   deferred job is actually dispatched (simulating a host that starts
   loading a new triangle into the same wires), unit1's result must
   still reflect the values latched AT THE PULSE, not the corrupted
   ones -- this is the actual bug the module's design doc flagged
   before any RTL was written for it.

Run:
  python3 software/tests/test_gpu_depth_dispatch_rtl_parity.py

Requirements: iverilog + vvp in PATH.
"""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "software" / "lib"))

from gpu_depth_v2_oracle import depth_interp_setup, triangle_edges  # noqa: E402

RTL_FILES = [
    "hardware/rtl/gpu/spu_depth_dispatch.v",
    "hardware/rtl/gpu/spu_depth_math.v",
    "hardware/rtl/gpu/spu_reciprocal_core.v",
    "hardware/rtl/gpu/spu_shared_mult35.v",
]

TRI_A = ((10, 10), (600, 30), (300, 460), 0, 65535, 32768)
TRI_B = ((10, 10), (630, 12), (320, 470), 1000, 60000, 30000)
# A THIRD, distinct triangle used only as "corruption" for scenario 3 --
# if the RTL incorrectly re-reads inputs at dispatch time instead of at
# the pulse, unit1's result would match THIS triangle's oracle values
# instead of TRI_B's, which the test checks for explicitly.
TRI_CORRUPT = ((0, 0), (639, 1), (320, 479), 5000, 6000, 7000)


def signed_lit(v: int, width: int) -> str:
    return f"{width}'sd{v}" if v >= 0 else f"-{width}'sd{-v}"


def edges_of(tri):
    v0, v1, v2, z0, z1, z2 = tri
    e0, e1, e2, D = triangle_edges(v0, v1, v2)
    return e0, e1, e2, (z0, z1, z2)


def expected_of(tri):
    v0, v1, v2, z0, z1, z2 = tri
    return depth_interp_setup(v0, v1, v2, z0, z1, z2)


TB_TEMPLATE = r"""
`timescale 1ns/1ps
module dispatch_tb;
    reg clk = 0, rst_n = 0, depth_setup0 = 0, depth_setup1 = 0;
    reg signed [15:0] a0_0={A0_A}, b0_0={B0_A}, a1_0={A1_A}, b1_0={B1_A}, a2_0={A2_A}, b2_0={B2_A};
    reg signed [31:0] c0_0={C0_A}, c1_0={C1_A}, c2_0={C2_A};
    reg [15:0] z0_0={Z0_A}, z1_0={Z1_A}, z2_0={Z2_A};
    reg signed [15:0] a0_1={A0_B}, b0_1={B0_B}, a1_1={A1_B}, b1_1={B1_B}, a2_1={A2_B}, b2_1={B2_B};
    reg signed [31:0] c0_1={C0_B}, c1_1={C1_B}, c2_1={C2_B};
    reg [15:0] z0_1={Z0_B}, z1_1={Z1_B}, z2_1={Z2_B};

    wire signed [55:0] A_z0, B_z0, C_z0, A_z1, B_z1, C_z1;
    wire [6:0] frac_bits0, frac_bits1;
    wire ready0, ready1;

    spu_depth_dispatch u_dut (
        .clk(clk), .rst_n(rst_n),
        .depth_setup0(depth_setup0), .depth_setup1(depth_setup1),
        .a0_0(a0_0), .b0_0(b0_0), .a1_0(a1_0), .b1_0(b1_0), .a2_0(a2_0), .b2_0(b2_0),
        .c0_0(c0_0), .c1_0(c1_0), .c2_0(c2_0), .z0_0(z0_0), .z1_0(z1_0), .z2_0(z2_0),
        .a0_1(a0_1), .b0_1(b0_1), .a1_1(a1_1), .b1_1(b1_1), .a2_1(a2_1), .b2_1(b2_1),
        .c0_1(c0_1), .c1_1(c1_1), .c2_1(c2_1), .z0_1(z0_1), .z1_1(z1_1), .z2_1(z2_1),
        .A_z0(A_z0), .B_z0(B_z0), .C_z0(C_z0), .frac_bits0(frac_bits0), .ready0(ready0),
        .A_z1(A_z1), .B_z1(B_z1), .C_z1(C_z1), .frac_bits1(frac_bits1), .ready1(ready1)
    );

    always #5 clk = ~clk;

    initial begin
        rst_n = 0;
        repeat (3) @(negedge clk);
        rst_n = 1;
        @(negedge clk);

{STIMULUS}

        repeat (60) @(negedge clk);
        $finish;
    end

    always @(posedge clk) begin
        if (ready0) $display("READY0 %0d %0d %0d %0d", A_z0, B_z0, C_z0, frac_bits0);
        if (ready1) $display("READY1 %0d %0d %0d %0d", A_z1, B_z1, C_z1, frac_bits1);
    end
endmodule
"""


def fmt_tri(e, z, suffix):
    e0, e1, e2 = e
    (a0, b0, c0), (a1, b1, c1), (a2, b2, c2) = e0, e1, e2
    z0, z1, z2 = z
    return {
        f"A0_{suffix}": signed_lit(a0, 16), f"B0_{suffix}": signed_lit(b0, 16), f"C0_{suffix}": signed_lit(c0, 32),
        f"A1_{suffix}": signed_lit(a1, 16), f"B1_{suffix}": signed_lit(b1, 16), f"C1_{suffix}": signed_lit(c1, 32),
        f"A2_{suffix}": signed_lit(a2, 16), f"B2_{suffix}": signed_lit(b2, 16), f"C2_{suffix}": signed_lit(c2, 32),
        f"Z0_{suffix}": z0, f"Z1_{suffix}": z1, f"Z2_{suffix}": z2,
    }


def run(stimulus, tri_a, tri_b, name):
    e_a, z_a = edges_of(tri_a)[:3], edges_of(tri_a)[3]
    e_b, z_b = edges_of(tri_b)[:3], edges_of(tri_b)[3]
    fields = {**fmt_tri(e_a, z_a, "A"), **fmt_tri(e_b, z_b, "B"), "STIMULUS": stimulus}
    tb_src = TB_TEMPLATE.format(**fields)

    build_dir = REPO / "build"
    build_dir.mkdir(exist_ok=True)
    tb_path = build_dir / f"dispatch_tb_{name}.v"
    tb_path.write_text(tb_src)
    vvp_path = build_dir / f"dispatch_tb_{name}.vvp"
    subprocess.run(
        ["iverilog", "-g2012", "-o", str(vvp_path), str(tb_path)]
        + [str(REPO / f) for f in RTL_FILES],
        check=True, cwd=REPO,
    )
    result = subprocess.run(["vvp", str(vvp_path)], check=True,
                             capture_output=True, text=True, cwd=REPO)
    got0, got1 = [], []
    for line in result.stdout.splitlines():
        if line.startswith("READY0 "):
            got0.append(tuple(int(x) for x in line.split()[1:]))
        elif line.startswith("READY1 "):
            got1.append(tuple(int(x) for x in line.split()[1:]))
    return got0, got1


def check(label, got_list, expected, results):
    ok = len(got_list) == 1 and got_list[0] == expected
    results.append(ok)
    status = "OK" if ok else "MISMATCH"
    print(f"  {label}: expected={expected} got={got_list} [{status}]")


def main() -> int:
    results = []

    # Scenario 1: unit0 only.
    stim = "        depth_setup0 = 1;\n        @(negedge clk);\n        depth_setup0 = 0;\n        repeat (25) @(negedge clk);\n"
    got0, got1 = run(stim, TRI_A, TRI_B, "unit0_only")
    print("Scenario 1: unit0 only")
    check("unit0", got0, expected_of(TRI_A), results)
    if got1:
        print(f"  UNEXPECTED unit1 output: {got1}")
        results.append(False)

    # Scenario 2: unit1 only.
    stim = "        depth_setup1 = 1;\n        @(negedge clk);\n        depth_setup1 = 0;\n        repeat (25) @(negedge clk);\n"
    got0, got1 = run(stim, TRI_A, TRI_B, "unit1_only")
    print("Scenario 2: unit1 only")
    check("unit1", got1, expected_of(TRI_B), results)
    if got0:
        print(f"  UNEXPECTED unit0 output: {got0}")
        results.append(False)

    # Scenario 3: simultaneous pulses -- unit0 priority, unit1 not dropped.
    stim = ("        depth_setup0 = 1; depth_setup1 = 1;\n"
            "        @(negedge clk);\n"
            "        depth_setup0 = 0; depth_setup1 = 0;\n"
            "        repeat (40) @(negedge clk);\n")
    got0, got1 = run(stim, TRI_A, TRI_B, "simultaneous")
    print("Scenario 3: simultaneous depth_setup0 + depth_setup1")
    check("unit0", got0, expected_of(TRI_A), results)
    check("unit1", got1, expected_of(TRI_B), results)

    # Scenario 4: unit1's inputs latched at the pulse, not at dispatch --
    # depth_setup0 fires first (occupying the sequencer), depth_setup1
    # fires one cycle later with TRI_B's coefficients, then the raw
    # wires for unit1 are overwritten with TRI_CORRUPT's values BEFORE
    # unit1 is actually dispatched (it has to wait for unit0's ~20-cycle
    # pass to finish). If the RTL is correct, unit1's result still
    # matches TRI_B, not TRI_CORRUPT.
    e_c, z_c = edges_of(TRI_CORRUPT)[:3], edges_of(TRI_CORRUPT)[3]
    (a0, b0, c0), (a1, b1, c1), (a2, b2, c2) = e_c
    z0, z1, z2 = z_c
    corrupt_values = {
        "a0_1": signed_lit(a0, 16), "b0_1": signed_lit(b0, 16), "c0_1": signed_lit(c0, 32),
        "a1_1": signed_lit(a1, 16), "b1_1": signed_lit(b1, 16), "c1_1": signed_lit(c1, 32),
        "a2_1": signed_lit(a2, 16), "b2_1": signed_lit(b2, 16), "c2_1": signed_lit(c2, 32),
        "z0_1": z0, "z1_1": z1, "z2_1": z2,
    }
    corrupt_assigns = "\n".join(f"        {k} = {v};" for k, v in corrupt_values.items())
    stim = (
        "        depth_setup0 = 1;\n"
        "        @(negedge clk);\n"
        "        depth_setup0 = 0;\n"
        "        depth_setup1 = 1;\n"
        "        @(negedge clk);\n"
        "        depth_setup1 = 0;\n"
        "        // corrupt unit1's raw input wires while its job is still pending\n"
        f"{corrupt_assigns}\n"
        "        repeat (40) @(negedge clk);\n"
    )
    got0, got1 = run(stim, TRI_A, TRI_B, "latch_survives_corruption")
    print("Scenario 4: unit1 inputs latched at pulse time, survive later corruption")
    check("unit0", got0, expected_of(TRI_A), results)
    check("unit1 (must match TRI_B, not TRI_CORRUPT)", got1, expected_of(TRI_B), results)

    if not all(results):
        print(f"FAIL: {results.count(False)}/{len(results)} checks failed")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
