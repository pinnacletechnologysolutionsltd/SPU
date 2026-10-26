`timescale 1ns/1ps

module spu13_tensegrity_intersection_tb #(
    parameter USE_ZPHI_KARATSUBA = 0
);
    reg clk=0, rst_n=0, start=0;
    reg signed [31:0] p0_xa,p0_xb,p0_ya,p0_yb,p0_za,p0_zb;
    reg signed [31:0] p1_xa,p1_xb,p1_ya,p1_yb,p1_za,p1_zb;
    reg signed [31:0] q0_xa,q0_xb,q0_ya,q0_yb,q0_za,q0_zb;
    reg signed [31:0] q1_xa,q1_xb,q1_ya,q1_yb,q1_za,q1_zb;
    wire busy,done,contact;
    integer errors=0;
    always #5 clk=~clk;

    spu13_tensegrity_intersection #(
        .USE_ZPHI_KARATSUBA(USE_ZPHI_KARATSUBA)
    ) dut(.*);

    task set_point;
        output signed [31:0] xa,xb,ya,yb,za,zb;
        input integer ixa,ixb,iya,iyb,iza,izb;
        begin xa=ixa;xb=ixb;ya=iya;yb=iyb;za=iza;zb=izb; end
    endtask

    task run_case;
        input expected; input [8*32-1:0] name;
        integer cycles;
        begin
            @(negedge clk); start=1; @(posedge clk); #1;
            @(negedge clk); start=0;
            cycles = 0;
            while (!done && cycles < 200000) begin
                @(posedge clk); #1;
                cycles = cycles + 1;
            end
            if (!done) begin
                errors=errors+1;
                $display("FAIL %0s timeout", name);
            end
            if (contact !== expected) begin
                errors=errors+1; $display("FAIL %0s contact=%b expected=%b",name,contact,expected);
            end else $display("PASS %0s contact=%b",name,contact);
            $display("ZPHI_CYCLE kind=intersection fixture=%0s mode=%0d cycles=%0d decision=contact_%0d",
                     name, USE_ZPHI_KARATSUBA, cycles, contact);
            @(posedge clk);
        end
    endtask

    initial begin
        set_point(p0_xa,p0_xb,p0_ya,p0_yb,p0_za,p0_zb, 0,0,0,0,0,0);
        set_point(p1_xa,p1_xb,p1_ya,p1_yb,p1_za,p1_zb, 0,2,0,0,0,0);
        set_point(q0_xa,q0_xb,q0_ya,q0_yb,q0_za,q0_zb, 0,1,-1,0,0,0);
        set_point(q1_xa,q1_xb,q1_ya,q1_yb,q1_za,q1_zb, 0,1,1,0,0,0);
        repeat(2) @(posedge clk); rst_n=1;
        run_case(1,"genuine_phi_crossing");

        set_point(p0_xa,p0_xb,p0_ya,p0_yb,p0_za,p0_zb, 0,0,0,0,0,0);
        set_point(p1_xa,p1_xb,p1_ya,p1_yb,p1_za,p1_zb, 3,0,0,0,0,0);
        set_point(q0_xa,q0_xb,q0_ya,q0_yb,q0_za,q0_zb, 1,0,0,0,0,0);
        set_point(q1_xa,q1_xb,q1_ya,q1_yb,q1_za,q1_zb, 4,0,0,0,0,0);
        run_case(1,"collinear_overlap");

        set_point(p1_xa,p1_xb,p1_ya,p1_yb,p1_za,p1_zb, 2,0,0,0,0,0);
        set_point(q0_xa,q0_xb,q0_ya,q0_yb,q0_za,q0_zb, 1,0,0,0,0,0);
        set_point(q1_xa,q1_xb,q1_ya,q1_yb,q1_za,q1_zb, 1,0,1,0,0,0);
        run_case(1,"closed_t_junction");

        set_point(q0_xa,q0_xb,q0_ya,q0_yb,q0_za,q0_zb, 0,0,1,0,0,0);
        set_point(q1_xa,q1_xb,q1_ya,q1_yb,q1_za,q1_zb, 2,0,1,0,0,0);
        run_case(0,"parallel_disjoint");

        set_point(p0_xa,p0_xb,p0_ya,p0_yb,p0_za,p0_zb, -2,0,0,0,0,0);
        set_point(p1_xa,p1_xb,p1_ya,p1_yb,p1_za,p1_zb, 2,0,0,0,0,0);
        set_point(q0_xa,q0_xb,q0_ya,q0_yb,q0_za,q0_zb, 0,0,-2,0,0,0);
        set_point(q1_xa,q1_xb,q1_ya,q1_yb,q1_za,q1_zb, 0,0,2,0,0,0);
        run_case(1,"antipodal_origin_crossing");

        set_point(q0_xa,q0_xb,q0_ya,q0_yb,q0_za,q0_zb, 3,0,-2,0,0,0);
        set_point(q1_xa,q1_xb,q1_ya,q1_yb,q1_za,q1_zb, 3,0,2,0,0,0);
        run_case(0,"nonparallel_outside");

        // XY projections cross, but the lines are separated in Z. This pins
        // the remaining-coordinate equality after the 2x2 solve.
        set_point(q0_xa,q0_xb,q0_ya,q0_yb,q0_za,q0_zb, 0,0,-2,0,1,0);
        set_point(q1_xa,q1_xb,q1_ya,q1_yb,q1_za,q1_zb, 0,0,2,0,1,0);
        run_case(0,"skew_projection_only");

        // Reverse both endpoint orders to exercise the opposite determinant
        // and interval signs without changing the geometric contact.
        set_point(p0_xa,p0_xb,p0_ya,p0_yb,p0_za,p0_zb, 2,0,0,0,0,0);
        set_point(p1_xa,p1_xb,p1_ya,p1_yb,p1_za,p1_zb, -2,0,0,0,0,0);
        set_point(q0_xa,q0_xb,q0_ya,q0_yb,q0_za,q0_zb, 0,0,2,0,0,0);
        set_point(q1_xa,q1_xb,q1_ya,q1_yb,q1_za,q1_zb, 0,0,-2,0,0,0);
        run_case(1,"reversed_orientation_crossing");

        if(errors==0) $display("SPU13_TENSEGRITY_INTERSECTION_TB: PASS");
        else $display("SPU13_TENSEGRITY_INTERSECTION_TB: FAIL errors=%0d",errors);
        $finish(errors!=0);
    end
endmodule
