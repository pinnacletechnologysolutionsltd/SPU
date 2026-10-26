#!/usr/bin/env python3
"""Compare the D4 reflection RTL with independent P0 formula vectors."""

from __future__ import annotations

from itertools import product
import random
import shutil
import subprocess
import tempfile
from pathlib import Path

from test_d4_reflection_oracle import ROOTS, reflect_formula


ROOT = Path(__file__).resolve().parents[2]
RTL = ROOT / "hardware/rtl/math/spu_d4_reflection_unit.v"


def signed16(value: int) -> int:
    return value & 0xFFFF


def pack_lanes(values: tuple[int, ...]) -> int:
    packed = 0
    for value in values:
        packed = (packed << 16) | signed16(value)
    return packed


def expected(values: tuple[int, ...], selector: int) -> tuple[int, bool]:
    result = reflect_formula(values, ROOTS[selector])
    invalid = any(value < -32768 or value > 32767 for value in result)
    return (pack_lanes(result) if not invalid else 0), invalid


def cases():
    reduced = range(-8, 8)
    for vector in product(reduced, repeat=4):
        for selector in range(4):
            yield vector, selector

    boundaries = (-32768, -32767, -1, 0, 1, 32766, 32767)
    for vector in product(boundaries, repeat=4):
        for selector in range(4):
            yield vector, selector

    rng = random.Random(0xD4_2026)
    for _ in range(4096):
        vector = tuple(rng.randint(-32768, 32767) for _ in range(4))
        for selector in range(4):
            yield vector, selector


def main() -> int:
    if not shutil.which("iverilog") or not shutil.which("vvp"):
        raise SystemExit("iverilog and vvp are required")

    test_cases = list(cases())
    with tempfile.TemporaryDirectory(prefix="d4_rtl_") as temp:
        work = Path(temp)
        vector_path = work / "vectors.mem"
        with vector_path.open("w", encoding="ascii") as stream:
            for vector, selector in test_cases:
                out, invalid = expected(vector, selector)
                packed = (pack_lanes(vector) << 67) | (selector << 65) | (out << 1) | int(invalid)
                stream.write(f"{packed:033x}\n")

        tb_path = work / "tb.v"
        tb_path.write_text(
            """module tb;
  localparam integer N = CASE_COUNT;
  reg [130:0] vectors [0:N-1];
  reg [63:0] in_v;
  reg [1:0] root_sel;
  wire [63:0] out_v, generic_out_v;
  wire invalid_flag, generic_invalid_flag;
  integer i;
  integer errors = 0;
  spu_d4_reflection_unit dut(.in_v(in_v), .root_sel(root_sel),
                             .out_v(out_v), .invalid_flag(invalid_flag));
  spu_d4_reflection_generic generic_dut(.in_v(in_v), .root_sel(root_sel),
                                        .out_v(generic_out_v),
                                        .invalid_flag(generic_invalid_flag));
  initial begin
    $readmemh("VECTOR_FILE", vectors);
    for (i = 0; i < N; i = i + 1) begin
      {in_v, root_sel} = vectors[i][130:65];
      #1;
      if (invalid_flag !== vectors[i][0]) begin
        $display("STATUS mismatch case=%0d selector=%0d", i, root_sel);
        errors = errors + 1;
      end
      if (generic_invalid_flag !== vectors[i][0]) begin
        $display("GENERIC STATUS mismatch case=%0d selector=%0d", i, root_sel);
        errors = errors + 1;
      end
      if (!vectors[i][0] && out_v !== vectors[i][64:1]) begin
        $display("DATA mismatch case=%0d selector=%0d got=%h expected=%h",
                 i, root_sel, out_v, vectors[i][64:1]);
        errors = errors + 1;
      end
      if (!vectors[i][0] && generic_out_v !== vectors[i][64:1]) begin
        $display("GENERIC DATA mismatch case=%0d selector=%0d got=%h expected=%h",
                 i, root_sel, generic_out_v, vectors[i][64:1]);
        errors = errors + 1;
      end
    end
    if (errors == 0) $display("D4 RTL/P0 equivalence: PASS cases=%0d", N);
    else $display("D4 RTL/P0 equivalence: FAIL cases=%0d errors=%0d", N, errors);
    $finish;
  end
endmodule
""".replace("CASE_COUNT", str(len(test_cases))).replace(
                "VECTOR_FILE", str(vector_path))
        )
        sim = work / "sim.out"
        generic_rtl = ROOT / "hardware/rtl/math/spu_d4_reflection_generic.v"
        subprocess.run(["iverilog", "-g2012", "-s", "tb", "-o", str(sim),
                        str(RTL), str(generic_rtl), str(tb_path)],
                       check=True, cwd=ROOT)
        result = subprocess.run(["vvp", str(sim)], check=True, text=True,
                                capture_output=True, cwd=ROOT)
        print(result.stdout, end="")
        if "D4 RTL/P0 equivalence: PASS" not in result.stdout:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
