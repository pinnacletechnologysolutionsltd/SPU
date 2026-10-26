`timescale 1ns/1ps
module pade_eval_debug_tb;
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

    integer c;
    integer seen_ref;
    integer seen_local;
    integer failures;

    initial begin
        x_q32 = 64'sh0000000100000000; // 1.0
        seen_ref = 0;
        seen_local = 0;
        failures = 0;
        #50;
        // fire start and tick clocks, printing internal states each cycle
        start = 1;
        repeat (5) @(posedge clk);
        start = 0;
        // The local polynomial path completes quickly, but the reference
        // multi-cycle evaluator needs more than 12 cycles.  Keep enough trace
        // window to observe both completion pulses.
        for (c = 0; c < 40; c = c + 1) begin
            @(posedge clk);
            if (done_ref) seen_ref = 1;
            if (done_local) seen_local = 1;
            $display("C=%0d time=%0t ref_state=%0d ref_acc_num=%0d ref_mult=%0h ref_acc_den=%0d ref_tmp_numer=%0d ref_quot=%0d ref_exp=%0d done_ref=%b", c, $time, dut_ref.state, dut_ref.acc_num, dut_ref.mult_tmp, dut_ref.acc_den, dut_ref.tmp_numer, dut_ref.tmp_quot, dut_ref.exp_q16, done_ref);
            $display("C=%0d time=%0t loc_state=%0d loc_acc_num=%0d loc_poly3=%0d poly2=%0d poly1=%0d poly0=%0d loc_acc_den=%0d polyd3=%0d polyd2=%0d polyd1=%0d polyd0=%0d loc_exp=%0d done_loc=%b", c, $time, dut_local.state, dut_local.acc_num, dut_local.poly_num_out_3, dut_local.poly_num_out_2, dut_local.poly_num_out_1, dut_local.poly_num_out_0, dut_local.acc_den, dut_local.poly_den_out_3, dut_local.poly_den_out_2, dut_local.poly_den_out_1, dut_local.poly_den_out_0, dut_local.exp_q16, done_local);
        end
        $display("TRACE_DONE");
        if (!seen_ref || !seen_local) begin
            $display("FAIL: debug trace did not observe both done pulses");
            failures = failures + 1;
        end
        if (exp_ref !== exp_local) begin
            $display("FAIL: debug reference/local mismatch ref=%0d local=%0d",
                     exp_ref, exp_local);
            failures = failures + 1;
        end
        if (failures == 0) begin
            $display("PASS");
            $finish;
        end else begin
            $display("FAIL: %0d debug check(s)", failures);
            $finish(1);
        end
    end
endmodule
