// spu13_scoreboard_v2_tb.v — self-checking testbench for the done-coupled
// scoreboard. Covers the five hazard edge cases that gate any concurrency
// claim in the papers:
//   1. Independent issue during a tower run (no stall)
//   2. Dependent stall on rs1 / rs2 / rd of the pending tower destination
//   3. Release on tower_done, immediate reuse next cycle
//   4. Zero-norm early abort (FLAGS.V path) releases without writeback
//   5. Structural stall: second tower op mid-run; same-cycle done+reissue
//      collision stalls that cycle and is accepted the next
`timescale 1ns/1ps

module spu13_scoreboard_v2_tb;

    reg         clk = 0;
    reg         rst = 1;
    reg         issue_valid = 0;
    reg  [4:0]  issue_rs1 = 0, issue_rs2 = 0, issue_rd = 0;
    reg         issue_uses_rs1 = 0, issue_uses_rs2 = 0;
    reg         issue_is_tower = 0;
    reg         tower_done = 0, tower_abort = 0;
    wire        hazard_stall, tower_busy;

    integer errors = 0;
    integer checks = 0;

    spu13_scoreboard_v2 #(.REG_COUNT(32), .REG_BITS(5)) dut (
        .clk(clk), .rst(rst),
        .issue_valid(issue_valid),
        .issue_rs1(issue_rs1), .issue_rs2(issue_rs2), .issue_rd(issue_rd),
        .issue_uses_rs1(issue_uses_rs1), .issue_uses_rs2(issue_uses_rs2),
        .issue_is_tower(issue_is_tower),
        .tower_done(tower_done), .tower_abort(tower_abort),
        .hazard_stall(hazard_stall), .tower_busy(tower_busy)
    );

    always #5 clk = ~clk;

    task check(input cond, input [255:0] name);
        begin
            checks = checks + 1;
            if (!cond) begin
                $display("FAIL: %0s", name);
                errors = errors + 1;
            end else begin
                $display("  ok: %0s", name);
            end
        end
    endtask

    // Drive an issue request combinationally, sample stall, optionally hold
    task attempt(input tower, input [4:0] rd, input use1, input [4:0] rs1,
                 input use2, input [4:0] rs2);
        begin
            issue_valid    = 1;
            issue_is_tower = tower;
            issue_rd       = rd;
            issue_uses_rs1 = use1; issue_rs1 = rs1;
            issue_uses_rs2 = use2; issue_rs2 = rs2;
            #1; // settle combinational stall
        end
    endtask

    task idle;
        begin
            issue_valid = 0; issue_is_tower = 0;
            issue_uses_rs1 = 0; issue_uses_rs2 = 0;
        end
    endtask

    initial begin
        repeat (2) @(posedge clk);
        rst = 0;
        @(posedge clk);

        // ── Case 1+2 setup: accept a tower op writing R3 ──────────────
        attempt(1, 5'd3, 1, 5'd1, 1, 5'd2);
        check(!hazard_stall, "tower to R3 accepted when idle");
        @(posedge clk); idle; #1;
        check(tower_busy, "tower_busy high after accept");

        // ── Case 1: independent single-cycle op mid-run: no stall ─────
        attempt(0, 5'd0, 1, 5'd1, 1, 5'd2);   // R0 = R1 op R2
        check(!hazard_stall, "independent MAC issues during tower run");
        idle; #1;

        // ── Case 2: dependent ops on R3 stall (rs1, rs2, rd) ──────────
        attempt(0, 5'd4, 1, 5'd3, 0, 5'd0);
        check(hazard_stall, "read of pending R3 via rs1 stalls");
        attempt(0, 5'd4, 0, 5'd0, 1, 5'd3);
        check(hazard_stall, "read of pending R3 via rs2 stalls");
        attempt(0, 5'd3, 1, 5'd1, 0, 5'd0);
        check(hazard_stall, "write to pending R3 (WAW) stalls");
        idle; #1;

        // ── Case 5a: structural — second tower op, different regs ─────
        attempt(1, 5'd7, 1, 5'd8, 1, 5'd9);
        check(hazard_stall, "second tower op stalls mid-run (structural)");
        idle; #1;

        // ── Case 3: done releases R3; reuse next cycle ────────────────
        tower_done = 1;
        @(posedge clk);
        tower_done = 0; #1;
        check(!tower_busy, "tower_busy clears after done");
        attempt(0, 5'd4, 1, 5'd3, 0, 5'd0);
        check(!hazard_stall, "R3 readable after done");
        idle; #1;

        // ── Case 4: zero-norm abort releases without writeback ────────
        attempt(1, 5'd5, 1, 5'd1, 0, 5'd0);
        check(!hazard_stall, "tower to R5 accepted");
        @(posedge clk); idle; #1;
        tower_abort = 1;
        @(posedge clk);
        tower_abort = 0; #1;
        check(!tower_busy, "tower_busy clears on zero-norm abort");
        attempt(0, 5'd6, 1, 5'd5, 0, 5'd0);
        check(!hazard_stall, "R5 released after abort (no writeback)");
        idle; #1;

        // ── Case 5b: same-cycle done + reissue collision ──────────────
        attempt(1, 5'd10, 1, 5'd1, 0, 5'd0);
        check(!hazard_stall, "tower to R10 accepted");
        @(posedge clk); idle; #1;
        // done pulses in the same cycle a new tower op to R10 is attempted
        tower_done = 1;
        attempt(1, 5'd10, 1, 5'd1, 0, 5'd0);
        check(hazard_stall, "same-cycle done+reissue stalls (set-over-clear)");
        @(posedge clk);
        tower_done = 0; #1;
        // next cycle: released, reissue accepted, busy window restarts
        check(!hazard_stall, "reissue accepted the cycle after done");
        @(posedge clk); idle; #1;
        check(tower_busy, "new busy window active after reissue");
        attempt(0, 5'd11, 1, 5'd10, 0, 5'd0);
        check(hazard_stall, "R10 busy again in the new window");
        idle; #1;

        if (errors == 0)
            $display("PASS: spu13_scoreboard_v2_tb — all %0d checks", checks);
        else
            $display("FAIL: spu13_scoreboard_v2_tb — %0d errors", errors);
        $finish;
    end

    initial begin
        #10000;
        $display("FAIL: timeout");
        $finish;
    end

endmodule
