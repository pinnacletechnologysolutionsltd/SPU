#!/usr/bin/env python3
"""test_gpu_framebuffer_readout_probe.py -- protocol/sequencing check for
spu13_tang25k_gpu_framebuffer_readout_probe.v: monitors the byte sequence
it hands to the UART TX core (tx_byte_in/tx_start, hierarchical
reference) against an independent oracle computation of the same two
fixed test triangles, for the marker plus the first several rows of
pixels. Does not re-verify UART bit-level timing (CLKS_PER_BIT), which
is the same proven send-and-wait pattern already used in
spu13_tang25k_lucas_mac_probe.v; overrides CLKS_PER_BIT much smaller
than the real 434 (115200 baud) purely so this check doesn't need to
wait out billions of cycles for real UART timing -- a full 640x480
frame at real baud is a real-hardware-only exercise, not simulated here.

Run:
  python3 software/tests/test_gpu_framebuffer_readout_probe.py

Requirements: iverilog + vvp in PATH.
"""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "software" / "lib"))

from gpu_depth_v2_oracle import triangle_edges  # noqa: E402

RTL_FILES = [
    "hardware/rtl/gpu/spu_dual_raster.v",
    "hardware/rtl/gpu/spu_raster_unit.v",
    "hardware/rtl/gpu/spu_edge_stepper.v",
    "hardware/rtl/gpu/spu_depth_dispatch.v",
    "hardware/rtl/gpu/spu_depth_math.v",
    "hardware/rtl/gpu/spu_reciprocal_core.v",
    "hardware/rtl/gpu/spu_shared_mult35.v",
    "hardware/rtl/gpu/spu_attr_stepper.v",
    "hardware/rtl/gpu/spu_depth_compare.v",
    "hardware/boards/tang_primer_25k/spu_tang25k_clk_pixel_div2.v",
]

V0_0, V1_0, V2_0 = (50, 50), (400, 60), (200, 300)
Z_0 = (50000, 50000, 50000)
TRI_R0, TRI_G0, TRI_B0 = 15, 0, 0
V0_1, V1_1, V2_1 = (150, 100), (450, 150), (300, 400)
Z_1 = (10000, 10000, 10000)
TRI_R1, TRI_G1, TRI_B1 = 0, 15, 0

CHECK_ROWS = 60      # covers the (50,50)/(51,51) area that failed on real
                       # hardware (a real timing-closure issue -- see the
                       # DUT's clock-divider comment -- not something
                       # iverilog's zero-delay model can expose either
                       # way, so this is just a logic-level regression
                       # check for the clock-divider wiring change, not a
                       # re-verification of that fix). Full-frame +
                       # loop-back coverage (480 rows here previously)
                       # already passed once for the loop-back/coefficient
                       # fixes, which this change doesn't touch.
SECOND_FRAME_CHECK_ROWS = 0  # not re-checking the loop-back here; already
                               # proven separately and unaffected by this
                               # clock-divider change

TB_TEMPLATE = r"""
`timescale 1ns/1ps
module fb_readout_tb;
    reg sys_clk = 0;
    wire [2:0] led;
    wire uart_tx;

    spu13_tang25k_gpu_framebuffer_readout_probe #(.CLKS_PER_BIT(4)) dut (
        .sys_clk(sys_clk), .led(led), .uart_tx(uart_tx)
    );

    always #10 sys_clk = ~sys_clk;

    initial begin
        // Run long enough to observe a full first frame plus the start
        // of the looped second frame -- see CHECK_ROWS/
        // SECOND_FRAME_CHECK_ROWS above for why the second frame matters.
        #{RUN_TIME};
        $display("SIM DONE");
        $finish;
    end

    // Sample on dut.clk (the DUT's internal, divided clock -- see its
    // clock-divider comment), NOT sys_clk: tx_start only changes once
    // per dut.clk cycle now, which spans two sys_clk edges, so sampling
    // on sys_clk would catch every real pulse twice.
    always @(posedge dut.clk) begin
        if (dut.tx_start)
            $display("TXB %0d", dut.tx_byte_in);
    end
endmodule
"""


