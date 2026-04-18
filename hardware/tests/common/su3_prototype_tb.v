`timescale 1ns/1ps
module su3_prototype_tb;
    reg clk = 0;
    always #5 clk = ~clk;
    reg rst_n = 0;
    initial begin #20 rst_n = 1; end

    // Pade evaluator (scalar exp)
    reg start_pade = 0;
    reg signed [63:0] x_q32;
    wire signed [31:0] exp_q16;
    wire done_pade;
    wire busy_pade;

    // runtime config placeholders
    reg cfg_wr_en = 1'b0;
    reg [2:0] cfg_wr_sel = 3'd0;
    reg [2:0] cfg_wr_addr = 3'd0;
    reg [63:0] cfg_wr_data = 64'd0;

    pade_eval_4_4 pade (
        .clk(clk), .rst_n(rst_n), .start(start_pade), .x_q32(x_q32),
        .cfg_wr_en(cfg_wr_en), .cfg_wr_sel(cfg_wr_sel), .cfg_wr_addr(cfg_wr_addr), .cfg_wr_data(cfg_wr_data),
        .exp_q16(exp_q16), .done(done_pade), .busy(busy_pade)
    );

    // SU(3) accel stub
    reg start_accel = 0;
    reg signed [31:0] g00,g01,g02,g10,g11,g12,g20,g21,g22;
    wire signed [31:0] e00,e01,e02,e10,e11,e12,e20,e21,e22;
    wire done_accel;
    wire busy_accel;

    su3_taylor_accel accel (
        .clk(clk), .rst_n(rst_n), .start(start_accel),
        .g00(g00), .g01(g01), .g02(g02),
        .g10(g10), .g11(g11), .g12(g12),
        .g20(g20), .g21(g21), .g22(g22),
        .e00(e00), .e01(e01), .e02(e02),
        .e10(e10), .e11(e11), .e12(e12),
        .e20(e20), .e21(e21), .e22(e22),
        .done(done_accel), .busy(busy_accel)
    );

    initial begin
        // small test: choose x = 0x0000000001000000 (Q32 ~ 2^-8)
        x_q32 = 64'h0000000001000000; // small scalar
        // convert to Q16 approx: x_q32 >> 16 => 256
        g00 = 32'sd256; g11 = 32'sd256; g22 = 32'sd256;
        g01 = 32'sd0; g02 = 32'sd0; g10 = 32'sd0; g12 = 32'sd0; g20 = 32'sd0; g21 = 32'sd0;

        #50;

        // Run Pade eval
        @(posedge clk);
        start_pade <= 1'b1; @(posedge clk); start_pade <= 1'b0;
        wait (done_pade == 1'b1);
        @(posedge clk);

        // Run accel stub
        @(posedge clk);
        start_accel <= 1'b1; @(posedge clk); start_accel <= 1'b0;
        wait (done_accel == 1'b1);
        @(posedge clk);

        $display("SU3_PROTOTYPE: exp_q16=%0d e00=%0d e11=%0d e22=%0d", exp_q16, e00, e11, e22);
        if (exp_q16 == e00 && exp_q16 == e11 && exp_q16 == e22) begin
            $display("SU3_PROTOTYPE_PASS");
        end else begin
            $display("SU3_PROTOTYPE_FAIL: exp=%0d e00=%0d e11=%0d e22=%0d", exp_q16, e00, e11, e22);
        end
        $finish;
    end
endmodule
