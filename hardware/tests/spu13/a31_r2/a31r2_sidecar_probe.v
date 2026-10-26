// a31r2_sidecar_probe.v - A31-R2 directed refusal-path probe (PRESERVED EVIDENCE, not a regression gate).
// Derived from hardware/tests/spu13/spu13_rplu2_pade_sidecar_tb.v; read-only hierarchical observers added.
// Run: python3 hardware/tests/spu13/a31_r2/run_a31_r2.py ; see docs/isa/ISA_V02_A31R2_FINDINGS.md.
// The file name deliberately avoids 'tb' so run_all_tests.py does not auto-discover it.
`timescale 1ns / 1ps

// spu13_rplu2_pade_sidecar_tb.v - coreless Artix Padé sidecar smoke test.

module a31r2_sidecar_probe #(parameter FIRST_FAIL=0,
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


    always @(posedge clk) begin
        if (uut.pade_done)
            $display("EV t=%0t pade_done pade_flags_v=%b result_c=%h/%h/%h/%h", $time, uut.pade_flags_v,
                     uut.result_c0, uut.result_c1, uut.result_c2, uut.result_c3);
        if (error) $display("EV t=%0t sidecar error pulse", $time);
        if (qr_commit_valid)
            $display("EV t=%0t sidecar qr_commit_valid lane=%0d A=%h B=%h C=%h D=%h", $time,
                     qr_commit_lane, qr_commit_A, qr_commit_B, qr_commit_C, qr_commit_D);
    end
    task setden0; input [31:0] c0; input [31:0] c1; input [31:0] c2; input [31:0] c3;
        begin cfg_write(CFG_PADE_DEN, 10'd0, {c1, c0}); cfg_write(CFG_PADE_DEN, 10'd8, {c3, c2}); end endtask
    task txn; input [255:0] m; integer k;
        begin $display("---- %0s ----", m);
              issue_pulse(pack(8'h2A, 8'd4, 8'd0, 16'd0, 16'd0));
              for (k=0;k<1500;k=k+1) @(posedge clk); end endtask
    initial begin
        #30 rst_n = 1'b1;
        repeat (2) @(posedge clk);
        cfg_write(CFG_PADE_NUM, 10'd0, {32'd0, 32'd2});
        cfg_write(CFG_PADE_NUM, 10'd8, 64'd0);
        cfg_write(CFG_BTU_ROW, 10'd1, {32'd0, 32'd1});
        cfg_write(CFG_BTU_ROW, 10'd65, 64'd0);
        if (FIRST_FAIL==0) begin
            txn("A: success (den=1, num0=2)");
            setden0(32'h2CEE24B2,32'd0,32'd0,32'd1);
            txn("B: zero-divisor after success");
            setden0(32'd1,32'd0,32'd0,32'd0);
            txn("C: recovery");
        end else begin
            setden0(32'h2CEE24B2,32'd0,32'd0,32'd1);
            txn("B0: zero-divisor first after rst");
        end
        $finish;
    end
endmodule
