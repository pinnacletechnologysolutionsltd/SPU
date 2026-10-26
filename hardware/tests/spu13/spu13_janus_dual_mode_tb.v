// spu13_janus_dual_mode_tb.v -- tests piston/seesaw/independent Janus modes.

`timescale 1ns / 1ps

module spu13_janus_dual_mode_tb;

    localparam MODE_PISTON      = 2'd0;
    localparam MODE_SEESAW      = 2'd1;
    localparam MODE_INDEPENDENT = 2'd2;
    localparam MODE_HOLD        = 2'd3;

    localparam SCREW_STRAIGHT = 2'd0;
    localparam SCREW_CW       = 2'd1;
    localparam SCREW_CCW      = 2'd2;
    localparam SCREW_DUAL     = 2'd3;

    reg clk;
    reg rst_n;
    reg [1:0] dual_mode;
    reg [1:0] screw_mode;
    reg [3:0] phase_offset;
    reg pos_boundary;
    reg neg_boundary;

    reg [15:0] pos_ab_in, pos_ac_in, pos_ad_in;
    reg [15:0] pos_bc_in, pos_bd_in, pos_cd_in;
    reg [15:0] neg_ab_in, neg_ac_in, neg_ad_in;
    reg [15:0] neg_bc_in, neg_bd_in, neg_cd_in;

    wire [15:0] pos_ab_out, pos_ac_out, pos_ad_out;
    wire [15:0] pos_bc_out, pos_bd_out, pos_cd_out;
    wire [15:0] neg_ab_out, neg_ac_out, neg_ad_out;
    wire [15:0] neg_bc_out, neg_bd_out, neg_cd_out;
    wire fire_pos, fire_neg;
    wire phase_match, phase_mismatch;

    integer errors;

    spu13_janus_dual_mode #(.WIDTH(16), .OFFSET_WIDTH(4)) uut (
        .clk(clk),
        .rst_n(rst_n),
        .dual_mode(dual_mode),
        .screw_mode(screw_mode),
        .phase_offset(phase_offset),
        .pos_boundary(pos_boundary),
        .neg_boundary(neg_boundary),
        .pos_ab_in(pos_ab_in),
        .pos_ac_in(pos_ac_in),
        .pos_ad_in(pos_ad_in),
        .pos_bc_in(pos_bc_in),
        .pos_bd_in(pos_bd_in),
        .pos_cd_in(pos_cd_in),
        .neg_ab_in(neg_ab_in),
        .neg_ac_in(neg_ac_in),
        .neg_ad_in(neg_ad_in),
        .neg_bc_in(neg_bc_in),
        .neg_bd_in(neg_bd_in),
        .neg_cd_in(neg_cd_in),
        .pos_ab_out(pos_ab_out),
        .pos_ac_out(pos_ac_out),
        .pos_ad_out(pos_ad_out),
        .pos_bc_out(pos_bc_out),
        .pos_bd_out(pos_bd_out),
        .pos_cd_out(pos_cd_out),
        .neg_ab_out(neg_ab_out),
        .neg_ac_out(neg_ac_out),
        .neg_ad_out(neg_ad_out),
        .neg_bc_out(neg_bc_out),
        .neg_bd_out(neg_bd_out),
        .neg_cd_out(neg_cd_out),
        .fire_pos(fire_pos),
        .fire_neg(fire_neg),
        .phase_match(phase_match),
        .phase_mismatch(phase_mismatch)
    );

    always #5 clk = ~clk;

    task expect_dual_edges;
        input [255:0] name;
        input [15:0] exp_pos_ab, exp_pos_ac, exp_pos_ad;
        input [15:0] exp_pos_bc, exp_pos_bd, exp_pos_cd;
        input [15:0] exp_neg_ab, exp_neg_ac, exp_neg_ad;
        input [15:0] exp_neg_bc, exp_neg_bd, exp_neg_cd;
        begin
            #1;
            if (pos_ab_out === exp_pos_ab && pos_ac_out === exp_pos_ac &&
                pos_ad_out === exp_pos_ad && pos_bc_out === exp_pos_bc &&
                pos_bd_out === exp_pos_bd && pos_cd_out === exp_pos_cd &&
                neg_ab_out === exp_neg_ab && neg_ac_out === exp_neg_ac &&
                neg_ad_out === exp_neg_ad && neg_bc_out === exp_neg_bc &&
                neg_bd_out === exp_neg_bd && neg_cd_out === exp_neg_cd) begin
                $display("PASS: %0s", name);
            end else begin
                $display("FAIL: %0s", name);
                $display("  pos got      AB=%h AC=%h AD=%h BC=%h BD=%h CD=%h",
                         pos_ab_out, pos_ac_out, pos_ad_out,
                         pos_bc_out, pos_bd_out, pos_cd_out);
                $display("  pos expected AB=%h AC=%h AD=%h BC=%h BD=%h CD=%h",
                         exp_pos_ab, exp_pos_ac, exp_pos_ad,
                         exp_pos_bc, exp_pos_bd, exp_pos_cd);
                $display("  neg got      AB=%h AC=%h AD=%h BC=%h BD=%h CD=%h",
                         neg_ab_out, neg_ac_out, neg_ad_out,
                         neg_bc_out, neg_bd_out, neg_cd_out);
                $display("  neg expected AB=%h AC=%h AD=%h BC=%h BD=%h CD=%h",
                         exp_neg_ab, exp_neg_ac, exp_neg_ad,
                         exp_neg_bc, exp_neg_bd, exp_neg_cd);
                errors = errors + 1;
            end
        end
    endtask

    task expect_flags;
        input [255:0] name;
        input exp_fire_pos;
        input exp_fire_neg;
        input exp_phase_match;
        input exp_phase_mismatch;
        begin
            #1;
            if (fire_pos === exp_fire_pos &&
                fire_neg === exp_fire_neg &&
                phase_match === exp_phase_match &&
                phase_mismatch === exp_phase_mismatch) begin
                $display("PASS: %0s", name);
            end else begin
                $display("FAIL: %0s", name);
                $display("  fire_pos=%b fire_neg=%b phase_match=%b phase_mismatch=%b",
                         fire_pos, fire_neg, phase_match, phase_mismatch);
                $display("  expected %b %b %b %b",
                         exp_fire_pos, exp_fire_neg,
                         exp_phase_match, exp_phase_mismatch);
                errors = errors + 1;
            end
        end
    endtask

    task clear_boundaries;
        begin
            @(negedge clk);
            pos_boundary = 1'b0;
            neg_boundary = 1'b0;
            @(posedge clk);
            #1;
        end
    endtask

    initial begin
        clk = 1'b0;
        rst_n = 1'b0;
        dual_mode = MODE_HOLD;
        screw_mode = SCREW_CW;
        phase_offset = 4'd0;
        pos_boundary = 1'b0;
        neg_boundary = 1'b0;
        errors = 0;

        pos_ab_in = 16'hA001;
        pos_ac_in = 16'hA002;
        pos_ad_in = 16'hA003;
        pos_bc_in = 16'hA004;
        pos_bd_in = 16'hA005;
        pos_cd_in = 16'hA006;

        neg_ab_in = 16'hB001;
        neg_ac_in = 16'hB002;
        neg_ad_in = 16'hB003;
        neg_bc_in = 16'hB004;
        neg_bd_in = 16'hB005;
        neg_cd_in = 16'hB006;

        repeat (2) @(posedge clk);
        rst_n = 1'b1;
        @(posedge clk);

        $display("spu13_janus_dual_mode_tb");

        // Piston mode: positive side stays fixed; negative side twists when its
        // boundary strobe arrives.
        @(negedge clk);
        dual_mode = MODE_PISTON;
        screw_mode = SCREW_CW;
        pos_boundary = 1'b0;
        neg_boundary = 1'b1;
        expect_flags("piston fires negative only", 1'b0, 1'b1, 1'b0, 1'b0);
        expect_dual_edges("piston keeps positive static and screws negative",
                          16'hA001, 16'hA002, 16'hA003,
                          16'hA004, 16'hA005, 16'hA006,
                          16'hB006, 16'hB005, 16'hB004,
                          16'hB001, 16'hB003, 16'hB002);
        clear_boundaries();

        // SeeSaw mode: both sides must reach the boundary together. The output
        // is cross-coupled after the screw permutation.
        @(negedge clk);
        dual_mode = MODE_SEESAW;
        pos_boundary = 1'b1;
        neg_boundary = 1'b1;
        expect_flags("seesaw fires both sides", 1'b1, 1'b1, 1'b0, 1'b0);
        expect_dual_edges("seesaw cross-couples permuted tetrahedra",
                          16'hB006, 16'hB005, 16'hB004,
                          16'hB001, 16'hB003, 16'hB002,
                          16'hA006, 16'hA005, 16'hA004,
                          16'hA001, 16'hA003, 16'hA002);
        @(posedge clk);
        expect_flags("seesaw phase match pulse", 1'b1, 1'b1, 1'b1, 1'b0);
        clear_boundaries();

        @(negedge clk);
        dual_mode = MODE_SEESAW;
        pos_boundary = 1'b1;
        neg_boundary = 1'b0;
        expect_flags("seesaw mismatch does not fire", 1'b0, 1'b0, 1'b0, 1'b0);
        expect_dual_edges("seesaw mismatch holds both sides",
                          16'hA001, 16'hA002, 16'hA003,
                          16'hA004, 16'hA005, 16'hA006,
                          16'hB001, 16'hB002, 16'hB003,
                          16'hB004, 16'hB005, 16'hB006);
        @(posedge clk);
        expect_flags("seesaw mismatch pulse", 1'b0, 1'b0, 1'b0, 1'b1);
        clear_boundaries();

        // Independent mode: each side may hit the boundary separately. The
        // registered phase checker reports whether the second boundary arrives
        // exactly phase_offset cycles after the first.
        @(negedge clk);
        dual_mode = MODE_INDEPENDENT;
        phase_offset = 4'd2;
        pos_boundary = 1'b1;
        neg_boundary = 1'b0;
        expect_flags("independent fires positive first", 1'b1, 1'b0, 1'b0, 1'b0);
        expect_dual_edges("independent screws positive only",
                          16'hA006, 16'hA005, 16'hA004,
                          16'hA001, 16'hA003, 16'hA002,
                          16'hB001, 16'hB002, 16'hB003,
                          16'hB004, 16'hB005, 16'hB006);
        @(posedge clk);
        @(negedge clk);
        pos_boundary = 1'b0;
        neg_boundary = 1'b0;
        @(posedge clk);
        @(negedge clk);
        neg_boundary = 1'b1;
        expect_flags("independent fires negative second", 1'b0, 1'b1, 1'b0, 1'b0);
        @(posedge clk);
        expect_flags("independent phase offset matched", 1'b0, 1'b1, 1'b1, 1'b0);
        clear_boundaries();

        @(negedge clk);
        dual_mode = MODE_INDEPENDENT;
        phase_offset = 4'd3;
        pos_boundary = 1'b1;
        neg_boundary = 1'b0;
        @(posedge clk);
        @(negedge clk);
        pos_boundary = 1'b0;
        neg_boundary = 1'b1;
        @(posedge clk);
        expect_flags("independent phase offset mismatch", 1'b0, 1'b1, 1'b0, 1'b1);
        clear_boundaries();

        if (errors == 0) begin
            $display("PASS");
            $finish;
        end else begin
            $display("FAIL");
            $finish;
        end
    end

endmodule
