// rational_surd5_add.v — Add two packed RationalSurd5 numbers (64-bit inputs)
// Input/Output format (64-bit): [63:32] = signed P (32-bit), [31:0] = signed Q (32-bit)
// Output (64-bit): { P_out[31:0], Q_out[31:0] } with saturation on overflow

module rational_surd5_add (
    input  wire [63:0] a,
    input  wire [63:0] b,
    output wire [63:0] out
);

wire signed [31:0] aP;
assign aP = a[63:32];
wire signed [31:0] aQ;
assign aQ = a[31:0];
wire signed [31:0] bP;
assign bP = b[63:32];
wire signed [31:0] bQ;
assign bQ = b[31:0];

wire signed [32:0] p_tmp;
assign p_tmp = {aP[31], aP} + {bP[31], bP};
wire signed [32:0] q_tmp;
assign q_tmp = {aQ[31], aQ} + {bQ[31], bQ};

reg signed [31:0] p_out_reg;
reg signed [31:0] q_out_reg;

always @* begin
    // Clamp P
    if (p_tmp >  33'sh7FFFFFFF) p_out_reg = 32'sh7FFFFFFF;
    else if (p_tmp < -33'sh80000000) p_out_reg = 32'sh80000000;
    else p_out_reg = p_tmp[31:0];

    // Clamp Q
    if (q_tmp >  33'sh7FFFFFFF) q_out_reg = 32'sh7FFFFFFF;
    else if (q_tmp < -33'sh80000000) q_out_reg = 32'sh80000000;
    else q_out_reg = q_tmp[31:0];
end

assign out = {p_out_reg, q_out_reg};

endmodule
