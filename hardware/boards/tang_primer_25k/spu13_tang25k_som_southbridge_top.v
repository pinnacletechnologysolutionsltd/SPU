// spu13_tang25k_som_southbridge_top.v — SOM+SPI southbridge
// Minimal build: SOM/BMU classifier + SPI config + UART telemetry.
// Disables rotor core, math pipeline, RPLU, lattice, torus, GPU.

module spu13_tang25k_som_southbridge_top (
    input  wire        sys_clk,
    input  wire        spi_cs_n,
    input  wire        spi_sck,
    input  wire        spi_mosi,
    output wire        spi_miso,
    output wire        uart_tx,
    output wire [2:0]  led
);

    spu13_tang25k_southbridge_top #(
        .CORE_ENABLE_MATH(0),
        .CORE_ENABLE_SEQUENCER(1),
        .CORE_ENABLE_SOM(1),
        .CORE_ENABLE_RPLU(0),
        .CORE_ENABLE_RPLU_V2(0),
        .CORE_ENABLE_LATTICE(0),
        .CORE_ENABLE_TORUS(0)
    ) u_sb (
        .sys_clk(sys_clk),
        .spi_cs_n(spi_cs_n),
        .spi_sck(spi_sck),
        .spi_mosi(spi_mosi),
        .spi_miso(spi_miso),
        .uart_tx(uart_tx),
        .led(led)
    );

endmodule
