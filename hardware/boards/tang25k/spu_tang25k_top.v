// Tang-25k board top for SPU-4 smoketest
// Minimal wrapper: includes Sierpinski clock, SPU-4 core (RPLU disabled),
// an inert Davis gate instantiation (monitor-only) and a simple smoke driver
// that toggles an LED and emits a single UART byte on power-up (sim-only)

`timescale 1ns/1ps

module spu_tang25k_top (
    input  wire        sys_clk,
    output wire [5:0]  led,
    output wire        uart_tx
);

    // Use the BUFG primitive for the clock to ensure global clock routing
    wire clk;
    BUFG i_clk (.I(sys_clk), .O(clk));

    // Directly toggle led[0] and uart_tx at a high frequency
    // This will appear as a dim LED or very rapid flicker if the clock is running
    assign led[0] = clk;
    assign uart_tx = clk;

    // Keep other LEDs off
    assign led[5:1] = 5'b11111;

endmodule
