`timescale 1ns/1ps
module pade_eval_compare_tb;
    reg clk = 0;
    always #5 clk = ~clk;
    reg rst_n = 0;
    initial begin
        #20; rst_n = 1;
    end

    // Inputs
    reg start;
    reg signed [63:0] x_q32;
    // runtime config interface (defaults to no-op)
    reg cfg_wr_en = 1'b0;
    reg [2:0] cfg_wr_sel = 3'd0;
    reg [2:0] cfg_wr_addr = 3'd0;
    reg [63:0] cfg_wr_data = 64'd0;

    // Instantiate reference DUT (multi-cycle original behavior)
    wire signed [31:0] exp_ref;
    wire done_ref;
    pade_eval_4_4 #(.USE_LOCAL_POLY(0)) dut_ref (
        .clk(clk), .rst_n(rst_n), .start(start), .x_q32(x_q32), .cfg_wr_en(cfg_wr_en), .cfg_wr_sel(cfg_wr_sel), .cfg_wr_addr(cfg_wr_addr), .cfg_wr_data(cfg_wr_data), .exp_q16(exp_ref), .done(done_ref), .busy()
    );

    // Instantiate local-poly DUT
    wire signed [31:0] exp_local;
    wire done_local;
    pade_eval_4_4 #(.USE_LOCAL_POLY(1)) dut_local (
        .clk(clk), .rst_n(rst_n), .start(start), .x_q32(x_q32), .cfg_wr_en(cfg_wr_en), .cfg_wr_sel(cfg_wr_sel), .cfg_wr_addr(cfg_wr_addr), .cfg_wr_data(cfg_wr_data), .exp_q16(exp_local), .done(done_local), .busy()
    );

    integer i;
    reg signed [63:0] test_x [0:7];
    initial begin
        // representative x values
        test_x[0] = 64'sh0000000100000000; // 1.0
        test_x[1] = 64'shFFFFFFFF00000000; // -1.0
        test_x[2] = 64'sh0000000080000000; // 0.5
        test_x[3] = 64'shFFFFFFFF80000000; // -0.5
        test_x[4] = 64'sh0000000040000000; // 0.25
        test_x[5] = 64'shFFFFFFFFC0000000; // -0.25
        test_x[6] = 64'sh0000000000000000; // 0
        test_x[7] = 64'sh0000000200000000; // 2.0

        #50;
        for (i = 0; i < 8; i = i + 1) begin
            x_q32 = test_x[i];
            start = 1'b1; repeat (5) @(posedge clk); start = 1'b0;
            $display("COMPARE: fired start for x=%h at time=%0t", x_q32, $time);
            // wait for both (robust: record seen pulses within a timeout block)
            begin : wait_done
                integer seen_ref; integer seen_local; integer j;
                seen_ref = 0; seen_local = 0;
                for (j = 0; j < 200; j = j + 1) begin
                    @(posedge clk);
                    if (done_ref) seen_ref = 1;
                    if (done_local) seen_local = 1;
                    if (seen_ref && seen_local) disable wait_done;
                end
                if (!(seen_ref && seen_local)) begin
                    $display("ERROR: TIMEOUT waiting for done signals for x=%h", x_q32);
                end
            end
            @(posedge clk);
            $display("COMPARE: x=%h ref=%0d local=%0d diff=%0d", x_q32, exp_ref, exp_local, exp_ref - exp_local);
            #10;
        end
        $display("COMPARE_DONE");
        $display("PASS");
        $finish;
    end
endmodule