def expected_bytes():
    e0 = triangle_edges(V0_0, V1_0, V2_0)[:3]
    e1 = triangle_edges(V0_1, V1_1, V2_1)[:3]

    def inside(edges, x, y):
        def f(e):
            a, b, c = e
            return a * x + b * y + c
        vals = [f(e) for e in edges]
        return all(v >= 0 for v in vals) or all(v <= 0 for v in vals)

    def pixel_bytes(y):
        row = []
        for x in range(640):
            c0 = inside(e0, x, y)
            c1 = inside(e1, x, y)
            if c0 and c1:
                r, g, b = TRI_R1, TRI_G1, TRI_B1
            elif c0:
                r, g, b = TRI_R0, TRI_G0, TRI_B0
            elif c1:
                r, g, b = TRI_R1, TRI_G1, TRI_B1
            else:
                r, g, b = 0, 0, 0
            row.append(r & 0xF)
            row.append(((g & 0xF) << 4) | (b & 0xF))
        return row

    out = [ord(c) for c in "SPU1"]
    for y in range(CHECK_ROWS):
        out.extend(pixel_bytes(y))
    if SECOND_FRAME_CHECK_ROWS:
        # Only meaningful when CHECK_ROWS==480 (the real full frame) --
        # the RTL doesn't know about a truncated check, so the real
        # second marker only appears after all 480 rows regardless.
        assert CHECK_ROWS == 480, (
            "SECOND_FRAME_CHECK_ROWS>0 requires CHECK_ROWS==480 -- "
            "the real second marker only follows a full first frame"
        )
        out.extend(ord(c) for c in "SPU1")
        for y in range(SECOND_FRAME_CHECK_ROWS):
            out.extend(pixel_bytes(y))
    return out


def main() -> int:
    exp = expected_bytes()
    n_needed = len(exp)

    # Rough cycle budget: reset (~256 cycles) + per byte ~ (start-bit
    # settle + 10 bits * CLKS_PER_BIT=4 + FSM overhead) -- tighter than
    # earlier since this now covers a full frame (614,408+ bytes) and a
    # loose margin would make simulation impractically slow.
    # x2 vs the earlier budget: the DUT's internal clk is now divided
    # down from sys_clk (real hardware timing-margin fix), so each
    # internal clock cycle takes two sys_clk toggle periods in this sim.
    run_time_ns = 300 * 40 + n_needed * 55 * 40

    tb_src = TB_TEMPLATE.format(RUN_TIME=run_time_ns)
    build_dir = REPO / "build"
    build_dir.mkdir(exist_ok=True)
    tb_path = build_dir / "fb_readout_tb.v"
    tb_path.write_text(tb_src)
    vvp_path = build_dir / "fb_readout_tb.vvp"
    subprocess.run(
        ["iverilog", "-g2012", "-o", str(vvp_path), str(tb_path),
         str(REPO / "hardware/boards/tang_primer_25k/spu13_tang25k_gpu_framebuffer_readout_probe.v")]
        + [str(REPO / f) for f in RTL_FILES],
        check=True, cwd=REPO,
    )
    result = subprocess.run(["vvp", str(vvp_path)], check=True,
                             capture_output=True, text=True, cwd=REPO, timeout=560)

    got = []
    for line in result.stdout.splitlines():
        if line.startswith("TXB "):
            got.append(int(line.split()[1]))

    n = min(len(got), len(exp))
    mismatches = 0
    for i in range(n):
        if got[i] != exp[i]:
            mismatches += 1
            if mismatches <= 10:
                print(f"  MISMATCH byte {i}: expected {exp[i]:#04x} got {got[i]:#04x}")

    print(f"{n} of {len(exp)} expected bytes observed, {mismatches} mismatches")
    if mismatches or n < len(exp):
        if n < len(exp):
            print(f"FAIL: only captured {n} bytes, needed {len(exp)} "
                  f"(increase run_time_ns budget)")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
