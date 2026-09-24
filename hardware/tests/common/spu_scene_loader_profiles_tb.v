`timescale 1ns/1ps

module spu_scene_loader_profile_case #(
    parameter integer PAYLOAD_BYTES = 63,
    parameter integer SCENE_BITS = PAYLOAD_BYTES * 8
) (
    input wire clk,
    output reg done = 1'b0,
    output reg failed = 1'b0
);
    reg rst_n = 1'b0;
    reg [7:0] rx_byte = 8'd0;
    reg rx_valid = 1'b0;
    reg activate_raw_bank = 1'b0;
    wire [SCENE_BITS-1:0] active_scene;
    wire [SCENE_BITS-1:0] candidate_scene;
    wire commit_pending;
    reg [SCENE_BITS-1:0] expected_scene;
    integer i;

    spu_scene_loader #(
        .SCENE_BITS(SCENE_BITS),
        .PAYLOAD_BYTES(PAYLOAD_BYTES)
    ) dut (
        .clk(clk), .rst_n(rst_n), .rx_byte(rx_byte), .rx_valid(rx_valid),
        .activate_raw_bank(activate_raw_bank), .active_scene(active_scene),
        .candidate_scene(candidate_scene), .commit_pending(commit_pending)
    );

    task send_byte(input [7:0] value);
        begin
            @(negedge clk); rx_byte=value; rx_valid=1'b1;
            @(negedge clk); rx_byte=0; rx_valid=1'b0;
        end
    endtask

    task fail(input [8*96-1:0] label);
        begin
            failed=1'b1;
            $display("FAIL: %0s payload=%0d count=%0d pending=%b",
                label, PAYLOAD_BYTES, dut.payload_count, commit_pending);
        end
    endtask

    initial begin
        expected_scene=0;
        for (i=0;i<PAYLOAD_BYTES;i=i+1)
            expected_scene[i*8 +: 8]=i[7:0];
        repeat(2) @(negedge clk);
        rst_n=1'b1;
        send_byte(8'hA5);

        // One-under boundary: no candidate may commit before its final byte.
        for (i=0;i<PAYLOAD_BYTES-1;i=i+1) begin
            send_byte(i[7:0]);
            if (commit_pending || !dut.receiving ||
                dut.payload_count !== i+1)
                fail("early or missing payload progress before final byte");
        end
        if (commit_pending || dut.payload_count !== PAYLOAD_BYTES-1)
            fail("one-under payload boundary");

        // Exact boundary: the configured final byte commits, in order.
        send_byte((PAYLOAD_BYTES-1) & 8'hff);
        if (!commit_pending || dut.receiving || dut.payload_count !== 0)
            fail("exact payload completion boundary");
        if (candidate_scene !== expected_scene)
            fail("payload byte order or scene reconstruction");

        // One-over boundary: pending loader ignores the next byte.
        send_byte(8'h5A);
        if (!commit_pending || candidate_scene !== expected_scene)
            fail("one-over byte changed a completed candidate");

        done=1'b1;
    end
endmodule

module spu_scene_loader_profiles_tb;
    reg clk=1'b0;
    wire done63, done126, done150, done174;
    wire fail63, fail126, fail150, fail174;

    spu_scene_loader_profile_case #(.PAYLOAD_BYTES(63), .SCENE_BITS(504)) p63
        (.clk(clk), .done(done63), .failed(fail63));
    spu_scene_loader_profile_case #(.PAYLOAD_BYTES(126), .SCENE_BITS(1008)) p126
        (.clk(clk), .done(done126), .failed(fail126));
    spu_scene_loader_profile_case #(.PAYLOAD_BYTES(150), .SCENE_BITS(1200)) p150
        (.clk(clk), .done(done150), .failed(fail150));
    spu_scene_loader_profile_case #(.PAYLOAD_BYTES(174), .SCENE_BITS(1392)) p174
        (.clk(clk), .done(done174), .failed(fail174));

    always #5 clk=~clk;

    initial begin
        wait(done63 && done126 && done150 && done174);
        if (fail63 || fail126 || fail150 || fail174)
            $display("FAIL: scene loader profile boundary regression");
        else
            $display("PASS: scene loader 63/126/150/174-byte exact, one-under, and one-over boundaries");
        $finish;
    end
endmodule
