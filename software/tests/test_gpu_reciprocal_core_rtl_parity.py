#!/usr/bin/env python3
"""test_gpu_reciprocal_core_rtl_parity.py -- bit-exact parity between
gpu_depth_v2_oracle.py's full_reciprocal() (normalize incl. real
truncation -> core -> denormalize) and the real RTL
(spu_reciprocal_core.v + spu_shared_mult35.v), across the full input
width range the reciprocal contract characterized (1-34 bits), not just
the idealized already-normalized mantissa domain.

Also checks the degenerate d_in==0 case forces a defined, safe output
(y_out=0, degenerate=1) instead of running the leading-one detector on
undefined input -- the halt-and-flag finding that added this case to
the RTL in the first place.

Run:
  python3 software/tests/test_gpu_reciprocal_core_rtl_parity.py

Requirements: iverilog + vvp in PATH.
"""
import random
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "software" / "lib"))

from gpu_depth_v2_oracle import full_reciprocal  # noqa: E402

RTL_FILES = [
    "hardware/rtl/gpu/spu_reciprocal_core.v",
    "hardware/rtl/gpu/spu_shared_mult35.v",
]


def build_vectors():
    """One vector per bit-width 1..34: MSB-only, all-ones, and two
    pseudo-random values in [2**(w-1), 2**w), plus d_in=0 for the
    degenerate case. Deterministic seed for reproducibility."""
    rng = random.Random(20260825)
    vectors = [0]
    for w in range(1, 35):
        lo = 1 << (w - 1)
        hi = (1 << w) - 1
        vectors.append(lo)
        vectors.append(hi)
        vectors.append(rng.randint(lo, hi))
        vectors.append(rng.randint(lo, hi))
    return vectors


def golden(vectors):
    out = []
    for d in vectors:
        if d == 0:
            out.append((0, 0, 1))
        else:
            y, exp = full_reciprocal(d)
            out.append((y, exp, 0))
    return out


TB_TEMPLATE = r"""
`timescale 1ns/1ps
module recip_parity_tb;
    reg clk = 0, rst_n = 0, start = 0;
    reg [33:0] d_in = 0;
    wire [15:0] y_out;
    wire [6:0] exp_out;
    wire done, degenerate;
    wire [39:0] mult_a;
    wire [16:0] mult_b;
    wire [56:0] mult_p;

    spu_shared_mult35 u_mult (.a(mult_a), .b(mult_b), .p(mult_p));
    spu_reciprocal_core u_dut (
        .clk(clk), .rst_n(rst_n), .start(start), .d_in(d_in),
        .y_out(y_out), .exp_out(exp_out), .done(done),
        .degenerate(degenerate),
        .mult_a(mult_a), .mult_b(mult_b), .mult_p(mult_p)
    );

    always #5 clk = ~clk;

    integer i;
    reg [33:0] vecs [0:{N_MINUS_1}];

    initial begin
{VEC_INIT}
        rst_n = 0;
        repeat (3) @(negedge clk);
        rst_n = 1;
        @(negedge clk);

        for (i = 0; i <= {N_MINUS_1}; i = i + 1) begin
            d_in = vecs[i];
            start = 1;
            @(negedge clk);
            start = 0;
            while (!done) @(negedge clk);
            $display("VEC %0d Y=%0d EXP=%0d DEG=%0d", i, y_out, exp_out, degenerate);
            @(negedge clk);
        end
        $finish;
    end
endmodule
"""


def gen_tb(vectors):
    n = len(vectors)
    vec_init = "\n".join(f"        vecs[{i}] = {v};" for i, v in enumerate(vectors))
    return TB_TEMPLATE.format(N_MINUS_1=n - 1, VEC_INIT=vec_init)


def run_rtl(vectors, build_dir: Path):
    tb_path = build_dir / "recip_parity_tb.v"
    tb_path.write_text(gen_tb(vectors))
    vvp_path = build_dir / "recip_parity_tb.vvp"
    subprocess.run(
        ["iverilog", "-g2012", "-o", str(vvp_path), str(tb_path)]
        + [str(REPO / f) for f in RTL_FILES],
        check=True, cwd=REPO,
    )
    result = subprocess.run(["vvp", str(vvp_path)], check=True,
                             capture_output=True, text=True, cwd=REPO)
    got = {}
    for line in result.stdout.splitlines():
        if line.startswith("VEC "):
            parts = line.split()
            idx = int(parts[1])
            y = int(parts[2].split("=")[1])
            exp = int(parts[3].split("=")[1])
            deg = int(parts[4].split("=")[1])
            got[idx] = (y, exp, deg)
    return got


def main() -> int:
    vectors = build_vectors()
    expected = golden(vectors)

    build_dir = REPO / "build"
    build_dir.mkdir(exist_ok=True)
    got = run_rtl(vectors, build_dir)

    mismatches = []
    for i, exp_tuple in enumerate(expected):
        if i not in got:
            mismatches.append((i, vectors[i], exp_tuple, None))
            continue
        if got[i] != exp_tuple:
            mismatches.append((i, vectors[i], exp_tuple, got[i]))

    print(f"spu_reciprocal_core.v RTL parity: {len(vectors)} vectors "
          f"(bit-widths 1-34 + degenerate), {len(mismatches)} mismatches")
    for i, d, exp_t, got_t in mismatches[:20]:
        print(f"  MISMATCH vec {i} d_in={d}: expected {exp_t}, got {got_t}")

    if mismatches:
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
