`timescale 1ns / 1ps

// rplu_stall_propagation_tb.v — Pipeline hazard & stall propagation stress test
//
// Exercises five scenarios through rplu_pipeline control logic:
//   A) Single SOM launch → baseline one-thimble output
//   B) SOM launch → pipeline busy → second som_start is properly handled
//   C) Multi-cycle burst: pipeline returns to clean idle after full cycle
//   D) Rapid starts while busy: verify launch gating and clean drain
//   E) Rapid back-to-back SOM launches with full drain between

module rplu_stall_propagation_tb;

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
        .clk(clk), .rst_n(rst_n),
        .som_features(som_features), .som_start(som_start),
        .som_done(som_done), .som_best_id(som_best_id),
        .som_cluster_label(som_cluster_label), .som_best_q(som_best_q),
        .pade_coeff_we(1'b0), .pade_coeff_is_den(1'b0),
        .pade_coeff_addr(3'd0), .pade_c0(32'd0), .pade_c1(32'd0),
        .pade_c2(32'd0), .pade_c3(32'd0),
        .btu_cfg_we(1'b0), .btu_cfg_addr(6'd0),
        .btu_cfg_pair(1'b0), .btu_cfg_data(64'd0),
        .quadray_target_kappa(32'd0),
        .thimble_c0(thimble_c0), .thimble_c1(thimble_c1),
        .thimble_c2(thimble_c2), .thimble_c3(thimble_c3),
        .thimble_valid(thimble_valid),
        .quadray_delta(quadray_delta), .quadray_coherent(quadray_coherent),
        .quadray_valid(quadray_valid),
        .pipeline_busy(pipeline_busy), .pipeline_stall(pipeline_stall)
    );

    always #5 clk = ~clk;

    integer test_pass, test_total;
    integer cycle;
    reg busy_on_start;
    reg thimble_seen;
    reg idle_after;
    integer thimble_count;
    reg second_start_gated;

    task check;
        input ok;
        input [255:0] msg;
        begin
            test_total = test_total + 1;
            if (ok) test_pass = test_pass + 1;
            else $display("FAIL: %0s", msg);
        end
    endtask

    task send_som_start;
        begin
            @(posedge clk);
            som_start = 1'b1;
            @(posedge clk);
            som_start = 1'b0;
        end
    endtask

    initial begin
        clk = 1'b0;
        rst_n = 1'b0;
        som_start = 1'b0;
        som_features = 144'd0;
        test_pass = 0; test_total = 0;

        #30 rst_n = 1'b1;
        #20;

        // ═══════════════════════════════════════════════════════════
        // Scenario A: Single SOM launch → baseline one-thimble output
        // ═══════════════════════════════════════════════════════════
        thimble_count = 0;
        send_som_start();

        // Wait for pipeline to complete (Padé ~82 cycles + SOM ~78 cycles + margin)
        for (cycle = 0; cycle < 2000; cycle = cycle + 1) begin
            #10;
            if (thimble_valid) thimble_count = thimble_count + 1;
        end

        check(thimble_count == 1, "A: single SOM launch produces exactly one thimble_valid");
        check(!pipeline_busy, "A: pipeline returns idle after single launch");

        // ═══════════════════════════════════════════════════════════
        // Scenario B: Second som_start while pipeline is busy
        // ═══════════════════════════════════════════════════════════
        thimble_count = 0;
        send_som_start();  // Launch 1

        // Wait for SOM_ACTIVE but before Padé completes
        #400;  // SOM should be done (~78 cycles), Padé in flight (~82 cycles)
        check(pipeline_busy, "B1: pipeline busy before second launch");

        // Issue second SOM start while busy
        second_start_gated = 1'b1;
        send_som_start();  // Launch 2 (may be ignored if SOM is busy)
        #10;

        // Count thimbles over full pipeline cycle
        for (cycle = 0; cycle < 2000; cycle = cycle + 1) begin
            #10;
            if (thimble_valid) thimble_count = thimble_count + 1;
        end

        // Busy starts are explicitly gated. A second pulse while the pipeline
        // is occupied must not duplicate or corrupt the in-flight result.
        check(thimble_count == 1, "B2: busy second launch is ignored exactly once");
        check(!pipeline_busy, "B3: pipeline returns idle after dual launch");

        // ═══════════════════════════════════════════════════════════
        // Scenario C: Multi-cycle burst — full back-to-back stress
        // ═══════════════════════════════════════════════════════════
        for (int burst = 0; burst < 3; burst = burst + 1) begin
            send_som_start();
            // Wait for completion
            for (cycle = 0; cycle < 1500; cycle = cycle + 1) begin
                #10;
            end
            check(!pipeline_busy, "C: burst cycle returns idle");
        end

        // ═══════════════════════════════════════════════════════════
        // Scenario D: Rapid SOM launches — verify no hanging flags
        // ═══════════════════════════════════════════════════════════
        thimble_count = 0;
        // Fire 4 SOM starts, each after a brief gap
        for (int i = 0; i < 4; i = i + 1) begin
            send_som_start();
            #200;  // partial gap (not full completion)
        end
        // Drain remaining pipeline
        for (cycle = 0; cycle < 3000; cycle = cycle + 1) begin
            #10;
            if (thimble_valid) thimble_count = thimble_count + 1;
        end
        check(thimble_count == 1, "D: rapid launches while busy produce exactly one thimble");
        check(!pipeline_busy, "D: pipeline clean after rapid burst");

        // ═══════════════════════════════════════════════════════════
        // Scenario E: Verify pipeline_busy coherency across multiple
        //             start-stop cycles
        // ═══════════════════════════════════════════════════════════
        for (int rep = 0; rep < 3; rep = rep + 1) begin
            send_som_start();
            for (cycle = 0; cycle < 1500; cycle = cycle + 1) begin
                #10;
            end
            check(!pipeline_busy, "E: clean idle after rep");
            check(!pipeline_stall, "E: no stall on one-hot");
        end

        // Summary
        if (test_pass == test_total)
            $display("PASS: rplu_stall_propagation_tb (%0d/%0d)", test_pass, test_total);
        else
            $display("FAIL: rplu_stall_propagation_tb (%0d/%0d)", test_pass, test_total);
        $finish;
    end

endmodule
