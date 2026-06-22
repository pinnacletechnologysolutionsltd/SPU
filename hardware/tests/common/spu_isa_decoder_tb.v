// spu_isa_decoder_tb.v — Testbench for spu_isa_decoder
//
// Verifies all instruction formats decode correctly and that
// temporal opcodes (OFFR/CNFM/PHSLK/INVJ) produce the right
// control signal bundles.
//
// Usage: iverilog -g2012 -I ../../rtl/arch -I ../../rtl/core/shared \
//          spu_isa_decoder_tb.v ../../rtl/core/shared/spu_isa_decoder.v \
//          -o spu_isa_decoder_tb.vvp && vvp spu_isa_decoder_tb.vvp

`timescale 1ns/1ps

`include "spu_isa_defines.vh"

module spu_isa_decoder_tb;

    reg  [63:0] instr_word;
    reg         instr_valid;

    wire [ 7:0] dec_opcode;
    wire [ 4:0] dec_dest, dec_srcA, dec_srcB;
    wire [ 9:0] dec_offset;
    wire [50:0] dec_immediate;

    wire rplu_cfg_wr_en;
    wire [ 2:0] rplu_cfg_sel;
    wire [ 7:0] rplu_cfg_material;
    wire [ 9:0] rplu_cfg_addr;
    wire [63:0] rplu_cfg_data;

    wire rau_start;
    wire [ 3:0] rau_opcode;
    wire phslk_start, invj_en, phclr_en;
    wire branch_taken;
    wire [50:0] branch_offset;
    wire mfold_en, stat_en, hex_en;
    wire reg_write_en;
    wire [4:0] reg_write_addr;
    wire reg_offer_sel;
    wire [4:0] reg_readA_addr, reg_readB_addr;
    wire reg_readA_O_sel, reg_readB_O_sel;
    wire halt, sync;

    // DUT
    spu_isa_decoder uut (
        .instr_word(instr_word),
        .instr_valid(instr_valid),
        .dec_opcode(dec_opcode),
        .dec_dest(dec_dest),
        .dec_srcA(dec_srcA),
        .dec_srcB(dec_srcB),
        .dec_offset(dec_offset),
        .dec_immediate(dec_immediate),
        .rplu_cfg_wr_en(rplu_cfg_wr_en),
        .rplu_cfg_sel(rplu_cfg_sel),
        .rplu_cfg_material(rplu_cfg_material),
        .rplu_cfg_addr(rplu_cfg_addr),
        .rplu_cfg_data(rplu_cfg_data),
        .rau_start(rau_start),
        .rau_opcode(rau_opcode),
        .phslk_start(phslk_start),
        .invj_en(invj_en),
        .phclr_en(phclr_en),
        .branch_taken(branch_taken),
        .branch_offset(branch_offset),
        .mfold_en(mfold_en),
        .stat_en(stat_en),
        .hex_en(hex_en),
        .reg_write_en(reg_write_en),
        .reg_write_addr(reg_write_addr),
        .reg_offer_sel(reg_offer_sel),
        .reg_readA_addr(reg_readA_addr),
        .reg_readB_addr(reg_readB_addr),
        .reg_readA_O_sel(reg_readA_O_sel),
        .reg_readB_O_sel(reg_readB_O_sel),
        .halt(halt),
        .sync(sync)
    );

    integer errors;

    task check_str;
        input [63:0] got;
        input [63:0] expected;
        input [200:0] desc;
        if (got !== expected) begin
            $display("FAIL: %s: got 0x%h, expected 0x%h", desc, got, expected);
            errors = errors + 1;
        end else begin
            $display("PASS: %s", desc);
        end
    endtask

    task check_int;
        input integer got;
        input integer expected;
        input [200:0] desc;
        if (got !== expected) begin
            $display("FAIL: %s: got %0d, expected %0d", desc, got, expected);
            errors = errors + 1;
        end else begin
            $display("PASS: %s", desc);
        end
    endtask

    initial begin
        errors = 0;
        instr_valid = 0;
        instr_word = 64'd0;

        #10;

        // ═════════════════════════════════════════════════════════════════
        // 1. Format R — PHSLK R12, R10, R11
        // ═════════════════════════════════════════════════════════════════
        $display("\n── Format R: PHSLK R12, R10, R11 ──");
        // opcode=0x42, dest=12, srcA=10, srcB=11
        instr_word = {8'h42, 5'd12, 5'd10, 5'd11, 41'd0};
        instr_valid = 1;
        #10;
        check_int(dec_opcode, `SPU_OP_PHSLK, "PHSLK: opcode");
        check_int(dec_dest,   12,          "PHSLK: dest");
        check_int(dec_srcA,   10,          "PHSLK: srcA");
        check_int(dec_srcB,   11,          "PHSLK: srcB");
        check_int(phslk_start, 1,          "PHSLK: phslk_start");
        check_int(reg_readA_O_sel, 1,      "PHSLK: readA=.O (Offer)");
        check_int(reg_readB_O_sel, 0,      "PHSLK: readB=.C (Confirm)");
        check_int(reg_write_en, 1,         "PHSLK: reg_write");
        check_int(reg_write_addr, 12,      "PHSLK: dest=12");
        check_int(reg_offer_sel, 1,        "PHSLK: write to .O");

        // ═════════════════════════════════════════════════════════════════
        // 2. Format R — OFFR R8, R1, R5   (material=1, addr=5)
        // ═════════════════════════════════════════════════════════════════
        $display("\n── Format R: OFFR R8, R1, R5 ──");
        instr_word = {8'h40, 5'd8, 5'd1, 5'd5, 41'd0};
        instr_valid = 1;
        #10;
        check_int(dec_opcode, `SPU_OP_OFFR, "OFFR: opcode");
        check_int(rplu_cfg_wr_en, 1,          "OFFR: rplu_cfg_wr_en");
        check_int(rplu_cfg_material, 8'd1,    "OFFR: material=1");
        check_int(rplu_cfg_addr, 10'd5,       "OFFR: addr=5");
        check_int(reg_write_en, 1,            "OFFR: reg_write");
        check_int(reg_write_addr, 8,          "OFFR: dest=8");
        check_int(reg_offer_sel, 1,           "OFFR: write to .O");

        // ═════════════════════════════════════════════════════════════════
        // 3. Format R — CNFM R9, R0, R10  (material=0, addr=10)
        // ═════════════════════════════════════════════════════════════════
        $display("\n── Format R: CNFM R9, R0, R10 ──");
        instr_word = {8'h41, 5'd9, 5'd0, 5'd10, 41'd0};
        instr_valid = 1;
        #10;
        check_int(dec_opcode, `SPU_OP_CNFM, "CNFM: opcode");
        check_int(rplu_cfg_wr_en, 1,          "CNFM: rplu_cfg_wr_en");
        check_int(reg_write_en, 1,            "CNFM: reg_write");
        check_int(reg_write_addr, 9,          "CNFM: dest=9");
        check_int(reg_offer_sel, 0,           "CNFM: write to .C");

        // ═════════════════════════════════════════════════════════════════
        // 4. Format U — INVJ R16, R15
        // ═════════════════════════════════════════════════════════════════
        $display("\n── Format U: INVJ R16, R15 ──");
        instr_word = {8'h43, 5'd16, 5'd15, 2'd0, 44'd0};
        instr_valid = 1;
        #10;
        check_int(dec_opcode, `SPU_OP_INVJ, "INVJ: opcode");
        check_int(invj_en, 1,                "INVJ: invj_en");
        check_int(reg_write_en, 1,           "INVJ: reg_write");
        check_int(reg_write_addr, 16,        "INVJ: dest=16");
        check_int(reg_offer_sel, 1,          "INVJ: write to .O");

        // ═════════════════════════════════════════════════════════════════
        // 5. Format I — MOVI R1, 0x1000
        // ═════════════════════════════════════════════════════════════════
        $display("\n── Format I: MOVI R1, 0x1000 ──");
        instr_word = {8'h13, 5'd1, 51'd4096};
        instr_valid = 1;
        #10;
        check_int(dec_opcode, `SPU_OP_MOVI, "MOVI: opcode");
        check_int(reg_write_en, 1,           "MOVI: reg_write");
        check_int(reg_write_addr, 1,         "MOVI: dest=1");

        // ═════════════════════════════════════════════════════════════════
        // 6. Format X — HALT
        // ═════════════════════════════════════════════════════════════════
        $display("\n── Format X: HALT ──");
        instr_word = {8'h01, 56'd0};
        instr_valid = 1;
        #10;
        check_int(halt, 1, "HALT: halt");

        // ═════════════════════════════════════════════════════════════════
        // 7. Format X — MFOLD
        // ═════════════════════════════════════════════════════════════════
        $display("\n── Format X: MFOLD ──");
        instr_word = {8'h70, 56'd0};
        instr_valid = 1;
        #10;
        check_int(mfold_en, 1, "MFOLD: mfold_en");

        // ═════════════════════════════════════════════════════════════════
        // 8. Format B — JZ offset=2
        // ═════════════════════════════════════════════════════════════════
        $display("\n── Format B: JZ +2 ──");
        instr_word = {8'h62, 5'd0, 51'd2};
        instr_valid = 1;
        #10;
        check_int(dec_opcode, `SPU_OP_JZ, "JZ: opcode");
        check_int(branch_taken, 1,         "JZ: branch_taken");

        // ═════════════════════════════════════════════════════════════════
        // 9. Format L — LDC R3, offset=100  (load to .C)
        // ═════════════════════════════════════════════════════════════════
        $display("\n── Format L: LDC R3, 100 ──");
        instr_word = {8'h15, 5'd3, 5'd0, 10'd100, 36'd0};
        instr_valid = 1;
        #10;
        check_int(dec_opcode, `SPU_OP_LDC, "LDC: opcode");
        check_int(reg_write_en, 1,          "LDC: reg_write");
        check_int(reg_write_addr, 3,        "LDC: dest=3");
        check_int(reg_offer_sel, 0,         "LDC: write to .C");

        // ═════════════════════════════════════════════════════════════════
        // 10. No valid instruction — all outputs should be zero
        // ═════════════════════════════════════════════════════════════════
        $display("\n── No valid instruction ──");
        instr_valid = 0;
        #10;
        check_int(rplu_cfg_wr_en, 0, "no valid: rplu_cfg_wr_en=0");
        check_int(reg_write_en, 0,   "no valid: reg_write_en=0");
        check_int(phslk_start, 0,    "no valid: phslk_start=0");
        check_int(mfold_en, 0,       "no valid: mfold_en=0");

        // ═════════════════════════════════════════════════════════════════
        // Results
        // ═════════════════════════════════════════════════════════════════
        #10;
        $display("\n── SUMMARY ──");
        if (errors == 0)
            $display("ALL TESTS PASSED");
        else
            $display("%0d TESTS FAILED", errors);
        $finish;
    end

endmodule
