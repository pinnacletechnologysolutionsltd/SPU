#!/usr/bin/env python3
"""Exercise frozen T1i A/B/C/A packets through UART RX and scene loader."""

from __future__ import annotations

import hashlib
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = {
    "A": ("gpu_t1i_scene_a_wire_175b.hex",
          "8077acb3efbb92756fdee4c137500417e32f6f3664784c3b21f150c398d0dae9"),
    "B": ("gpu_t1i_scene_b_wire_175b.hex",
          "f71ec97d18c37cdae7067accbc3b0100bad3689d4fcbc856f55efc11207525d1"),
    "C": ("gpu_t1i_scene_c_wire_175b.hex",
          "604fea47bee07549e28212b87bb5da18dbe6b72d32412ed57bddb6decb8cb89d"),
}

TB = r"""
`timescale 1ns/1ps
module t1i_uv_uart_loader_tb;
    localparam integer BIT_CYCLES=217;
    localparam [1391:0] SCENE_A=1392'h@@A@@;
    localparam [1391:0] SCENE_B=1392'h@@B@@;
    localparam [1391:0] SCENE_C=1392'h@@C@@;
    reg clk=0, rst_n=0, uart_rx=1, frame_start=0;
    wire [7:0] rx_byte;
    wire rx_valid, frame_err;
    wire [1391:0] active_scene, candidate_scene;
    wire commit_pending;
    integer failures=0, received=0, frame_errors=0, i;

    always #20 clk=~clk;
    always @(posedge clk) begin
        if (rx_valid) received=received+1;
        if (frame_err) frame_errors=frame_errors+1;
    end

    spu_uart_rx #(.CLK_HZ(25_000_000),.BAUD(115200)) u_uart (
        .clk(clk),.rst_n(rst_n),.rx(uart_rx),.data(rx_byte),
        .valid(rx_valid),.frame_err(frame_err));
    spu_scene_loader #(.SCENE_BITS(1392),.PAYLOAD_BYTES(174)) u_loader (
        .clk(clk),.rst_n(rst_n),.rx_byte(rx_byte),.rx_valid(rx_valid),
        .activate_raw_bank(frame_start),.active_scene(active_scene),
        .candidate_scene(candidate_scene),.commit_pending(commit_pending));

    task send_byte(input [7:0] value);
        integer bit_index;
        begin
            uart_rx=0;
            repeat(BIT_CYCLES) @(negedge clk);
            for(bit_index=0;bit_index<8;bit_index=bit_index+1) begin
                uart_rx=value[bit_index];
                repeat(BIT_CYCLES) @(negedge clk);
            end
            uart_rx=1;
            repeat(BIT_CYCLES) @(negedge clk);
        end
    endtask

    task send_scene(input [1391:0] scene);
        begin
            send_byte(8'hA5);
            for(i=0;i<174;i=i+1) send_byte(scene[i*8+:8]);
        end
    endtask

    task check_activate(input [1391:0] old_scene,input [1391:0] scene);
        begin
            if(candidate_scene!==scene || !commit_pending || active_scene!==old_scene) begin
                failures=failures+1;
                $display("FAIL: UART packet reconstruction or pending bank mismatch");
            end
            @(negedge clk);frame_start=1;
            @(posedge clk);#0.1;frame_start=0;
            if(active_scene!==scene || commit_pending) begin
                failures=failures+1;
                $display("FAIL: activation bank mismatch");
            end
        end
    endtask

    initial begin
        repeat(4) @(negedge clk);rst_n=1;
        send_scene(SCENE_A);check_activate(1392'd0,SCENE_A);
        send_scene(SCENE_B);check_activate(SCENE_A,SCENE_B);
        send_scene(SCENE_C);check_activate(SCENE_B,SCENE_C);
        send_scene(SCENE_A);check_activate(SCENE_C,SCENE_A);
        if(received!=700 || frame_errors!=0) begin
            failures=failures+1;
            $display("FAIL: UART counts bytes=%0d frame_errors=%0d",received,frame_errors);
        end
        if(failures==0) $display("PASS: T1i 115200 8N1 A/B/C/A bytes, banks, and return-A payload");
        else $display("FAIL: T1i UART loader failures=%0d",failures);
        $finish;
    end
    initial begin #200000000;$display("FAIL: UART loader timeout");$finish;end
endmodule
"""


def fixture_scene(name: str) -> str:
    fixture_name, expected_hash = FIXTURES[name]
    wire = bytes.fromhex((ROOT / "fixtures" / fixture_name).read_text().strip())
    if len(wire) != 175 or wire[0] != 0xA5:
        raise AssertionError(f"{fixture_name}: invalid frozen transaction")
    digest = hashlib.sha256(wire).hexdigest()
    if digest != expected_hash:
        raise AssertionError(f"{fixture_name}: hash {digest} != {expected_hash}")
    return f"{int.from_bytes(wire[1:], 'little'):0348x}"


def main() -> int:
    bench = TB.replace("@@A@@", fixture_scene("A"))
    bench = bench.replace("@@B@@", fixture_scene("B"))
    bench = bench.replace("@@C@@", fixture_scene("C"))
    rtl = [
        "hardware/rtl/peripherals/whisper/spu_uart_rx.v",
        "hardware/rtl/gpu/spu_scene_loader.v",
    ]
    with tempfile.TemporaryDirectory(prefix="spu_t1i_uv_uart_") as directory:
        temp = Path(directory)
        source, binary = temp / "uart_loader_tb.v", temp / "uart_loader_tb.vvp"
        source.write_text(bench)
        compile_result = subprocess.run(
            ["iverilog", "-g2012", "-s", "t1i_uv_uart_loader_tb", "-o", str(binary),
             str(source), *[str(ROOT / item) for item in rtl]],
            cwd=ROOT, text=True, capture_output=True, check=False)
        if compile_result.returncode:
            print(compile_result.stderr)
            return 1
        result = subprocess.run(["vvp", str(binary)], cwd=ROOT, text=True,
                                capture_output=True, check=False, timeout=60)
    if result.returncode or "PASS: T1i 115200 8N1 A/B/C/A" not in result.stdout:
        print(result.stdout)
        print(result.stderr)
        return 1
    print("PASS: frozen T1i A/B/C/A packets decode and activate exactly through UART RX")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
