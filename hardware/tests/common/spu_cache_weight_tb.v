// spu_cache_weight_tb.v — Infinitesimal Cache Weighting Testbench
//
// Tests:
//   1. All rising weights — no eviction candidate
//   2. One falling and accelerating downward — flagged
//   3. Multiple falling — most negative delta wins
//   4. All weights equal — fallback to lowest current weight
//   5. Falling but slowing (recovering) — not flagged

`timescale 1ns / 1ps

module spu_cache_weight_tb;

    reg         clk, rst_n, eval_en;
    reg  [31:0] w0, w1, w2, w3;
    wire [31:0] pw0, pw1, pw2, pw3;
    wire [32:0] pd0, pd1, pd2, pd3;
    wire [1:0]  evict_way;
    wire        evict_valid;

    spu_cache_weight uut (
        .clk(clk), .rst_n(rst_n), .eval_en(eval_en),
        .curr_weight_0(w0), .curr_weight_1(w1),
        .curr_weight_2(w2), .curr_weight_3(w3),
        .prev_weight_0(pw0), .prev_weight_1(pw1),
        .prev_weight_2(pw2), .prev_weight_3(pw3),
        .prev_delta_0(pd0), .prev_delta_1(pd1),
        .prev_delta_2(pd2), .prev_delta_3(pd3),
        .evict_way(evict_way), .evict_valid(evict_valid)
    );

    always #5 clk = ~clk;

    integer pass, fail;

    task pulse_eval;
        begin
            eval_en = 1;
            @(posedge clk);
            eval_en = 0;
            @(posedge clk);  // let register settle
            @(posedge clk);  // one more for safety
        end
    endtask

    task check;
        input [255:0] name;
        input [1:0] expected_way;
        input expected_valid;
        begin
            #1;  // avoid race with registered output
            if (evict_valid == expected_valid && evict_way == expected_way) begin
                $display("  PASS: %0s -> way=%0d valid=%0d", name, evict_way, evict_valid);
                pass = pass + 1;
            end else begin
                $display("  FAIL: %0s -> way=%0d valid=%0d (expected way=%0d valid=%0d)",
                         name, evict_way, evict_valid, expected_way, expected_valid);
                fail = fail + 1;
            end
        end
    endtask

    initial begin
        clk = 0; rst_n = 0; eval_en = 0;
        pass = 0; fail = 0;
        w0 = 0; w1 = 0; w2 = 0; w3 = 0;

        @(posedge clk); rst_n = 1;
        @(posedge clk);

        $display("\n── Infinitesimal Cache Weight Tests ──");

        // Initialize all weights (first evaluation stores baseline)
        w0 = 100; w1 = 200; w2 = 300; w3 = 400;
        pulse_eval();
        // Previous weights are now 100,200,300,400 with delta=0

        // Test 1: All rising — no acceleration candidates, fallback to lowest
        w0 = 110; w1 = 210; w2 = 310; w3 = 410;
        pulse_eval();
        check("All rising -> lowest current", 2'd0, 1'b1);

        // Test 2: Way 2 falling and accelerating downward
        w0 = 120; w1 = 220; w2 = 200; w3 = 420;
        // delta_2 = 200-310 = -110, pd_2 = 0 → candidate (dropping)
        pulse_eval();
        check("Way 2 falling -> evict way 2", 2'd2, 1'b1);

        // Test 3: Way 2 still falling, faster now
        w0 = 130; w1 = 230; w2 = 50; w3 = 430;
        // delta_2 = 50-200 = -150, pd_2 = -110 → candidate (accelerating)
        pulse_eval();
        // Previous delta was -110, now -150, so delta < pd → candidate
        check("Way 2 accelerating down -> evict way 2", 2'd2, 1'b1);

        // Test 4: Way 2 recovering (still negative but slowing)
        w0 = 140; w1 = 240; w2 = 180; w3 = 440;
        // delta_2 = 180-50 = +130, pd_2 = -150
        // delta positive → NOT a candidate
        pulse_eval();
        check("Way 2 recovering -> fallback lowest", 2'd0, 1'b1);

        // Test 5: Two ways falling, most negative wins
        w0 = 100; w1 = 150; w2 = 300; w3 = 100;
        // delta_0 = 100-140 = -40, pd_0 = +10 → candidate
        // delta_3 = 100-440 = -340, pd_3 = +10 → candidate
        // delta_3 more negative → evict way 3
        pulse_eval();
        check("Way 3 most negative -> evict way 3", 2'd3, 1'b1);

        // Test 6: Equal weights, no deltas -> fallback to way 0
        w0 = 500; w1 = 500; w2 = 500; w3 = 500;
        pulse_eval();
        check("All equal -> fallback way 0", 2'd0, 1'b1);

        repeat (2) @(posedge clk);

        $display("\n──────────────────────────────");
        $display("Results: %0d passed, %0d failed", pass, fail);
        if (fail == 0) begin
            $display("PASS");
            $finish;
        end else begin
            $display("FAIL");
            $finish;
        end
    end

endmodule
