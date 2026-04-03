// spu_13_top.v
module spu_13_top (
    input clk_12mhz, clk_1mhz, rst_n,
    // Legacy SPU-4 Link (for backward compatibility / Genesis TB)
    input [15:0] spu4_rx,
    output [31:0] spu4_tx,
    output [7:0] uart_tx_byte,
    output uart_tx_en,
    output piranha_pulse,
    input  alu_start,
    output alu_done,

    // SPI Flash Interface (The Soul)
    output flash_cs,
    output flash_clk,
    input  flash_miso,
    output flash_mosi,

    // Ground Control Telemetry
    output uart_tx
);

    wire sync_alert;
    wire [7:0] satellite_dissonance;
    // Interconnect logic must happen after prime_anchor is defined.
    // We will place link_inst lower down.

    // Internal BRAM for Thomson Primes
    wire [23:0] prime_anchor;
    wire [3:0]  prime_addr;
    wire        bram_we;
    wire        boot_complete;

    // --- Metastability Guard (Double-Flop Sync) ---
    // Protects the Core domain from SPI clock skew
    reg [1:0] boot_sync;
    always @(posedge clk_12mhz or negedge rst_n) begin
        if (!rst_n) boot_sync <= 2'b00;
        else boot_sync <= {boot_sync[0], boot_complete};
    end
    wire boot_synced = boot_sync[1];

    // 1. The Laminar Boot (SPI Controller)
    spu_laminar_boot boot_unit (
        .clk(clk_12mhz),
        .rst_n(rst_n),
        .flash_cs(flash_cs),
        .flash_sck(flash_clk),
        .flash_miso(flash_miso),
        .flash_mosi(flash_mosi),
        .bram_data(prime_anchor),
        .bram_addr(prime_addr),
        .bram_we(bram_we),
        .boot_done(boot_complete)
    );

    // 1.5 The Mother-to-Satellite Broadcaster
    spu_node_link link_inst (
        .clk(clk_12mhz), 
        .rst_n(rst_n), 
        .prime_anchor_in(prime_anchor),
        .rx_frame(spu4_rx), 
        .tx_frame(spu4_tx), 
        .sync_alert(sync_alert),
        .satellite_dissonance(satellite_dissonance)
    );

    // 2. The 13D Recursive Engine (The Body)
    // The previous implementation used spu_unified_alu_tdm
    wire [17:0] alu_result_18;
    wire [31:0] operand_A, operand_B; // Driven by testbench force
    spu_unified_alu_tdm alu_inst (
        .clk(clk_12mhz), 
        .rst_n(rst_n), 
        .reset(~rst_n),
        .start(alu_start),
        .done(alu_done),
        .sync_alert(sync_alert), 
        .led_status(),
        .A_in(operand_A),
        .B_in(operand_B),
        .result_18(alu_result_18)
    );

    wire [23:0] current_surd = {6'b0, alu_result_18};

    // 3. The Janus Mirror (The Shadow / Sanity Gate)
    wire [31:0] shadow_out;
    wire        symmetry_lock;
    spu_janus_mirror mirror_unit (
        .clk(clk_12mhz),
        .rst_n(rst_n),
        .surd_in({8'b0, current_surd}),
        .shadow_out(shadow_out),
        .snap_laminar(symmetry_lock),
        .snap_null(),
        .snap_shadow(),
        .quadrance_out()
    );
    assign piranha_pulse = symmetry_lock;

    // 4. The Berry Gate (The Observer)
    reg [23:0] prev_surd;
    always @(posedge clk_12mhz) if (rst_n) prev_surd <= current_surd;

    wire [23:0] berry_residue;
    spu_berry_gate observer_unit (
        .clk(clk_12mhz),
        .rst_n(rst_n),
        .s_vector(current_surd),
        .s_prev(prev_surd),
        .holonomy_residue(berry_residue)
    );

    // 5. UART Heartbeat (The Telemetry)
    // Transmits [Surd | Berry Residue] to Ground Control
    // Since we don't have uart_tx_telemetry, we use a assign for now.
    assign uart_tx = ^berry_residue;
    assign uart_tx_byte = berry_residue[7:0];
    assign uart_tx_en = boot_synced;

endmodule
