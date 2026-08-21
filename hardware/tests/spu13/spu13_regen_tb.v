// spu13_regen_tb.v — Stage A REGEN module testbench
// (contract_regen_stageA_2026-08-20.md §4.1 vectors)
//
// Drives the module directly: eligible_op pulses stand in for executed
// E_REGEN instructions; start/declared_k stand in for a dispatched REGEN.
`timescale 1ns/1ps

module spu13_regen_tb;
    reg clk = 0;
    reg rst_n = 0;
    always #5 clk = ~clk;

    reg        start = 0;
    reg [15:0] declared_k = 0;
    reg        eligible_op = 0;
    reg        bk_valid = 1;

    // Stage B measurement interface
    reg [41:0] bk_qr0_ma, bk_qr0_mb, bk_qr0_mc, bk_qr0_md;
    reg [41:0] bk_qr1_ma, bk_qr1_mb, bk_qr1_mc, bk_qr1_md;
    reg [9:0]  bk_sigma_exp0 = 0;
    reg [9:0]  bk_sigma_exp1 = 0;
    reg [15:0] bk_angle_k = 0;

    wire       done;
    wire       regen_prec_fault;
    wire [15:0] block_op_count;
    wire [15:0] regen_debug_status;
    wire [31:0] rec_qr0_a, rec_qr0_b, rec_qr0_c, rec_qr0_d;
    wire [31:0] rec_qr1_a, rec_qr1_b, rec_qr1_c, rec_qr1_d;
    wire       commit_valid;

    integer errors = 0;
    integer tick = 0;

    spu13_regen uut (
        .clk(clk), .rst_n(rst_n),
        .start(start), .declared_k(declared_k),
        .eligible_op(eligible_op), .bk_valid(bk_valid),
        .bk_qr0_meas_a(bk_qr0_ma), .bk_qr0_meas_b(bk_qr0_mb),
        .bk_qr0_meas_c(bk_qr0_mc), .bk_qr0_meas_d(bk_qr0_md),
        .bk_qr1_meas_a(bk_qr1_ma), .bk_qr1_meas_b(bk_qr1_mb),
        .bk_qr1_meas_c(bk_qr1_mc), .bk_qr1_meas_d(bk_qr1_md),
        .bk_sigma_exp0(bk_sigma_exp0), .bk_sigma_exp1(bk_sigma_exp1),
        .bk_angle_k(bk_angle_k),
        .rec_qr0_a(rec_qr0_a), .rec_qr0_b(rec_qr0_b),
        .rec_qr0_c(rec_qr0_c), .rec_qr0_d(rec_qr0_d),
        .rec_qr1_a(rec_qr1_a), .rec_qr1_b(rec_qr1_b),
        .rec_qr1_c(rec_qr1_c), .rec_qr1_d(rec_qr1_d),
        .commit_valid(commit_valid),
        .done(done), .regen_prec_fault(regen_prec_fault),
        .block_op_count(block_op_count),
        .regen_debug_status(regen_debug_status)
    );

    task pulse_eligible;
        begin
            eligible_op = 1;
            @(posedge clk);
            eligible_op = 0;
            @(posedge clk);
        end
    endtask

    task fire_regen;
        input [15:0] k;
        input        bkv;
        begin
            declared_k = k;
            bk_valid   = bkv;
            start = 1;
            @(posedge clk);
            start = 0;
            @(posedge clk);   // S_DONE: done pulse + fault result visible
            if (done !== 1'b1) begin
                $display("FAIL: REGEN K=%0d did not complete", k);
                errors = errors + 1;
            end
            @(posedge clk);
        end
    endtask

    task check;
        input [255:0] label;
        input cond;
        begin
            if (!cond) begin
                $display("FAIL: %0s", label);
                errors = errors + 1;
            end else begin
                $display("PASS: %0s", label);
            end
        end
    endtask

    initial begin
        $dumpfile("spu13_regen_tb.vcd");
        $dumpvars(0, uut);
        repeat (4) @(posedge clk);
        rst_n = 1;
        repeat (2) @(posedge clk);

        // Vector 1: two eligible ops, REGEN K=2 -> clean pass, counter cleared
        pulse_eligible; pulse_eligible;
        fire_regen(16'd2, 1'b1);
        check("V1: REGEN K=2 after 2 eligible ops -> no fault", regen_prec_fault === 1'b0);
        check("V1: counter cleared", block_op_count === 16'd0);

        // Vector 2: one eligible op, REGEN K=2 -> REGEN_PREC fault, counter kept
        pulse_eligible;
        fire_regen(16'd2, 1'b1);
        check("V2: REGEN K=2 after 1 eligible op -> REGEN_PREC fault",
              regen_prec_fault === 1'b1);
        check("V2: counter NOT cleared (debug visibility)", block_op_count === 16'd1);
        // fault kept the count; clear it with a matching REGEN before V3
        fire_regen(16'd1, 1'b1);
        check("V2-clear: REGEN K=1 clears the faulted counter",
              regen_prec_fault === 1'b0 && block_op_count === 16'd0);

        // Vector 3: REGEN K=0 on empty block -> idempotence REGEN(REGEN(S))=S
        fire_regen(16'd0, 1'b1);
        check("V3: REGEN K=0 on exact state -> no fault (idempotence)",
              regen_prec_fault === 1'b0);
        check("V3: counter cleared", block_op_count === 16'd0);

        // Vector 4: three eligible ops, REGEN K=2 -> too-long fault
        pulse_eligible; pulse_eligible; pulse_eligible;
        fire_regen(16'd2, 1'b1);
        check("V4: REGEN K=2 after 3 eligible ops -> REGEN_PREC fault",
              regen_prec_fault === 1'b1);
        check("V4: counter kept at 3", block_op_count === 16'd3);
        fire_regen(16'd3, 1'b1);
        check("V4-clear: REGEN K=3 clears", regen_prec_fault === 1'b0);

        // Vector 5: eligible; REGEN K=1; REGEN K=0 -> first clears, second clean
        pulse_eligible;
        fire_regen(16'd1, 1'b1);
        check("V5a: REGEN K=1 after 1 eligible op -> no fault",
              regen_prec_fault === 1'b0);
        fire_regen(16'd0, 1'b1);
        check("V5b: subsequent REGEN K=0 -> clean pass-through",
              regen_prec_fault === 1'b0);

        // Vector 6: bk_valid deasserted (simulated out-of-envelope) -> fault
        fire_regen(16'd0, 1'b0);
        check("V6: bk_valid=0 (out-of-envelope) -> REGEN_PREC fault",
              regen_prec_fault === 1'b1);

        // ── Stage B: measurement interface + BQE + compensation ──
        // (each vector primes the counter with one eligible op so the
        //  K>0 valid path — the BQE — is exercised; K=0 is a pass-through)
        // V7: BQE at m=0 recovers v=7 from meas = 7*2^38 (Q2.40)
        bk_qr0_ma = 42'sd1924145348608;  // 7 * 2^38
        bk_qr0_mb = 42'sd0; bk_qr0_mc = 42'sd0; bk_qr0_md = 42'sd0;
        bk_qr1_ma = 42'sd0; bk_qr1_mb = 42'sd0;
        bk_qr1_mc = 42'sd0; bk_qr1_md = 42'sd0;
        bk_sigma_exp0 = 10'd0; bk_angle_k = 16'd0;
        pulse_eligible;
        fire_regen(16'd1, 1'b1);
        check("V7: BQE m=0 recovers v=7", rec_qr0_a === 32'sd7);

        // V8: BQE at m=3 recovers v=7 from meas = 7*2^35
        bk_qr0_ma = 42'sd240518168576;   // 7 * 2^35
        bk_sigma_exp0 = 10'd3;
        pulse_eligible;
        fire_regen(16'd1, 1'b1);
        check("V8: BQE m=3 recovers v=7", rec_qr0_a === 32'sd7);

        // V9: compensation — attenuated meas (cos(1000*2^-16)) + trim restores 7
        bk_qr0_ma = 42'sd1923921352954;  // 7*2^38*cos(theta), theta=1000*2^-16
        bk_sigma_exp0 = 10'd0; bk_angle_k = 16'd1000;
        pulse_eligible;
        fire_regen(16'd1, 1'b1);
        check("V9: trim restores v=7 from cos-attenuated measurement",
              rec_qr0_a === 32'sd7);

        if (errors == 0)
            $display("spu13_regen_tb: PASS");
        else
            $display("spu13_regen_tb: FAIL (%0d errors)", errors);
        $finish;
    end
endmodule
