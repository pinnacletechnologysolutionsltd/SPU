// spu_sierpinski_clk.v (v1.0 - Fractal Timing Source)
// Objective: Generate 8/13/21 Fibonacci pulses for Ghost OS.
// Standard: 34-cycle frame (Rational Fibonacci Cadence).

module spu_sierpinski_clk (
    input  wire clk,
    input  wire rst_n,
    output wire phi_8,
    output wire phi_13,
    output wire phi_21,
    output wire heartbeat // Global resonant pulse
);
    reg [5:0] count;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) count <= 0;
        else count <= (count == 33) ? 0 : count + 1;
    end

    assign phi_8  = (count == 8);
    assign phi_13 = (count == 13);
    assign phi_21 = (count == 21);
    assign heartbeat = phi_8 | phi_13 | phi_21;

endmodule
