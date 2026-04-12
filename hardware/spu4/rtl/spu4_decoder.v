// spu4_decoder.v
// Fixed 24-bit Instruction Decoder for iCE40 Nano (LP1K)
// Hardened for "Laminar Purity" (Zero-Branch Logic).

module spu4_decoder (
    input [23:0] inst_word,      // 8-bit Op, 8-bit Dest, 8-bit Src/Imm
    output [3:0] alu_op,         // Control signal for the Quadray ALU
    output [2:0] reg_dest,       // R0-R7 Destination
    output [2:0] reg_src,        // R0-R7 Source
    output [7:0] immediate,      // 8-bit Immediate value
    output use_imm,              // Flag: Use immediate instead of reg_src
    output snap_en,              // Flag: Enable 15-Sigma Snap logic
    output whisper_en            // Flag: Trigger 60-degree Dual-Wire Tx
);

    // Internal Opcode Definitions (The "Soul" of the ISA)
    localparam OP_QLDI = 8'h10; // Load Immediate
    localparam OP_QADD = 8'h40; // Quadray Add
    localparam OP_QROT = 8'h45; // Rational Rotation
    localparam OP_SNAP = 8'h80; // Assert Lock
    localparam OP_W60T = 8'hA0; // Whisper Transmit

    // Laminar Detection: Constant-Time Opcode Check
    wire is_qldi;
    assign is_qldi = (inst_word[23:16] == OP_QLDI);
    wire is_qadd;
    assign is_qadd = (inst_word[23:16] == OP_QADD);
    wire is_qrot;
    assign is_qrot = (inst_word[23:16] == OP_QROT);
    wire is_snap;
    assign is_snap = (inst_word[23:16] == OP_SNAP);
    wire is_w60t;
    assign is_w60t = (inst_word[23:16] == OP_W60T);

    // Initial Default assignments (Laminar Idle)
    assign reg_dest   = inst_word[15:8];
    assign reg_src    = inst_word[7:0];
    assign immediate  = inst_word[7:0];

    // Algebraic Muxing for Control Signals
    assign use_imm    = is_qldi;
    assign snap_en    = is_snap;
    assign whisper_en = is_w60t;

    // ALU Op Muxing (4-bit signal)
    // 0: NOP, 1: PASS_THROUGH (QLDI), 2: VECTOR_SUM (QADD), 3: THOMSON_ROT (QROT)
    assign alu_op = ({4{is_qldi}} & 4'h1) |
                    ({4{is_qadd}} & 4'h2) |
                    ({4{is_qrot}} & 4'h3);

endmodule
