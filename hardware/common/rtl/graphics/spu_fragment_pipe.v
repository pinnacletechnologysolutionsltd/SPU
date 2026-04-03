// Sovereign Fragment Pipeline (v1.0)
// Objective: Calculate interpolated pixel energy using barycentric weights.
// Logic: Linear Interpolation (LERP) in the 60-degree Quadray space.

module spu_fragment_pipe (
    input  wire         clk,
    input  wire         reset,
    input  wire         pixel_inside,
    input  wire [31:0]  lambda0, // 16.16 Fixed Point
    input  wire [31:0]  lambda1,
    input  wire [31:0]  lambda2,
    
    // Vertex Attributes (A,B,C,D colors or normals)
    input  wire [63:0]  v0_attr, 
    input  wire [63:0]  v1_attr,
    input  wire [63:0]  v2_attr,
    
    output reg  [63:0]  pixel_energy // Interpolated Quadray Vector
);

    // 1. High-Fidelity Interpolation (The Laminar Mix)
    // Formula: P = lambda0*V0 + lambda1*V1 + lambda2*V2
    // We use three multipliers to resolve the interpolation in one cycle.

    wire [63:0] term0, term1, term2;
    
    // Using 32-bit integer components for the 'Seed' implementation
    assign term0 = (v0_attr[31:0] * lambda0[31:16]);
    assign term1 = (v1_attr[31:0] * lambda1[31:16]);
    assign term2 = (v2_attr[31:0] * lambda2[31:16]);

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            pixel_energy <= 64'b0;
        end else if (pixel_inside) begin
            pixel_energy <= term0 + term1 + term2;
        end else begin
            pixel_energy <= 64'b0;
        end
    end

endmodule
