// spu_scene_unpack.v -- canonical T1a 252-bit triangle record unpacker.
// Fields occupy increasing bit positions in a0,b0,c0,...,z2 order.
// One instance decodes one 252-bit triangle; a complete T1 scene uses two
// instances per bank. Keeping this mapping in one module prevents active and
// candidate paths from acquiring subtly different hand-written slices.
// The module is combinational by construction.
// CC0 1.0 Universal.

module spu_scene_unpack (
    input  wire [251:0] scene,
    output wire signed [15:0] a0, b0,
    output wire signed [31:0] c0,
    output wire signed [15:0] a1, b1,
    output wire signed [31:0] c1,
    output wire signed [15:0] a2, b2,
    output wire signed [31:0] c2,
    output wire [3:0] r, g, b,
    output wire [15:0] z0, z1, z2
);

    // Canonical record map (inclusive ranges):
    //
    //   15:0    a0      31:16   b0      63:32   c0
    //   79:64   a1      95:80   b1     127:96   c1
    //  143:128  a2     159:144  b2     191:160  c2
    //  195:192  r      199:196  g      203:200  b
    //  219:204  z0     235:220  z1     251:236  z2
    //
    // The assignments are deliberately only wires. This module owns no
    // buffering, representation conversion, sign conversion, or activation
    // state. Signed output declarations preserve the existing coefficient
    // interpretation while retaining the packet's exact bit pattern.

    assign a0 = scene[15:0];
    assign b0 = scene[31:16];
    assign c0 = scene[63:32];
    assign a1 = scene[79:64];
    assign b1 = scene[95:80];
    assign c1 = scene[127:96];
    assign a2 = scene[143:128];
    assign b2 = scene[159:144];
    assign c2 = scene[191:160];
    assign r  = scene[195:192];
    assign g  = scene[199:196];
    assign b  = scene[203:200];
    assign z0 = scene[219:204];
    assign z1 = scene[235:220];
    assign z2 = scene[251:236];

endmodule
