`timescale 1ns/1ps

module spu13_core_nsa_handshake_tb;
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
    integer cycles;

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
        .boot_done(1'b0), .pell_data(32'd0), .pell_addr(3'd0),
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

    initial begin
        $dumpfile("build/spu13_core_nsa_handshake_tb.vcd");
        $dumpvars(0, spu13_core_nsa_handshake_tb);

        #20 rst_n = 1;
        repeat (2) @(posedge clk);

        $display("TEST: NSA_DQADD waits for NSA core completion");
        @(negedge clk);
        inst_word = {8'h4C, 4'd0, 4'd0, 4'd1, 44'd0};
        inst_valid = 1'b1;

        @(posedge clk);
        #1;
        if (inst_done) begin
            $display("FAIL: NSA_DQADD completed through catch-all path");
            errors = errors + 1;
        end

        cycles = 1;
        while (!inst_done && cycles < 80) begin
            @(posedge clk);
            #1;
            cycles = cycles + 1;
        end

        inst_valid = 1'b0;
        inst_word = 64'd0;

        if (!inst_done) begin
            $display("FAIL: NSA_DQADD did not complete");
            errors = errors + 1;
        end else if (cycles <= 1) begin
            $display("FAIL: NSA_DQADD completion was not delayed");
            errors = errors + 1;
        end else begin
            $display("PASS: NSA_DQADD completion delayed %0d cycles", cycles);
        end

        if (errors == 0)
            $display("PASS");
        else
            $display("FAIL");
        $finish;
    end

endmodule
