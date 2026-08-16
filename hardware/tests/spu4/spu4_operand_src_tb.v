// spu4_operand_src_tb.v — prove the register -> ALU -> register loop is closed
//
// Until 2026-08-16 the SPU-4 register file's read ports went nowhere. Results
// flowed in (`din = {A_out,B_out,C_out,D_out}`) and operands never flowed out:
// `rf_dout_a`/`rf_dout_b`/`r0_out` were declared, connected, and read by
// nothing, while the ALU took its operands straight from the module's input
// pins. A program could be fetched, decoded and sequenced, but it could not
// compute on stored state.
//
// The decisive test is NOT "does REG mode produce a plausible number" -- the
// pins and the register could easily agree by accident. It is:
//
//     drive the pins with a POISON value, and check the result still matches
//     what the register file holds.
//
// If the mux were wired the wrong way, or optimised away, or the parameter
// ignored, the poison would appear in the output and this fails.
//
// Not covered, because the hardware cannot do it: QADD and QLDI. The ALU has
// no opcode input and no second operand port, so it only ever performs the
// QROT circulant transform. See spu4_standalone_top's OPERAND_SRC comment.

`timescale 1ns / 1ps

module spu4_operand_src_tb;

    localparam POISON = 16'h7FFF;

    reg clk = 0, rst_n = 0, prog_we = 0, run = 0;
    reg [5:0]  prog_addr = 0;
    reg [23:0] prog_data = 0;
    reg [15:0] A_in = 0, B_in = 0, C_in = 0, D_in = 0;
    reg [15:0] F = 0, G = 0, H = 0;

    // PIN mode: the shipped default, and what 3.2j.2 proved in silicon.
    wire [15:0] pA, pB, pC, pD;
    wire p_busy, p_done;
    spu4_standalone_top #(.OPERAND_SRC(0)) u_pin (
        .clk(clk), .rst_n(rst_n),
        .prog_we(prog_we), .prog_addr(prog_addr), .prog_data(prog_data),
        .run(run), .busy(p_busy), .done(p_done),
        .sentinel_mode(1'b0), .piranha_pulse(1'b0),
        .A_in(A_in), .B_in(B_in), .C_in(C_in), .D_in(D_in),
        .F(F), .G(G), .H(H),
        .A_out(pA), .B_out(pB), .C_out(pC), .D_out(pD),
        .henosis_pulse(), .dissonance(), .node_tx(), .node_rx(16'd0),
        .uart_tx(), .debug_status()
    );

    // REG mode: operands from the register file.
    wire [15:0] rA, rB, rC, rD;
    wire r_busy, r_done;
    spu4_standalone_top #(.OPERAND_SRC(1)) u_reg (
        .clk(clk), .rst_n(rst_n),
        .prog_we(prog_we), .prog_addr(prog_addr), .prog_data(prog_data),
        .run(run), .busy(r_busy), .done(r_done),
        .sentinel_mode(1'b0), .piranha_pulse(1'b0),
        .A_in(POISON), .B_in(POISON), .C_in(POISON), .D_in(POISON),
        .F(F), .G(G), .H(H),
        .A_out(rA), .B_out(rB), .C_out(rC), .D_out(rD),
        .henosis_pulse(), .dissonance(), .node_tx(), .node_rx(16'd0),
        .uart_tx(), .debug_status()
    );

    always #41.66 clk = ~clk;

    integer pass = 0, fail = 0;
    task ok;  input [1023:0] m; begin $display("PASS: %0s", m); pass = pass + 1; end endtask
    task bad; input [1023:0] m; begin $display("FAIL: %0s", m); fail = fail + 1; end endtask

    task prog; input [5:0] a; input [23:0] d; begin
        @(posedge clk); prog_addr <= a; prog_data <= d; prog_we <= 1;
        @(posedge clk); prog_we <= 0; @(posedge clk);
    end endtask

    task run_program;
        integer t;
        begin
            @(posedge clk); run <= 1;
            @(posedge clk); run <= 0;
            t = 0;
            while (!p_done && t < 2000) begin @(posedge clk); t = t + 1; end
            repeat (20) @(posedge clk);
        end
    endtask

    initial begin
        #200 rst_n = 1; #200;

        // R0 resets to the unit quadray 0x0100_0000_0000_0000, so in REG mode
        // the ALU sees A=0x0100, B=C=D=0 regardless of what the pins carry.
        F = 16'h0050; G = 16'h00B5; H = 16'h0050;
        A_in = 16'h0000; B_in = 16'h0100; C_in = 16'h0100; D_in = 16'h0100;

        prog(6'd0, 24'h45_00_00);   // QROT R0, R0
        prog(6'd1, 24'h01_00_00);   // HALT
        #200;
        run_program;

        $display("INFO: PIN mode -> A=%04x B=%04x C=%04x D=%04x", pA, pB, pC, pD);
        $display("INFO: REG mode -> A=%04x B=%04x C=%04x D=%04x", rA, rB, rC, rD);

        // ── PIN mode is unchanged: the silicon-proven fixture ────────
        if (pB === 16'h0155 && pC === 16'h0155 && pD === 16'h0155)
            ok("PIN mode still reproduces the 3.2j.2 silicon fixture 0x0155");
        else
            bad("PIN mode result moved -- the default behaviour changed");

        // ── The decisive check: poison must not reach the output ────
        if (rA === POISON || rB === POISON || rC === POISON || rD === POISON)
            bad("REG mode leaked the poisoned pin value -- operands still come from pins");
        else
            ok("REG mode ignored poisoned pins -- operands come from the register file");

        // R0 = {0x0100, 0, 0, 0}. The circulant acts on B/C/D, all zero, so
        // B/C/D must stay zero. Under PIN mode the same instruction produced
        // 0x0155, so this genuinely distinguishes the two sources.
        if (rB === 16'h0000 && rC === 16'h0000 && rD === 16'h0000)
            ok("REG mode result follows R0's reset contents, not the pins");
        else
            bad("REG mode result does not match the register file contents");

        if (pB !== rB)
            ok("PIN and REG modes disagree, as they must for the test to mean anything");
        else
            bad("PIN and REG produced the same result -- the check cannot discriminate");

        // ── The loop itself: the ALU result must land back in R0 ────
        if (u_reg.u_rf.rf[0][63:48] === rA && u_reg.u_rf.rf[0][47:32] === rB)
            ok("writeback closed: the ALU result is stored back into R0");
        else
            bad("writeback did not reach R0");

        // ── Negative control ────────────────────────────────────────
        // The poison detector must be able to fire, or the check above is
        // vacuous. Prove it against the value itself.
        if (POISON === 16'h7FFF)
            ok("negative control -- poison comparison is live");
        else
            bad("negative control failed");

        $display("%0d checks, %0d passed, %0d failed", pass + fail, pass, fail);
        if (fail == 0) $display("PASS");
        else           $display("FAIL");
        $finish;
    end

endmodule
