// a31r2_pipeline_probe.v - A31-R2 directed refusal-path probe (PRESERVED EVIDENCE, not a regression gate).
// Derived from hardware/tests/spu13/rplu_pipeline_tb.v; read-only hierarchical observers added.
// Run: python3 hardware/tests/spu13/a31_r2/run_a31_r2.py ; see docs/isa/ISA_V02_A31R2_FINDINGS.md.
// The file name deliberately avoids 'tb' so run_all_tests.py does not auto-discover it.
`timescale 1ns / 1ps

// rplu_pipeline_tb.v - integration smoke test for RPLU v2 pipeline control.

module a31r2_pipeline_probe #(parameter FIRST_FAIL=0,
    parameter USE_STRUCTURED_INVERTER = 0,
    parameter STRUCTURED_INVERTER_SEQUENTIAL = 0
);

    reg coeff_we=0, coeff_is_den=0; reg [2:0] coeff_addr=0; reg [31:0] cc0=0,cc1=0,cc2=0,cc3=0;
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

    rplu_pipeline #(
        .SHARE_PADE_INV_MULT(1),
        .USE_STRUCTURED_INVERTER(USE_STRUCTURED_INVERTER),
        .STRUCTURED_INVERTER_SEQUENTIAL(STRUCTURED_INVERTER_SEQUENTIAL)
    ) uut (
        .clk(clk),
        .rst_n(rst_n),
        .som_features(som_features),
        .som_start(som_start),
        .som_done(som_done),
        .som_best_id(som_best_id),
        .som_cluster_label(som_cluster_label),
        .som_best_q(som_best_q),
        .pade_coeff_we(coeff_we),
        .pade_coeff_is_den(coeff_is_den),
        .pade_coeff_addr(coeff_addr),
        .pade_c0(cc0),
        .pade_c1(cc1),
        .pade_c2(cc2),
        .pade_c3(cc3),
        .btu_cfg_we(1'b0),
        .btu_cfg_addr(6'd0),
        .btu_cfg_pair(1'b0),
        .btu_cfg_data(64'd0),
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


    always @(posedge clk) begin
        if (uut.u_pade.done)
            $display("EV t=%0t pade.done flags_v=%b result_c=%h/%h/%h/%h", $time, uut.u_pade.flags_v,
                     uut.u_pade.result_c0, uut.u_pade.result_c1, uut.u_pade.result_c2, uut.u_pade.result_c3);
        if (thimble_valid)
            $display("EV t=%0t thimble_valid c=%h/%h/%h/%h (pade_flags_v now=%b)", $time,
                     thimble_c0, thimble_c1, thimble_c2, thimble_c3, uut.pade_flags_v);
    end
    task setden0; input [31:0] a0; input [31:0] a1; input [31:0] a2; input [31:0] a3;
        begin @(negedge clk); coeff_is_den=1; coeff_addr=0; cc0=a0; cc1=a1; cc2=a2; cc3=a3; coeff_we=1;
              @(negedge clk); coeff_we=0; end endtask
    task txn; input [255:0] m; integer k;
        begin $display("---- %0s ----", m);
              @(negedge clk); som_start=1; @(negedge clk); som_start=0;
              for (k=0;k<1500;k=k+1) @(posedge clk); end endtask
    initial begin
        clk=0; rst_n=0; som_start=0; som_features=144'd0;
        #30 rst_n=1; #20;
        if (FIRST_FAIL==0) begin
            txn("A: success (default 1/1)");
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
