// SPU-13 CIC Resonant Bio-Filter (v1.0)
// Target: Unified SPU-13 Fleet
// Objective: Filter Cubic 60Hz hum from 61.44 kHz Bio-Pulse.
// Logic: Cascaded Integrator-Comb (CIC) optimized for low gate count.

module spu_bio_filter (
    input  wire        clk,
    input  wire        reset,
    input  wire [15:0] signal_in,
    output wire [15:0] signal_out
);

    // Integrator Stage
    reg signed [31:0] integrator;
    always @(posedge clk or posedge reset) begin
        if (reset) integrator <= 0;
        else integrator <= integrator + signal_in;
    end

    // Comb Stage (Differential Delay)
    reg signed [31:0] delay_z1;
    always @(posedge clk) delay_z1 <= integrator;

    assign signal_out = integrator[31:16] - delay_z1[31:16];

endmodule
