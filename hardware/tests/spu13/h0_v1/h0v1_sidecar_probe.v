// h0v1_sidecar_probe.v - H0-V1 directed instruction-acceptance probe (PRESERVED EVIDENCE, not a regression gate).
// Exercises spu13_rplu2_pade_sidecar busy handling; read-only hierarchical observers; core-level stimulus, NOT the SPI transport.
// Run: python3 hardware/tests/spu13/h0_v1/run_h0_v1.py ; see docs/isa/ISA_V02_H0V1_FINDINGS.md.
// The file name deliberately avoids 'tb' so run_all_tests.py does not auto-discover it.
// a31r2_sidecar_probe.v - A31-R2 directed refusal-path probe (PRESERVED EVIDENCE, not a regression gate).
// Derived from hardware/tests/spu13/spu13_rplu2_pade_sidecar_tb.v; read-only hierarchical observers added.
// Run: python3 hardware/tests/spu13/a31_r2/run_a31_r2.py ; see docs/isa/ISA_V02_A31R2_FINDINGS.md.
// The file name deliberately avoids 'tb' so run_all_tests.py does not auto-discover it.
`timescale 1ns / 1ps

// spu13_rplu2_pade_sidecar_tb.v - coreless Artix Padé sidecar smoke test.

module h0v1_sidecar_probe #(parameter FIRST_FAIL=0,
    parameter USE_STRUCTURED_INVERTER = 0,
    parameter STRUCTURED_INVERTER_SEQUENTIAL = 0,
    parameter PADE_PIPELINED = 0
);

    reg clk = 1'b0;
    reg rst_n = 1'b0;
    always #5 clk = ~clk;

    reg         inst_valid = 1'b0;
    reg [63:0] inst_word = 64'd0;
    reg         cfg_wr_en = 1'b0;
    reg [2:0]   cfg_sel = 3'd0;
    reg [9:0]   cfg_addr = 10'd0;
    reg [63:0]  cfg_data = 64'd0;

    wire inst_claimed;
    wire busy;
    wire error;
    wire qr_commit_valid;
    wire [3:0] qr_commit_lane;
    wire [63:0] qr_commit_A;
    wire [63:0] qr_commit_B;
    wire [63:0] qr_commit_C;
    wire [63:0] qr_commit_D;
    wire [7:0] debug_status;
    wire [2:0] debug_state;

    integer errors = 0;
    integer wait_i;
    reg seen_claim;
    reg seen_done;
    reg seen_qr_commit;
    reg error_seen;
    reg [3:0] qr_lane_seen;
    reg [63:0] qr_A_seen;
    reg [63:0] qr_B_seen;
    reg [63:0] qr_C_seen;
    reg [63:0] qr_D_seen;

    localparam [2:0] CFG_PADE_NUM = 3'd1;
    localparam [2:0] CFG_BTU_ROW  = 3'd3; localparam [2:0] CFG_PADE_DEN = 3'd2;

    spu13_rplu2_pade_sidecar #(
        .USE_STRUCTURED_INVERTER(USE_STRUCTURED_INVERTER),
        .STRUCTURED_INVERTER_SEQUENTIAL(STRUCTURED_INVERTER_SEQUENTIAL),
        .PADE_PIPELINED(PADE_PIPELINED)
    ) uut (
        .clk(clk),
        .rst_n(rst_n),
        .inst_valid(inst_valid),
        .inst_word(inst_word),
        .inst_claimed(inst_claimed),
        .busy(busy),
        .error(error),
        .cfg_wr_en(cfg_wr_en),
        .cfg_sel(cfg_sel),
        .cfg_addr(cfg_addr),
        .cfg_data(cfg_data),
        .qr_commit_valid(qr_commit_valid),
        .qr_commit_lane(qr_commit_lane),
        .qr_commit_A(qr_commit_A),
        .qr_commit_B(qr_commit_B),
        .qr_commit_C(qr_commit_C),
        .qr_commit_D(qr_commit_D),
        .debug_status(debug_status),
        .debug_state(debug_state)
    );

    function [63:0] pack;
        input [7:0] op;
        input [7:0] r1;
        input [7:0] r2;
        input [15:0] p1_a;
        input [15:0] p1_b;
        begin
            pack = {op, r1, r2, p1_a, p1_b, 8'd0};
        end
    endfunction

    task cfg_write;
        input [2:0] sel;
        input [9:0] addr;
        input [63:0] data;
        begin
            @(negedge clk);
            cfg_sel = sel;
            cfg_addr = addr;
            cfg_data = data;
            cfg_wr_en = 1'b1;
            @(negedge clk);
            cfg_wr_en = 1'b0;
            cfg_sel = 3'd0;
            cfg_addr = 10'd0;
            cfg_data = 64'd0;
        end
    endtask

    task issue_pulse;
        input [63:0] word;
        begin
            @(negedge clk);
            inst_word = word;
            inst_valid = 1'b1;
            seen_claim = seen_claim || inst_claimed;
            @(posedge clk);
            seen_claim = seen_claim || inst_claimed;
            @(negedge clk);
            inst_valid = 1'b0;
            inst_word = 64'd0;
        end
    endtask



    integer cyc = 0, n_err = 0, n_commit = 0, n_done = 0, n_claim = 0, c_done = -1, c_first_commit = -1;
    reg logging = 0, verbose = 0, busy_seen_hi = 0;
    always @(posedge clk) if (logging) begin
        cyc <= cyc + 1;
        if (error) begin n_err <= n_err + 1; if (verbose) $display("  c=%0d error pulse", cyc); end
        if (qr_commit_valid) begin n_commit <= n_commit + 1; if (c_first_commit < 0) c_first_commit <= cyc;
            if (verbose) $display("  c=%0d commit lane=%0d A=%h", cyc, qr_commit_lane, qr_commit_A[31:0]); end
        if (uut.pade_done) begin n_done <= n_done + 1; c_done <= cyc; if (verbose) $display("  c=%0d pade_done", cyc); end
        if (inst_claimed) n_claim <= n_claim + 1;
        if (busy) busy_seen_hi <= 1;
    end
    task clear_counts; begin cyc = 0; n_err = 0; n_commit = 0; n_done = 0; n_claim = 0; c_done = -1; c_first_commit = -1; busy_seen_hi = 0; end endtask
    task do_setup; begin
        logging = 0; rst_n = 0; inst_valid = 0; repeat (4) @(posedge clk); rst_n <= 1; repeat (4) @(posedge clk);
        cfg_write(CFG_PADE_NUM, 10'd0, {32'd0, 32'd2}); cfg_write(CFG_PADE_NUM, 10'd8, 64'd0);
        cfg_write(CFG_BTU_ROW, 10'd1, {32'd0, 32'd1}); cfg_write(CFG_BTU_ROW, 10'd65, 64'd0); end endtask
    task run2; input [63:0] w1, w2; input integer gap, settle; integer c; begin
        clear_counts; logging = 1;
        if (gap == 1) $display("   NOTE gap=1: consecutive strobes hold inst_valid high (continuous-valid); not an independent collision");
        for (c = 0; c < settle; c = c + 1) begin
            @(posedge clk);
            inst_valid <= (c == 0) || (gap >= 1 && c == gap);
            inst_word  <= (c == 0) ? w1 : w2;
        end
        @(posedge clk); inst_valid <= 0; logging = 0; end endtask
    integer g;
    initial begin
        $display("== SC0 baseline single 0x2A");
        do_setup; verbose = 1; run2(pack(8'h2A, 8'd4, 8'd0, 16'd0, 16'd0), 64'd0, -1, 400); verbose = 0;
        $display("RES sidecar single claim=%0d err=%0d commit=%0d pade_done_cycle=%0d busy_end=%0d", n_claim, n_err, n_commit, c_done, busy);
        $display("== SC1 second 0x2A at gap g (first accept c=1)");
        for (g = 1; g <= 7; g = g + 1) begin do_setup;
            run2(pack(8'h2A, 8'd4, 8'd0, 16'd0, 16'd0), pack(8'h2A, 8'd5, 8'd0, 16'd0, 16'd0), g, 1500);
            $display("RES sidecar 2A+2A gap=%0d claim=%0d err=%0d commits=%0d done=%0d%s", g, n_claim, n_err, n_commit, n_done,
                     (n_commit == 1 && n_err == 1) ? "  (second rejected with error pulse)" : ((n_commit == 2) ? "  (both executed)" : "  <-- see detail")); end
        for (g = 10; g <= 200; g = g + 95) begin do_setup; verbose = 1;
            run2(pack(8'h2A, 8'd4, 8'd0, 16'd0, 16'd0), pack(8'h2A, 8'd5, 8'd0, 16'd0, 16'd0), g, 1500); verbose = 0;
            $display("RES sidecar 2A+2A gap=%0d claim=%0d err=%0d commits=%0d done=%0d", g, n_claim, n_err, n_commit, n_done); end
        $display("== SC2 second 0x2A just after completion");
        for (g = 112; g <= 122; g = g + 1) begin do_setup;
            run2(pack(8'h2A, 8'd4, 8'd0, 16'd0, 16'd0), pack(8'h2A, 8'd5, 8'd0, 16'd0, 16'd0), g, 1500);
            $display("RES sidecar 2A+2A gap=%0d claim=%0d err=%0d commits=%0d done=%0d", g, n_claim, n_err, n_commit, n_done); end
        $finish;
    end
endmodule
