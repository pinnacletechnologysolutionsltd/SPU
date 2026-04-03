// spu_smoke_blinky.v — SPU-13 iCEsugar Level 0 Smoke Test
// Target : iCEsugar v1.5 (iCE40UP5K-SG48)
// Purpose: Verify FPGA programs, oscillator runs, RGB LED responds.
//
// The counter threshold uses Fibonacci numbers (8, 13, 21... ×100k cycles)
// to give each colour a Phi-proportioned hold time. No external pins needed.
//
// LED sequence (cycling): BLUE (booting) → GREEN (laminar) → RED (janus)
// Period ≈ (8+13+21) × 100,000 cycles = 42M / 12MHz ≈ 3.5 s per full cycle

`default_nettype none

module spu_smoke_blinky (
    input  wire clk,       // 12 MHz onboard oscillator
    output wire LED_R,
    output wire LED_G,
    output wire LED_B
);

    // -------------------------------------------------------------------
    // Fibonacci phase counter
    // Phase 0: 8  × 100_000 = 800_000 cycles  → BLUE
    // Phase 1: 13 × 100_000 = 1_300_000 cycles → GREEN
    // Phase 2: 21 × 100_000 = 2_100_000 cycles → RED
    // -------------------------------------------------------------------
    localparam FIB_0 =  800_000;   // 8 × 100k
    localparam FIB_1 = 2_100_000;  // 8+13 × 100k (cumulative)
    localparam FIB_2 = 4_200_000;  // 8+13+21 × 100k (full cycle)

    reg [22:0] counter = 0;
    reg [1:0]  phase   = 0;

    always @(posedge clk) begin
        if (counter == FIB_2 - 1)
            counter <= 0;
        else
            counter <= counter + 1;

        if      (counter < FIB_0) phase <= 2'd0;  // Blue
        else if (counter < FIB_1) phase <= 2'd1;  // Green
        else                      phase <= 2'd2;  // Red
    end

    // -------------------------------------------------------------------
    // RGB driver — iCE40UP5K hardened current-source LED driver
    // CURREN=1 enables the driver, RGBLEDEN=1 enables PWM outputs.
    // Full-current mode (0b11) on all channels; phase MUX selects colour.
    // -------------------------------------------------------------------
    wire r_on = (phase == 2'd2);
    wire g_on = (phase == 2'd1);
    wire b_on = (phase == 2'd0);

    SB_RGBA_DRV #(
        .CURRENT_MODE ("0b0"),        // Half-current mode (saves power)
        .RGB0_CURRENT ("0b000001"),   // ~4 mA Red
        .RGB1_CURRENT ("0b000001"),   // ~4 mA Green
        .RGB2_CURRENT ("0b000001")    // ~4 mA Blue
    ) u_rgb (
        .CURREN   (1'b1),
        .RGBLEDEN (1'b1),
        .RGB0PWM  (r_on),   // Red
        .RGB1PWM  (g_on),   // Green
        .RGB2PWM  (b_on),   // Blue
        .RGB0     (LED_R),
        .RGB1     (LED_G),
        .RGB2     (LED_B)
    );

endmodule
