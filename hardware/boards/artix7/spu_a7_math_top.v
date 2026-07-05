// spu_a7_math_top.v — Artix-7 Minimal Math Probe
// Direct sequencer → core, bypasses SPI slave for validation.

module spu_a7_math_top (
    input  wire        clk,
    input  wire        rst_n,
    output wire [1:0]  led
);

    wire        inst_valid, inst_done;
    wire [63:0] inst_word;
    wire        hex_valid;
    wire [15:0] hex_q, hex_r;
    wire        axiomatic_fault;
    wire [1:0]  fault_type;
    wire [15:0] fault_count;

    spu_sequencer #(.IMEM_DEPTH(64)) u_seq (
        .clk(clk), .rst_n(rst_n), .boot_done(1'b1),
        .inst_valid(inst_valid), .inst_word(inst_word),
        .inst_done(inst_done), .pc_out(), .halted(), .program_size()
    );

    spu13_core #(
        .DEVICE("GW2A"), .ENABLE_RPLU(0), .ENABLE_LATTICE(0),
        .ENABLE_MATH(1), .ENABLE_SEQUENCER(0), .ENABLE_CORE_SOM(0)
    ) u_core (
        .clk(clk), .rst_n(rst_n),
        .phi_8(1'b0), .phi_13(1'b0), .phi_21(1'b0),
        .dec_fast_cfg_wr_en(1'b0), .dec_fast_cfg_sel(3'd0),
        .dec_fast_cfg_material(8'd0), .dec_fast_cfg_addr(10'd0),
        .dec_fast_cfg_data(64'd0), .phinary_cfg(16'h000C),
        .prime_data(24'd0), .prime_addr(4'd0), .prime_we(1'b0),
        .boot_done(1'b1), .pell_data(32'd0), .pell_addr(3'd0),
        .pell_we(1'b0), .manual_rotor_en(1'b0), .manual_rotor_data(64'd0),
        .mem_ready(1'b1), .mem_burst_rd(), .mem_burst_wr(),
        .mem_addr(), .mem_rd_manifold(832'd0), .mem_wr_manifold(),
        .mem_burst_done(1'b0),
        .artery_wr_en(), .artery_wr_data(),
        .current_axis_ptr(), .current_axis_data(),
        .inst_valid(inst_valid), .inst_word(inst_word), .inst_done(inst_done),
        .ratio_cmp_res(), .ratio_cmp_valid(),
        .manifold_out(), .bloom_complete(), .scale_table_out(),
        .scale_overflow_out(), .is_janus_point(),
        .audio_mode(), .gasket_sum_out(), .quadrance_out(), .cycle_wrap(),
        .rplu_dissoc_out(), .rplu_dissoc_mask_out(), .rplu_addr_out(),
        .i2s_bclk(), .i2s_lrclk(), .i2s_dout(),
        .laminar_flow_index_out(), .thermal_pressure_out(),
        .hex_valid(hex_valid), .hex_q(hex_q), .hex_r(hex_r),
        .audio_p_out(), .audio_q_out(),
        .axiomatic_fault(axiomatic_fault), .fault_type(fault_type),
        .fault_count(fault_count),
        .rns_error(),
        .ecc_single_err(),
        .ecc_double_err()
    );

    assign led = {axiomatic_fault, inst_done};

endmodule
