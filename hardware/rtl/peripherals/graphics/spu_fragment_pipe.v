// spu_fragment_pipe.v — Spread-Weighted Fragment Blender (v2.0)
// Replaces 16.16 fixed-point lambda barycentric weights with rational Spread
// numerators. All arithmetic stays in Q(√3) — no float, no division.
//
// Blend formula (per Quadray axis i):
//   pixel_energy_n[axis_i] = w0*v0[axis_i] + w1*v1[axis_i] + w2*v2[axis_i]
//   pixel_w_total           = w0 + w1 + w2  (downstream divides if needed)
//
// By keeping numerator + denominator separate the result is bit-exact.
// Vertex attributes are 4×16-bit Quadray components packed as 64 bits:
//   [63:48]=axis0, [47:32]=axis1, [31:16]=axis2, [15:0]=axis3
//
// Output: pixel_energy_n (4×32-bit = 128-bit) — rational numerators
//         pixel_w_total  (16-bit)              — common denominator
//
// 1-cycle registered pipeline stage. Purely integer, no DSP mandated.
// CC0 1.0 Universal.

module spu_fragment_pipe (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         pixel_inside,
    // Spread weights — numerators of si = wi_n / (w0_n+w1_n+w2_n)
    input  wire [15:0]  w0_n,
    input  wire [15:0]  w1_n,
    input  wire [15:0]  w2_n,
    // Vertex Quadray attributes: 4×16-bit packed
    input  wire [63:0]  v0_attr,
    input  wire [63:0]  v1_attr,
    input  wire [63:0]  v2_attr,
    // Output: blend numerator (4×32-bit) and weight denominator
    output reg  [127:0] pixel_energy_n,  // 4 axis numerators (each 32-bit)
    output reg  [15:0]  pixel_w_total    // w0+w1+w2 (implicit denominator)
);

    // Extract 4 axes per vertex (16-bit each)
    wire [15:0] v0a0 = v0_attr[63:48]; wire [15:0] v0a1 = v0_attr[47:32];
    wire [15:0] v0a2 = v0_attr[31:16]; wire [15:0] v0a3 = v0_attr[15:0];
    wire [15:0] v1a0 = v1_attr[63:48]; wire [15:0] v1a1 = v1_attr[47:32];
    wire [15:0] v1a2 = v1_attr[31:16]; wire [15:0] v1a3 = v1_attr[15:0];
    wire [15:0] v2a0 = v2_attr[63:48]; wire [15:0] v2a1 = v2_attr[47:32];
    wire [15:0] v2a2 = v2_attr[31:16]; wire [15:0] v2a3 = v2_attr[15:0];

    // Combinational blend: Σ wi_n × vi_axis  (32-bit each, 16×16 products)
    wire [31:0] bnd_a0 = w0_n*v0a0 + w1_n*v1a0 + w2_n*v2a0;
    wire [31:0] bnd_a1 = w0_n*v0a1 + w1_n*v1a1 + w2_n*v2a1;
    wire [31:0] bnd_a2 = w0_n*v0a2 + w1_n*v1a2 + w2_n*v2a2;
    wire [31:0] bnd_a3 = w0_n*v0a3 + w1_n*v1a3 + w2_n*v2a3;
    wire [15:0] w_total = w0_n + w1_n + w2_n;

    always @(posedge clk) begin
        if (!rst_n) begin
            pixel_energy_n <= 128'b0;
            pixel_w_total  <= 16'b0;
        end else if (pixel_inside) begin
            pixel_energy_n <= {bnd_a0, bnd_a1, bnd_a2, bnd_a3};
            pixel_w_total  <= w_total;
        end else begin
            pixel_energy_n <= 128'b0;
            pixel_w_total  <= 16'b0;
        end
    end

endmodule
