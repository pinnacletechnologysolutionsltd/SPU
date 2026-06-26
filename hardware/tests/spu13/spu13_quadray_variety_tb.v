`timescale 1ns / 1ps

// Testbench: spu13_quadray_variety
// Verifies the native Quadray SQR residual over M31.

module spu13_quadray_variety_tb;

    localparam [31:0] P = 32'h7FFFFFFF;

    reg clk, rst_n, valid_in;
    reg [31:0] coord_a, coord_b, coord_c, coord_d, target_kappa;
    wire valid_out, coherent;
    wire [31:0] delta_out;

    spu13_quadray_variety uut (
        .clk(clk),
        .rst_n(rst_n),
        .valid_in(valid_in),
        .coord_a(coord_a),
        .coord_b(coord_b),
        .coord_c(coord_c),
        .coord_d(coord_d),
        .target_kappa(target_kappa),
        .valid_out(valid_out),
        .delta_out(delta_out),
        .coherent(coherent)
    );

    always #5 clk = ~clk;

    integer test_pass, test_total;

    task check_variety;
        input [31:0] a, b, c, d, kappa;
        input [31:0] exp_delta;
        input        exp_coherent;
        begin
            test_total = test_total + 1;

            @(negedge clk);
            coord_a = a;
            coord_b = b;
            coord_c = c;
            coord_d = d;
            target_kappa = kappa;
            valid_in = 1'b1;

            @(posedge clk);
            @(negedge clk);
            valid_in = 1'b0;

            @(posedge clk);
            @(posedge clk);
            #1;
            if (valid_out !== 1'b1 ||
                delta_out !== exp_delta ||
                coherent !== exp_coherent) begin
                $display("FAIL: Q(%h,%h,%h,%h)-%h", a, b, c, d, kappa);
                $display("  expected valid=1 delta=%h coherent=%b",
                         exp_delta, exp_coherent);
                $display("  got      valid=%b delta=%h coherent=%b",
                         valid_out, delta_out, coherent);
            end else begin
                test_pass = test_pass + 1;
            end

            @(posedge clk);
            #1;
            if (valid_out !== 1'b0) begin
                $display("FAIL: valid_out did not clear");
            end
        end
    endtask

    initial begin
        clk = 0;
        rst_n = 0;
        valid_in = 0;
        coord_a = 0;
        coord_b = 0;
        coord_c = 0;
        coord_d = 0;
        target_kappa = 0;
        test_pass = 0;
        test_total = 0;

        #20 rst_n = 1;

        // Q(0,0,0,0) = 0.
        check_variety(32'd0, 32'd0, 32'd0, 32'd0, 32'd0, 32'd0, 1'b1);

        // Q(1,0,0,0) = 3.
        check_variety(32'd1, 32'd0, 32'd0, 32'd0, 32'd3, 32'd0, 1'b1);

        // Q(1,1,0,0) = 4.
        check_variety(32'd1, 32'd1, 32'd0, 32'd0, 32'd4, 32'd0, 1'b1);

        // Q(1,0,0,0) - 4 = -1 mod M31.
        check_variety(32'd1, 32'd0, 32'd0, 32'd0, 32'd4, P - 1, 1'b0);

        // (-1)^2 appears on three pairs, so Q(P-1,0,0,0) = 3.
        check_variety(P - 1, 32'd0, 32'd0, 32'd0, 32'd3, 32'd0, 1'b1);

        // Canonical normalization: P is the same residue as 0.
        check_variety(P, 32'd0, 32'd0, 32'd0, 32'd0, 32'd0, 1'b1);
        check_variety(32'd0, 32'd0, 32'd0, 32'd0, P, 32'd0, 1'b1);

        // Q(10,4,2,0) = 224, so residual against 200 is 24.
        check_variety(32'd10, 32'd4, 32'd2, 32'd0, 32'd200, 32'd24, 1'b0);

        if (test_pass == test_total)
            $display("PASS: spu13_quadray_variety_tb (%0d/%0d)", test_pass, test_total);
        else
            $display("FAIL: spu13_quadray_variety_tb (%0d/%0d)", test_pass, test_total);
        $finish;
    end

endmodule
