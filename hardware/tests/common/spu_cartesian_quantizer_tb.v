`timescale 1ns/1ps
// Cartesian bridge ingest quantizer — acceptance TB.
// Contract: docs/CARTESIAN_BRIDGE_SPEC.md §7. Expected values below are
// ORACLE-DERIVED (software/lib/cartesian_bridge.py quantize_scalar(v, 1),
// generated 2026-07-12), not hand-computed. Do not edit vectors to fit an
// implementation — the oracle is the authority.

module spu_cartesian_quantizer_tb();
    reg clk = 0;
    reg rst_n = 0;
    reg in_valid = 0;
    reg signed [31:0] in_fixed = 32'd0;
    wire out_valid;
    wire [31:0] out_surd;
    wire out_saturated;

    integer errors = 0;

    spu_cartesian_quantizer uut (
        .clk(clk),
        .rst_n(rst_n),
        .in_valid(in_valid),
        .in_fixed(in_fixed),
        .out_valid(out_valid),
        .out_surd(out_surd),
        .out_saturated(out_saturated)
    );

    always #5 clk = ~clk;

    // Drive one S24.8 word for exactly one cycle; check the registered
    // output one cycle later, and that out_valid is a strobe (drops after).
    task apply;
        input signed [31:0] fixed;
        input signed [15:0] exp_p;
        input exp_sat;
        begin
            @(negedge clk);
            in_valid = 1'b1;
            in_fixed = fixed;
            @(negedge clk);
            in_valid = 1'b0;
            in_fixed = 32'hxxxxxxxx;  // input must have been registered
            if (out_valid !== 1'b1) begin
                errors = errors + 1;
                $display("FAIL: in=%h out_valid not asserted", fixed);
            end
            if (out_surd !== {exp_p, 16'd0}) begin
                errors = errors + 1;
                $display("FAIL: in=%h got surd %h want %h",
                         fixed, out_surd, {exp_p, 16'd0});
            end
            if (out_saturated !== exp_sat) begin
                errors = errors + 1;
                $display("FAIL: in=%h got sat %b want %b",
                         fixed, out_saturated, exp_sat);
            end
            @(negedge clk);
            if (out_valid !== 1'b0) begin
                errors = errors + 1;
                $display("FAIL: in=%h out_valid stuck high", fixed);
            end
        end
    endtask

    initial begin
        #12 rst_n = 1;
        @(negedge clk);
        if (out_valid !== 1'b0 || out_surd !== 32'd0 || out_saturated !== 1'b0) begin
            errors = errors + 1;
            $display("FAIL: outputs not zeroed after reset");
        end

        //     S24.8 input     expected P   sat   (real value)
        apply(32'h00000000, -16'sd0,     1'b0);  //  0.0
        apply(32'h00000280,  16'sd2,     1'b0);  //  2.5 midpoint -> even down
        apply(32'h00000380,  16'sd4,     1'b0);  //  3.5 midpoint -> even up
        apply(32'hFFFFFD80, -16'sd2,     1'b0);  // -2.5 midpoint -> even (-2)
        apply(32'hFFFFFC80, -16'sd4,     1'b0);  // -3.5 midpoint -> even (-4)
        apply(32'h000002C0,  16'sd3,     1'b0);  //  2.75 -> 3
        apply(32'hFFFFFFC0, -16'sd0,     1'b0);  // -0.25 -> 0
        apply(32'h00006421,  16'sd100,   1'b0);  //  100.12890625 -> 100
        apply(32'h007FFF00,  16'sd32767, 1'b0);  //  32767.0 in range
        apply(32'h007FFF80,  16'sd32767, 1'b1);  //  32767.5 rounds OUT -> clamp
        apply(32'h007FFE80,  16'sd32766, 1'b0);  //  32766.5 midpoint -> even
        apply(32'hFF800000, -16'sd32768, 1'b0);  // -32768.0 in range
        apply(32'hFF7FFF80, -16'sd32768, 1'b0);  // -32768.5 rounds back IN
        apply(32'hFF7FFF00, -16'sd32768, 1'b1);  // -32769.0 -> clamp
        apply(32'h7FFFFFFF,  16'sd32767, 1'b1);  //  S24.8 max -> clamp
        apply(32'h80000000, -16'sd32768, 1'b1);  //  S24.8 min -> clamp

        // Back-to-back streaming: two words on consecutive cycles.
        @(negedge clk);
        in_valid = 1'b1;
        in_fixed = 32'h00000280;  // 2.5 -> 2
        @(negedge clk);
        in_fixed = 32'h00000380;  // 3.5 -> 4
        if (out_surd !== {16'sd2, 16'd0} || out_valid !== 1'b1) begin
            errors = errors + 1;
            $display("FAIL: streaming word 0 got %h", out_surd);
        end
        @(negedge clk);
        in_valid = 1'b0;
        in_fixed = 32'hxxxxxxxx;
        if (out_surd !== {16'sd4, 16'd0} || out_valid !== 1'b1) begin
            errors = errors + 1;
            $display("FAIL: streaming word 1 got %h", out_surd);
        end

        if (errors == 0)
            $display("PASS");
        else
            $display("FAIL: %0d errors", errors);
        $finish;
    end
endmodule
