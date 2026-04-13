// rational_surd5_mul64.v — Multiply two packed RationalSurd5 numbers (64-bit inputs)
// Input/Output format (64-bit): [63:32] = signed P (32-bit), [31:0] = signed Q (32-bit)
// Output (64-bit): { P_out[31:0], Q_out[31:0] } with saturation on overflow

module rational_surd5_mul64 (
    input  wire [63:0] a,
    input  wire [63:0] b,
    output wire [63:0] out
);

// Unpack inputs
wire signed [31:0] aP;
assign aP = a[63:32];
wire signed [31:0] aQ;
assign aQ = a[31:0];
wire signed [31:0] bP;
assign bP = b[63:32];
wire signed [31:0] bQ;
assign bQ = b[31:0];

// Intermediate products (signed 64-bit)
wire signed [63:0] p1p2;
assign p1p2 = aP * bP;
wire signed [63:0] q1q2;
assign q1q2 = aQ * bQ;
wire signed [63:0] p1q2;
assign p1q2 = aP * bQ;
wire signed [63:0] p2q1;
assign p2q1 = bP * aQ;

// Compute P_out = p1p2 + 5*q1q2  (needs up to 67 bits)
// Compute Q_out = p1q2 + p2q1      (needs up to 65 bits)
wire signed [66:0] p_tmp;
assign p_tmp = p1p2 + (q1q2 * 5);
wire signed [65:0] q_tmp;
assign q_tmp = p1q2 + p2q1;

reg signed [31:0] p_out_reg;
reg signed [31:0] q_out_reg;

always @* begin
    // Clamp P
    if (p_tmp >  64'sh7FFFFFFF) p_out_reg = 32'sh7FFFFFFF;
    else if (p_tmp < -64'sh80000000) p_out_reg = 32'sh80000000;
    else p_out_reg = p_tmp[31:0];

    // Clamp Q
    if (q_tmp >  64'sh7FFFFFFF) q_out_reg = 32'sh7FFFFFFF;
    else if (q_tmp < -64'sh80000000) q_out_reg = 32'sh80000000;
    else q_out_reg = q_tmp[31:0];
end

assign out = {p_out_reg, q_out_reg};

endmodule
