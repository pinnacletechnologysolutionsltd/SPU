`timescale 1ns/1ps
module spu_scene_loader_tb;
    reg clk = 1'b0;
    reg rst_n = 1'b0;
    reg [7:0] rx_byte = 8'h00;
    reg rx_valid = 1'b0;
    reg activate_raw_bank = 1'b0;
    wire [503:0] active_scene;
    wire [503:0] candidate_scene;
    wire commit_pending;
    localparam [503:0] SCENE_A = 504'hbbb8b5b2afaca9a6a3a09d9a9794918e8b8885827f7c797673706d6a6764615e5b5855524f4c494643403d3a3734312e2b2825221f1c191613100d0a070401;
    localparam [503:0] SCENE_B = 504'h3d38332e29241f1a15100b0601fcf7f2ede8e3ded9d4cfcac5c0bbb6b1aca7a29d98938e89847f7a75706b6661a557524d48433e39342f2a25201b16110c07;

    integer checks = 0;
    integer failures = 0;
    integer i;
    reg prior_active_bank;
    reg edge_was_eligible;

    spu_scene_loader dut (
        .clk(clk), .rst_n(rst_n), .rx_byte(rx_byte), .rx_valid(rx_valid),
        .activate_raw_bank(activate_raw_bank), .active_scene(active_scene),
        .candidate_scene(candidate_scene), .commit_pending(commit_pending));

    always #5 clk = ~clk;
    task check;
        input condition;
        input [8*72-1:0] label;
        begin
            checks = checks + 1;
            if (condition !== 1'b1) begin
                failures = failures + 1;
                $display("FAIL: %0s", label);
            end
        end
    endtask
    task send_byte;
        input [7:0] value;
        begin
            @(negedge clk); rx_byte = value; rx_valid = 1'b1;
            @(negedge clk); rx_valid = 1'b0; rx_byte = 8'h00;
        end
    endtask

    task send_payload;
        input [503:0] value;
        integer j;
        reg [503:0] held_active;
        begin
            held_active = active_scene;
            send_byte(8'hA5);
            for (j = 0; j < 63; j = j + 1) begin
                send_byte(value[j*8 +: 8]);
                check(active_scene === held_active,
                      "inactive write changed active scene");
                if (j < 62)
                    check(!commit_pending, "commit asserted before payload byte 63");
            end
        end
    endtask

    task pulse_frame;
        begin
            @(negedge clk); activate_raw_bank = 1'b1;
            @(negedge clk); activate_raw_bank = 1'b0;
        end
    endtask

    task reset_loader;
        begin
            @(negedge clk); rst_n = 1'b0;
            repeat (2) @(negedge clk);
            #1 rst_n = 1'b1;
            prior_active_bank = dut.active_bank;
            @(negedge clk);
        end
    endtask

    always @(posedge clk)
        edge_was_eligible <= rst_n && commit_pending && activate_raw_bank;

    always @(negedge clk) begin
        if (rst_n) begin
            check(active_scene === (dut.active_bank ? dut.scene_bank1 : dut.scene_bank0),
                  "active_scene must equal one complete bank");
            if (dut.active_bank != prior_active_bank)
                check(edge_was_eligible, "active bank changed without eligible frame_start");
            prior_active_bank = dut.active_bank;
        end
    end

    initial begin
        edge_was_eligible = 1'b0;
        prior_active_bank = 1'b0;
        reset_loader();
        check(active_scene === 504'b0 && !commit_pending, "reset semantics");

        // N3: payload-like traffic without a start byte is ignored.
        send_byte(8'h11); send_byte(8'h22); send_byte(8'h5A);
        pulse_frame();
        check(active_scene === 504'b0 && !commit_pending && !dut.receiving,
              "N3 no-start traffic ignored");
        // P1: load and activate scene A through the normal path.
        send_payload(SCENE_A);
        check(active_scene === 504'b0 && commit_pending, "P1 completion defers A");
        check(candidate_scene === SCENE_A, "P1 candidate output reconstructs A");
        pulse_frame();
        check(active_scene === SCENE_A && !commit_pending, "P1 scene A activates exactly");
        // N1: an incomplete B cannot commit at any frame boundary.
        send_byte(8'hA5);
        for (i = 0; i < 17; i = i + 1) send_byte(SCENE_B[i*8 +: 8]);
        pulse_frame(); pulse_frame();
        check(active_scene === SCENE_A && !commit_pending && dut.receiving,
              "N1 truncated packet never activates");
        // Reset abandons N1, then establish A normally again.
        reset_loader();
        send_payload(SCENE_A); pulse_frame();
        check(active_scene === SCENE_A, "A restored after truncated reset");
        // P2/N2/N4: B completes mid-frame; byte 17 is embedded A5 data.
        send_payload(SCENE_B);
        check(active_scene === SCENE_A && commit_pending,
              "P2 N2 completion cannot alter active A");
        check(candidate_scene === SCENE_B, "P2 candidate output reconstructs B");
        check((dut.active_bank ? dut.scene_bank0 : dut.scene_bank1) === SCENE_B,
              "N4 embedded A5 preserved in candidate B");
        // N5: pending state ignores every byte, including a start byte.
        send_byte(8'hA5); send_byte(8'hDE); send_byte(8'hAD);
        check((dut.active_bank ? dut.scene_bank0 : dut.scene_bank1) === SCENE_B,
              "N5 pending candidate cannot be overwritten");
        pulse_frame();
        check(active_scene === SCENE_B && !commit_pending, "P2 B activates atomically");
        // N6: complete A on a frame_start edge; it must wait for a later edge.
        send_byte(8'hA5);
        for (i = 0; i < 62; i = i + 1) send_byte(SCENE_A[i*8 +: 8]);
        @(negedge clk);
        rx_byte = SCENE_A[62*8 +: 8]; rx_valid = 1'b1; activate_raw_bank = 1'b1;
        @(negedge clk);
        rx_valid = 1'b0; activate_raw_bank = 1'b0; rx_byte = 8'h00;
        check(active_scene === SCENE_B && commit_pending,
              "N6 completion/frame collision cannot activate");
        pulse_frame();
        check(active_scene === SCENE_A && !commit_pending,
              "N6 candidate activates on later frame_start");
        if (failures == 0)
            $display("PASS: spu_scene_loader P1 P2 N1 N2 N3 N4 N5 N6 (%0d checks)", checks);
        else
            $display("FAIL: spu_scene_loader %0d/%0d checks failed", failures, checks);
        $finish;
    end
endmodule
