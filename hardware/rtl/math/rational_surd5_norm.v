// rational_surd5_norm.v - Normalization helper for RationalSurd5 packed values
// Input/Output format (64-bit): [63:32] = signed P (32-bit), [31:0] = signed Q (32-bit)
// Behavior: If magnitude of P or Q exceeds MAX_MAG, arithmetic-right-shift both P and Q by 1
// and set scale_shift=1. Outputs normalized value and shift count (0/1) and overflow flag.

module rational_surd5_norm (
    input  wire [63:0] in,       // {P[31:0], Q[31:0]}
    output wire [63:0] out,      // normalized {P,Q}
    output wire [3:0]  scale_shift, // number of right shifts applied (0 or 1)
    output wire        overflow  // true if still out-of-range after one shift
);

localparam signed [31:0] MAX_MAG = 32'sh3FFF_FFFF; // 2^30 - 1, leave headroom

// Unpack
wire signed [31:0] inP;
assign inP = in[63:32];
wire signed [31:0] inQ;
assign inQ = in[31:0];

// Extend to 33 bits for safe abs handling (handles INT32_MIN)
wire signed [32:0] inP_ext;
assign inP_ext = {inP[31], inP};
wire signed [32:0] inQ_ext;
assign inQ_ext = {inQ[31], inQ};
wire signed [32:0] MAX_MAG_EXT;
assign MAX_MAG_EXT = {1'b0, MAX_MAG};

// Absolute values (33-bit)
wire signed [32:0] absP_ext;
assign absP_ext = (inP_ext < 0) ? -inP_ext : inP_ext;
wire signed [32:0] absQ_ext;
assign absQ_ext = (inQ_ext < 0) ? -inQ_ext : inQ_ext;

wire need_shift;
assign need_shift = (absP_ext > MAX_MAG_EXT) || (absQ_ext > MAX_MAG_EXT);

// Perform arithmetic right shift if needed
wire signed [31:0] sP;
assign sP = need_shift ? (inP >>> 1) : inP;
wire signed [31:0] sQ;
assign sQ = need_shift ? (inQ >>> 1) : inQ;

// Check post-shift magnitudes (extend to 33-bit)
wire signed [32:0] sP_ext;
assign sP_ext = {sP[31], sP};
wire signed [32:0] sQ_ext;
assign sQ_ext = {sQ[31], sQ};
wire signed [32:0] absP2_ext;
assign absP2_ext = (sP_ext < 0) ? -sP_ext : sP_ext;
wire signed [32:0] absQ2_ext;
assign absQ2_ext = (sQ_ext < 0) ? -sQ_ext : sQ_ext;
wire still_bad;
assign still_bad = (absP2_ext > MAX_MAG_EXT) || (absQ2_ext > MAX_MAG_EXT);

assign out = {sP, sQ};
assign scale_shift = need_shift ? 4'd1 : 4'd0;
assign overflow = need_shift ? still_bad : 1'b0;

endmodule
