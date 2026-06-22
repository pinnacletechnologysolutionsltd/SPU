// spu_pipeline_ctrl.v — SPU-13 4-Stage Pipeline Controller
//
// Stages:
//   0: FETCH    — Read instruction from chord FIFO (inst_valid/inst_word)
//   1: DECODE   — spu_isa_decoder extracts control signals
//   2: EXECUTE  — RAU computes (dual-read: Offer .O + Confirm .C)
//   3: WRITEBACK— Write result to twin-register file, emit telemetry
//
// The Wheeler-Feynman handshake is encoded in the RAU read ports:
//   Port A reads R[srcA].O (Offer wave, Tetrahedron A)
//   Port B reads R[srcB].C (Confirmation wave, Tetrahedron B)
//   Both propagate in parallel → resolved in same RAU cycle
//
// No hazard detection: RP2350 sends at ~1 kHz, FPGA clock = 6.25 MHz.
// Pipeline is never contended (~6000 free cycles per instruction).

`include "spu_isa_defines.vh"

module spu_pipeline_ctrl (
    input  wire         clk,
    input  wire         rst_n,

    // ── Instruction input (from SPI slave CDC) ──
    input  wire         inst_valid,
    input  wire [63:0]  inst_word,
    output wire         inst_ready,        // pipeline ready for next instruction

    // ── Decoder interface ──
    output wire [63:0]  dec_instr_word,
    output wire         dec_instr_valid,

    // ── Twin-register file interface ──
    output wire [ 4:0]  rf_raddrA,         // srcA (Offer)
    output wire [ 4:0]  rf_raddrB,         // srcB (Confirmation)
    output wire         rf_rselA_O,         // 1=read .O
    output wire         rf_rselB_O,         // 1=read .O, 0=read .C
    input  wire [63:0]  rf_rdataA,
    input  wire [63:0]  rf_rdataB,
    output wire         rf_wren,
    output wire [ 4:0]  rf_waddr,
    output wire         rf_wsel_O,          // 1=write .O, 0=write .C
    output wire [63:0]  rf_wdata,

    // ── RAU interface ──
    output wire [63:0]  rau_opA_O,
    output wire [63:0]  rau_opB_C,
    output wire [ 3:0]  rau_op,
    input  wire [63:0]  rau_result,
    input  wire         rau_coherent,
    input  wire         rau_result_zero,
    input  wire         rau_result_sign,

    // ── Decoder control outputs (from pipeline stage 1) ──
    // These are the outputs of spu_isa_decoder, latched at decode stage
    output wire [ 7:0]  pipe_opcode,
    output wire         pipe_phslk,
    output wire         pipe_invj,
    output wire         pipe_mfold,
    output wire         pipe_stat,
    output wire         pipe_halt,

    // ── Telemetry output (from pipeline stage 3) ──
    output reg          telem_valid,
    output reg  [ 7:0]  telem_opcode,
    output reg  [63:0]  telem_data
);

    // ── Pipeline registers ──
    reg [63:0]  stage_fetch_instr;
    reg         stage_fetch_valid;

    reg [63:0]  stage_decode_instr;
    reg         stage_decode_valid;

    reg [63:0]  stage_exec_instr;
    reg         stage_exec_valid;

    reg [63:0]  stage_wb_instr;
    reg         stage_wb_valid;

    // ── Decoded fields (latched at decode stage) ──
    reg [ 7:0]  stage_opcode;
    reg [ 4:0]  stage_dest, stage_srcA, stage_srcB;
    reg         stage_rselA_O, stage_rselB_O;
    reg         stage_rf_wren;
    reg         stage_rf_wsel_O;
    reg [ 3:0]  stage_rau_op;
    reg         stage_is_phslk;
    reg         stage_is_invj;
    reg         stage_is_load;        // true for LOAD/LDO/LDC/MOVI
    reg         stage_is_mfold;
    reg         stage_is_stat;
    reg         stage_is_halt;
    reg [63:0]  stage_offset_or_imm;  // captured offset/immediate for loads

    // ── Decoder instantiation ──
    wire [ 7:0] dec_opcode;
    wire [ 4:0] dec_dest, dec_srcA, dec_srcB;
    wire        dec_reg_write_en, dec_reg_offer_sel;
    wire        dec_rau_start;
    wire [ 3:0] dec_rau_opcode;
    wire        dec_phslk_start, dec_invj_en;
    wire        dec_mfold_en, dec_stat_en;
    wire        dec_halt;
    // Unused decoder outputs
    wire [ 9:0] dec_offset;
    wire [50:0] dec_immediate;
    wire        dec_rplu_cfg_wr_en;
    wire [ 2:0] dec_rplu_cfg_sel;
    wire [ 7:0] dec_rplu_cfg_material;
    wire [ 9:0] dec_rplu_cfg_addr;
    wire [63:0] dec_rplu_cfg_data;
    wire        dec_branch_taken;
    wire [50:0] dec_branch_offset;
    wire        dec_phclr_en;
    wire        dec_hex_en;
    wire        dec_sync;

    spu_isa_decoder u_decoder (
        .instr_word(inst_word),
        .instr_valid(inst_valid),
        .dec_opcode(dec_opcode),
        .dec_dest(dec_dest),
        .dec_srcA(dec_srcA),
        .dec_srcB(dec_srcB),
        .dec_offset(dec_offset),
        .dec_immediate(dec_immediate),
        .rplu_cfg_wr_en(dec_rplu_cfg_wr_en),
        .rplu_cfg_sel(dec_rplu_cfg_sel),
        .rplu_cfg_material(dec_rplu_cfg_material),
        .rplu_cfg_addr(dec_rplu_cfg_addr),
        .rplu_cfg_data(dec_rplu_cfg_data),
        .rau_start(dec_rau_start),
        .rau_opcode(dec_rau_opcode),
        .phslk_start(dec_phslk_start),
        .invj_en(dec_invj_en),
        .phclr_en(dec_phclr_en),
        .branch_taken(dec_branch_taken),
        .branch_offset(dec_branch_offset),
        .mfold_en(dec_mfold_en),
        .stat_en(dec_stat_en),
        .hex_en(dec_hex_en),
        .reg_write_en(dec_reg_write_en),
        .reg_write_addr(dec_dest),
        .reg_offer_sel(dec_reg_offer_sel),
        .reg_readA_addr(dec_srcA),
        .reg_readB_addr(dec_srcB),
        .reg_readA_O_sel(),
        .reg_readB_O_sel(),
        .halt(dec_halt),
        .sync(dec_sync)
    );

    // Decoder is purely combinational — valid when inst_valid is high
    assign dec_instr_word   = inst_word;
    assign dec_instr_valid  = inst_valid;

    // Pipeline ready: always ready (no backpressure from RP2350 at 1 kHz)
    assign inst_ready = 1'b1;

    // ── Pipeline register interface ──
    assign rf_raddrA  = stage_srcA;
    assign rf_raddrB  = stage_srcB;
    assign rf_rselA_O = 1'b1;              // Port A always reads .O
    assign rf_rselB_O = 1'b0;              // Port B always reads .C
    assign rf_rselA_O = 1'b1;              // Port A always reads .O
    assign rf_rselB_O = 1'b0;              // Port B always reads .C

    assign rau_opA_O  = rf_rdataA;
    assign rau_opB_C  = rf_rdataB;
    assign rau_op     = stage_rau_op;

    assign rf_wren    = stage_rf_wren;
    assign rf_waddr   = stage_dest;
    assign rf_wsel_O  = stage_rf_wsel_O;

    // Writeback data mux:
    //   - LOAD/LDO/LDC: use the instruction offset or immediate field
    //   - INVJ: negate the RAU result (two's complement)
    //   - All others: use RAU result
    wire [63:0] wb_load_data;
    assign wb_load_data = {52'd0, stage_offset_or_imm[11:0]};  // offset or low 12 bits
    assign rf_wdata = stage_is_load ? wb_load_data : 
                      stage_is_invj ? ~rau_result + 1'b1 : 
                      rau_result;
    // INVJ: negate result (two's complement: invert + 1)
    // For quadray negation: ( -a, -b, -c, -d ) = ~result + 1 in each component
    // Simpler: just use RAU's own result for all non-INVJ ops

    // Pipe decoder outputs
    assign pipe_opcode = stage_opcode;
    assign pipe_phslk  = stage_is_phslk;
    assign pipe_invj   = stage_is_invj;
    assign pipe_mfold  = stage_is_mfold;
    assign pipe_stat   = stage_is_stat;
    assign pipe_halt   = stage_is_halt;

    // ── Pipeline control logic ──
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            stage_fetch_valid  <= 1'b0;
            stage_decode_valid <= 1'b0;
            stage_exec_valid   <= 1'b0;
            stage_wb_valid     <= 1'b0;

            stage_opcode  <= 8'd0;
            stage_dest    <= 5'd0;
            stage_srcA    <= 5'd0;
            stage_srcB    <= 5'd0;
            stage_rau_op  <= 4'd0;
            stage_rf_wren <= 1'b0;
            stage_rf_wsel_O <= 1'b1;
            stage_rselA_O <= 1'b1;
            stage_rselB_O <= 1'b0;
            stage_is_phslk <= 1'b0;
            stage_is_invj  <= 1'b0;
            stage_is_load  <= 1'b0;
            stage_is_mfold <= 1'b0;
            stage_is_stat  <= 1'b0;
            stage_is_halt  <= 1'b0;
            stage_offset_or_imm <= 64'd0;

            telem_valid <= 1'b0;
            telem_opcode <= 8'd0;
            telem_data <= 64'd0;
        end else begin
            // ── Defaults ──
            telem_valid <= 1'b0;

            // ── Stage 0 → Stage 1 (FETCH → DECODE) ──
            stage_fetch_instr  <= inst_word;
            stage_fetch_valid  <= inst_valid;

            // ── Stage 1 → Stage 2 (DECODE → EXECUTE) ──
            if (stage_fetch_valid) begin
                // Latch decoded fields from combinational decoder
                stage_decode_instr  <= stage_fetch_instr;
                stage_decode_valid  <= 1'b1;
                stage_opcode  <= dec_opcode;
                stage_dest    <= dec_dest;
                stage_srcA    <= dec_srcA;
                stage_srcB    <= dec_srcB;
                stage_rau_op  <= dec_rau_opcode;
                stage_rf_wren <= dec_reg_write_en;
                stage_rf_wsel_O <= dec_reg_offer_sel;
                stage_is_phslk <= (dec_opcode == `SPU_OP_PHSLK);
                stage_is_invj  <= (dec_opcode == `SPU_OP_INVJ);
                stage_is_load  <= (dec_opcode == `SPU_OP_LOAD || 
                                   dec_opcode == `SPU_OP_LDO  ||
                                   dec_opcode == `SPU_OP_LDC  ||
                                   dec_opcode == `SPU_OP_MOVI);
                stage_is_mfold <= (dec_opcode == `SPU_OP_MFOLD);
                stage_is_stat  <= (dec_opcode == `SPU_OP_STAT);
                stage_is_halt  <= (dec_opcode == `SPU_OP_HALT);
                // Capture offset/immediate from instruction word
                // Format L: offset at [45:36] (10-bit signed)
                // Format I: immediate at [50:0] (51-bit)
                stage_offset_or_imm <= {54'd0, stage_fetch_instr[45:36]};
            end else begin
                stage_decode_valid <= 1'b0;
            end

            // ── Stage 2 → Stage 3 (EXECUTE → WRITEBACK) ──
            if (stage_decode_valid) begin
                stage_exec_instr <= stage_decode_instr;
                stage_exec_valid <= 1'b1;
            end else begin
                stage_exec_valid <= 1'b0;
            end

            // ── Stage 3: WRITEBACK ──
            if (stage_exec_valid) begin
                stage_wb_valid <= 1'b1;

                // Telemetry emission
                if (stage_is_mfold) begin
                    telem_valid  <= 1'b1;
                    telem_opcode <= `SPU_OP_MFOLD;
                    telem_data   <= rau_result;
                end
                if (stage_is_stat) begin
                    telem_valid  <= 1'b1;
                    telem_opcode <= `SPU_OP_STAT;
                    telem_data   <= {56'd0, rau_coherent, rau_result_zero, rau_result_sign, 5'd0};
                end
                if (stage_is_halt) begin
                    // HALT: pipeline stops processing
                end
            end else begin
                stage_wb_valid <= 1'b0;
            end
        end
    end

endmodule
