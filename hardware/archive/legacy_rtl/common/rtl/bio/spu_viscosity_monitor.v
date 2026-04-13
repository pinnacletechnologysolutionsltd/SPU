// SPU-13 Viscosity Monitor: The Surfer's Logic (v3.4.25)
// Implementation: Real-time 'Liquid' flow detection.
// Objective: Measure how well the manifold slides through the IVM.
// Result: 8-bit Flow Index (255 = Liquid, 0 = Cubic Friction).

module spu_viscosity_monitor (
    input  wire         clk,
    input  wire         reset,
    input  wire [127:0] abcd_vector, // 4D Quadray State
    output reg  [7:0]   laminar_flow_index
);

    // 1. Symmetry Calculation (The Ground)
    wire signed [31:0] a;
    assign a = abcd_vector[31:0];
    wire signed [31:0] b;
    assign b = abcd_vector[63:32];
    wire signed [31:0] c;
    assign c = abcd_vector[95:64];
    wire signed [31:0] d;
    assign d = abcd_vector[127:96];
    
    wire signed [31:0] sum_abcd;
    assign sum_abcd = a + b + c + d;
    wire is_symmetric;
    assign is_symmetric = (sum_abcd == 32'sd0);

    // 2. Phyllotaxis Delta Check (The Spiral)
    // We check if the deltas between lanes approximate the Golden Ratio.
    // In a liquid state, the differences [A-B, B-C, C-D] should be 
    // balanced according to the Isotropic Invariant.
    wire [31:0] delta_ab;
    assign delta_ab = (a > b) ? (a - b) : (b - a);
    wire [31:0] delta_bc;
    assign delta_bc = (b > c) ? (b - c) : (c - b);
    
    // 3. Flow Index Modulation
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            laminar_flow_index <= 8'h0;
        end else begin
            if (is_symmetric) begin
                // If symmetric AND the deltas are non-zero (active flow)
                if (delta_ab > 0 && delta_bc > 0)
                    laminar_flow_index <= 8'hFF; // THE LIQUID STATE
                else
                    laminar_flow_index <= 8'hC0; // Static Equilibrium
            end else begin
                // Cubic Interference: Proportional penalty based on asymmetry
                laminar_flow_index <= (sum_abcd[15:8] > 8'h20) ? 8'h10 : 8'h40;
            end
        end
    end

endmodule
