// spu_fragment_pipe_tb.v — Testbench: spu_fragment_pipe v2.0
// Verifies spread-weighted blending: pixel_energy_n = Σ wi_n × vi_axis
// with exact Q(√3) integer arithmetic and no 16.16 fixed-point.
//
// Test vectors:
//   T1: w0=3, w1=1, w2=0 (IVM-like weights), v0=all 4, v1=all 8, v2=all 16
//     axis0: 3×4 + 1×8 + 0×16 = 20  w_total=4
//   T2: Equal weights w0=w1=w2=1, v0=(1,2,3,4), v1=(5,6,7,8), v2=(9,10,11,12)
//     axis0: 1+5+9=15  axis1: 2+6+10=18  axis2: 3+7+11=21  axis3: 4+8+12=24  w_total=3
//   T3: pixel_inside=0 → all outputs zero

`timescale 1ns/1ps

module spu_fragment_pipe_tb;

    reg         clk = 0;
    reg         rst_n = 0;
    reg         pixel_inside = 0;
    reg  [15:0] w0_n, w1_n, w2_n;
    reg  [63:0] v0_attr, v1_attr, v2_attr;
    wire [127:0] pixel_energy_n;
    wire [15:0]  pixel_w_total;

    spu_fragment_pipe u_dut (
        .clk(clk), .rst_n(rst_n), .pixel_inside(pixel_inside),
        .w0_n(w0_n), .w1_n(w1_n), .w2_n(w2_n),
        .v0_attr(v0_attr), .v1_attr(v1_attr), .v2_attr(v2_attr),
        .pixel_energy_n(pixel_energy_n), .pixel_w_total(pixel_w_total)
    );

    always #10 clk = ~clk;

    integer fail = 0;

    task check32;
        input [31:0]  got;
        input [31:0]  exp;
        input [127:0] name;
        begin
            if (got !== exp) begin
                $display("FAIL: %0s  got=%0d  exp=%0d", name, got, exp);
                fail = fail + 1;
            end
        end
    endtask
    task check16;
        input [15:0]  got;
        input [15:0]  exp;
        input [127:0] name;
        begin
            if (got !== exp) begin
                $display("FAIL: %0s  got=%0d  exp=%0d", name, got, exp);
                fail = fail + 1;
            end
        end
    endtask

    initial begin
        @(posedge clk); rst_n = 1;

        // T1: w=(3,1,0), v0=all4, v1=all8, v2=all16
        pixel_inside = 1;
        w0_n=3; w1_n=1; w2_n=0;
        v0_attr = {16'd4, 16'd4, 16'd4, 16'd4};
        v1_attr = {16'd8, 16'd8, 16'd8, 16'd8};
        v2_attr = {16'd16,16'd16,16'd16,16'd16};
        @(posedge clk); @(posedge clk);
        // axis0 = 3×4 + 1×8 + 0×16 = 20
        check32(pixel_energy_n[127:96], 32'd20, "T1 axis0");
        check32(pixel_energy_n[95:64],  32'd20, "T1 axis1");
        check32(pixel_energy_n[63:32],  32'd20, "T1 axis2");
        check32(pixel_energy_n[31:0],   32'd20, "T1 axis3");
        check16(pixel_w_total, 16'd4, "T1 w_total");

        // T2: equal weights w=1,1,1, three different vertices
        w0_n=1; w1_n=1; w2_n=1;
        v0_attr = {16'd1, 16'd2, 16'd3, 16'd4};
        v1_attr = {16'd5, 16'd6, 16'd7, 16'd8};
        v2_attr = {16'd9, 16'd10,16'd11,16'd12};
        @(posedge clk); @(posedge clk);
        check32(pixel_energy_n[127:96], 32'd15, "T2 axis0=15");
        check32(pixel_energy_n[95:64],  32'd18, "T2 axis1=18");
        check32(pixel_energy_n[63:32],  32'd21, "T2 axis2=21");
        check32(pixel_energy_n[31:0],   32'd24, "T2 axis3=24");
        check16(pixel_w_total, 16'd3, "T2 w_total=3");

        // T3: pixel_inside=0 → zero output
        pixel_inside = 0;
        @(posedge clk); @(posedge clk);
        check32(pixel_energy_n[127:96], 32'd0, "T3 zero when outside");
        check16(pixel_w_total, 16'd0, "T3 w_total zero when outside");

        // T4: zero weights → zero output (even with pixel_inside)
        pixel_inside = 1;
        w0_n=0; w1_n=0; w2_n=0;
        v0_attr = {16'd100,16'd200,16'd300,16'd400};
        v1_attr = v0_attr; v2_attr = v0_attr;
        @(posedge clk); @(posedge clk);
        check32(pixel_energy_n[127:96], 32'd0, "T4 zero weights");
        check16(pixel_w_total, 16'd0, "T4 w_total zero");

        if (fail == 0)
            $display("PASS");
        else
            $display("FAIL (%0d failures)", fail);
        $finish;
    end

endmodule
