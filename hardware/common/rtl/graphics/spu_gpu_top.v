// Sovereign GPU: Top-Level Manifold Orchestrator (v1.1)
// Objective: Unify the "Laminar" graphics primitives into a cohesive adapter.

`include "spu_hal_interface.vh"

module spu_gpu_top #(
    parameter RES_X = 240,
    parameter RES_Y = 240
)(
    input  wire         clk,
    input  wire         reset,
    
    // Vertex Interface (Quadray Stream)
    input  wire         v_valid,
    input  wire [63:0]  v0_abcd, // Projected Vertex 0 (x[31:0], y[63:32])
    input  wire [63:0]  v1_abcd,
    input  wire [63:0]  v2_abcd,
    input  wire [63:0]  v0_attr, // Vertex Attributes (e.g. Color or Normal)
    input  wire [63:0]  v1_attr,
    input  wire [63:0]  v2_attr,
    
    // Display Interface (SPI/OLED)
    output wire         spi_cs_n,
    output wire         spi_sck,
    output wire         spi_mosi,
    output wire         spi_dc,
    
    // Display Interface (VGA 640x480 @ 60Hz)
    output wire         vga_hsync,
    output wire         vga_vsync,
    output wire [3:0]   vga_r,
    output wire [3:0]   vga_g,
    output wire [3:0]   vga_b,
    
    output wire         display_ready, // Added display_ready output
    
    // SDRAM Bridge for external memory
    output wire [24:0]  sdram_addr,
    output wire [15:0]  sdram_wr_data,
    input  wire [15:0]  sdram_rd_data,
    output wire         sdram_wr_en,
    input  wire         sdram_ready,

    // PSRAM Interface (APS6404L QPI)
    output wire         psram_ce_n,
    output wire         psram_clk,
    inout  wire [3:0]   psram_dq,

    // Bio-Resonance Chord
    input  wire [15:0]  bio_chord,

    // Phase-Angle Context Control
    input  wire [1:0]   phase_target,
    input  wire         phase_trigger,

    // SD Card SPI Interface
    output wire         sd_cs_n,
    output wire         sd_sclk,
    output wire         sd_mosi,
    input  wire         sd_miso
);

    // --- 1. Vertex Buffer (FIFO) ---
    wire        fifo_empty, fifo_full;
    wire        fifo_rd_en;
    wire [63:0] rd_v0, rd_v1, rd_v2;
    wire [63:0] rd_attr_0, rd_attr_1, rd_attr_2;

    // Forward declarations for DMA / PSRAM signals (used before their
    // driving instantiation to avoid iverilog Verilog-2001 ordering issues)
    wire        m_psram_rd_en;
    wire [22:0] m_psram_addr;
    wire [7:0]  m_psram_rd_data;
    wire        m_psram_ready;
    wire        pour_psram_wr_en;
    wire [22:0] pour_psram_addr;
    wire [31:0] pour_psram_data;
    wire        storage_rd_en;
    wire [31:0] storage_addr;

    spu_vertex_buffer #(
        .DEPTH(16)
    ) u_vbuf (
        .clk(clk), .reset(reset),
        .wr_en(v_valid),
        .wr_v0(v0_abcd), .wr_v1(v1_abcd), .wr_v2(v2_abcd),
        .wr_attr_v0(v0_attr), .wr_attr_v1(v1_attr), .wr_attr_v2(v2_attr),
        .rd_en(fifo_rd_en),
        .rd_v0(rd_v0), .rd_v1(rd_v1), .rd_v2(rd_v2),
        .rd_attr_v0(rd_attr_0), .rd_attr_v1(rd_attr_1), .rd_attr_v2(rd_attr_2),
        .empty(fifo_empty), .full(fifo_full)
    );

    // --- 2. Command Processor (Z-Propagation) ---
    wire        rast_valid;
    wire [63:0] rast_v0, rast_v1, rast_v2;
    wire [15:0] rast_v0_z, rast_v1_z, rast_v2_z;
    wire [31:0] rast_px, rast_py;
    wire        frame_done;

    spu_command_processor #(
        .RES_X(RES_X), .RES_Y(RES_Y)
    ) u_cmd_proc (
        .clk(clk), .reset(reset),
        .fifo_empty(fifo_empty), .fifo_rd_en(fifo_rd_en),
        .v0_abcd(rd_v0), .v1_abcd(rd_v1), .v2_abcd(rd_v2),
        .v0_attr(rd_attr_0), .v1_attr(rd_attr_1), .v2_attr(rd_attr_2),
        .rast_valid(rast_valid),
        .rast_v0(rast_v0), .rast_v1(rast_v1), .rast_v2(rast_v2),
        .rast_v0_z(rast_v0_z), .rast_v1_z(rast_v1_z), .rast_v2_z(rast_v2_z),
        .rast_px(rast_px), .rast_py(rast_py),
        .frame_done(frame_done)
    );

    // --- 3. Isotropic Rasterizer (Interpolation) ---
    wire        pixel_inside;
    wire [31:0] l0, l1, l2;
    wire [15:0] pixel_z;

    spu_rasterizer u_raster (
        .clk(clk), .reset(reset),
        .v0_abcd(rast_v0), .v1_abcd(rast_v1), .v2_abcd(rast_v2),
        .v0_z(rast_v0_z), .v1_z(rast_v1_z), .v2_z(rast_v2_z),
        .pixel_x(rast_px), .pixel_y(rast_py),
        .pixel_inside(pixel_inside),
        .lambda0(l0), .lambda1(l1), .lambda2(l2),
        .pixel_z(pixel_z)
    );

    // --- 4. Fragment/Lighting Pipe (PBR) ---
    wire [63:0] fragment_energy;
    spu_fragment_pipe u_fragment (
        .clk(clk), .reset(reset),
        .pixel_inside(pixel_inside),
        .lambda0(l0), .lambda1(l1), .lambda2(l2),
        .v0_attr(rd_attr_0), .v1_attr(rd_attr_1), .v2_attr(rd_attr_2),
        .pixel_energy(fragment_energy)
    );

    // --- 5. VGA Render Signals & Framebuffer ---
    wire [15:0] vga_rd_x, vga_rd_y;
    wire [63:0] vram_qa, vram_qb, vram_qc, vram_qd;
    wire [7:0]  vram_energy;

    // --- [NEW] 5. Synergetic Buffer (Z-Occlusion) ---
    wire [24:0] sbuf_addr;
    wire [15:0] sbuf_wr_data;
    wire        sbuf_wr_en;
    wire        z_test_pass;

    spu_synergetic_buffer #(
        .RES_X(RES_X), .RES_Y(RES_Y)
    ) u_sbuf (
        .clk(clk), .reset(reset),
        .test_en(rast_valid && pixel_inside),
        .test_x(rast_px[15:0]), .test_y(rast_py[15:0]),
        .test_z(pixel_z), .test_state(8'h0),
        .test_pass(z_test_pass),
        .sbuf_addr(sbuf_addr), .sbuf_wr_data(sbuf_wr_data),
        .sbuf_rd_data(sdram_rd_data), .sbuf_wr_en(sbuf_wr_en), .sbuf_ready(sdram_ready)
    );

    // --- 6. VRAM Dual-Port Framebuffer ---
    wire [24:0] vram_sdram_addr;
    wire [15:0] vram_sdram_wr_data;
    wire        vram_sdram_wr_en;

    spu_vram_controller #(
        .RES_X(RES_X), .RES_Y(RES_Y)
    ) u_vram (
        .clk(clk), .reset(reset),
        .pixel_inside(pixel_inside && rast_valid),
        .lambda0(l0), .lambda1(l1), .lambda2(l2),
        .interpolated_energy(fragment_energy),
        .wr_x(rast_px[15:0]), .wr_y(rast_py[15:0]),
        .wr_z(pixel_z),
        .z_test_pass(z_test_pass),
        .rd_clk(clk), .rd_x(vga_rd_x), .rd_y(vga_rd_y),
        .out_qa(vram_qa), .out_qb(vram_qb), .out_qc(vram_qc), .out_qd(vram_qd),
        .out_energy(vram_energy),
        .sdram_addr(vram_sdram_addr), .sdram_wr_data(vram_sdram_wr_data),
        .sdram_rd_data(sdram_rd_data), .sdram_wr_en(vram_sdram_wr_en), .sdram_ready(sdram_ready)
    );

    // --- SDRAM Arbiter ---
    assign sdram_addr = sbuf_wr_en ? sbuf_addr : vram_sdram_addr;
    assign sdram_wr_data = sbuf_wr_en ? sbuf_wr_data : vram_sdram_wr_data;
    assign sdram_wr_en = sbuf_wr_en || vram_sdram_wr_en;

    // --- 6. Resonant UI & Command Overlay Composition ---
    wire [7:0]  res_energy;
    wire [23:0] res_rgb;
    wire [15:0] p_tick;

    // Pulse generator for animations
    reg [18:0] p_tick_cnt; reg [15:0] p_tick_val;
    always @(posedge clk or posedge reset) begin
        if (reset) begin p_tick_cnt <= 0; p_tick_val <= 0; end
        else if (p_tick_cnt == 416666) begin p_tick_cnt <= 0; p_tick_val <= p_tick_val + 1; end
        else p_tick_cnt <= p_tick_cnt + 1;
    end
    assign p_tick = p_tick_val;

    spu_resonance_gen #(
        .RES_X(RES_X), .RES_Y(RES_Y)
    ) u_res_gen (
        .clk(clk), .reset(reset), .tick(p_tick),
        .cur_x(vga_rd_x), .cur_y(vga_rd_y),
        .intensity(res_energy), .rgb_out(res_rgb),
        .ctrl_chord(bio_chord)
    );

    wire        cmd_overlay_active;
    wire [7:0]  cmd_overlay_energy;
    wire [23:0] cmd_overlay_rgb;
    wire [15:0] cp_cmd_data = 16'h0; // Placeholder for UI command word
    wire        cp_cmd_valid = 1'b0;

    spu_lithic_overlay #(
        .RES_X(RES_X), .RES_Y(RES_Y)
    ) u_overlay (
        .clk(clk), .reset(reset),
        .cmd_word(cp_cmd_data), .cmd_valid(cp_cmd_valid),
        .cur_x(vga_rd_x), .cur_y(vga_rd_y),
        .overlay_active(cmd_overlay_active),
        .overlay_intensity(cmd_overlay_energy),
        .overlay_rgb(cmd_overlay_rgb)
    );

    // Composite Final Signal
    wire [7:0] final_energy = cmd_overlay_active ? cmd_overlay_energy : 
                             (vram_energy > 0) ? vram_energy : res_energy;
    
    wire [23:0] final_rgb = cmd_overlay_active ? cmd_overlay_rgb :
                           (vram_energy > 0) ? 24'hFFFFFF : res_rgb;

    // --- 8. VGA Display HAL ---
    spu_hal_vga #(
        .RES_X(RES_X), .RES_Y(RES_Y)
    ) u_vga (
        .clk_25mhz(clk), // Assuming master clock is 25.175MHz for VGA
        .reset(reset),
        .rd_x(vga_rd_x),
        .rd_y(vga_rd_y),
        .in_energy(final_energy), // Use composed energy
        .in_rgb(final_rgb),       // New input for RGB
        .vga_hsync(vga_hsync),
        .vga_vsync(vga_vsync),
        .vga_r(vga_r),
        .vga_g(vga_g),
        .vga_b(vga_b)
    );

    // --- 9. SPI Display HAL (Legacy/Secondary Output) ---
    wire display_ready_wire; 

    spu_hal_cartesian #(
        .RES_X(RES_X), .RES_Y(RES_Y)
    ) u_display (
        .clk(clk), .reset(reset),
        .q_a(vram_qa), 
        .q_b(vram_qb), 
        .q_c(vram_qc), 
        .q_energy(vram_energy), 
        .rational_scale(16'h1000), 
        .pulse_61k(clk), 
        .display_ready(display_ready_wire), 
        .spi_cs_n(spi_cs_n), .spi_sck(spi_sck), .spi_mosi(spi_mosi), .spi_dc(spi_dc)
    );
    
    // --- [NEW] 10. Phase-Angle Context Switcher ---
    wire [22:0] translated_psram_addr;
    wire [22:0] logical_psram_addr = m_psram_rd_en ? m_psram_addr : pour_psram_addr;
    
    spu_phase_switch u_phase_sw (
        .clk(clk), .reset(reset),
        .target_phase(phase_target),
        .switch_trigger(phase_trigger),
        .logical_addr(logical_psram_addr),
        .physical_addr(translated_psram_addr),
        .current_phase()
    );

    // --- [NEW] 11. SPU SD Controller (Storage) ---
    wire         sd_ready;
    wire [127:0] sd_data;
    wire         sd_valid;

    spu_sd_controller u_sd (
        .clk(clk), .reset(reset),
        .sclk(sd_sclk), .mosi(sd_mosi), .miso(sd_miso), .cs_n(sd_cs_n),
        .read_trigger(storage_rd_en),
        .read_sector(storage_addr),
        .data_out(sd_data),
        .data_valid(sd_valid),
        .ready(sd_ready),
        .error()
    );

    // --- [NEW] 12. QFS Geometric Pour Controller ---
    spu_qfs_pour u_pour (
        .clk(clk), .reset(reset),
        .storage_ready(sd_ready),
        .storage_data(sd_data),
        .storage_valid(sd_valid),
        .storage_rd_en(storage_rd_en), .storage_addr(storage_addr),
        .psram_wr_en(pour_psram_wr_en),
        .psram_addr(pour_psram_addr),
        .psram_wr_data(pour_psram_data),
        .psram_ready(m_psram_ready),
        .pour_trigger(1'b0), .pour_start_addr(32'h0), .pour_count(16'h0), .pour_busy()
    );

    HAL_PSRAM_APS6404L u_psram_hal (
        .clk(clk), .reset(reset),
        .rd_en(m_psram_rd_en), .wr_en(pour_psram_wr_en),
        .addr(translated_psram_addr), .wr_data(pour_psram_data[7:0]), // Simplified byte write for now
        .rd_data(m_psram_rd_data), .ready(m_psram_ready),
        .psram_ce_n(psram_ce_n), .psram_clk(psram_clk), .psram_dq(psram_dq)
    );

    // --- [NEW] 11. Laminar DMA Bridge ---
    wire        dma_stream_valid;
    wire [7:0]  dma_stream_data;
    
    spu_dma_manifold u_dma (
        .clk(clk), .reset(reset),
        .psram_rd_en(m_psram_rd_en),
        .psram_addr(m_psram_addr),
        .psram_rd_data(m_psram_rd_data),
        .psram_ready(m_psram_ready),
        
        .dma_trigger(1'b0), // Skeleton: trigger by command/timer later
        .dma_start_addr(23'h0),
        .dma_length(16'h100),
        .dma_busy(),
        
        .stream_data(dma_stream_data),
        .stream_valid(dma_stream_valid)
    );

    assign display_ready = display_ready_wire && m_psram_ready;
endmodule
