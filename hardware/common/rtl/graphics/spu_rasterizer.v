// SPU-13 Isotropic Rasterizer (v3.9 Sovereign Edition)
// Function: Deterministic Edge-Function Logic with True Barycentric Outputs.
// Logic: Bit-exact 64-bit integer coverage check with rational normalization using LUT approximation.

`include "spu_rational_lut.v" // Include the reciprocal LUT

module spu_rasterizer (
    input  wire         clk,
    input  wire         reset,
    input  wire [63:0]  v0_abcd, // Projected Vertex 0 (y[31:0], x[31:0])
    input  wire [63:0]  v1_abcd, // Projected Vertex 1
    input  wire [63:0]  v2_abcd, // Projected Vertex 2
    input  wire [15:0]  v0_z, v1_z, v2_z,
    input  wire [31:0]  pixel_x,
    input  wire [31:0]  pixel_y,
    output reg          pixel_inside,
    output reg  [31:0]  lambda0, // 16.16 Fixed Point
    output reg  [31:0]  lambda1, // 16.16 Fixed Point
    output reg  [31:0]  lambda2, // 16.16 Fixed Point
    output reg  [15:0]  pixel_z
);

    // 1. Surd-Aware Edge Functions (Linear Determinants)
    wire signed [63:0] edge0 = ($signed(pixel_x) - $signed(v0_abcd[31:0])) * ($signed(v1_abcd[63:32]) - $signed(v0_abcd[63:32])) - 
                               ($signed(pixel_y) - $signed(v0_abcd[63:32])) * ($signed(v1_abcd[31:0]) - $signed(v0_abcd[31:0]));
                               
    wire signed [63:0] edge1 = ($signed(pixel_x) - $signed(v1_abcd[31:0])) * ($signed(v2_abcd[63:32]) - $signed(v1_abcd[63:32])) - 
                               ($signed(pixel_y) - $signed(v1_abcd[63:32])) * ($signed(v2_abcd[31:0]) - $signed(v1_abcd[31:0]));
                               
    wire signed [63:0] edge2 = ($signed(pixel_x) - $signed(v2_abcd[31:0])) * ($signed(v0_abcd[63:32]) - $signed(v2_abcd[63:32])) - 
                               ($signed(pixel_y) - $signed(v2_abcd[63:32])) * ($signed(v0_abcd[31:0]) - $signed(v2_abcd[31:0]));

    // 2. Total Triangle Area (The Manifold Sum)
    wire signed [63:0] total_area = edge0 + edge1 + edge2;

    // 3. Normalization Logic (The Rational Forge)
    wire [7:0] total_area_mantissa; 
    wire [31:0] reciprocal_val;    // Output from LUT is 1.23 fixed point

    assign total_area_mantissa = total_area[63:56]; 

    spu_rational_lut rec_lut (
        .addr(total_area_mantissa),
        .reciprocal(reciprocal_val) 
    );

    // Fixed-point multiplication: lambda_i = (edge_i * reciprocal_val) >> 7
    wire signed [95:0] prod0, prod1, prod2;
    
    // Perform signed multiplication.
    // edge_i is signed [63:0]. reciprocal_val is [31:0] (1.23).
    // Concatenation with 32'b0 implicitly zero-extends reciprocal_val.
    // Multiplication with signed edge_i will promote the result to signed [95:0].
    assign prod0 = $signed(edge0) * {32'b0, reciprocal_val}; 
    assign prod1 = $signed(edge1) * {32'b0, reciprocal_val};
    assign prod2 = $signed(edge2) * {32'b0, reciprocal_val};

    always @(*) begin
        // Combinational logic for pixel_inside and lambda assignments.

        // Check if pixel is inside triangle
        pixel_inside = (edge0[63] == total_area[63]) &&
                       (edge1[63] == total_area[63]) &&
                       (edge2[63] == total_area[63]);

        if (pixel_inside) begin
            // Assign the computed 16.16 fixed-point values directly.
            // Take the lower 32 bits of the shifted product [38:7].
            lambda0 = prod0[38:7]; 
            lambda1 = prod1[38:7];
            lambda2 = prod2[38:7];
            
            // Interpolate Z-depth: (lambda * Z) >> 16
            // lambdai is [31:0] (16.16), vi_z is [15:0] 
            pixel_z = (lambda0[31:0] * {16'b0, v0_z} + 
                       lambda1[31:0] * {16'b0, v1_z} + 
                       lambda2[31:0] * {16'b0, v2_z}) >> 16;
        end else begin
            lambda0 = 0; lambda1 = 0; lambda2 = 0;
            pixel_z = 16'hFFFF; // Far plane
        end
    end

endmodule
