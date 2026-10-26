
`default_nettype none

module spu_ecp5_top (
    input wire          clk_50m,          // 50 MHz clock
    input wire          rst,              // Asynchronous reset (active high)
    output wire [2:0]   led,              // LEDs (active low)

    // SPI Southbridge Bus (RP2350 -> ECP5)
    input wire          spi_cs,
    input wire          spi_sck,
    input wire          spi_mosi,
    output wire         spi_miso,

    // PIO Parallel Bus (RP2350 <-> ECP5)
    inout wire  [7:0]   pio_d,
    input wire          pio_strobe,
    output wire         pio_ready,
    input wire          pio_dir,

    // Dedicated SPI Flash Interface (ECP5 as master to U3 config flash)
    output wire         flash_cs_o,     // ECP5 drives CS#
    output wire         flash_clk_o,    // ECP5 drives SCK
    input wire          flash_miso_i,   // Data from flash
    output wire         flash_mosi_o    // Data to flash
);

    wire clk_12mhz_int;
    wire rst_n_int;
    assign rst_n_int = ~rst; // Invert active-high reset to active-low

    // Simple clock divider for 12MHz from 50MHz
    // TODO: Use PLL for proper clock generation
    reg [1:0] clk_div_cnt = 2'b00;
    always @(posedge clk_50m or negedge rst_n_int) begin
        if (!rst_n_int) clk_div_cnt <= 2'b00;
        else if (clk_div_cnt == 2'd3) clk_div_cnt <= 2'b00;
        else clk_div_cnt <= clk_div_cnt + 2'd1;
    end
    assign clk_12mhz_int = (clk_div_cnt == 2'd0);

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
        .uart_tx(led[0]), // Map to LED0 for now
        .piranha_pulse(led[1]), // Map to LED1 for now
        .alu_done(led[2]),     // Map to LED2 for now

        .alu_start(1'b0), // Driven by RP2350 via Southbridge SPI/PIO, tie to 0 for now
        .alu_opcode(3'b0), // Driven by RP2350 via Southbridge SPI/PIO, tie to 0 for now

        // SPI Flash Interface (ECP5 as master to U3 config flash)
        .flash_cs(flash_cs_o),
        .flash_clk(flash_clk_o),
        .flash_miso(flash_miso_i),
        .flash_mosi(flash_mosi_o)
    );

    // Southbridge SPI/PIO placeholders (TODO: Implement logic to connect to spu13_top control signals)
    assign spi_miso = 1'b0;
    assign pio_ready = 1'b0;

endmodule
