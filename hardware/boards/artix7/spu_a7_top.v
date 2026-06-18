// spu_a7_top.v — SPU-13 Artix-7 Unified Top-Level (v1.1)
//
// Spin selection via SPIN parameter — no need to manually toggle ENABLE_*:
//
//   SPIN = "MULTIMEDIA"  — MATH + GPU + RPLU + I2S  (gaming, visualisation, audio)
//   SPIN = "INTELLIGENCE" — SOM + GATEKEEPER + RPLU  (synthetic intelligence, clustering)
//   SPIN = "ROBOTICS"    — MATH + GATEKEEPER          (kinematics, avionics, simulation)
//   SPIN = "FULL"        — everything                  (development, 100T/200T)
//   SPIN = "SENSOR"      — MATH only, minimal          (medical wearables, iCESugar)
//   SPIN = "CUSTOM"      — use individual ENABLE_* parameters
//
// RP2350 Southbridge: SPI slave Mode 0, 2 MHz.
//   CMD 0xA0 → read manifold burst (32 bytes)
//   CMD 0xAC → read status (label, ambiguous, fault_type, fault_count)
//   CMD 0xB0 → write instruction word (8 bytes)
//   CMD 0xB1 → write + pulse inst_valid

module spu_a7_top #(
    parameter DEVICE            = "A7_100T",
    parameter SPIN              = "FULL",
    parameter ENABLE_MATH       = 1,
    parameter ENABLE_SOM        = 1,
    parameter ENABLE_GATEKEEPER = 1,
    parameter ENABLE_GPU        = 1,
    parameter ENABLE_RPLU       = 0,
    parameter ENABLE_I2S        = 0,
    parameter ENABLE_LATTICE    = 0,
    parameter ENABLE_SDRAM      = 0
)(
    input  wire        clk_100mhz,
    input  wire        rst_n,
    input  wire        spi_cs_n, spi_sck, spi_mosi,
    output wire        spi_miso,
    output wire        uart_tx,
    output wire [3:0]  hdmi_d_p, hdmi_d_n,
    output wire        hdmi_clk_p, hdmi_clk_n,
    output wire        i2s_bclk, i2s_lrclk, i2s_dout,
    input  wire [7:0]  sensor_in,
    output wire [3:0]  led_out,
    output wire        fault_led
);

    // ── Spin → parameter resolution ────────────────────────────
    localparam _M = (SPIN == "CUSTOM") ? ENABLE_MATH :
        (SPIN != "INTELLIGENCE") ? 1 : 0;
    localparam _S = (SPIN == "CUSTOM") ? ENABLE_SOM :
        (SPIN == "INTELLIGENCE" || SPIN == "FULL") ? 1 : 0;
    localparam _K = (SPIN == "CUSTOM") ? ENABLE_GATEKEEPER :
        (SPIN == "SENSOR") ? 0 : 1;
    localparam _G = (SPIN == "CUSTOM") ? ENABLE_GPU :
        (SPIN == "MULTIMEDIA" || SPIN == "FULL") ? 1 : 0;
    localparam _R = (SPIN == "CUSTOM") ? ENABLE_RPLU :
        (SPIN == "MULTIMEDIA" || SPIN == "INTELLIGENCE" || SPIN == "FULL") ? 1 : 0;
    localparam _I = (SPIN == "CUSTOM") ? ENABLE_I2S :
        (SPIN == "MULTIMEDIA" || SPIN == "FULL") ? 1 : 0;

    wire clk_fast = clk_100mhz;
    wire inst_valid, inst_done;
    wire [63:0] inst_word;
    wire hex_valid;
    wire [15:0] hex_q, hex_r;
    wire axiomatic_fault;
    wire [1:0] fault_type;
    wire [15:0] fault_count;

    // ── Sierpiński Floorplanner (Fibonacci 8/13/21 timing) ──
    wire phi_8, phi_13, phi_21, phi_heart;
    spu_sierpinski_clk u_floorplan (
        .clk(clk_fast), .rst_n(rst_n),
        .phi_8(phi_8), .phi_13(phi_13), .phi_21(phi_21),
        .heartbeat(phi_heart)
    );

    // ── SPU-13 Core ──────────────────────────────────────────
    spu13_core #(
        .DEVICE(DEVICE == "A7_35T" ? "GW2A" : "GW5A"),
        .ENABLE_RPLU(_R), .ENABLE_LATTICE(ENABLE_LATTICE),
        .ENABLE_MATH(_M), .ENABLE_SEQUENCER(0), .ENABLE_CORE_SOM(_S)
    ) u_core (
        .clk(clk_fast), .rst_n(rst_n),
        .phi_8(phi_8), .phi_13(phi_13), .phi_21(phi_21),
        .dec_fast_cfg_wr_en(1'b0), .dec_fast_cfg_sel(3'd0),
        .dec_fast_cfg_material(8'd0), .dec_fast_cfg_addr(10'd0),
        .dec_fast_cfg_data(64'd0),
        .phinary_cfg({12'd0, (_K ? 2'b00 : 2'b11)}),
        .prime_data(24'd0), .prime_addr(4'd0), .prime_we(1'b0),
        .boot_done(1'b1),
        .pell_data(32'd0), .pell_addr(3'd0), .pell_we(1'b0),
        .manual_rotor_en(1'b0), .manual_rotor_data(64'd0),
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
        .i2s_bclk(i2s_bclk), .i2s_lrclk(i2s_lrclk), .i2s_dout(i2s_dout),
        .laminar_flow_index_out(), .thermal_pressure_out(),
        .hex_valid(hex_valid), .hex_q(hex_q), .hex_r(hex_r),
        .audio_p_out(), .audio_q_out(),
        .axiomatic_fault(axiomatic_fault), .fault_type(fault_type),
        .fault_count(fault_count)
    );

    // ── SPI Slave → Instruction Bridge ──────────────────────
    spu_spi_slave u_spi (
        .clk(clk_fast), .rst_n(rst_n),
        .spi_cs_n(spi_cs_n), .spi_sck(spi_sck),
        .spi_mosi(spi_mosi), .spi_miso(spi_miso),
        .inst_valid(inst_valid), .inst_word(inst_word),
        .inst_done(inst_done),
        .hex_valid(hex_valid), .hex_q(hex_q), .hex_r(hex_r),
        .axiomatic_fault(axiomatic_fault), .fault_type(fault_type),
        .fault_count(fault_count)
    );

    // ── UART TX ─────────────────────────────────────────────
    spu_uart_tx #(.BAUD(115200), .CLK_HZ(100_000_000)) u_uart (
        .clk(clk_fast), .rst_n(rst_n),
        .tx_data({hex_q, hex_r}), .tx_valid(hex_valid),
        .tx(uart_tx), .tx_ready()
    );

    assign led_out = {3'b0, inst_done};
    assign fault_led = axiomatic_fault;

endmodule
