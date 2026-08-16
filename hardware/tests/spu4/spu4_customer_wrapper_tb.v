// spu4_customer_wrapper_tb.v — the ABI v1.0 contract, asserted
//
// This file is the executable form of docs/SPU4_ABI.md. Every numbered
// guarantee in that document has a check here, and the check is written to
// fail if the guarantee is withdrawn. A contract nobody can observe breaking
// is not a contract.
//
// The guarantee that motivated the whole wrapper is G1. `spu4_standalone_top`
// -- the module the claim ledger previously named as the product interface --
// declares `uart_tx` and `node_tx[31:0]` as outputs and drives NEITHER. Both
// read `z`, verified 2026-08-16. Every consumer had left them unconnected, so
// nothing ever noticed. That is the same failure shape as the `dissonance`
// port being absent from the wrapper entirely (T7.4) and as the residual
// reading laminar at maximum fault (3.2j.1): a product surface asserted in a
// document and never exercised.

`timescale 1ns / 1ps

module spu4_customer_wrapper_tb;

    reg clk = 0, rst_n = 0, start = 0;
    reg signed [15:0] a_in = 0, b_in = 0, c_in = 0, d_in = 0;
    reg signed [15:0] coeff_f = 0, coeff_g = 0, coeff_h = 0;

    wire busy, done;
    wire signed [15:0] a_out, b_out, c_out, d_out;
    wire [7:0] dissonance, status;

    spu4_customer_wrapper dut (
        .clk(clk), .rst_n(rst_n),
        .start(start), .busy(busy), .done(done),
        .a_in(a_in), .b_in(b_in), .c_in(c_in), .d_in(d_in),
        .coeff_f(coeff_f), .coeff_g(coeff_g), .coeff_h(coeff_h),
        .a_out(a_out), .b_out(b_out), .c_out(c_out), .d_out(d_out),
        .dissonance(dissonance), .status(status)
    );

    always #41.66 clk = ~clk;          // 12 MHz, matching the reference build

    integer pass = 0, fail = 0;
    integer latency, worst_latency = 0, best_latency = 99999;

    // Deliberately undriven, for the negative control at the end: it proves
    // the X/Z detector used by every G1 check is capable of firing.
    wire undriven_probe;

    task ok; input [1023:0] what; begin
        $display("PASS: %0s", what); pass = pass + 1; end
    endtask
    task bad; input [1023:0] what; begin
        $display("FAIL: %0s", what); fail = fail + 1; end
    endtask

    // Drive one operation and measure its latency in clocks from the accepted
    // `start` edge to `done`.
    //
    // The `#1` after the accept edge is load-bearing, not cosmetic. `done` is
    // a level held from the PREVIOUS operation until the next accepted start,
    // so without letting the nonblocking updates settle the wait loop below
    // samples the stale `done == 1` and returns instantly. That produced a
    // measured latency of 0 and, worse, two checks that passed while asserting
    // nothing -- the result registers still held the previous operation's
    // correct value, so a comparison against it succeeded vacuously.
    task launch;
        input signed [15:0] a, b, c, d, f, g, h;
        begin
            while (busy) @(posedge clk);
            @(posedge clk);
            a_in <= a; b_in <= b; c_in <= c; d_in <= d;
            coeff_f <= f; coeff_g <= g; coeff_h <= h;
            start <= 1'b1;
            @(posedge clk);            // the accept edge
            start <= 1'b0;
            #1;                        // let done_q/busy_q reflect the accept
        end
    endtask

    task await_done;
        begin
            latency = 0;
            while (!done && latency < 5000) begin
                @(posedge clk);
                latency = latency + 1;
            end
            if (latency > worst_latency) worst_latency = latency;
            if (latency < best_latency) best_latency = latency;
        end
    endtask

    task run_op;
        input signed [15:0] a, b, c, d, f, g, h;
        begin
            launch(a, b, c, d, f, g, h);
            await_done;
        end
    endtask

    // Put the result registers into a state that is NOT the reference answer,
    // so any later comparison against 0x0155 can only succeed if the operation
    // under test genuinely ran. Without this, a check that never launches
    // still sees the previous 0x0155 and passes for the wrong reason.
    task poison_results;
        begin
            run_op(16'sh0000, 16'sh0000, 16'sh0000, 16'sh0000,
                   16'sh0000, 16'sh0000, 16'sh0000);
            if (b_out === 16'sh0155)
                bad("poison_results failed to displace the reference value");
        end
    endtask

    // Any X or Z on any output is a G1 violation.
    task check_no_xz; input [1023:0] where; begin
        if (^{busy, done, a_out, b_out, c_out, d_out, dissonance, status} === 1'bx)
            bad({"G1 undriven/unknown output at ", where});
        else
            ok({"G1 all outputs driven at ", where});
    end endtask

    initial begin
        // ── G1 at reset, before anything has run ─────────────────────
        // The strongest place to catch an undriven port: nothing has
        // executed, so a driven output must still read a defined value.
        #200 rst_n = 1; @(posedge clk);
        check_no_xz("reset release");

        if (done !== 1'b0) bad("G3 done must be low from reset until a result");
        else               ok("G3 done low from reset");

        // ── Operation 1: the QROT reference fixture ──────────────────
        // Same vector as the silicon probe: B=C=D=0x0100 under F=0x50,
        // G=0xB5, H=0x50 rotates to B=C=D=0x155.
        run_op(16'sh0000, 16'sh0100, 16'sh0100, 16'sh0100,
               16'sh0050, 16'sh00B5, 16'sh0050);

        if (!done) bad("operation 1 never completed");
        else begin
            ok("operation 1 completed");
            check_no_xz("after operation 1");
            if (b_out === 16'sh0155 && c_out === 16'sh0155 && d_out === 16'sh0155)
                ok("QROT reference fixture reproduces 0x0155 on B, C, D");
            else
                bad("QROT reference fixture wrong result");
            // Residual is 0 + 3*0x155 = 0x3FF, which saturates.
            if (dissonance === 8'hFF) ok("dissonance saturates on the reference fixture");
            else                      bad("dissonance wrong on the reference fixture");
            if (status[3] !== 1'b1) bad("status.saturated must track dissonance == FF");
            else                    ok("status.saturated tracks dissonance");
            if (status[1] !== 1'b1) bad("status.done must mirror done");
            else                    ok("status.done mirrors done");
        end

        // ── G3: results are held stable until the next accepted start ──
        // Read them again well after `done`; nothing may have moved.
        begin : hold_check
            reg signed [15:0] ha, hb, hc, hd;
            ha = a_out; hb = b_out; hc = c_out; hd = d_out;
            repeat (50) @(posedge clk);
            if (a_out === ha && b_out === hb && c_out === hc && d_out === hd)
                ok("G3 results held stable for 50 cycles after done");
            else
                bad("G3 results moved while idle");
            if (done !== 1'b1)
                bad("G3 done must stay asserted until the next accepted start");
            else
                ok("G3 done held until next start");
        end

        // ── G2: inputs are captured at start ─────────────────────────
        // Launch the reference fixture, then corrupt every input one cycle
        // later. A wrapper that did not capture would produce a different
        // result -- this is the check that would fail if the capture
        // registers were removed and the ALU wired straight to the pins,
        // which is what spu4_standalone_top does today.
        poison_results;
        launch(16'sh0000, 16'sh0100, 16'sh0100, 16'sh0100,
               16'sh0050, 16'sh00B5, 16'sh0050);
        // Corrupt everything while the operation is in flight.
        a_in <= 16'sh7FFF; b_in <= 16'sh7FFF; c_in <= 16'sh7FFF; d_in <= 16'sh7FFF;
        coeff_f <= 16'sh7FFF; coeff_g <= 16'sh7FFF; coeff_h <= 16'sh7FFF;
        await_done;
        if (b_out === 16'sh0155 && c_out === 16'sh0155 && d_out === 16'sh0155)
            ok("G2 operands and coefficients captured at start, immune to input churn");
        else
            bad("G2 result corrupted by inputs changing mid-operation");

        // ── G4: start while busy is ignored and reported ─────────────
        poison_results;
        launch(16'sh0000, 16'sh0100, 16'sh0100, 16'sh0100,
               16'sh0050, 16'sh00B5, 16'sh0050);
        @(posedge clk);
        if (!busy) bad("G4 setup: expected busy during an operation");
        // Assert start again mid-flight, with poisoned operands.
        a_in <= 16'sh7FFF; b_in <= 16'sh7FFF; c_in <= 16'sh7FFF; d_in <= 16'sh7FFF;
        @(posedge clk); start <= 1'b1;
        @(posedge clk); start <= 1'b0;
        await_done;
        if (b_out === 16'sh0155 && c_out === 16'sh0155 && d_out === 16'sh0155)
            ok("G4 start during busy did not disturb the operation in flight");
        else
            bad("G4 start during busy corrupted the operation");
        if (status[4] === 1'b1)
            ok("G4 status.start_ignored reports the handshake violation");
        else
            bad("G4 status.start_ignored did not report a start during busy");

        // A clean operation must clear the sticky violation flag.
        run_op(16'sh0000, 16'sh0100, 16'sh0100, 16'sh0100,
               16'sh0050, 16'sh00B5, 16'sh0050);
        if (status[4] === 1'b0)
            ok("G4 status.start_ignored cleared by the next accepted start");
        else
            bad("G4 status.start_ignored is stuck");

        // ── G5: latency is bounded, and the bound is real ────────────
        // Sweep operand and coefficient corners. A data-dependent stall
        // would show up as a spread in worst_latency.
        run_op(16'sh7FFF, 16'sh7FFF, 16'sh7FFF, 16'sh7FFF,
               16'sh7FFF, 16'sh7FFF, 16'sh7FFF);
        run_op(16'sh8000, 16'sh8000, 16'sh8000, 16'sh8000,
               16'sh8000, 16'sh8000, 16'sh8000);
        run_op(16'sh0000, 16'sh0000, 16'sh0000, 16'sh0000,
               16'sh0000, 16'sh0000, 16'sh0000);
        run_op(16'sh0001, 16'shFFFF, 16'sh0001, 16'shFFFF,
               16'sh0001, 16'shFFFF, 16'sh0001);

        // Randomised sweep, to establish the bound rather than trust four
        // corners. A product latency guarantee taken from a handful of
        // hand-picked vectors is not a guarantee.
        begin : latency_sweep
            integer k;
            for (k = 0; k < 120; k = k + 1)
                run_op($random, $random, $random, $random,
                       $random, $random, $random);
        end

        $display("INFO: latency over %0d operations: min=%0d max=%0d clocks",
                 124, best_latency, worst_latency);

        if (worst_latency > 0 && worst_latency <= 200)
            ok("G5 every operation completed within the 200-clock bound");
        else
            bad("G5 latency bound exceeded or measurement failed");

        // Fixed vs bounded is a real distinction for the ABI: a customer
        // scheduling around this core can use a constant only if latency does
        // not depend on operand values. Measured 2026-08-16: it DOES vary,
        // because the multiplier is serial -- so the contract says bounded.
        // This check pins the spread. A change that introduces a large
        // data-dependent stall fails here even while staying under the bound.
        if (worst_latency - best_latency <= 8)
            ok("G5 data-dependent spread within the documented 8 clocks");
        else
            bad("G5 data-dependent latency spread exceeds the documented 8 clocks");

        // ── G6: reset returns the contract to its defined state ──────
        @(posedge clk); rst_n = 0;
        repeat (4) @(posedge clk);
        rst_n = 1;
        @(posedge clk); @(posedge clk);
        check_no_xz("after re-assert of reset");
        if (busy === 1'b0 && done === 1'b0 && status === 8'h00)
            ok("G6 reset clears busy, done and status");
        else
            bad("G6 reset did not return the contract to its defined state");

        // ── Negative control ─────────────────────────────────────────
        // The X/Z detector must be capable of firing, or every G1 PASS above
        // is vacuous. Prove it on a deliberately undriven local wire rather
        // than on the DUT, which would require breaking the DUT.
        begin : negative_control
            if (^{undriven_probe} === 1'bx)
                ok("negative control -- the X/Z detector fires on an undriven wire");
            else
                bad("negative control -- X/Z detector cannot fire, G1 checks are vacuous");
        end

        $display("%0d checks, %0d passed, %0d failed", pass + fail, pass, fail);
        if (fail == 0) $display("PASS");
        else           $display("FAIL");
        $finish;
    end

endmodule
