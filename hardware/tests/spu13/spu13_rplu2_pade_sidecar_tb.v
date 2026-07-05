`timescale 1ns / 1ps

// spu13_rplu2_pade_sidecar_tb.v - coreless Artix Padé sidecar smoke test.

module spu13_rplu2_pade_sidecar_tb;

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
    localparam [2:0] CFG_BTU_ROW  = 3'd3;

    spu13_rplu2_pade_sidecar uut (
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

    initial begin
        #30 rst_n = 1'b1;
        repeat (2) @(posedge clk);

        // Padé numerator coefficient 0 = (2,0,0,0), denominator default is one.
        cfg_write(CFG_PADE_NUM, 10'd0, {32'd0, 32'd2});
        cfg_write(CFG_PADE_NUM, 10'd8, 64'd0);

        // Direct Padé sidecar uses BTU row 1 config as the saddle tuple.
        cfg_write(CFG_BTU_ROW, 10'd1, {32'd0, 32'd1});
        cfg_write(CFG_BTU_ROW, 10'd65, 64'd0);

        seen_claim = 1'b0;
        seen_done = 1'b0;
        seen_qr_commit = 1'b0;
        error_seen = 1'b0;
        qr_lane_seen = 4'd0;
        qr_A_seen = 64'd0;
        qr_B_seen = 64'd0;
        qr_C_seen = 64'd0;
        qr_D_seen = 64'd0;

        issue_pulse(pack(8'h2A, 8'd4, 8'd0, 16'd0, 16'd0));

        for (wait_i = 0; wait_i < 1200; wait_i = wait_i + 1) begin
            @(posedge clk);
            if (error)
                error_seen = 1'b1;
            if (uut.pade_done)
                seen_done = 1'b1;
            if (qr_commit_valid) begin
                seen_qr_commit = 1'b1;
                qr_lane_seen = qr_commit_lane;
                qr_A_seen = qr_commit_A;
                qr_B_seen = qr_commit_B;
                qr_C_seen = qr_commit_C;
                qr_D_seen = qr_commit_D;
            end
        end

        if (!seen_claim) begin
            $display("FAIL: Padé sidecar did not claim opcode 0x2A");
            errors = errors + 1;
        end
        if (!seen_done) begin
            $display("FAIL: Padé sidecar did not complete");
            errors = errors + 1;
        end
        if (error_seen) begin
            $display("FAIL: Padé sidecar asserted error");
            errors = errors + 1;
        end
        if (!seen_qr_commit || qr_lane_seen !== 4'd4 ||
            qr_A_seen !== 64'd2 || qr_B_seen !== 64'd0 ||
            qr_C_seen !== 64'd0 || qr_D_seen !== 64'd0) begin
            $display("FAIL: QR commit seen=%b lane=%0d A=%h B=%h C=%h D=%h",
                     seen_qr_commit, qr_lane_seen,
                     qr_A_seen, qr_B_seen, qr_C_seen, qr_D_seen);
            errors = errors + 1;
        end
        if (busy) begin
            $display("FAIL: Padé sidecar remained busy after evaluation");
            errors = errors + 1;
        end

        if (errors == 0)
            $display("PASS: spu13_rplu2_pade_sidecar_tb");
        else
            $display("FAIL: spu13_rplu2_pade_sidecar_tb (%0d errors)", errors);

        $finish;
    end

endmodule
