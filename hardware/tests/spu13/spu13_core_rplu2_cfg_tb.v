`timescale 1ns / 1ps

// spu13_core_rplu2_cfg_tb.v - core-level RPLU2 config hydration smoke test.

module spu13_core_rplu2_cfg_tb;

    reg clk = 1'b0;
    reg rst_n = 1'b0;
    always #5 clk = ~clk;

    reg         cfg_wr_en = 1'b0;
    reg [2:0]   cfg_sel = 3'd0;
    reg [9:0]   cfg_addr = 10'd0;
    reg [63:0]  cfg_data = 64'd0;
    reg         inst_valid = 1'b0;
    reg [63:0]  inst_word = 64'd0;

    wire inst_done;
    wire rplu_dissoc_out;
    wire [12:0] rplu_dissoc_mask_out;
    wire mem_burst_rd;
    wire mem_burst_wr;
    wire [23:0] mem_addr;
    wire [831:0] mem_wr_manifold;
    wire qr_commit_valid;
    wire [3:0] qr_commit_lane;
    wire [63:0] qr_commit_A;
    wire [63:0] qr_commit_B;
    wire [63:0] qr_commit_C;
    wire [63:0] qr_commit_D;

    integer errors = 0;
    integer wait_i;
    reg seen_quad;
    reg seen_thimble;
    reg seen_qr_commit;
    reg quad_coherent_seen;
    reg quad_dissoc_seen;
    reg [31:0] quad_delta_seen;
    reg [31:0] thimble_c0_seen;
    reg [3:0] qr_lane_seen;
    reg [63:0] qr_A_seen;
    reg [63:0] qr_B_seen;
    reg [63:0] qr_C_seen;
    reg [63:0] qr_D_seen;

    localparam [2:0] CFG_PADE_NUM = 3'd1;
    localparam [2:0] CFG_PADE_DEN = 3'd2;
    localparam [2:0] CFG_BTU_ROW  = 3'd3;
    localparam [2:0] CFG_KAPPA    = 3'd6;

    spu13_core #(
        .DEVICE("SIM"),
        .ENABLE_RPLU(0),
        .ENABLE_LATTICE(0),
        .ENABLE_MATH(0),
        .ENABLE_SEQUENCER(0),
        .ENABLE_CORE_SOM(0),
        .ENABLE_CORE_RPLU_V2(1),
        .ENABLE_CORE_RPLU_V2_PIPELINE(1),
        .ENABLE_CORE_RPLU_V2_EXTENSIONS(0),
        .SHARE_RPLU_PADE_INV_MULT(1)
    ) uut (
        .clk(clk),
        .rst_n(rst_n),
        .phi_8(1'b0),
        .phi_13(1'b0),
        .phi_21(1'b0),
        .dec_fast_cfg_wr_en(cfg_wr_en),
        .dec_fast_cfg_sel(cfg_sel),
        .dec_fast_cfg_material(8'd0),
        .dec_fast_cfg_addr(cfg_addr),
        .dec_fast_cfg_data(cfg_data),
        .phinary_cfg(16'd0),
        .prime_data(24'd0),
        .prime_addr(4'd0),
        .prime_we(1'b0),
        .boot_done(1'b0),
        .pell_data(32'd0),
        .pell_addr(3'd0),
        .pell_we(1'b0),
        .manual_rotor_en(1'b0),
        .manual_rotor_data(64'd0),
        .mem_ready(1'b1),
        .mem_burst_rd(mem_burst_rd),
        .mem_burst_wr(mem_burst_wr),
        .mem_addr(mem_addr),
        .mem_rd_manifold(832'd0),
        .mem_wr_manifold(mem_wr_manifold),
        .mem_burst_done(1'b0),
        .artery_wr_en(),
        .artery_wr_data(),
        .current_axis_ptr(),
        .current_axis_data(),
        .qr_commit_valid(qr_commit_valid),
        .qr_commit_lane(qr_commit_lane),
        .qr_commit_A(qr_commit_A),
        .qr_commit_B(qr_commit_B),
        .qr_commit_C(qr_commit_C),
        .qr_commit_D(qr_commit_D),
        .inst_valid(inst_valid),
        .inst_word(inst_word),
        .inst_done(inst_done),
        .ratio_cmp_res(),
        .ratio_cmp_valid(),
        .manifold_out(),
        .bloom_complete(),
        .scale_table_out(),
        .scale_overflow_out(),
        .is_janus_point(),
        .audio_mode(),
        .gasket_sum_out(),
        .quadrance_out(),
        .cycle_wrap(),
        .rplu_dissoc_out(rplu_dissoc_out),
        .rplu_dissoc_mask_out(rplu_dissoc_mask_out),
        .rplu_addr_out(),
        .i2s_bclk(),
        .i2s_lrclk(),
        .i2s_dout(),
        .laminar_flow_index_out(),
        .thermal_pressure_out(),
        .hex_valid(),
        .hex_q(),
        .hex_r(),
        .audio_p_out(),
        .audio_q_out(),
        .axiomatic_fault(),
        .fault_type(),
        .fault_count(),
        .rns_error(),
        .ecc_single_err(),
        .ecc_double_err()
    );

    function [63:0] pack;
        input [7:0] op;
        input [7:0] r1;
        input [7:0] r2;
        input [15:0] p1_a;
        input [15:0] p1_b;
        begin
            pack = {op, r1, r2, p1_a, p1_b, 8'd0};
        end
    endfunction

    task cfg_write;
        input [2:0] sel;
        input [9:0] addr;
        input [63:0] data;
        begin
            @(negedge clk);
            cfg_sel = sel;
            cfg_addr = addr;
            cfg_data = data;
            cfg_wr_en = 1'b1;
            @(negedge clk);
            cfg_wr_en = 1'b0;
            cfg_sel = 3'd0;
            cfg_addr = 10'd0;
            cfg_data = 64'd0;
        end
    endtask

    task issue;
        input [63:0] word;
        integer guard;
        begin
            @(negedge clk);
            inst_word = word;
            inst_valid = 1'b1;
            guard = 0;
            while (!inst_done && guard < 80) begin
                @(posedge clk);
                guard = guard + 1;
            end
            @(negedge clk);
            inst_valid = 1'b0;
            inst_word = 64'd0;
            if (guard >= 80) begin
                $display("FAIL: instruction timeout word=%h", word);
                errors = errors + 1;
            end
        end
    endtask

    task issue_pulse;
        input [63:0] word;
        begin
            @(negedge clk);
            inst_word = word;
            inst_valid = 1'b1;
            @(negedge clk);
            inst_valid = 1'b0;
            inst_word = 64'd0;
        end
    endtask

    task run_rplu2;
        begin
            seen_quad = 1'b0;
            seen_thimble = 1'b0;
            seen_qr_commit = 1'b0;
            quad_coherent_seen = 1'b0;
            quad_dissoc_seen = 1'b0;
            quad_delta_seen = 32'd0;
            thimble_c0_seen = 32'd0;
            qr_lane_seen = 4'd0;
            qr_A_seen = 64'd0;
            qr_B_seen = 64'd0;
            qr_C_seen = 64'd0;
            qr_D_seen = 64'd0;

            issue_pulse(pack(8'h2A, 8'd4, 8'd0, 16'd0, 16'd0));

            for (wait_i = 0; wait_i < 1500; wait_i = wait_i + 1) begin
                @(posedge clk);
                if (uut.gen_rplu_v2.rplu2_quadray_valid) begin
                    seen_quad = 1'b1;
                    quad_coherent_seen = uut.gen_rplu_v2.rplu2_quadray_coherent;
                    quad_delta_seen = uut.gen_rplu_v2.rplu2_quadray_delta;
                    quad_dissoc_seen = rplu_dissoc_out;
                end
                if (uut.gen_rplu_v2.rplu2_thimble_valid) begin
                    seen_thimble = 1'b1;
                    thimble_c0_seen = uut.gen_rplu_v2.rplu2_thimble_c0;
                end
                if (qr_commit_valid) begin
                    seen_qr_commit = 1'b1;
                    qr_lane_seen = qr_commit_lane;
                    qr_A_seen = qr_commit_A;
                    qr_B_seen = qr_commit_B;
                    qr_C_seen = qr_commit_C;
                    qr_D_seen = qr_commit_D;
                end
            end
        end
    endtask

    initial begin
        #30 rst_n = 1'b1;
        repeat (2) @(posedge clk);

        // Padé numerator coefficient 0 = (2,0,0,0), denominator remains identity.
        cfg_write(CFG_PADE_NUM, 10'd0, {32'd0, 32'd2});
        cfg_write(CFG_PADE_NUM, 10'd8, 64'd0);

        // BTU row 1 = Quadray/A31 coordinate tuple (1,0,0,0).
        cfg_write(CFG_BTU_ROW, 10'd1, {32'd0, 32'd1});
        cfg_write(CFG_BTU_ROW, 10'd65, 64'd0);

        if (uut.gen_rplu_v2.u_rplu_v2.u_pade.num_coeff[0][0] !== 32'd2) begin
            $display("FAIL: Padé numerator coeff0 did not hydrate");
            errors = errors + 1;
        end
        if (uut.gen_rplu_v2.u_rplu_v2.u_btu.lane0_rom.mem[1] !== 32'd1) begin
            $display("FAIL: BTU row 1 lane0 did not hydrate");
            errors = errors + 1;
        end

        // Load QR0=(2,0,0,0), which the default SOM fixture classifies to node 1.
        issue(pack(8'h1D, 8'd0, 8'd0, 16'h0200, 16'h0000));

        // Coherent target: quadrance(1,0,0,0)=3.
        cfg_write(CFG_KAPPA, 10'd0, 64'd3);
        run_rplu2();
        if (!seen_quad || !quad_coherent_seen || quad_delta_seen !== 32'd0 || quad_dissoc_seen) begin
            $display("FAIL: coherent RPLU2 quad seen=%b coh=%b delta=%h dissoc=%b",
                     seen_quad, quad_coherent_seen, quad_delta_seen, quad_dissoc_seen);
            errors = errors + 1;
        end
        if (!seen_thimble || thimble_c0_seen !== 32'd2) begin
            $display("FAIL: Padé hydrated result seen=%b c0=%h", seen_thimble, thimble_c0_seen);
            errors = errors + 1;
        end
        if (!seen_qr_commit || qr_lane_seen !== 4'd4 ||
            qr_A_seen !== 64'd2 || qr_B_seen !== 64'd0 ||
            qr_C_seen !== 64'd0 || qr_D_seen !== 64'd0) begin
            $display("FAIL: Padé public commit seen=%b lane=%0d A=%h B=%h C=%h D=%h",
                     seen_qr_commit, qr_lane_seen,
                     qr_A_seen, qr_B_seen, qr_C_seen, qr_D_seen);
            errors = errors + 1;
        end

        // Off-variety target: same BTU row against kappa=4 yields delta=-1 mod M31.
        cfg_write(CFG_KAPPA, 10'd0, 64'd4);
        run_rplu2();
        if (!seen_quad || quad_coherent_seen || quad_delta_seen !== 32'h7ffffffe || !quad_dissoc_seen) begin
            $display("FAIL: off-variety RPLU2 quad seen=%b coh=%b delta=%h dissoc=%b",
                     seen_quad, quad_coherent_seen, quad_delta_seen, quad_dissoc_seen);
            errors = errors + 1;
        end

        if (errors == 0)
            $display("PASS: spu13_core_rplu2_cfg_tb");
        else
            $display("FAIL: spu13_core_rplu2_cfg_tb (%0d errors)", errors);

        $finish;
    end

endmodule
