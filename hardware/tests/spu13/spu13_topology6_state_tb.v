// spu13_topology6_state_tb.v -- six-line topology state tests.

`timescale 1ns / 1ps

module spu13_topology6_state_tb;

    localparam MODE_PISTON      = 2'd0;
    localparam MODE_SEESAW      = 2'd1;
    localparam MODE_INDEPENDENT = 2'd2;
    localparam MODE_HOLD        = 2'd3;

    localparam SCREW_CW = 2'd1;

    reg clk;
    reg rst_n;
    reg [3:0] rd_lane;
    wire [15:0] rd_pos_ab, rd_pos_ac, rd_pos_ad;
    wire [15:0] rd_pos_bc, rd_pos_bd, rd_pos_cd;
    wire [15:0] rd_neg_ab, rd_neg_ac, rd_neg_ad;
    wire [15:0] rd_neg_bc, rd_neg_bd, rd_neg_cd;

    reg load_en;
    reg [3:0] load_lane;
    reg [15:0] load_pos_ab, load_pos_ac, load_pos_ad;
    reg [15:0] load_pos_bc, load_pos_bd, load_pos_cd;
    reg [15:0] load_neg_ab, load_neg_ac, load_neg_ad;
    reg [15:0] load_neg_bc, load_neg_bd, load_neg_cd;

    reg janus_en;
    reg [3:0] janus_src_lane;
    reg [3:0] janus_dst_lane;
    reg [1:0] dual_mode;
    reg [1:0] screw_mode;
    reg [3:0] phase_offset;
    reg pos_boundary;
    reg neg_boundary;

    wire janus_done;
    wire fire_pos;
    wire fire_neg;
    wire phase_match;
    wire phase_mismatch;

    integer errors;

    spu13_topology6_state #(
        .WIDTH(16),
        .LANES(13),
        .LANE_WIDTH(4),
        .OFFSET_WIDTH(4)
    ) uut (
        .clk(clk),
        .rst_n(rst_n),
        .rd_lane(rd_lane),
        .rd_pos_ab(rd_pos_ab),
        .rd_pos_ac(rd_pos_ac),
        .rd_pos_ad(rd_pos_ad),
        .rd_pos_bc(rd_pos_bc),
        .rd_pos_bd(rd_pos_bd),
        .rd_pos_cd(rd_pos_cd),
        .rd_neg_ab(rd_neg_ab),
        .rd_neg_ac(rd_neg_ac),
        .rd_neg_ad(rd_neg_ad),
        .rd_neg_bc(rd_neg_bc),
        .rd_neg_bd(rd_neg_bd),
        .rd_neg_cd(rd_neg_cd),
        .load_en(load_en),
        .load_lane(load_lane),
        .load_pos_ab(load_pos_ab),
        .load_pos_ac(load_pos_ac),
        .load_pos_ad(load_pos_ad),
        .load_pos_bc(load_pos_bc),
        .load_pos_bd(load_pos_bd),
        .load_pos_cd(load_pos_cd),
        .load_neg_ab(load_neg_ab),
        .load_neg_ac(load_neg_ac),
        .load_neg_ad(load_neg_ad),
        .load_neg_bc(load_neg_bc),
        .load_neg_bd(load_neg_bd),
        .load_neg_cd(load_neg_cd),
        .janus_en(janus_en),
        .janus_src_lane(janus_src_lane),
        .janus_dst_lane(janus_dst_lane),
        .dual_mode(dual_mode),
        .screw_mode(screw_mode),
        .phase_offset(phase_offset),
        .pos_boundary(pos_boundary),
        .neg_boundary(neg_boundary),
        .janus_done(janus_done),
        .fire_pos(fire_pos),
        .fire_neg(fire_neg),
        .phase_match(phase_match),
        .phase_mismatch(phase_mismatch)
    );

    always #5 clk = ~clk;

    task set_load_values;
        input [15:0] pos_base;
        input [15:0] neg_base;
        begin
            load_pos_ab = pos_base + 16'd1;
            load_pos_ac = pos_base + 16'd2;
            load_pos_ad = pos_base + 16'd3;
            load_pos_bc = pos_base + 16'd4;
            load_pos_bd = pos_base + 16'd5;
            load_pos_cd = pos_base + 16'd6;
            load_neg_ab = neg_base + 16'd1;
            load_neg_ac = neg_base + 16'd2;
            load_neg_ad = neg_base + 16'd3;
            load_neg_bc = neg_base + 16'd4;
            load_neg_bd = neg_base + 16'd5;
            load_neg_cd = neg_base + 16'd6;
        end
    endtask

    task load_lane_state;
        input [3:0] lane;
        input [15:0] pos_base;
        input [15:0] neg_base;
        begin
            @(negedge clk);
            set_load_values(pos_base, neg_base);
            load_lane = lane;
            load_en = 1'b1;
            @(posedge clk);
            @(negedge clk);
            load_en = 1'b0;
        end
    endtask

    task apply_janus;
        input [3:0] src_lane;
        input [3:0] dst_lane;
        input [1:0] mode;
        input pos_b;
        input neg_b;
        begin
            @(negedge clk);
            janus_src_lane = src_lane;
            janus_dst_lane = dst_lane;
            dual_mode = mode;
            screw_mode = SCREW_CW;
            pos_boundary = pos_b;
            neg_boundary = neg_b;
            janus_en = 1'b1;
            @(posedge clk);
            #1;
            if (!janus_done) begin
                $display("FAIL: janus_done did not pulse");
                errors = errors + 1;
            end
            @(negedge clk);
            janus_en = 1'b0;
            pos_boundary = 1'b0;
            neg_boundary = 1'b0;
        end
    endtask

    task expect_lane;
        input [255:0] name;
        input [3:0] lane;
        input [15:0] exp_pos_ab, exp_pos_ac, exp_pos_ad;
        input [15:0] exp_pos_bc, exp_pos_bd, exp_pos_cd;
        input [15:0] exp_neg_ab, exp_neg_ac, exp_neg_ad;
        input [15:0] exp_neg_bc, exp_neg_bd, exp_neg_cd;
        begin
            rd_lane = lane;
            #1;
            if (rd_pos_ab === exp_pos_ab && rd_pos_ac === exp_pos_ac &&
                rd_pos_ad === exp_pos_ad && rd_pos_bc === exp_pos_bc &&
                rd_pos_bd === exp_pos_bd && rd_pos_cd === exp_pos_cd &&
                rd_neg_ab === exp_neg_ab && rd_neg_ac === exp_neg_ac &&
                rd_neg_ad === exp_neg_ad && rd_neg_bc === exp_neg_bc &&
                rd_neg_bd === exp_neg_bd && rd_neg_cd === exp_neg_cd) begin
                $display("PASS: %0s", name);
            end else begin
                $display("FAIL: %0s", name);
                $display("  pos got      AB=%h AC=%h AD=%h BC=%h BD=%h CD=%h",
                         rd_pos_ab, rd_pos_ac, rd_pos_ad,
                         rd_pos_bc, rd_pos_bd, rd_pos_cd);
                $display("  pos expected AB=%h AC=%h AD=%h BC=%h BD=%h CD=%h",
                         exp_pos_ab, exp_pos_ac, exp_pos_ad,
                         exp_pos_bc, exp_pos_bd, exp_pos_cd);
                $display("  neg got      AB=%h AC=%h AD=%h BC=%h BD=%h CD=%h",
                         rd_neg_ab, rd_neg_ac, rd_neg_ad,
                         rd_neg_bc, rd_neg_bd, rd_neg_cd);
                $display("  neg expected AB=%h AC=%h AD=%h BC=%h BD=%h CD=%h",
                         exp_neg_ab, exp_neg_ac, exp_neg_ad,
                         exp_neg_bc, exp_neg_bd, exp_neg_cd);
                errors = errors + 1;
            end
        end
    endtask

    task expect_phase;
        input [255:0] name;
        input exp_match;
        input exp_mismatch;
        begin
            #1;
            if (phase_match === exp_match && phase_mismatch === exp_mismatch) begin
                $display("PASS: %0s", name);
            end else begin
                $display("FAIL: %0s phase_match=%b phase_mismatch=%b expected %b %b",
                         name, phase_match, phase_mismatch, exp_match, exp_mismatch);
                errors = errors + 1;
            end
        end
    endtask

    initial begin
        clk = 1'b0;
        rst_n = 1'b0;
        rd_lane = 4'd0;
        load_en = 1'b0;
        load_lane = 4'd0;
        janus_en = 1'b0;
        janus_src_lane = 4'd0;
        janus_dst_lane = 4'd0;
        dual_mode = MODE_HOLD;
        screw_mode = SCREW_CW;
        phase_offset = 4'd0;
        pos_boundary = 1'b0;
        neg_boundary = 1'b0;
        set_load_values(16'h0000, 16'h0000);
        errors = 0;

        repeat (2) @(posedge clk);
        rst_n = 1'b1;
        @(posedge clk);

        $display("spu13_topology6_state_tb");

        load_lane_state(4'd2, 16'hA000, 16'hB000);
        expect_lane("load/hydrate lane 2", 4'd2,
                    16'hA001, 16'hA002, 16'hA003,
                    16'hA004, 16'hA005, 16'hA006,
                    16'hB001, 16'hB002, 16'hB003,
                    16'hB004, 16'hB005, 16'hB006);

        apply_janus(4'd2, 4'd3, MODE_PISTON, 1'b0, 1'b1);
        expect_lane("piston writes destination lane 3", 4'd3,
                    16'hA001, 16'hA002, 16'hA003,
                    16'hA004, 16'hA005, 16'hA006,
                    16'hB006, 16'hB005, 16'hB004,
                    16'hB001, 16'hB003, 16'hB002);
        expect_lane("source lane 2 preserved after out-of-place piston", 4'd2,
                    16'hA001, 16'hA002, 16'hA003,
                    16'hA004, 16'hA005, 16'hA006,
                    16'hB001, 16'hB002, 16'hB003,
                    16'hB004, 16'hB005, 16'hB006);

        load_lane_state(4'd4, 16'hC000, 16'hD000);
        apply_janus(4'd4, 4'd4, MODE_SEESAW, 1'b1, 1'b1);
        expect_lane("seesaw in-place cross-coupled lane 4", 4'd4,
                    16'hD006, 16'hD005, 16'hD004,
                    16'hD001, 16'hD003, 16'hD002,
                    16'hC006, 16'hC005, 16'hC004,
                    16'hC001, 16'hC003, 16'hC002);

        load_lane_state(4'd5, 16'hE000, 16'hF000);
        phase_offset = 4'd2;
        apply_janus(4'd5, 4'd5, MODE_INDEPENDENT, 1'b1, 1'b0);
        expect_lane("independent first boundary screws positive only", 4'd5,
                    16'hE006, 16'hE005, 16'hE004,
                    16'hE001, 16'hE003, 16'hE002,
                    16'hF001, 16'hF002, 16'hF003,
                    16'hF004, 16'hF005, 16'hF006);
        @(posedge clk);
        apply_janus(4'd5, 4'd5, MODE_INDEPENDENT, 1'b0, 1'b1);
        expect_phase("independent second boundary phase match", 1'b1, 1'b0);
        expect_lane("independent second boundary screws negative", 4'd5,
                    16'hE006, 16'hE005, 16'hE004,
                    16'hE001, 16'hE003, 16'hE002,
                    16'hF006, 16'hF005, 16'hF004,
                    16'hF001, 16'hF003, 16'hF002);

        if (errors == 0) begin
            $display("PASS");
            $finish;
        end else begin
            $display("FAIL");
            $finish;
        end
    end

endmodule
