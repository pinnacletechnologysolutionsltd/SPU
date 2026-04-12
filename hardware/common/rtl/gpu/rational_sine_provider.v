// Rational Sine Provider - selects 16-bit packed ROM or 32-bit P/Q ROM
// Outputs signed 32-bit P and Q fields (Q(\u221A3) basis)
module rational_sine_provider #(
    parameter DEPTH = 4096,
    parameter HIGH_PRECISION = 0
) (
    input wire [$clog2(DEPTH)-1:0] addr,
    output wire signed [31:0] pout,
    output wire signed [31:0] qout
);

generate
if (HIGH_PRECISION) begin : gp_q32
    // 32-bit P/Q ROM
    rational_sine_rom_q32 #(.DEPTH(DEPTH)) rom_q32 (.addr(addr), .dout_p(pout), .dout_q(qout));
end else begin : gp_q16
    // packed 16-bit ROM (upper 16 = P, lower 16 = Q)
    wire [31:0] dout16;
    rational_sine_rom #(.DEPTH(DEPTH)) rom16 (.addr(addr), .dout(dout16));
    // sign-extend 16->32
    // extract signed 16-bit fields and sign-extend to 32-bit
    wire signed [15:0] p16;
    assign p16 = dout16[31:16];
    wire signed [15:0] q16;
    assign q16 = dout16[15:0];
    assign pout = { {16{p16[15]}}, p16 };
    assign qout = { {16{q16[15]}}, q16 };
end
endgenerate

endmodule
