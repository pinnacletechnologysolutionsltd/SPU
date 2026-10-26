// Bench-only clock adaptation. Classifier and interactive consumer unchanged.
// 50 MHz source -> 25 MHz fabric; 217 fabric clocks per UART bit.
module spu4_ina226_bench25_top #(
    parameter DIAGNOSTIC = 0
) (
    input wire sys_clk,
    input wire uart_rx,
    output wire uart_tx,
    output wire [2:0] led,
    output wire flash_cs, flash_sck, flash_mosi,
    input wire flash_miso
);
    // Gowin nextpnr CLOCK net attribute inserts BUFG/global-clock routing.
    (* keep = 1, CLOCK = 1 *) reg clk_25 = 1'b0;
    always @(posedge sys_clk) clk_25 <= ~clk_25;

    spu13_tang25k_spu4_som_edge_interactive_probe #(
        .CLK_FREQ(25000000), .CLKS_PER_BIT(217), .DIAGNOSTIC(DIAGNOSTIC)
    ) u_probe (
        .sys_clk(clk_25), .uart_rx(uart_rx), .uart_tx(uart_tx), .led(led),
        .flash_cs(flash_cs), .flash_sck(flash_sck),
        .flash_mosi(flash_mosi), .flash_miso(flash_miso)
    );
endmodule
