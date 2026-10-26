// spu13_janus_screw_lines_tb.v -- tests tetrahedral Janus screw topology.

`timescale 1ns / 1ps

module spu13_janus_screw_lines_tb;

    localparam MODE_STRAIGHT = 2'd0;
    localparam MODE_SCREW_CW = 2'd1;
    localparam MODE_SCREW_CCW = 2'd2;
    localparam MODE_DUAL = 2'd3;

    reg [1:0] mode;

    reg  [15:0] ab_in, ac_in, ad_in, bc_in, bd_in, cd_in;
    wire [15:0] ab_out, ac_out, ad_out, bc_out, bd_out, cd_out;

    wire [15:0] inv_ab_out, inv_ac_out, inv_ad_out;
    wire [15:0] inv_bc_out, inv_bd_out, inv_cd_out;

    wire [15:0] dual2_ab_out, dual2_ac_out, dual2_ad_out;
    wire [15:0] dual2_bc_out, dual2_bd_out, dual2_cd_out;

    integer errors;

    spu13_janus_screw_lines #(.WIDTH(16)) uut (
        .mode(mode),
        .line_ab_in(ab_in),
        .line_ac_in(ac_in),
        .line_ad_in(ad_in),
        .line_bc_in(bc_in),
        .line_bd_in(bd_in),
        .line_cd_in(cd_in),
        .line_ab_out(ab_out),
        .line_ac_out(ac_out),
        .line_ad_out(ad_out),
        .line_bc_out(bc_out),
        .line_bd_out(bd_out),
        .line_cd_out(cd_out)
    );

    // CCW after CW must restore the original edge order.
    spu13_janus_screw_lines #(.WIDTH(16)) u_inverse_check (
        .mode(MODE_SCREW_CCW),
        .line_ab_in(ab_out),
        .line_ac_in(ac_out),
        .line_ad_in(ad_out),
        .line_bc_in(bc_out),
        .line_bd_in(bd_out),
        .line_cd_in(cd_out),
        .line_ab_out(inv_ab_out),
        .line_ac_out(inv_ac_out),
        .line_ad_out(inv_ad_out),
        .line_bc_out(inv_bc_out),
        .line_bd_out(inv_bd_out),
        .line_cd_out(inv_cd_out)
    );

    // Dual/opposite-edge inversion is an involution.
    spu13_janus_screw_lines #(.WIDTH(16)) u_dual2_check (
        .mode(MODE_DUAL),
        .line_ab_in(ab_out),
        .line_ac_in(ac_out),
        .line_ad_in(ad_out),
        .line_bc_in(bc_out),
        .line_bd_in(bd_out),
        .line_cd_in(cd_out),
        .line_ab_out(dual2_ab_out),
        .line_ac_out(dual2_ac_out),
        .line_ad_out(dual2_ad_out),
        .line_bc_out(dual2_bc_out),
        .line_bd_out(dual2_bd_out),
        .line_cd_out(dual2_cd_out)
    );

    task expect_edges;
        input [255:0] name;
        input [15:0] exp_ab, exp_ac, exp_ad, exp_bc, exp_bd, exp_cd;
        begin
            #1;
            if (ab_out === exp_ab && ac_out === exp_ac &&
                ad_out === exp_ad && bc_out === exp_bc &&
                bd_out === exp_bd && cd_out === exp_cd) begin
                $display("PASS: %0s", name);
            end else begin
                $display("FAIL: %0s", name);
                $display("  got      AB=%h AC=%h AD=%h BC=%h BD=%h CD=%h",
                         ab_out, ac_out, ad_out, bc_out, bd_out, cd_out);
                $display("  expected AB=%h AC=%h AD=%h BC=%h BD=%h CD=%h",
                         exp_ab, exp_ac, exp_ad, exp_bc, exp_bd, exp_cd);
                errors = errors + 1;
            end
        end
    endtask

    task expect_inverse_identity;
        input [255:0] name;
        begin
            #1;
            if (inv_ab_out === ab_in && inv_ac_out === ac_in &&
                inv_ad_out === ad_in && inv_bc_out === bc_in &&
                inv_bd_out === bd_in && inv_cd_out === cd_in) begin
                $display("PASS: %0s", name);
            end else begin
                $display("FAIL: %0s", name);
                $display("  got      AB=%h AC=%h AD=%h BC=%h BD=%h CD=%h",
                         inv_ab_out, inv_ac_out, inv_ad_out,
                         inv_bc_out, inv_bd_out, inv_cd_out);
                $display("  expected AB=%h AC=%h AD=%h BC=%h BD=%h CD=%h",
                         ab_in, ac_in, ad_in, bc_in, bd_in, cd_in);
                errors = errors + 1;
            end
        end
    endtask

    task expect_dual_involution;
        input [255:0] name;
        begin
            #1;
            if (dual2_ab_out === ab_in && dual2_ac_out === ac_in &&
                dual2_ad_out === ad_in && dual2_bc_out === bc_in &&
                dual2_bd_out === bd_in && dual2_cd_out === cd_in) begin
                $display("PASS: %0s", name);
            end else begin
                $display("FAIL: %0s", name);
                $display("  got      AB=%h AC=%h AD=%h BC=%h BD=%h CD=%h",
                         dual2_ab_out, dual2_ac_out, dual2_ad_out,
                         dual2_bc_out, dual2_bd_out, dual2_cd_out);
                $display("  expected AB=%h AC=%h AD=%h BC=%h BD=%h CD=%h",
                         ab_in, ac_in, ad_in, bc_in, bd_in, cd_in);
                errors = errors + 1;
            end
        end
    endtask

    initial begin
        errors = 0;
        ab_in = 16'hAB01;
        ac_in = 16'hAC02;
        ad_in = 16'hAD03;
        bc_in = 16'hBC04;
        bd_in = 16'hBD05;
        cd_in = 16'hCD06;

        $display("spu13_janus_screw_lines_tb");

        mode = MODE_STRAIGHT;
        expect_edges("straight pass-through",
                     16'hAB01, 16'hAC02, 16'hAD03,
                     16'hBC04, 16'hBD05, 16'hCD06);

        mode = MODE_SCREW_CW;
        expect_edges("screw clockwise",
                     16'hCD06, 16'hBD05, 16'hBC04,
                     16'hAB01, 16'hAD03, 16'hAC02);
        expect_inverse_identity("ccw after cw restores input");

        mode = MODE_SCREW_CCW;
        expect_edges("screw counter-clockwise",
                     16'hBC04, 16'hCD06, 16'hBD05,
                     16'hAD03, 16'hAC02, 16'hAB01);

        mode = MODE_DUAL;
        expect_edges("opposite-edge dual inversion",
                     16'hCD06, 16'hBD05, 16'hBC04,
                     16'hAD03, 16'hAC02, 16'hAB01);
        expect_dual_involution("dual applied twice restores input");

        if (errors == 0) begin
            $display("PASS");
            $finish;
        end else begin
            $display("FAIL");
            $finish;
        end
    end

endmodule
