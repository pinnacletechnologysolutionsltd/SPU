// Wukong Artix-7 wrapper for the writable SOM-SIDECAR product path.
//
// Deliberately instantiates the Tang-silicon-proven sidecar top unchanged so
// both vendors exercise the same SPI receiver, hydrated map/label storage,
// fixed-schedule BMU, SOM1 encoder, and legacy telemetry logic.  This wrapper
// contains board plumbing only; the unused Tang compatibility UART and LEDs
// are allowed to be pruned by synthesis.

module spu_a7_som_sidecar_top (
    input  wire sys_clk,
    input  wire spi_cs_n,
    input  wire spi_sck,
    input  wire spi_mosi,
    output wire spi_miso,
    output wire uart_tx
);
    wire       unused_uart_telemetry;
    wire [2:0] unused_led;

    spu13_tang25k_som_sidecar_top u_sidecar (
        .sys_clk(sys_clk),
        .spi_cs_n(spi_cs_n),
        .spi_sck(spi_sck),
        .spi_mosi(spi_mosi),
        .spi_miso(spi_miso),
        .uart_tx(uart_tx),
        .uart_tx_telemetry(unused_uart_telemetry),
        .led(unused_led)
    );
endmodule
