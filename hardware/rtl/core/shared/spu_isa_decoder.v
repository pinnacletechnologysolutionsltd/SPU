// spu_isa_decoder.v — SPU-13 ISA v1.0 Adapter Decoder
//
// Combinational decoder: maps 64-bit instruction word to control signals
// for the existing SPU-13 core, RPLU, RAU, and SPI telemetry bus.
//
// This is the thin adapter layer between the SPU slave interface and
// the existing RTL. No existing modules are modified.
//
// Instruction format (from spu_isa_defines.vh):
//   [63:56] opcode    [55:51] dest    [50:46] srcA    [45:41] srcB
//   Format R: reserved[40:0]
//   Format L: base[50:46]  offset[45:36]  reserved[35:0]
//   Format I: immediate[50:0]
//   Format U: src[50:46]  cond[45:44]  reserved[43:0]
//   Format B: flags[55:51]  offset[50:0]
//   Format X: reserved[55:0]

`include "spu_isa_defines.vh"

module spu_isa_decoder (
    input  wire [63:0]  instr_word,       // 64-bit instruction from SPI slave
    input  wire         instr_valid,       // strobe: new instruction available

    // ── Decoded fields (for testbench / pipeline visibility) ──
    output reg  [ 7:0]  dec_opcode,
    output reg  [ 4:0]  dec_dest,
    output reg  [ 4:0]  dec_srcA,
    output reg  [ 4:0]  dec_srcB,
    output reg  [ 9:0]  dec_offset,        // Format L: signed 10-bit
    output reg  [50:0]  dec_immediate,      // Format I: 51-bit

    // ── Control signal bundles ──

    // RPLU config write (OFFR/CNFM → material table read)
    output reg          rplu_cfg_wr_en,
    output reg  [ 2:0]  rplu_cfg_sel,
    output reg  [ 7:0]  rplu_cfg_material,
    output reg  [ 9:0]  rplu_cfg_addr,
    output reg  [63:0]  rplu_cfg_data,

    // RAU control (quadrance arithmetic + geometric ops)
    output reg          rau_start,         // strobe: start RAU computation
    output reg  [ 2:0]  rau_opcode,        // RAU operation select

    // Phase-lock control
    output reg          phslk_start,       // strobe: execute phase-lock
    output reg          invj_en,           // enable Janus inversion
    output reg          phclr_en,          // clear phase-lock status

    // Flow control
    output reg          branch_taken,      // branch condition met
    output reg  [50:0]  branch_offset,     // signed 51-bit offset

    // Telemetry mux
    output reg          mfold_en,          // emit manifold
    output reg          stat_en,           // emit status
    output reg          hex_en,            // emit hex

    // Register file control
    output reg          reg_write_en,      // write to register file
    output reg  [ 4:0]  reg_write_addr,    // destination register
    output reg          reg_offer_sel,     // 1=write to .O, 0=write to .C
    output reg  [ 4:0]  reg_readA_addr,   // source A register
    output reg  [ 4:0]  reg_readB_addr,   // source B register
    output reg          reg_readA_O_sel,  // 1=read from .O, 0=read from .C
    output reg          reg_readB_O_sel,  // 1=read from .O, 0=read from .C

    // System
    output reg          halt,              // halt execution
    output reg          sync               // sync (wait for pending ops)
);

    // ── Field extraction (matching spu_isa_defines.vh) ──
    wire [7:0] opcode = instr_word[`SPU_FIELD_OPCODE];

    // Format R fields
    wire [4:0] fR_dest = instr_word[`SPU_R_DEST];
    wire [4:0] fR_srcA = instr_word[`SPU_R_SRCA];
    wire [4:0] fR_srcB = instr_word[`SPU_R_SRCB];

    // Format L fields
    wire [4:0] fL_dest  = instr_word[`SPU_L_DEST];
    wire [4:0] fL_base  = instr_word[`SPU_L_BASE];
    wire [9:0] fL_offset = instr_word[`SPU_L_OFFSET];

    // Format I fields
    wire [4:0] fI_dest = instr_word[`SPU_I_DEST];
    wire [50:0] fI_imm = instr_word[`SPU_I_IMM];

    // Format U fields
    wire [4:0] fU_dest = instr_word[`SPU_U_DEST];
    wire [4:0] fU_src  = instr_word[`SPU_U_SRC];
    wire [1:0] fU_cond = instr_word[`SPU_U_COND];

    // Format B fields
    wire [4:0] fB_flags  = instr_word[`SPU_B_FLAGS];
    wire [50:0] fB_offset = instr_word[`SPU_B_OFFSET];

    // ── Opcode decode (combinational) ──
    always @(*) begin
        // Start with defaults
        dec_opcode    = opcode;
        dec_dest      = fR_dest;
        dec_srcA      = fR_srcA;
        dec_srcB      = fR_srcB;
        dec_offset    = fL_offset;
        dec_immediate = fI_imm;
        halt          = 1'b0;
        sync          = 1'b0;
        rplu_cfg_wr_en     = 1'b0;
        rplu_cfg_sel       = 3'd0;
        rplu_cfg_material  = 8'd0;
        rplu_cfg_addr      = 10'd0;
        rplu_cfg_data      = 64'd0;

        rau_start     = 1'b0;
        rau_opcode    = 3'd0;

        phslk_start   = 1'b0;
        invj_en       = 1'b0;
        phclr_en      = 1'b0;

        branch_taken  = 1'b0;
        branch_offset = 51'd0;

        mfold_en = 1'b0;
        stat_en  = 1'b0;
        hex_en   = 1'b0;

        reg_write_en    = 1'b0;
        reg_write_addr  = fR_dest;
        reg_offer_sel   = 1'b1;
        reg_readA_addr  = fR_srcA;
        reg_readB_addr  = fR_srcB;
        reg_readA_O_sel = 1'b1;
        reg_readB_O_sel = 1'b1;

        if (!instr_valid) begin
            // No valid instruction — all outputs remain at default (zero)
        end else case (opcode)

            // ═══════════════════════════════════════════════════════════════
            // System & Control
            // ═══════════════════════════════════════════════════════════════
            `SPU_OP_NOP: begin end

            `SPU_OP_HALT: begin
                halt = 1'b1;
            end

            `SPU_OP_SYNC: begin
                sync = 1'b1;
            end

            // ═══════════════════════════════════════════════════════════════
            // Data Movement
            // ═══════════════════════════════════════════════════════════════
            `SPU_OP_LOAD, `SPU_OP_LDO: begin
                // LOAD/LDO: load from memory offset → R[dest].O
                reg_write_en   = 1'b1;
                reg_write_addr = fL_dest;
                reg_offer_sel  = 1'b1;    // .O slot
            end

            `SPU_OP_STORE: begin
                // STORE: R[srcA].O → memory
            end

            `SPU_OP_MOV: begin
                reg_write_en   = 1'b1;
                reg_write_addr = fR_dest;
                reg_readA_addr = fR_srcA;
                reg_readA_O_sel = 1'b1;
            end

            `SPU_OP_MOVI: begin
                reg_write_en   = 1'b1;
                reg_write_addr = fI_dest;
            end

            `SPU_OP_LDC: begin
                // LDC: load to Confirmation slot
                reg_write_en   = 1'b1;
                reg_write_addr = fL_dest;
                reg_offer_sel  = 1'b0;    // .C slot
            end

            // ═══════════════════════════════════════════════════════════════
            // Quadrance Arithmetic → RAU
            // ═══════════════════════════════════════════════════════════════
            `SPU_OP_QADD: begin
                rau_start   = 1'b1;
                rau_opcode  = 3'd1;       // RAU ADD
                reg_write_en   = 1'b1;
                reg_write_addr = fR_dest;
                reg_readA_addr = fR_srcA;
                reg_readB_addr = fR_srcB;
            end

            `SPU_OP_QSUB: begin
                rau_start   = 1'b1;
                rau_opcode  = 3'd2;       // RAU SUB
                reg_write_en   = 1'b1;
                reg_write_addr = fR_dest;
                reg_readA_addr = fR_srcA;
                reg_readB_addr = fR_srcB;
            end

            `SPU_OP_QMUL: begin
                rau_start   = 1'b1;
                rau_opcode  = 3'd3;       // RAU MUL
                reg_write_en   = 1'b1;
                reg_write_addr = fR_dest;
                reg_readA_addr = fR_srcA;
                reg_readB_addr = fR_srcB;
            end

            `SPU_OP_QCMP: begin
                rau_opcode  = 3'd4;       // RAU CMP
                reg_readA_addr = fR_srcA;
                reg_readB_addr = fR_srcB;
            end

            // ═══════════════════════════════════════════════════════════════
            // Geometric Operations → RAU
            // ═══════════════════════════════════════════════════════════════
            `SPU_OP_SPRD, `SPU_OP_ROTR, `SPU_OP_CROSS,
            `SPU_OP_DOT, `SPU_OP_TNSR, `SPU_OP_SOM: begin
                rau_start   = 1'b1;
                rau_opcode  = 3'd5;       // RAU GEOMETRIC
                reg_write_en   = 1'b1;
                reg_write_addr = fR_dest;
                reg_readA_addr = fR_srcA;
                reg_readB_addr = fR_srcB;
            end

            // ═══════════════════════════════════════════════════════════════
            // Temporal Operations (Wheeler-Feynman)
            // ═══════════════════════════════════════════════════════════════
            `SPU_OP_OFFR: begin
                // OFFR: load RPLU material params into R[dest].O
                rplu_cfg_wr_en    = 1'b1;
                rplu_cfg_sel      = 3'd0;       // params_elements
                rplu_cfg_material = {4'd0, fR_srcA[3:0]};  // material from srcA
                rplu_cfg_addr     = {5'd0, fR_srcB};       // addr from srcB
                reg_write_en      = 1'b1;
                reg_write_addr    = fR_dest;
                reg_offer_sel     = 1'b1;       // .O slot
            end

            `SPU_OP_CNFM: begin
                // CNFM: load RPLU material params into R[dest].C
                rplu_cfg_wr_en    = 1'b1;
                rplu_cfg_sel      = 3'd0;
                rplu_cfg_material = {4'd0, fR_srcA[3:0]};
                rplu_cfg_addr     = {5'd0, fR_srcB};
                reg_write_en      = 1'b1;
                reg_write_addr    = fR_dest;
                reg_offer_sel     = 1'b0;       // .C slot
            end

            `SPU_OP_PHSLK: begin
                // PHSLK: phase-lock Offer ∩ Confirmation
                phslk_start       = 1'b1;
                reg_readA_addr    = fR_srcA;
                reg_readB_addr    = fR_srcB;
                reg_readA_O_sel   = 1'b1;       // srcA = Offer
                reg_readB_O_sel   = 1'b0;       // srcB = Confirmation
                // Result goes to RAU cross-multiply comparator
                reg_write_en      = 1'b1;
                reg_write_addr    = fR_dest;
                reg_offer_sel     = 1'b1;       // result → .O
            end

            `SPU_OP_INVJ: begin
                // INVJ: invert through Janus point
                invj_en          = 1'b1;
                reg_write_en     = 1'b1;
                reg_write_addr   = fU_dest;
                reg_readA_addr   = fU_src;
                reg_readA_O_sel  = 1'b1;
            end

            `SPU_OP_PHSTA: begin
                // PHSTA: read phase-lock status
                reg_write_en   = 1'b1;
                reg_write_addr = fU_dest;
            end

            `SPU_OP_PHCLR: begin
                phclr_en = 1'b1;
            end

            // ═══════════════════════════════════════════════════════════════
            // RPLU Configuration
            // ═══════════════════════════════════════════════════════════════
            `SPU_OP_RCFG: begin
                // RCFG: write RPLU config record
                rplu_cfg_wr_en    = 1'b1;
                rplu_cfg_sel      = 3'd7;       // command select
                rplu_cfg_material = 8'd0;
                rplu_cfg_addr     = 10'd0;
                rplu_cfg_data     = instr_word; // pass through
            end

            // ═══════════════════════════════════════════════════════════════
            // Flow Control
            // ═══════════════════════════════════════════════════════════════
            `SPU_OP_JMP, `SPU_OP_JZ, `SPU_OP_JNZ,
            `SPU_OP_JC, `SPU_OP_JNC, `SPU_OP_CALL: begin
                branch_taken  = 1'b1;
                branch_offset = fB_offset;
            end

            `SPU_OP_RET: begin
                branch_taken = 1'b1;
            end

            // ═══════════════════════════════════════════════════════════════
            // Telemetry
            // ═══════════════════════════════════════════════════════════════
            `SPU_OP_MFOLD: mfold_en = 1'b1;
            `SPU_OP_STAT:  stat_en  = 1'b1;
            `SPU_OP_HEX:   hex_en   = 1'b1;

            default: begin end
        endcase
    end

endmodule
