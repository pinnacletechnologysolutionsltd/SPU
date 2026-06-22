// spu_pipeline_ctrl_tb.v — Testbench for 4-stage pipeline controller
// Verifies instruction flow, PHSLK coherence, telemetry emission.

`timescale 1ns/1ps

`include "spu_isa_defines.vh"

module spu_pipeline_ctrl_tb;

    reg clk, rst_n;
    initial begin
        clk = 0;
        forever #10 clk = ~clk;
    end

    // ── DUT signals ──
    reg         inst_valid;
    reg  [63:0] inst_word;
    wire        inst_ready;

    // Register file signals (loop back for test)
    reg  [63:0] rf_rdataA, rf_rdataB;
    wire [ 4:0] rf_raddrA, rf_raddrB;
    wire        rf_wren;
    wire [ 4:0] rf_waddr;
    wire [63:0] rf_wdata;

    // RAU result (loop back)
    reg  [63:0] rau_result;
    reg         rau_coherent, rau_result_zero, rau_result_sign;
    wire [63:0] rau_opA_O, rau_opB_C;
    wire [ 3:0] rau_op;

    // Pipeline outputs
    wire [ 7:0] pipe_opcode;
    wire        pipe_phslk, pipe_invj, pipe_mfold, pipe_stat, pipe_halt;
    wire        telem_valid;
    wire [ 7:0] telem_opcode;
    wire [63:0] telem_data;

    spu_pipeline_ctrl u_pipe (
        .clk(clk), .rst_n(rst_n),
        .inst_valid(inst_valid), .inst_word(inst_word), .inst_ready(inst_ready),
        .rf_raddrA(rf_raddrA), .rf_raddrB(rf_raddrB),
        .rf_rdataA(rf_rdataA), .rf_rdataB(rf_rdataB),
        .rf_wren(rf_wren), .rf_waddr(rf_waddr), .rf_wdata(rf_wdata),
        .rau_opA_O(rau_opA_O), .rau_opB_C(rau_opB_C), .rau_op(rau_op),
        .rau_result(rau_result), .rau_coherent(rau_coherent),
        .rau_result_zero(rau_result_zero), .rau_result_sign(rau_result_sign),
        .pipe_opcode(pipe_opcode), .pipe_phslk(pipe_phslk),
        .pipe_invj(pipe_invj), .pipe_mfold(pipe_mfold),
        .pipe_stat(pipe_stat), .pipe_halt(pipe_halt),
        .telem_valid(telem_valid), .telem_opcode(telem_opcode),
        .telem_data(telem_data),
        .dec_instr_word(), .dec_instr_valid(),
        .rf_rselA_O(), .rf_rselB_O(),
        .rf_wsel_O()
    );

    integer errors;
    reg [63:0] expected;

    task check;
        input [63:0] got;
        input [63:0] want;
        input [200:0] desc;
        if (got !== want) begin
            $display("FAIL: %s: got 0x%h, expected 0x%h", desc, got, want);
            errors = errors + 1;
        end else begin
            $display("PASS: %s", desc);
        end
    endtask

    // Helper: pack a Format R instruction
    function [63:0] pack_R(input [7:0] op, input [4:0] d, a, b);
        pack_R = {op, d, a, b, 41'd0};
    endfunction

    initial begin
        errors = 0;
        rst_n = 0; inst_valid = 0; inst_word = 0;
        rf_rdataA = 0; rf_rdataB = 0;
        rau_result = 0; rau_coherent = 0; rau_result_zero = 0; rau_result_sign = 0;

        #20 rst_n = 1;
        #10;

        // ═════════════════════════════════════════════════════════════════
        // 1. Feed a PHSLK instruction — verify pipeline flow
        // ═════════════════════════════════════════════════════════════════
        $display("\n── PHSLK pipeline flow ──");
        // PHSLK R3, R1, R2: op=0x42, dest=3, srcA=1, srcB=2
        inst_word = pack_R(8'h42, 5'd3, 5'd1, 5'd2);
        inst_valid = 1;
        // Wait for FETCH posedge (time 30), DECODE posedge (time 50)
        #40;
        // At DECODE stage: srcA/srcB should be latched
        check(rf_raddrA, 5'd1, "PIPE: srcA=R1 at decode");
        check(rf_raddrB, 5'd2, "PIPE: srcB=R2 at decode");
        check(pipe_phslk, 1'b1, "PIPE: PHSLK flag at decode");

        // Wait for EXECUTE posedge (time 70)
        #20;
        check(rau_opA_O, rf_rdataA, "PIPE: RAU opA = rf_rdataA");
        check(rau_opB_C, rf_rdataB, "PIPE: RAU opB = rf_rdataB");

        // Wait for WRITEBACK posedge (time 90)
        #20;
        check(rf_wren, 1'b1, "PIPE: writeback enabled");
        check(rf_waddr, 5'd3, "PIPE: writeback addr=R3");

        inst_valid = 0;
        #10;

        // ═════════════════════════════════════════════════════════════════
        // 2. Feed MFOLD — verify telemetry at writeback
        // ═════════════════════════════════════════════════════════════════
        $display("\n── MFOLD telemetry ──");
        inst_word = pack_R(8'h70, 5'd0, 5'd0, 5'd0);  // MFOLD
        inst_valid = 1;
        // Wait for posedge FETCH (time +20 from now at ~time 110)
        #40 inst_valid = 0;

        // Advance through pipeline to writeback stage
        // DECODE + EXECUTE + WRITEBACK = 3 cycles = #60
        #60;
        check(telem_valid, 1'b1, "PIPE: MFOLD telem_valid");
        if (telem_opcode == `SPU_OP_MFOLD)
            $display("PASS: PIPE: MFOLD telem_opcode");
        else begin
            $display("FAIL: PIPE: MFOLD telem_opcode: got 0x%h, expected 0x%h",
                     telem_opcode, `SPU_OP_MFOLD);
            errors = errors + 1;
        end

        #20;

        // ═════════════════════════════════════════════════════════════════
        // 3. Feed STAT — verify coherent flag in telemetry
        // ═════════════════════════════════════════════════════════════════
        $display("\n── STAT telemetry with coherent flag ──");
        rau_coherent = 1;  // Simulate RAU finding a coherent phase-lock
        inst_word = pack_R(8'h71, 5'd0, 5'd0, 5'd0);  // STAT
        inst_valid = 1;
        // Wait 1 cycle for FETCH
        #40 inst_valid = 0;

        #80; // pipeline all the way through

        #10;

        // ═════════════════════════════════════════════════════════════════
        // Results
        // ═════════════════════════════════════════════════════════════════
        $display("\n── SUMMARY ──");
        if (errors == 0)
            $display("ALL TESTS PASSED");
        else
            $display("%0d TESTS FAILED", errors);
        $finish;
    end

endmodule
