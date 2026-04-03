// SPU-13 Quadray Vector Primitive (v2.9.22)
// Holds four Surd pairs [A, B, C, D] as an atomic hardware primitive.
// Total Bit-Width: 8 Lanes * 32-bit = 256 bits (Spatial Core)

module spu_quadray_vec (
    input  wire         clk,
    input  wire         reset,
    input  wire [255:0] d_in,
    output reg  [255:0] q_out
);

    // Named Lane Definitions for Isotropic Clarity
    // Lane 0-1: Axis A [Rational, Irrational]
    // Lane 2-3: Axis B [Rational, Irrational]
    // Lane 4-5: Axis C [Rational, Irrational]
    // Lane 6-7: Axis D [Rational, Irrational]

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            q_out <= 256'b0;
        end else begin
            q_out <= d_in;
        end
    end

endmodule
