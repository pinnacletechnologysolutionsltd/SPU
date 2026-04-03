// SPU Laminar Power Dispatcher (v4.0)
// Hardened for "Laminar Purity" (Zero-Branch Logic).
// Objective: Implement bitwise parametric state scaling for the manifold.

module spu_laminar_power #(
    parameter WIDTH = 128 // SPU-4 Default
)(
    input  wire             clk,
    input  wire             rst_n,      // Active-low cluster reset
    input  wire [7:0]       bloom_intensity,
    input  wire [WIDTH-1:0] reg_in,
    output reg  [WIDTH-1:0] reg_out
);

    // Power Scale Mux Controls (Algebraic Selection)
    wire c_100 = (bloom_intensity == 8'hFF);
    wire c_75  = (bloom_intensity >= 8'hC0 && !c_100);
    wire c_50  = (bloom_intensity >= 8'h80 && !c_100 && !c_75);
    wire c_25  = (bloom_intensity >= 8'h40 && !c_100 && !c_75 && !c_50);
    wire c_0   = (!c_100 && !c_75 && !c_50 && !c_25);

    // Scaling Vectors
    wire [WIDTH-1:0] val_100 = reg_in;
    wire [WIDTH-1:0] val_75  = reg_in - (reg_in >> 2);
    wire [WIDTH-1:0] val_50  = (reg_in >> 1);
    wire [WIDTH-1:0] val_25  = (reg_in >> 2);
    wire [WIDTH-1:0] val_0   = {WIDTH{1'b0}};

    // Manifold Mux Selection (Laminar Flow)
    wire [WIDTH-1:0] next_out = 
        ({WIDTH{c_100}} & val_100) | 
        ({WIDTH{c_75}}  & val_75)  |
        ({WIDTH{c_50}}  & val_50)  |
        ({WIDTH{c_25}}  & val_25)  |
        ({WIDTH{c_0}}   & val_0);

    always @(posedge clk) begin
        if (!rst_n) begin
            reg_out <= {WIDTH{1'b0}};
        end else begin
            reg_out <= next_out;
        end
    end

endmodule
