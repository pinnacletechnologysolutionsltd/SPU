// spu_pdm_audio.v — Q(√3) Sigma-Delta PDM Audio Driver  v1.0
//
// Converts a 32-bit RationalSurd sample (P[31:16] + Q[15:0]) into a
// 1-bit PDM stream suitable for low-pass filtering → speaker/DAC.
//
// Architecture: First-order sigma-delta modulator.
//   Accumulator updates at CLK_FREQ.
//   Samples are latched every SAMPLE_PERIOD clocks (default 44.1 kHz @ 27 MHz).
//
// Q(√3) → audio mapping:
//   sample = P + Q   (integer; approximation that keeps path 100% integer)
//   Caller should scale P/Q values so `P + Q` fits in 16 bits signed.
//
// Piranha Pulse tie-in:
//   piranha_en is a gate from spu_sierpinski_clk (61.44 kHz reference).
//   When piranha_en is high the sample register is refreshed, ensuring
//   audio updates are phase-locked to the Fibonacci heartbeat.

`default_nettype none

module spu_pdm_audio #(
    parameter CLK_FREQ     = 27_000_000,
    parameter SAMPLE_RATE  = 44_100,
    parameter SAMPLE_PERIOD = CLK_FREQ / SAMPLE_RATE   // 612 @ 27 MHz
)(
    input  wire        clk,
    input  wire        reset,

    // Q(√3) sample: P = [31:16], Q = [15:0] (both signed 16-bit)
    input  wire [31:0] sample_in,

    // 1-cycle Piranha Pulse gate from spu_sierpinski_clk
    input  wire        piranha_en,

    // 1-bit PDM output → RC low-pass → speaker
    output reg         pdm_out
);

    // Q(√3) → signed 16-bit: P + Q (clamped)
    wire signed [15:0] P = $signed(sample_in[31:16]);
    wire signed [15:0] Q = $signed(sample_in[15:0]);
    wire signed [16:0] samp_wide = {P[15], P} + {Q[15], Q};
    wire signed [15:0] samp_clamped =
        (samp_wide[16] != samp_wide[15]) ?
            (samp_wide[16] ? 16'sh8000 : 16'sh7FFF) :
            samp_wide[15:0];

    // Sample latch (refreshed by Piranha Pulse or at SAMPLE_PERIOD)
    reg [15:0]  sample_latch;
    reg [19:0]  samp_timer;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            sample_latch <= 16'h0;
            samp_timer   <= 20'd0;
        end else begin
            if (piranha_en || samp_timer == SAMPLE_PERIOD - 1) begin
                sample_latch <= samp_clamped;
                samp_timer   <= 20'd0;
            end else
                samp_timer <= samp_timer + 1'b1;
        end
    end

    // First-order sigma-delta modulator
    reg signed [16:0] acc;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            acc     <= 17'sh0;
            pdm_out <= 1'b0;
        end else begin
            if (!acc[16]) begin          // accumulator non-negative → output 1
                acc     <= acc + {{1{sample_latch[15]}}, sample_latch} - 17'sh7FFF;
                pdm_out <= 1'b1;
            end else begin
                acc     <= acc + {{1{sample_latch[15]}}, sample_latch} + 17'sh7FFF;
                pdm_out <= 1'b0;
            end
        end
    end

endmodule
`default_nettype wire
