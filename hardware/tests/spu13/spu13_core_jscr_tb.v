`timescale 1ns/1ps

module spu13_core_jscr_tb;
    reg clk = 0;
    reg rst_n = 0;
    always #5 clk = ~clk;

    reg inst_valid = 1'b0;
    reg [63:0] inst_word = 64'd0;
    wire inst_done;

    wire mem_burst_rd;
    wire mem_burst_wr;
    wire [23:0] mem_addr;
    wire [831:0] mem_wr_manifold;
    integer errors = 0;

    localparam MODE_PISTON = 2'd0;
    localparam SCREW_CW = 2'd1;

    spu13_core #(
        .DEVICE("SIM"),
        .ENABLE_RPLU(0),
        .ENABLE_LATTICE(0),
        .ENABLE_MATH(1),
        .ENABLE_SEQUENCER(0),
        .ENABLE_CORE_SOM(0),
        .ENABLE_CORE_RPLU_V2(1),
        .ENABLE_CORE_RPLU_V2_EXTENSIONS(1)
    ) uut (
        .clk(clk), .rst_n(rst_n),
        .phi_8(1'b0), .phi_13(1'b0), .phi_21(1'b0),
        .dec_fast_cfg_wr_en(1'b0), .dec_fast_cfg_sel(3'd0),
        .dec_fast_cfg_material(8'd0), .dec_fast_cfg_addr(10'd0),
        .dec_fast_cfg_data(64'd0), .phinary_cfg(16'd0),
        .prime_data(24'd0), .prime_addr(4'd0), .prime_we(1'b0),
        .boot_done(1'b1)  /* canonical boot contract: hydration interlock makes early writes safe (BOOT_SEQUENCE_FSM.md) */, .pell_data(32'd0), .pell_addr(3'd0),
        .pell_we(1'b0), .manual_rotor_en(1'b0), .manual_rotor_data(64'd0),
        .mem_ready(1'b1), .mem_burst_rd(mem_burst_rd),
        .mem_burst_wr(mem_burst_wr), .mem_addr(mem_addr),
        .mem_rd_manifold(832'd0), .mem_wr_manifold(mem_wr_manifold),
        .mem_burst_done(1'b0),
        .artery_wr_en(), .artery_wr_data(),
        .current_axis_ptr(), .current_axis_data(),
        .qr_commit_valid(), .qr_commit_lane(),
        .qr_commit_A(), .qr_commit_B(), .qr_commit_C(), .qr_commit_D(),
        .inst_valid(inst_valid), .inst_word(inst_word), .inst_done(inst_done),
        .ratio_cmp_res(), .ratio_cmp_valid(),
        .manifold_out(), .bloom_complete(), .scale_table_out(),
        .scale_overflow_out(), .is_janus_point(),
        .audio_mode(), .gasket_sum_out(), .quadrance_out(), .cycle_wrap(),
        .rplu_dissoc_out(), .rplu_dissoc_mask_out(), .rplu_addr_out(),
        .i2s_bclk(), .i2s_lrclk(), .i2s_dout(),
        .laminar_flow_index_out(), .thermal_pressure_out(),
        .hex_valid(), .hex_q(), .hex_r(), .audio_p_out(), .audio_q_out(),
        .axiomatic_fault(), .fault_type(), .fault_count(),
        .rns_error(),
        .ecc_single_err(),
        .ecc_double_err()
    );

    function [63:0] pack_legacy;
        input [7:0] op;
        input [7:0] r1;
        input [7:0] r2;
        input [15:0] p1_a;
        input [15:0] p1_b;
        begin
            pack_legacy = {op, r1, r2, p1_a, p1_b, 8'd0};
        end
    endfunction

    function [63:0] pack_jscr;
        input [4:0] dst;
        input [4:0] src;
        input [1:0] dual_mode;
        input [1:0] screw_mode;
        input pos_boundary;
        input neg_boundary;
        input [10:0] phase_offset;
        begin
            pack_jscr = {8'h48, dst, src, dual_mode, screw_mode,
                         pos_boundary, neg_boundary, 29'd0, phase_offset};
        end
    endfunction

    task issue;
        input [63:0] word;
        integer guard;
        begin
            @(posedge clk);
            inst_word <= word;
            inst_valid <= 1'b1;
            guard = 0;
            while (!inst_done && guard < 80) begin
                @(posedge clk);
                guard = guard + 1;
            end
            inst_valid <= 1'b0;
            inst_word <= 64'd0;
            @(posedge clk);
            #1;
            if (guard >= 80) begin
                $display("FAIL: instruction timeout word=%h", word);
                errors = errors + 1;
            end
        end
    endtask

    task check_edge;
        input [255:0] name;
        input [63:0] got;
        input [63:0] expected;
        begin
            if (got === expected) begin
                $display("PASS: %0s", name);
            end else begin
                $display("FAIL: %0s got=%h expected=%h", name, got, expected);
                errors = errors + 1;
            end
        end
    endtask

    initial begin
        $dumpfile("build/spu13_core_jscr_tb.vcd");
        $dumpvars(0, spu13_core_jscr_tb);

        #20 rst_n = 1;
        repeat (2) @(posedge clk);

        $display("TEST 1: QLDI hydrates topology6 shadow lane 2");
        issue(pack_legacy(8'h1D, 8'd2, 8'd0, 16'h0A14, 16'h1E28));

        check_edge("lane2 pos AB = A-B", uut.gen_nsa_core.u_topology6.pos_ab[2],
                   64'h00000000_FFFFFFF6);
        check_edge("lane2 pos AC = A-C", uut.gen_nsa_core.u_topology6.pos_ac[2],
                   64'h00000000_FFFFFFEC);
        check_edge("lane2 pos AD = A-D", uut.gen_nsa_core.u_topology6.pos_ad[2],
                   64'h00000000_FFFFFFE2);
        check_edge("lane2 neg AD = D-A", uut.gen_nsa_core.u_topology6.neg_ad[2],
                   64'h00000000_0000001E);

        $display("TEST 2: JSCR piston writes topology lane 3");
        issue(pack_jscr(5'd3, 5'd2, MODE_PISTON, SCREW_CW, 1'b0, 1'b1, 11'd0));

        check_edge("lane3 pos AB unchanged", uut.gen_nsa_core.u_topology6.pos_ab[3],
                   64'h00000000_FFFFFFF6);
        check_edge("lane3 pos CD unchanged", uut.gen_nsa_core.u_topology6.pos_cd[3],
                   64'h00000000_FFFFFFF6);
        check_edge("lane3 neg AB = old neg CD", uut.gen_nsa_core.u_topology6.neg_ab[3],
                   64'h00000000_0000000A);
        check_edge("lane3 neg AC = old neg BD", uut.gen_nsa_core.u_topology6.neg_ac[3],
                   64'h00000000_00000014);
        check_edge("lane3 neg BD = old neg AD", uut.gen_nsa_core.u_topology6.neg_bd[3],
                   64'h00000000_0000001E);

        if (errors == 0) begin
            $display("PASS");
            $finish;
        end else begin
            $display("FAIL");
            $finish;
        end
    end

endmodule
