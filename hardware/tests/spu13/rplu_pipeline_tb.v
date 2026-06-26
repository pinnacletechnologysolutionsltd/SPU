`timescale 1ns / 1ps

// rplu_pipeline_tb.v - integration smoke test for RPLU v2 pipeline control.

module rplu_pipeline_tb;

    reg clk;
    reg rst_n;
    reg som_start;
    reg [143:0] som_features;

    wire som_done;
    wire [15:0] som_best_id;
    wire [15:0] som_cluster_label;
    wire [63:0] som_best_q;
    wire [31:0] thimble_c0, thimble_c1, thimble_c2, thimble_c3;
    wire thimble_valid;
    wire [31:0] quadray_delta;
    wire quadray_coherent;
    wire quadray_valid;
    wire pipeline_busy;
    wire pipeline_stall;

    rplu_pipeline uut (
        .clk(clk),
        .rst_n(rst_n),
        .som_features(som_features),
        .som_start(som_start),
        .som_done(som_done),
        .som_best_id(som_best_id),
        .som_cluster_label(som_cluster_label),
        .som_best_q(som_best_q),
        .pade_coeff_we(1'b0),
        .pade_coeff_is_den(1'b0),
        .pade_coeff_addr(3'd0),
        .pade_c0(32'd0),
        .pade_c1(32'd0),
        .pade_c2(32'd0),
        .pade_c3(32'd0),
        .quadray_target_kappa(32'd0),
        .thimble_c0(thimble_c0),
        .thimble_c1(thimble_c1),
        .thimble_c2(thimble_c2),
        .thimble_c3(thimble_c3),
        .thimble_valid(thimble_valid),
        .quadray_delta(quadray_delta),
        .quadray_coherent(quadray_coherent),
        .quadray_valid(quadray_valid),
        .pipeline_busy(pipeline_busy),
        .pipeline_stall(pipeline_stall)
    );

    always #5 clk = ~clk;

    integer cycle;
    integer valid_count;
    integer test_pass;
    integer test_total;
    reg busy_seen;
    reg result_ok;
    reg quadray_ok;

    task check;
        input ok;
        input [255:0] msg;
        begin
            test_total = test_total + 1;
            if (ok)
                test_pass = test_pass + 1;
            else
                $display("FAIL: %0s", msg);
        end
    endtask

    initial begin
        clk = 1'b0;
        rst_n = 1'b0;
        som_start = 1'b0;
        som_features = 144'd0;
        cycle = 0;
        valid_count = 0;
        test_pass = 0;
        test_total = 0;
        busy_seen = 1'b0;
        result_ok = 1'b0;
        quadray_ok = 1'b0;

        #30 rst_n = 1'b1;
        #20;

        som_start = 1'b1;
        #10;
        som_start = 1'b0;

        for (cycle = 0; cycle < 1500; cycle = cycle + 1) begin
            #10;
            if (pipeline_busy)
                busy_seen = 1'b1;
            if (quadray_valid && quadray_coherent && quadray_delta == 32'd0)
                quadray_ok = 1'b1;
            if (thimble_valid) begin
                valid_count = valid_count + 1;
                if (thimble_c0 == 32'd1 && thimble_c1 == 32'd0 &&
                    thimble_c2 == 32'd0 && thimble_c3 == 32'd0)
                    result_ok = 1'b1;
            end
        end

        check(busy_seen, "pipeline_busy asserted during launch");
        check(valid_count == 1, "single SOM launch produces exactly one thimble_valid pulse");
        check(result_ok, "default Padé coefficients return A31 one");
        check(quadray_ok, "zero BTU coordinates satisfy kappa-zero Quadray variety");
        check(!pipeline_busy, "pipeline returns idle after evaluation");
        check(!pipeline_stall, "pipeline does not stall on one-hot BMU result");

        if (test_pass == test_total)
            $display("PASS: rplu_pipeline_tb (%0d/%0d)", test_pass, test_total);
        else
            $display("FAIL: rplu_pipeline_tb (%0d/%0d)", test_pass, test_total);

        $finish;
    end

endmodule
