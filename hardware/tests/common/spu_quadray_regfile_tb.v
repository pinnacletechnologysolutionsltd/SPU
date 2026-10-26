// spu_quadray_regfile_tb.v — Quadray Register File Testbench
//
// Tests:
//   1. Read after reset: all lanes initialized to identity (A=1, B=C=D=0)
//   2. Write lane 5 with test vector, read back
//   3. Init lane 3 from bootloader hydration port
//   4. Consecutive writes to different lanes

`timescale 1ns / 1ps

module spu_quadray_regfile_tb;

    reg         clk, rst_n;
    reg  [3:0]  rd_lane;
    wire [63:0] rd_A, rd_B, rd_C, rd_D;
    reg         wr_en, init_en;
    reg  [3:0]  wr_lane, init_lane;
    reg  [63:0] wr_A, wr_B, wr_C, wr_D;
    reg  [63:0] init_A, init_B, init_C, init_D;
    wire [63:0] dbg_A, dbg_B, dbg_C, dbg_D;

    spu_quadray_regfile uut (
        .clk(clk), .rst_n(rst_n),
        .rd_lane(rd_lane), .rd_A(rd_A), .rd_B(rd_B), .rd_C(rd_C), .rd_D(rd_D),
        .wr_en(wr_en), .wr_lane(wr_lane), .wr_A(wr_A), .wr_B(wr_B), .wr_C(wr_C), .wr_D(wr_D),
        .init_en(init_en), .init_lane(init_lane),
        .init_A(init_A), .init_B(init_B), .init_C(init_C), .init_D(init_D),
        .dbg_A(dbg_A), .dbg_B(dbg_B), .dbg_C(dbg_C), .dbg_D(dbg_D)
    );

    always #5 clk = ~clk;

    integer pass, fail;

    task write_lane;
        input [3:0] lane;
        input [63:0] a, b, c, d;
        begin
            @(posedge clk);  // sync to clock edge first
            wr_en = 1; wr_lane = lane;
            wr_A = a; wr_B = b; wr_C = c; wr_D = d;
            @(posedge clk);
            wr_en = 0;
            @(posedge clk);
        end
    endtask

    task check_lane;
        input [255:0] name;
        input [3:0] lane;
        input [63:0] exp_A, exp_B, exp_C, exp_D;
        begin
            rd_lane = lane;
            #1;  // let combinational read settle
            if (rd_A === exp_A && rd_B === exp_B && rd_C === exp_C && rd_D === exp_D) begin
                $display("  PASS: %0s", name);
                pass = pass + 1;
            end else begin
                $display("  FAIL: %0s", name);
                $display("    A: got %h, expected %h", rd_A, exp_A);
                $display("    B: got %h, expected %h", rd_B, exp_B);
                $display("    C: got %h, expected %h", rd_C, exp_C);
                $display("    D: got %h, expected %h", rd_D, exp_D);
                fail = fail + 1;
            end
        end
    endtask

    initial begin
        clk = 0; rst_n = 0;
        rd_lane = 0; wr_en = 0; init_en = 0;
        pass = 0; fail = 0;

        @(posedge clk); rst_n = 1;
        @(posedge clk);

        $display("\n── Quadray Register File Tests ──");

        // Test 1: Reset state — all lanes identity
        check_lane("lane 0 reset", 0,
            64'h0000_0001_0000_0000, 64'h0, 64'h0, 64'h0);
        check_lane("lane 7 reset", 7,
            64'h0000_0001_0000_0000, 64'h0, 64'h0, 64'h0);

        // Test 2: Write lane 5
        write_lane(5,
            64'h0000_0000_0000_0000,  // A=0
            64'h0000_0002_0000_0001,  // B = 1 + 2√3
            64'h0000_0000_0000_0000,  // C=0
            64'h0000_0000_0000_0000); // D=0
        check_lane("lane 5 after write", 5,
            64'h0000_0000_0000_0000,
            64'h0000_0002_0000_0001,
            64'h0, 64'h0);
        check_lane("lane 0 unchanged", 0,
            64'h0000_0001_0000_0000, 64'h0, 64'h0, 64'h0);

        // Test 3: Init lane 3 (hydration)
        @(posedge clk);
        init_en = 1; init_lane = 3;
        init_A = 64'h0000_0000_0000_0000;
        init_B = 64'h0000_0007_0000_0004;  // 4 + 7√3 (Pell r²)
        init_C = 64'h0;
        init_D = 64'h0;
        @(posedge clk);
        init_en = 0;
        @(posedge clk);
        check_lane("lane 3 hydrated", 3,
            64'h0, 64'h0000_0007_0000_0004, 64'h0, 64'h0);

        // Test 4: Consecutive writes
        write_lane(0, 64'd1, 64'd2, 64'd3, 64'd4);
        write_lane(1, 64'd5, 64'd6, 64'd7, 64'd8);
        check_lane("lane 0: (1,2,3,4)", 0, 64'd1, 64'd2, 64'd3, 64'd4);
        check_lane("lane 1: (5,6,7,8)", 1, 64'd5, 64'd6, 64'd7, 64'd8);
        check_lane("lane 2 unchanged", 2,
            64'h0000_0001_0000_0000, 64'h0, 64'h0, 64'h0);

        repeat (2) @(posedge clk);

        $display("\n──────────────────────────────");
        $display("Results: %0d passed, %0d failed", pass, fail);
        if (fail == 0) begin
            $display("PASS");
            $finish;
        end else begin
            $display("FAIL");
            $finish;
        end
    end

endmodule
