// spu13_m31_multiplier_seq_fallback.v
// Drop-in replacement for spu13_m31_multiplier using the sequential core.
// Include this file INSTEAD of spu13_m31_multiplier.v in area-constrained
// synthesis scripts.  Same port interface, ~52-cycle latency, 1 DSP.
//
// Usage in synth script: replace the read_verilog line for
// spu13_m31_multiplier.v with this file + spu13_m31_multiplier_seq.v

module spu13_m31_multiplier (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         start,
    input  wire [31:0]  a0, a1, a2, a3,
    input  wire [31:0]  b0, b1, b2, b3,
    output wire [31:0]  r0, r1, r2, r3,
    output wire         done,
    output wire         busy,
    output wire         rns_error
);
    spu13_m31_multiplier_seq #(.DEVICE("SIM")) u_seq (
        .clk(clk), .rst_n(rst_n), .start(start),
        .a0(a0), .a1(a1), .a2(a2), .a3(a3),
        .b0(b0), .b1(b1), .b2(b2), .b3(b3),
        .r0(r0), .r1(r1), .r2(r2), .r3(r3),
        .done(done), .busy(busy), .rns_error(rns_error)
    );
endmodule
