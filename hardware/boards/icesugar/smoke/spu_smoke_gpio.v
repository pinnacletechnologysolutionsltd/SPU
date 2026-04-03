// spu_smoke_gpio.v — SPU-13 iCEsugar Fallback Smoke Test
// Uses plain GPIO toggle (no SB_RGBA_DRV primitive).
// Blinks the user LED (pin 26) at ~1 Hz to prove the FPGA is alive.
// If this works but blinky doesn't, the issue is SB_RGBA_DRV pin mapping.
// If this doesn't work, the FPGA is not booting from flash.

`default_nettype none

module spu_smoke_gpio (
    input  wire clk,       // 12 MHz
    output wire user_led   // pin 26 — active LOW on iCEsugar
);

    reg [23:0] counter = 0;

    always @(posedge clk)
        counter <= counter + 1;

    // Toggle at bit 23 → period = 2^24 / 12MHz ≈ 1.4 s
    assign user_led = ~counter[23];

endmodule
