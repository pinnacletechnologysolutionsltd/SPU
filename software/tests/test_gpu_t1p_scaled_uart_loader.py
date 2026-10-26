#!/usr/bin/env python3
"""Check exact scaled T1p A/B/C/A packets through UART RX and scene banks."""

import hashlib
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "fixtures/gpu_t1i_scene_a_wire_175b.hex"
SOURCE_SHA256 = "8077acb3efbb92756fdee4c137500417e32f6f3664784c3b21f150c398d0dae9"
SELECTORS = tuple(bytes.fromhex(value) for value in
                  ("CCCCCCCC", "898EAAD9", "BDD88EF8", "CCCCCCCC"))

TB = r"""
`timescale 1ns/1ps
module t1p_scaled_uart_loader_tb;
    localparam integer BIT_CYCLES=217;
    localparam [1455:0] A=1456'h@@A@@;
    localparam [1455:0] B=1456'h@@B@@;
    localparam [1455:0] C=1456'h@@C@@;
    reg clk=0, rst_n=0, uart_rx=1, frame_start=0;
    wire [7:0] rx_byte;
    wire rx_valid, frame_err;
    wire [1455:0] active_scene, candidate_scene;
    wire commit_pending;
    integer failures=0, received=0, errors=0, i;

    always #20 clk=~clk;
    always @(posedge clk) begin
        if (rx_valid) received=received+1;
        if (frame_err) errors=errors+1;
    end
    spu_uart_rx #(.CLK_HZ(25_000_000),.BAUD(115200)) u_uart (
        .clk(clk),.rst_n(rst_n),.rx(uart_rx),.data(rx_byte),
        .valid(rx_valid),.frame_err(frame_err));
    spu_scene_loader #(.SCENE_BITS(1456),.PAYLOAD_BYTES(182),
        .VALIDATE_WINDOW_START(174),.VALIDATE_WINDOW_BYTES(4),
        .FINAL_BYTE_MAX(8'h05)) u_loader (
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

    task send_scene(input [1455:0] scene);
        begin
            send_byte(8'hA5);
            for(i=0;i<182;i=i+1) send_byte(scene[i*8+:8]);
        end
    endtask

    task check_activate(input [1455:0] old_scene,input [1455:0] scene);
        begin
            if(candidate_scene!==scene || !commit_pending || active_scene!==old_scene) begin
                failures=failures+1;
                $display("FAIL: pending T1p packet/bank mismatch");
            end
            @(negedge clk);frame_start=1;
            @(posedge clk);#0.1;frame_start=0;
            if(active_scene!==scene || commit_pending) begin
                failures=failures+1;
                $display("FAIL: T1p activation/return mismatch");
            end
        end
    endtask

    initial begin
        repeat(4) @(negedge clk);rst_n=1;
        send_scene(A);check_activate(1456'd0,A);
        send_scene(B);check_activate(A,B);
        send_scene(C);check_activate(B,C);
        send_scene(A);check_activate(C,A);
        if(received!=732 || errors!=0) begin
            failures=failures+1;
            $display("FAIL: T1p UART bytes=%0d frame_errors=%0d",received,errors);
        end
        if(failures==0) $display("PASS: exact scaled T1p UART A/B/C/A bank return");
        else $display("FAIL: scaled T1p UART failures=%0d",failures);
        $finish;
    end
    initial begin #100000000;$display("FAIL: scaled T1p UART timeout");$finish;end
endmodule
"""


def main():
    source = bytes.fromhex(FIXTURE.read_text())
    assert hashlib.sha256(source).hexdigest() == SOURCE_SHA256
    scene = int.from_bytes(source[1:], "little")
    for lane in range(4):
        for edge in range(3):
            bit = lane * 348 + edge * 64 + 32
            raw = (scene >> bit) & 0xFFFFFFFF
            signed = raw if raw < (1 << 31) else raw - (1 << 32)
            scaled = signed * 4
            assert -(1 << 31) <= scaled < (1 << 31)
            scene = (scene & ~(0xFFFFFFFF << bit)) | ((scaled & 0xFFFFFFFF) << bit)
    wire = b"\xA5" + scene.to_bytes(174, "little")
    assert hashlib.sha256(wire).hexdigest() == "1b6b066639da98f914f3e8512150656631dd7a55e18b6a1f65b9b7f222ca66df"
    packets = [wire + bytes((2, 2, 2, 2)) + selectors for selectors in SELECTORS]
    assert packets[0] == packets[-1] and all(len(packet) == 183 for packet in packets)
    bench = TB
    for label, packet in zip("ABCA", packets):
        bench = bench.replace("@@" + label + "@@", f"{int.from_bytes(packet[1:], 'little'):0364x}", 1)
    with tempfile.TemporaryDirectory(prefix="spu_t1p_scaled_uart_") as directory:
        root = Path(directory)
        source, executable = root / "tb.v", root / "tb.vvp"
        source.write_text(bench)
        subprocess.run(["iverilog", "-g2012", "-s", "t1p_scaled_uart_loader_tb",
                        "-o", str(executable), str(source),
                        str(ROOT / "hardware/rtl/peripherals/whisper/spu_uart_rx.v"),
                        str(ROOT / "hardware/rtl/gpu/spu_scene_loader.v")], check=True)
        output = subprocess.run(["vvp", str(executable)], capture_output=True,
                                text=True, check=True, timeout=60).stdout
    assert "PASS: exact scaled T1p UART A/B/C/A bank return" in output, output
    assert "FAIL:" not in output, output
    print(output.strip())


if __name__ == "__main__":
    main()
