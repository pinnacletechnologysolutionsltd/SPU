`default_nettype none

// spu_colorlight_i9_rplu2_top.v — Colorlight i9 RPLU2 pipeline probe
//
// Minimal wrapper: instantiates spu13_core with RPLU2 pipeline enabled.
// No SPI slave, no sidecars — just feeds constant stimuli so Yosys
// preserves the RPLU2 logic and gives us real resource numbers.

module spu_colorlight_i9_rplu2_top (
    input  wire        clk_25m,
    output wire        led,
    output wire        uart_tx,
    input  wire        spi_cs,
    input  wire        spi_sck,
    input  wire        spi_mosi,
    output wire        spi_miso,
    output wire        flash_cs_n,
    output wire        flash_clk,
    output wire        flash_mosi,
    input  wire        flash_miso
);

    // ── Clock: 25 MHz → ~12.5 MHz core ───────────────────────────
    reg clk_core = 1'b0;
    always @(posedge clk_25m) begin
        clk_core <= ~clk_core;
    end

    // ── Fibonacci phi pulses ─────────────────────────────────────
    reg [5:0] phi_cnt = 6'd0;
    wire phi_8, phi_13, phi_21;
    always @(posedge clk_core) begin
        phi_cnt <= (phi_cnt == 6'd41) ? 6'd0 : phi_cnt + 6'd1;
    end
    assign phi_8  = (phi_cnt == 6'd0)  || (phi_cnt == 6'd21);
    assign phi_13 = (phi_cnt == 6'd8)  || (phi_cnt == 6'd29);
    assign phi_21 = (phi_cnt == 6'd0);

    // ── Reset ────────────────────────────────────────────────────
    reg [3:0] rst_sync = 4'd0;
    wire rst_n;
    always @(posedge clk_core) begin
        rst_sync <= {rst_sync[2:0], 1'b1};
    end
    assign rst_n = rst_sync[3];

    // ── Manifold memory bus ──────────────────────────────────────
    wire        mem_ready;
    wire        mem_burst_rd;
    wire        mem_burst_wr;
    wire [23:0] mem_addr;
    wire [831:0] mem_rd_manifold;
    wire [831:0] mem_wr_manifold;
    wire        mem_burst_done;

    assign mem_ready = 1'b1;
    assign mem_rd_manifold = 832'd0;
    assign mem_burst_done = 1'b1;

    // ── External Padé multiplier interface (tied off) ────────────
    wire        pade_mult_start;
    wire [31:0] pade_mult_a0, pade_mult_a1, pade_mult_a2, pade_mult_a3;
    wire [31:0] pade_mult_b0, pade_mult_b1, pade_mult_b2, pade_mult_b3;
    wire [31:0] pade_mult_r0, pade_mult_r1, pade_mult_r2, pade_mult_r3;
    assign pade_mult_r0 = 32'd0; assign pade_mult_r1 = 32'd0;
    assign pade_mult_r2 = 32'd0; assign pade_mult_r3 = 32'd0;

    // ── SPU-13 core with RPLU2 pipeline ────────────────────────────
    spu13_core #(
        .DEVICE("GW5A"),
        .ENABLE_RPLU(0),
        .ENABLE_LATTICE(0),
        .ENABLE_MATH(1),
        .ENABLE_SEQUENCER(1),
        .ENABLE_CORE_SOM(0),
        .ENABLE_CORE_RPLU_V2(1),
        .ENABLE_CORE_RPLU_V2_PIPELINE(1),
        .ENABLE_CORE_RPLU_V2_EXTENSIONS(0),
        .EXTERNAL_RPLU_PADE_MULT(0),
        .SHARE_RPLU_PADE_INV_MULT(1),
        .ENABLE_TORUS(0),
        .MEM_FILE("hardware/rtl/arch/hw_test.mem")
    ) core_inst (
        .clk(clk_core),
        .rst_n(rst_n),
        .phi_8(phi_8),
        .phi_13(phi_13),
        .phi_21(phi_21),

        .dec_fast_cfg_wr_en(1'b0),
        .dec_fast_cfg_sel(3'd0),
        .dec_fast_cfg_material(8'd0),
        .dec_fast_cfg_addr(10'd0),
        .dec_fast_cfg_data(64'd0),
        .phinary_cfg(16'd0),

        .prime_data(24'd0),
        .prime_addr(4'd0),
        .prime_we(1'b0),
        .boot_done(1'b1),
        .pell_data(32'd0),
        .pell_addr(3'd0),
        .pell_we(1'b0),

        .manual_rotor_en(1'b0),
        .manual_rotor_data(64'd0),

        .mem_ready(mem_ready),
        .mem_burst_rd(mem_burst_rd),
        .mem_burst_wr(mem_burst_wr),
        .mem_addr(mem_addr),
        .mem_rd_manifold(mem_rd_manifold),
        .mem_wr_manifold(mem_wr_manifold),
        .mem_burst_done(mem_burst_done),

        .artery_wr_en(),
        .artery_wr_data(),
        .current_axis_ptr(),
        .current_axis_data(),

        .qr_commit_valid(),
        .qr_commit_lane(),
        .qr_commit_A(),
        .qr_commit_B(),
        .qr_commit_C(),
        .qr_commit_D(),

        .inst_valid(1'b0),
        .inst_word(64'd0),
        .inst_done(),

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
        .rplu_dissoc_out(),
        .rplu_dissoc_mask_out(),
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
        .ecc_double_err(),
        .rotc_debug_status(),

        .rplu_pade_mult_start(pade_mult_start),
        .rplu_pade_mult_a0(pade_mult_a0),
        .rplu_pade_mult_a1(pade_mult_a1),
        .rplu_pade_mult_a2(pade_mult_a2),
        .rplu_pade_mult_a3(pade_mult_a3),
        .rplu_pade_mult_b0(pade_mult_b0),
        .rplu_pade_mult_b1(pade_mult_b1),
        .rplu_pade_mult_b2(pade_mult_b2),
        .rplu_pade_mult_b3(pade_mult_b3),
        .rplu_pade_mult_r0(pade_mult_r0),
        .rplu_pade_mult_r1(pade_mult_r1),
        .rplu_pade_mult_r2(pade_mult_r2),
        .rplu_pade_mult_r3(pade_mult_r3),
        .rplu_pade_mult_done(1'b0),
        .rplu_pade_mult_busy(1'b0),
        .rplu_pade_mult_rns_error(1'b0)
    );

    // ── LED: slow blink ──────────────────────────────────────────
    reg [23:0] led_cnt = 24'd0;
    always @(posedge clk_core) begin
        led_cnt <= led_cnt + 24'd1;
    end
    assign led = ~led_cnt[23];

    // Tie unused outputs
    assign uart_tx = 1'b1;
    assign spi_miso = 1'b0;
    assign flash_cs_n = 1'b1;
    assign flash_clk = 1'b0;
    assign flash_mosi = 1'b0;

endmodule
