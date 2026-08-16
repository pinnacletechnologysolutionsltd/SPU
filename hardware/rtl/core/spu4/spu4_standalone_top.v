`timescale 1ns / 1ps

// spu4_standalone_top.v — Standalone SPU-4 with cluster interface.
//
// Extracted from spu4_core.v with modernized sequencer.
// Pipeline:  Sequencer → Decoder → Regfile → ALU → Regfile (writeback)
//
// Optional cluster interface (for SPU-13 integration):
//   node_tx[31:0] — status frame to governor
//   node_rx[15:0] — command frame from governor

module spu4_standalone_top #(
    parameter MEM_DEPTH = 64,
    parameter ADDR_W    = 6,
    // ── Operand source (Tier 1, 2026-08-16) ──────────────────────────
    //   0 = PIN  operands come from A_in..D_in. The original behaviour and
    //            the DEFAULT, so no existing bitstream moves. This is what
    //            hardware_evidence.md 3.2j.2 proved on silicon.
    //   1 = REG  operands come from the register file at reg_dest, so
    //            `QROT Rd` rotates the quadray held in Rd and writes it
    //            back. This is the closed register -> ALU -> register loop.
    //   2 = SELF the ALU feeds back its own output (mode_autonomous, which
    //            the ALU has always supported and which was hardwired off).
    //
    // Until this parameter existed the register file's read ports went
    // nowhere and register operands could never reach the ALU: results
    // flowed in, operands never flowed out. See docs/SPU4_ABI.md 1.
    //
    // NOT closed by this change: QADD and QLDI. The ALU has no opcode input
    // and no second operand port, so it can only ever perform the QROT
    // circulant transform. Those need arithmetic-core changes and are a
    // separate decision.
    parameter OPERAND_SRC = 0
) (
    input  wire         clk,
    input  wire         rst_n,

    // Program load (SPI slave interface)
    input  wire         prog_we,
    input  wire [ADDR_W-1:0] prog_addr,
    input  wire [23:0]  prog_data,

    // Execution control
    input  wire         run,
    output wire         busy,
    output wire         done,

    // Sentinel mode
    input  wire         sentinel_mode,
    input  wire         piranha_pulse,

    // Quadray inputs (slave mode)
    input  wire [15:0]  A_in, B_in, C_in, D_in,
    input  wire [15:0]  F, G, H,

    // Quadray outputs
    output wire [15:0]  A_out, B_out, C_out, D_out,
    output wire         henosis_pulse,

    // Saturating Quadray residual (T7.4, 2026-08-15)
    output wire [7:0]   dissonance,

    // Cluster link (to/from SPU-13 governor)
    output wire [31:0]  node_tx,
    input  wire [15:0]  node_rx,

    // UART telemetry
    output wire         uart_tx,

    // Status
    output wire [7:0]   debug_status
);
    // ── Sequencer ────────────────────────────────────────────────────
    wire [23:0] seq_instr;
    wire        alu_start, alu_done;
    wire        reg_we;
    wire [2:0]  reg_dest;
    wire [7:0]  reg_imm;
    wire [ADDR_W-1:0] pc;
    wire        seq_busy, seq_done;

    spu4_sequencer #(.MEM_DEPTH(MEM_DEPTH), .ADDR_W(ADDR_W)) u_seq (
        .clk(clk), .rst_n(rst_n),
        .prog_we(prog_we), .prog_addr(prog_addr), .prog_data(prog_data),
        .run(run), .sentinel_mode(sentinel_mode), .piranha_pulse(piranha_pulse),
        .busy(seq_busy), .done(seq_done),
        .instruction(seq_instr), .alu_start(alu_start), .alu_done(alu_done),
        .reg_we(reg_we), .reg_dest(reg_dest), .reg_imm(reg_imm),
        .branch_taken(1'b0), .pc(pc)
    );

    // ── Decoder ─────────────────────────────────────────────────────
    wire [3:0]  alu_op;
    wire [2:0]  dec_dest, dec_src;
    wire [7:0]  dec_imm;
    wire        use_imm, snap_en, whisper_en;

    spu4_decoder u_dec (
        .inst_word(seq_instr),
        .alu_op(alu_op),
        .reg_dest(dec_dest),
        .reg_src(dec_src),
        .immediate(dec_imm),
        .use_imm(use_imm),
        .snap_en(snap_en),
        .whisper_en(whisper_en)
    );

    // ── Register file ───────────────────────────────────────────────
    wire [63:0] rf_dout_a, rf_dout_b, r0_out;

    spu4_regfile u_rf (
        .clk(clk), .rst_n(rst_n),
        .we(reg_we),
        .addr_a(reg_dest),
        .addr_b(dec_src),
        .din({A_out, B_out, C_out, D_out}),
        .dout_a(rf_dout_a),
        .dout_b(rf_dout_b),
        .r0_out(r0_out)
    );

    // ── Operand mux ──────────────────────────────────────────────────
    // The register file stores {A,B,C,D} as one 64-bit word, A in the high
    // lane. Reading dout_a (addressed by reg_dest) is what closes the loop:
    // the destination register is also the operand source, so a rotation
    // composes onto the value already there.
    wire [15:0] op_A = (OPERAND_SRC == 1) ? rf_dout_a[63:48] : A_in;
    wire [15:0] op_B = (OPERAND_SRC == 1) ? rf_dout_a[47:32] : B_in;
    wire [15:0] op_C = (OPERAND_SRC == 1) ? rf_dout_a[31:16] : C_in;
    wire [15:0] op_D = (OPERAND_SRC == 1) ? rf_dout_a[15:0]  : D_in;

    // ── ALU ──────────────────────────────────────────────────────────
    wire mode_auto;

    spu4_euclidean_alu u_alu (
        .clk(clk), .reset(!rst_n),
        .start(alu_start),
        .bloom_intensity(8'hFF),
        .mode_autonomous(mode_auto),
        .A_in(op_A), .B_in(op_B), .C_in(op_C), .D_in(op_D),
        .F(F), .G(G), .H(H),
        .A_out(A_out), .B_out(B_out), .C_out(C_out), .D_out(D_out),
        .done(alu_done),
        .henosis_pulse(henosis_pulse)
    );

    // SELF mode routes operands through the ALU's own output registers.
    // This capability was always present in spu4_euclidean_alu and was
    // hardwired off, with a comment claiming the sequencer could set it --
    // it could not, it was a constant.
    assign mode_auto = (OPERAND_SRC == 2);

    // ── Cluster link (spu_node_link) ─────────────────────────────────
    // Placeholder: pack status into node_tx, unpack commands from node_rx

    // ── Dissonance: saturating absolute value of gasket residual ─────
    // Same module as spu4_core uses, over this wrapper's ALU outputs. It was
    // a copied expression until 2026-08-16; sharing the module is what makes
    // "the core and the wrapper must not diverge" structural rather than a
    // comment. See spu4_dissonance.v for the width reasoning.
    spu4_dissonance u_dissonance (
        .A(A_out), .B(B_out), .C(C_out), .D(D_out),
        .dissonance(dissonance)
    );

    // ── Output assignments ───────────────────────────────────────────
    assign busy = seq_busy;
    assign done = seq_done;

    // ── Debug ────────────────────────────────────────────────────────
    assign debug_status = {
        seq_busy,
        seq_done,
        henosis_pulse,
        snap_en,
        whisper_en,
        pc[2:0]
    };

endmodule
