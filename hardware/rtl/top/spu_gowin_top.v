// spu_gowin_top.v — Tang Primer 20K Sovereign Cluster Master Top
// Target: Gowin GW2A-LV18 (Sovereign Janus Node)
// Architecture: 1x SPU-13 Mother + 128MB DDR3 + HDMI Visualization

`include "spu_arch_defines.vh"

module spu_gowin_top (
    input  wire clk_27,            // 27MHz Onboard oscillator
    input  wire rst_n,             // Primary reset (Active-Low)

    output wire led_heartbeat,     // L16
    output wire [3:1] led,         // Status LEDs

    output wire uart_tx,
    input  wire uart_rx,

    // HDMI / DVI-D Output
    output wire        tmds_clk_p,
    output wire        tmds_clk_n,
    output wire [2:0]  tmds_d_p,
    output wire [2:0]  tmds_d_n,

    // SD Card (TF Slot)
    output wire        sd_cs,
    output wire        sd_clk,
    output wire        sd_mosi,
    input  wire        sd_miso,

    // DDR3 Interface (Will be connected to Gowin IP)
    // These ports are for the Gowin EDA IP Generator bridge
    output wire [12:0] ddr_addr,
    output wire [2:0]  ddr_bank,
    output wire        ddr_cs_n,
    output wire        ddr_ras_n,
    output wire        ddr_cas_n,
    output wire        ddr_we_n,
    output wire        ddr_ck,
    output wire        ddr_ck_n,
    output wire        ddr_cke,
    output wire        ddr_odt,
    output wire        ddr_reset_n,
    output wire [1:0]  ddr_dm,
    inout  wire [15:0] ddr_dq,
    inout  wire [1:0]  ddr_dqs,
    inout  wire [1:0]  ddr_dqs_n
);

    // --- 1. Clock Management (rPLL) ---
    wire clk_100;                  // System / SPU Core
    wire clk_video;                // Pixel Clock (e.g. 74.25 MHz)
    wire clk_video_x5;             // Serializer Clock (371.25 MHz)
    wire pll_lock;

    // TODO: Instantiate GwPLL for 27MHz -> 100MHz & Video Clocks
    // For synthesis verification, we'll use a stub.
    assign clk_100 = clk_27; 
    assign pll_lock = 1'b1;

    // --- 2. SPU Sovereign System ---
    wire [831:0] manifold_state;
    wire         is_janus_point;
    wire         clk_piranha;

    // Manifold Memory Bus (Bridged to DDR3)
    wire                   ext_mem_ready;
    wire                   ext_mem_burst_rd;
    wire                   ext_mem_burst_wr;
    wire [23:0]            ext_mem_addr;
    wire [831:0]           ext_mem_rd_manifold;
    wire [831:0]           ext_mem_wr_manifold;
    wire                   ext_mem_burst_done;

    spu_system u_janus_master (
        .clk_ghost(clk_100),
        .clk_piranha(clk_piranha),
        .clk_fast(clk_100),
        .rst_n(rst_n & pll_lock),

        .master_mode(1'b1),    // Force use of external DDR3 bus
        .is_janus_point(is_janus_point), 
        .manifold_state(manifold_state),

        // SD Card Hydration
        .sd_cs(sd_cs),
        .sd_sck(sd_clk),
        .sd_mosi(sd_mosi),
        .sd_miso(sd_miso),

        // Bridge to DDR3
        .ext_mem_ready(ext_mem_ready),
        .ext_mem_burst_rd(ext_mem_burst_rd),
        .ext_mem_burst_wr(ext_mem_burst_wr),
        .ext_mem_addr(ext_mem_addr),
        .ext_mem_rd_manifold(ext_mem_rd_manifold),
        .ext_mem_wr_manifold(ext_mem_wr_manifold),
        .ext_mem_burst_done(ext_mem_burst_done)
    );

    // --- 3. DDR3 Memory Bridge ---
    // Interfaces SPU manifold bus to Gowin DDR3 IP
    spu_ddr3_bridge_gowin u_ddr_bridge (
        .clk(clk_100),
        .rst_n(rst_n & pll_lock),
        
        .mem_ready(ext_mem_ready),
        .mem_burst_rd(ext_mem_burst_rd),
        .mem_burst_wr(ext_mem_burst_wr),
        .mem_addr(ext_mem_addr),
        .mem_rd_manifold(ext_mem_rd_manifold),
        .mem_wr_manifold(ext_mem_wr_manifold),
        .mem_burst_done(ext_mem_burst_done),

        // DDR3 IP Native Interface (Internal Bridge)
        .ddr_ready(1'b1),      // TODO: Connect to Gowin IP rdy
        .ddr_rd_valid(1'b0),   // TODO: Connect to Gowin IP rd_valid
        .ddr_wr_en(),
        .ddr_rd_en(),
        .ddr_addr(),
        .ddr_wr_data(),
        .ddr_rd_data(32'h0)
    );

    // --- 4. Janus Mirror (HDMI Visualization) ---
    // Reads manifold from memory and renders to DVI-D
    spu_dvi_out u_video (
        .clk_pixel(clk_video),
        .clk_serial(clk_video_x5),
        .rst_n(rst_n & pll_lock),
        .manifold(manifold_state),
        
        .tmds_clk_p(tmds_clk_p),
        .tmds_clk_n(tmds_clk_n),
        .tmds_d_p(tmds_d_p),
        .tmds_d_n(tmds_d_n)
    );

    // --- 4. Status Mapping ---
    assign led_heartbeat = !clk_piranha;
    assign led[1]        = is_janus_point;
    assign led[3:2]      = manifold_state[1:0];
    
    assign uart_tx = ^manifold_state;

endmodule
