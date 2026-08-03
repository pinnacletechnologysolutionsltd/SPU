`timescale 1ns / 1ps

// Full-width comparison of every structured request against the production
// general A31 multiplier. The frozen inverter corpus supplies extrema,
// cancellation-heavy values, units, zero, and nonzero zero divisors.
module spu13_m31_multiplier_structured_tb;
    localparam [31:0] P = 32'h7FFFFFFF;
    localparam VECTOR_COUNT = 31;
    localparam MAX_WORDS = 1 + VECTOR_COUNT * 9;

    reg clk, rst_n, start;
    reg [2:0] op;
    reg [31:0] a0, a1, a2, a3, b0, b1, b2, b3;
    wire [31:0] cr0, cr1, cr2, cr3;
    wire cdone, cbusy, crns_error;
    wire [4:0] logical_products;
    wire [31:0] rr0, rr1, rr2, rr3;
    wire rdone, rbusy, rrns_error;
    wire [31:0] sr0, sr1, sr2, sr3;
    wire sdone, sbusy, srns_error;
    wire [4:0] seq_logical_products;

    reg [31:0] golden [0:MAX_WORDS-1];
    integer failures, vector_index, base, next_base;
    reg [31:0] z0, z1, z2, z3;
    reg [31:0] w0, w1;
    reg [31:0] forced_value;
    reg [71:0] forced_accumulator;
    integer product_total;

    always #5 clk = ~clk;

    function [31:0] m31_neg;
        input [31:0] value;
        begin m31_neg = (value == 0) ? 0 : P - value; end
    endfunction

    spu13_m31_multiplier_structured u_candidate (
        .clk(clk), .rst_n(rst_n), .start(start), .op(op),
        .a0(a0), .a1(a1), .a2(a2), .a3(a3),
        .b0(b0), .b1(b1), .b2(b2), .b3(b3),
        .r0(cr0), .r1(cr1), .r2(cr2), .r3(cr3),
        .done(cdone), .busy(cbusy), .rns_error(crns_error),
        .logical_products(logical_products)
    );

    spu13_m31_multiplier u_reference (
        .clk(clk), .rst_n(rst_n), .start(start),
        .a0(a0), .a1(a1), .a2(a2), .a3(a3),
        .b0(b0), .b1(b1), .b2(b2), .b3(b3),
        .r0(rr0), .r1(rr1), .r2(rr2), .r3(rr3),
        .done(rdone), .busy(rbusy), .rns_error(rrns_error)
    );

    spu13_m31_multiplier_seq_structured u_seq_candidate (
        .clk(clk), .rst_n(rst_n), .start(start), .op(op),
        .a0(a0), .a1(a1), .a2(a2), .a3(a3),
        .b0(b0), .b1(b1), .b2(b2), .b3(b3),
        .r0(sr0), .r1(sr1), .r2(sr2), .r3(sr3),
        .done(sdone), .busy(sbusy), .rns_error(srns_error),
        .logical_products(seq_logical_products)
    );

    task launch_and_compare;
        input [2:0] request_op;
        input [4:0] expected_products;
        input [31:0] ia0, ia1, ia2, ia3;
        input [31:0] ib0, ib1, ib2, ib3;
        begin
            @(negedge clk);
            op = request_op;
            a0 = ia0; a1 = ia1; a2 = ia2; a3 = ia3;
            b0 = ib0; b1 = ib1; b2 = ib2; b3 = ib3;
            #1;
            if (logical_products !== expected_products) begin
                $display("FAIL product count op=%0d expected=%0d got=%0d",
                         request_op, expected_products, logical_products);
                failures = failures + 1;
            end
            if (seq_logical_products !== expected_products) begin
                $display("FAIL sequential product count op=%0d expected=%0d got=%0d",
                         request_op, expected_products, seq_logical_products);
                failures = failures + 1;
            end
            start = 1'b1;
            @(negedge clk);
            start = 1'b0;
            wait(cdone && rdone);
            #1;
            if ({cr3, cr2, cr1, cr0} !== {rr3, rr2, rr1, rr0}) begin
                $display("FAIL arithmetic vector=%0d op=%0d", vector_index, request_op);
                $display("  candidate %h %h %h %h", cr0, cr1, cr2, cr3);
                $display("  reference %h %h %h %h", rr0, rr1, rr2, rr3);
                failures = failures + 1;
            end
            if (crns_error !== 1'b0 || rrns_error !== 1'b0) begin
                $display("FAIL unexpected RNS error vector=%0d op=%0d", vector_index, request_op);
                failures = failures + 1;
            end
            wait(sdone);
            #1;
            if ({sr3, sr2, sr1, sr0} !== {rr3, rr2, rr1, rr0}) begin
                $display("FAIL sequential arithmetic vector=%0d op=%0d", vector_index, request_op);
                $display("  candidate %h %h %h %h", sr0, sr1, sr2, sr3);
                $display("  reference %h %h %h %h", rr0, rr1, rr2, rr3);
                failures = failures + 1;
            end
            if (srns_error !== 1'b0) begin
                $display("FAIL unexpected sequential RNS error vector=%0d op=%0d",
                         vector_index, request_op);
                failures = failures + 1;
            end
            product_total = product_total + expected_products;
        end
    endtask

    initial begin
        $readmemh("hardware/tests/spu13/spu13_fp4_inverter_golden.mem", golden);
        clk = 0;
        rst_n = 0;
        start = 0;
        op = 0;
        a0 = 0; a1 = 0; a2 = 0; a3 = 0;
        b0 = 0; b1 = 0; b2 = 0; b3 = 0;
        failures = 0;
        repeat (3) @(negedge clk);
        rst_n = 1;

        if (golden[0] !== VECTOR_COUNT) begin
            $display("FAIL golden vector count expected=%0d got=%0d",
                     VECTOR_COUNT, golden[0]);
            failures = failures + 1;
        end

        for (vector_index = 0; vector_index < VECTOR_COUNT; vector_index = vector_index + 1) begin
            base = 1 + vector_index * 9;
            next_base = 1 + ((vector_index + 1) % VECTOR_COUNT) * 9;
            z0 = golden[base+0]; z1 = golden[base+1];
            z2 = golden[base+2]; z3 = golden[base+3];

            // OP_FULL must remain bit-identical to production.
            launch_and_compare(3'd0, 5'd16, z0, z1, z2, z3,
                               golden[next_base+0], golden[next_base+1],
                               golden[next_base+2], golden[next_base+3]);

            product_total = 0;
            // Stage A reference: Z * (z0,z1,-z2,-z3).
            launch_and_compare(3'd1, 5'd6, z0, z1, z2, z3,
                               z0, z1, m31_neg(z2), m31_neg(z3));
            w0 = cr0;
            w1 = cr1;

            // Stage B reference: (w0,w1,0,0) * (w0,-w1,0,0).
            launch_and_compare(3'd2, 5'd2, w0, w1, 0, 0,
                               w0, m31_neg(w1), 0, 0);

            // Stage D1 reference: Z_conj * W_conj.
            launch_and_compare(3'd3, 5'd8,
                               z0, z1, m31_neg(z2), m31_neg(z3),
                               w0, m31_neg(w1), 0, 0);

            // Stage D2 shape: four independent scalar products.
            launch_and_compare(3'd4, 5'd4, z0, z1, z2, z3,
                               golden[next_base+0], 0, 0, 0);

            if (product_total != 20) begin
                $display("FAIL structured total vector=%0d expected=20 got=%0d",
                         vector_index, product_total);
                failures = failures + 1;
            end
        end

        // Fault injection demonstrates that a narrow result remains covered
        // by the independently delayed mod-3 residue shadow.
        @(negedge clk);
        op = 3'd4;
        a0 = 32'd9; a1 = 32'd8; a2 = 32'd7; a3 = 32'd6;
        b0 = 32'd5; b1 = 0; b2 = 0; b3 = 0;
        start = 1;
        @(negedge clk);
        start = 0;
        wait(cdone);
        #1;
        forced_value = cr0 ^ 32'd1;
        force u_candidate.s1_r0 = forced_value;
        #1;
        if (crns_error !== 1'b1) begin
            $display("FAIL narrow RNS fault injection was not detected");
            failures = failures + 1;
        end
        release u_candidate.s1_r0;

        wait(sdone);
        #1;
        forced_value = sr0 ^ 32'd1;
        force u_seq_candidate.r0 = forced_value;
        #1;
        if (srns_error !== 1'b1) begin
            $display("FAIL sequential narrow RNS fault injection was not detected");
            failures = failures + 1;
        end
        release u_seq_candidate.r0;

        // Corrupt the sequential accumulator after its residue shadow has
        // advanced but before final reduction. This is the boundary protected
        // by the production parallel multiplier's registered shadow.
        @(negedge clk);
        op = 3'd4;
        a0 = 32'd9; a1 = 32'd8; a2 = 32'd7; a3 = 32'd6;
        b0 = 32'd5; b1 = 0; b2 = 0; b3 = 0;
        start = 1;
        @(negedge clk);
        start = 0;
        wait(u_seq_candidate.state == 3'd3);
        #1;
        forced_accumulator = u_seq_candidate.acc0 ^ 72'd1;
        force u_seq_candidate.acc0 = forced_accumulator;
        wait(sdone);
        #1;
        if (srns_error !== 1'b1) begin
            $display("FAIL sequential accumulator RNS fault injection was not detected");
            failures = failures + 1;
        end
        release u_seq_candidate.acc0;

        if (failures == 0)
            $display("PASS: spu13_m31_multiplier_structured_tb (parallel+sequential, %0d vectors, 20 products/tower shape, RNS covered)", VECTOR_COUNT);
        else
            $display("FAIL: spu13_m31_multiplier_structured_tb (%0d failures)", failures);
        $finish;
    end
endmodule
