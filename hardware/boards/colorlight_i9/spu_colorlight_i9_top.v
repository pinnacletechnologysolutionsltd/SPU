
`default_nettype none

module spu_colorlight_i9_top (
    input wire          clk_25m,          // 25 MHz clock from on-board oscillator (P3)
    output wire         led,              // LED D2 (active low)

    // UART Telemetry (to external serial console @ 115.2 kbaud)
    output wire         uart_tx,

    // SPI Flash Interface (on-board W25Q64, optional: southbridge use)
    output wire         flash_cs_n,
    output wire         flash_clk,
    output wire         flash_mosi,
    input wire          flash_miso,

    // SPI Southbridge Bus (optional: for future RP2350 integration)
    input wire          spi_cs,
    input wire          spi_sck,
    input wire          spi_mosi,
    output wire         spi_miso
);

    wire clk_12mhz_int;
    wire rst_n_int;

    // Internal reset (tie high for now; Colorlight i9 manages reset internally)
    assign rst_n_int = 1'b1;  // Always out of reset

    // Clock divider: 25 MHz → 12 MHz (actually ~12.5 MHz, close enough for testing)
    // Fibonacci pulse timing is soft-timed, not hard-realtime
    reg [1:0] clk_div_cnt = 2'b00;
    always @(posedge clk_25m) begin
        if (clk_div_cnt == 2'd1) clk_div_cnt <= 2'b00;
        else clk_div_cnt <= clk_div_cnt + 2'd1;
    end
    assign clk_12mhz_int = (clk_div_cnt == 2'd0);  // 50% duty, ~12.5 MHz

    // Instantiate the SPU-13 core (including RPLU v2 pipeline)
    spu13_top spu13_core_inst (
        .clk_12mhz(clk_12mhz_int),
        .clk_1mhz(1'b0), // Tie off for now, needs proper generation
        .rst_n(rst_n_int),

        // Legacy SPU-4 Link - tie off
        .spu4_rx(16'b0),
        .spu4_tx(), // Unconnected output

        // Telemetry/Status Outputs
        .uart_tx_byte(), // Not connected to top-level pins for now
        .uart_tx_en(),   // Not connected to top-level pins for now
        .uart_tx(uart_tx), // Map to UART TX port
        .piranha_pulse(led), // Status pulse blink (Fibonacci-timed)
        .alu_done(),     // Not connected to LED (only one LED available)

        .alu_start(1'b0), // Driven by RP2350 via Southbridge SPI/PIO, tie to 0 for now
        .alu_opcode(3'b0), // Driven by RP2350 via Southbridge SPI/PIO, tie to 0 for now

        // SPI Flash Interface (on-board W25Q64, optional for bitstream or asset streaming)
        .flash_cs(flash_cs_n),
        .flash_clk(flash_clk),
        .flash_miso(flash_miso),
        .flash_mosi(flash_mosi)
    );

    // Southbridge SPI placeholder (TODO: Implement in Phase 1)
    assign spi_miso = 1'b0;

endmodule
