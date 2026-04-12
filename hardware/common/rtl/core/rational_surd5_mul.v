// rational_surd5_mul.v — Multiply two packed RationalSurd5 numbers
// Packed format (32-bit): [31:16] = signed P, [15:0] = signed Q
// Output (64-bit): { P_out[31:0], Q_out[31:0] }

module rational_surd5_mul (
    input  wire [31:0] a,
    input  wire [31:0] b,
    output wire [63:0] out
);

// Unpack inputs (signed 16-bit fields)
wire signed [15:0] aP;
assign aP = a[31:16];
wire signed [15:0] aQ;
assign aQ = a[15:0];
wire signed [15:0] bP;
assign bP = b[31:16];
wire signed [15:0] bQ;
assign bQ = b[15:0];

// Intermediate products (signed 32-bit)
wire signed [31:0] p1p2;
assign p1p2 = aP * bP;
wire signed [31:0] q1q2;
assign q1q2 = aQ * bQ;
wire signed [31:0] p1q2;
assign p1q2 = aP * bQ;
wire signed [31:0] p2q1;
assign p2q1 = bP * aQ;

// Compute P_out = p1p2 + 5*q1q2  (needs up to 34 bits)
// Compute Q_out = p1q2 + p2q1      (needs up to 33 bits)
wire signed [33:0] p_tmp;
assign p_tmp = p1p2 + (q1q2 * 5);
wire signed [32:0] q_tmp;
assign q_tmp = p1q2 + p2q1;

reg signed [31:0] p_out_reg;
reg signed [31:0] q_out_reg;

// Overflow detection via sign-extension check
wire overflow_p;
assign overflow_p = (p_tmp[33:31] != {3{p_tmp[31]}});
wire overflow_q;
assign overflow_q = (q_tmp[32:31] != {2{q_tmp[31]}});

always @* begin
    if (!overflow_p) p_out_reg = p_tmp[31:0];
    else if (p_tmp[33]) p_out_reg = 32'sh80000000; // negative clamp
    else p_out_reg = 32'sh7fffffff;                 // positive clamp

    if (!overflow_q) q_out_reg = q_tmp[31:0];
    else if (q_tmp[32]) q_out_reg = 32'sh80000000; // negative clamp
    else q_out_reg = 32'sh7fffffff;                 // positive clamp
end

assign out = {p_out_reg, q_out_reg};

endmodule
