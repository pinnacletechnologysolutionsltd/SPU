// spu_rotor_vault_tb.v — Pell Octave vault testbench
// Verifies:
//  1. Initial state: all axes at step=0, orbit=(1,0), octave=0
//  2. 8 ROT steps on axis 0 → orbit cycles through full Pell sequence
//  3. Step 8 on axis 0 → step wraps to 0, octave becomes 1, rotor_out=(1,0)
//  4. Step 9 (first of octave 1) → rotor_out=(2,1), octave=1
//  5. Axis 1 untouched → still at step=0, octave=0
//  6. 16 ROTs on axis 5 → octave=2, step=0, rotor_out=(1,0)
//  All Pell norm invariants checked: P²-3Q²=1 at every step

`timescale 1ns/1ps
`include "spu_rotor_vault.v"

module spu_rotor_vault_tb;

    reg        clk, reset;
    reg [3:0]  axis_id;
    reg        rot_en;
    wire [31:0] rotor_out;
    wire [7:0]  octave_out;
    wire [2:0]  step_out;

    integer fail = 0;
    integer k;

    spu_rotor_vault uut (
        .clk(clk), .reset(reset),
        .axis_id(axis_id), .rot_en(rot_en),
        .rotor_out(rotor_out), .octave_out(octave_out), .step_out(step_out)
    );

    always #5 clk = ~clk;

    // Check P²-3Q²=1 for rotor_out
    task check_norm;
        input [47:0] label;
        begin
            #1;
            begin : norm_check
                integer P, Q, norm;
                P = rotor_out[31:16];
                Q = rotor_out[15:0];
                norm = P*P - 3*Q*Q;
                if (norm !== 1) begin
                    $display("FAIL norm (%0s): P=%0d Q=%0d P²-3Q²=%0d (should be 1)",
                             label, P, Q, norm);
                    fail = fail + 1;
                end
            end
        end
    endtask

    task rot_axis;
        input [3:0] ax;
        begin
            @(negedge clk);
            axis_id = ax; rot_en = 1;
            @(posedge clk); #1;
            rot_en = 0;
        end
    endtask

    task read_axis;
        input [3:0] ax;
        begin
            @(negedge clk);
            axis_id = ax; rot_en = 0;
            @(posedge clk); #1;
        end
    endtask

    // Expected Pell orbit values {P, Q}
    reg [15:0] pell_P [0:7];
    reg [15:0] pell_Q [0:7];
    initial begin
        pell_P[0]=1;    pell_Q[0]=0;
        pell_P[1]=2;    pell_Q[1]=1;
        pell_P[2]=7;    pell_Q[2]=4;
        pell_P[3]=26;   pell_Q[3]=15;
        pell_P[4]=97;   pell_Q[4]=56;
        pell_P[5]=362;  pell_Q[5]=209;
        pell_P[6]=1351; pell_Q[6]=780;
        pell_P[7]=5042; pell_Q[7]=2911;
    end

    initial begin
        clk = 0; reset = 1; rot_en = 0; axis_id = 0;
        #12; reset = 0;

        // ── Case 1: Initial state — axis 0, step=0, orbit=(1,0), oct=0 ──
        read_axis(0);
        if (rotor_out !== 32'h00010000 || octave_out !== 0 || step_out !== 0) begin
            $display("FAIL init: rotor=%08h oct=%0d step=%0d",
                     rotor_out, octave_out, step_out);
            fail = fail + 1;
        end

        // ── Case 2: 7 ROT steps on axis 0 → walk full octave ────────────
        for (k = 1; k <= 7; k = k + 1) begin
            rot_axis(0);
            if (rotor_out[31:16] !== pell_P[k] || rotor_out[15:0] !== pell_Q[k]) begin
                $display("FAIL step %0d: got P=%0d Q=%0d, expected P=%0d Q=%0d",
                         k, rotor_out[31:16], rotor_out[15:0], pell_P[k], pell_Q[k]);
                fail = fail + 1;
            end
            check_norm("step");
            if (octave_out !== 0) begin
                $display("FAIL step %0d: octave should be 0, got %0d", k, octave_out);
                fail = fail + 1;
            end
        end

        // ── Case 3: Step 8 — octave boundary ─────────────────────────────
        rot_axis(0); // now at step=0, octave=1
        if (rotor_out !== 32'h00010000) begin
            $display("FAIL octave wrap: rotor should be (1,0), got %08h", rotor_out);
            fail = fail + 1;
        end
        if (octave_out !== 1) begin
            $display("FAIL octave wrap: octave should be 1, got %0d", octave_out);
            fail = fail + 1;
        end
        if (step_out !== 0) begin
            $display("FAIL octave wrap: step should be 0, got %0d", step_out);
            fail = fail + 1;
        end
        check_norm("oct_wrap");

        // ── Case 4: Step 9 — first step of octave 1 ──────────────────────
        rot_axis(0); // step=1, octave=1
        if (rotor_out[31:16] !== 2 || rotor_out[15:0] !== 1) begin
            $display("FAIL step9: got P=%0d Q=%0d, expected (2,1)",
                     rotor_out[31:16], rotor_out[15:0]);
            fail = fail + 1;
        end
        if (octave_out !== 1 || step_out !== 1) begin
            $display("FAIL step9: oct=%0d step=%0d, expected oct=1 step=1",
                     octave_out, step_out);
            fail = fail + 1;
        end
        check_norm("step9");

        // ── Case 5: Axis 1 untouched → still at (1,0), oct=0, step=0 ────
        read_axis(1);
        if (rotor_out !== 32'h00010000 || octave_out !== 0 || step_out !== 0) begin
            $display("FAIL axis1_untouched: rotor=%08h oct=%0d step=%0d",
                     rotor_out, octave_out, step_out);
            fail = fail + 1;
        end

        // ── Case 6: 16 ROTs on axis 5 → octave=2, step=0, rotor=(1,0) ───
        for (k = 0; k < 16; k = k + 1) rot_axis(5);
        if (octave_out !== 2 || step_out !== 0) begin
            $display("FAIL axis5_16rot: oct=%0d step=%0d, expected oct=2 step=0",
                     octave_out, step_out);
            fail = fail + 1;
        end
        if (rotor_out !== 32'h00010000) begin
            $display("FAIL axis5_16rot: rotor=%08h, expected 00010000", rotor_out);
            fail = fail + 1;
        end
        check_norm("axis5_16rot");

        // ── Summary ──────────────────────────────────────────────────────
        if (fail == 0)
            $display("PASS");
        else
            $display("FAIL: %0d error(s)", fail);
        $finish;
    end

endmodule
