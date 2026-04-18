// laminar_node.v — laminar primitive (Janus Bit -> Phinary multiplier)
// License: CC0 1.0 Universal

module laminar_node #(
    parameter WIDTH = 32
)(
    input  wire                 clk,
    input  wire                 rst_n,
    input  wire                 enable,
    input  wire [WIDTH-1:0]     surd_in,
    output reg  [WIDTH-1:0]     surd_out
);

// Phinary Janus prototype: interpret the input as two HALF-width packed
// RationalSurd5 values (each 32-bit: [31:16]=P, [15:0]=Q), multiply them,
// and output the product as {P_out[31:0], Q_out[31:0]} (64-bit). This
// replaces the earlier ad-hoc xor+add placeholder.

localparam HALF = WIDTH/2;

wire [HALF-1:0] a;
assign a = surd_in[WIDTH-1:HALF];
wire [HALF-1:0] b;
assign b = surd_in[HALF-1:0];

wire [63:0] mul_out;

rational_surd5_mul u_mul (
    .a(a),
    .b(b),
    .out(mul_out)
);

wire [63:0] norm_out;
wire [3:0] norm_shift;
wire norm_overflow;

rational_surd5_norm u_norm (
    .in(mul_out),
    .out(norm_out),
    .scale_shift(norm_shift),
    .overflow(norm_overflow)
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        surd_out <= {WIDTH{1'b0}};
    end else if (enable) begin
        surd_out <= norm_out; // normalized product
    end
end

endmodule
