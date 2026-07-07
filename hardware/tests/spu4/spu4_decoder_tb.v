// spu4_decoder_tb.v — Standalone testbench for SPU-4 instruction decoder.
// Verifies all 5 opcodes produce correct alu_op, use_imm, snap_en, whisper_en.

`timescale 1ns / 1ps

module spu4_decoder_tb;
    reg [23:0] inst;
    wire [3:0] alu_op;
    wire [2:0] reg_dest, reg_src;
    wire [7:0] immediate;
    wire use_imm, snap_en, whisper_en;

    spu4_decoder u_dut (inst, alu_op, reg_dest, reg_src, immediate, use_imm, snap_en, whisper_en);

    integer pass, fail;
    reg [23:0] expected;

    initial begin
        pass = 0; fail = 0;

        // QLDI: opcode 0x10
        inst = 24'h10_01_AB; #10;
        if (alu_op !== 1 || !use_imm || reg_dest !== 1 || immediate !== 8'hAB)
            begin $display("FAIL QLDI"); fail = fail + 1; end
        else begin $display("PASS QLDI"); pass = pass + 1; end

        // QADD: opcode 0x40
        inst = 24'h40_02_03; #10;
        if (alu_op !== 2 || use_imm || snap_en || whisper_en)
            begin $display("FAIL QADD"); fail = fail + 1; end
        else begin $display("PASS QADD"); pass = pass + 1; end

        // QROT: opcode 0x45
        inst = 24'h45_04_05; #10;
        if (alu_op !== 3 || use_imm || snap_en || whisper_en)
            begin $display("FAIL QROT"); fail = fail + 1; end
        else begin $display("PASS QROT"); pass = pass + 1; end

        // SNAP: opcode 0x80
        inst = 24'h80_06_07; #10;
        if (!snap_en || alu_op !== 0)
            begin $display("FAIL SNAP"); fail = fail + 1; end
        else begin $display("PASS SNAP"); pass = pass + 1; end

        // W60T: opcode 0xA0
        inst = 24'hA0_00_00; #10;
        if (!whisper_en || alu_op !== 0)
            begin $display("FAIL W60T"); fail = fail + 1; end
        else begin $display("PASS W60T"); pass = pass + 1; end

        // NOP: unknown opcode → alu_op=0, no flags
        inst = 24'hFF_00_00; #10;
        if (alu_op !== 0 || use_imm || snap_en || whisper_en)
            begin $display("FAIL NOP"); fail = fail + 1; end
        else begin $display("PASS NOP"); pass = pass + 1; end

        if (fail == 0) $display("PASS");
        else $display("FAIL");
        $finish;
    end
endmodule
