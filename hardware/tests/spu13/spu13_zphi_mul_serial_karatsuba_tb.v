`timescale 1ns/1ps

// Phase-1 transaction-contract regression for the three-product candidate.
//
// The default 72x34 instance and the production 39x39 equilibrium shape run
// the same acceptance, mutation, busy-collision, done-pulse, reset/recovery,
// directed-extrema, and deterministic-random checks.  Full-width exhaustive
// formal multiplication is intentionally not attempted here; the companion
// reduced-width formal harness proves the complete bit-vector domain.
module zphi_karatsuba_shape_checker #(
    parameter X_W = 72,
    parameter Y_W = 34,
    parameter OUT_W = X_W + Y_W + 2,
    parameter USE_MODULE_DEFAULTS = 0,
    parameter SHAPE_ID = 0
) (
    input  wire        clk,
    output reg         finished,
    output reg  [31:0] error_count
);
    localparam PRODUCT_W = X_W + Y_W;
    localparam signed [X_W-1:0] X_MAX = {1'b0, {(X_W-1){1'b1}}};
    localparam signed [X_W-1:0] X_MIN = {1'b1, {(X_W-1){1'b0}}};
    localparam signed [Y_W-1:0] Y_MAX = {1'b0, {(Y_W-1){1'b1}}};
    localparam signed [Y_W-1:0] Y_MIN = {1'b1, {(Y_W-1){1'b0}}};

    reg rst_n;
    reg start;
    reg signed [X_W-1:0] xa, xb;
    reg signed [Y_W-1:0] ya, yb;
    wire ref_busy, ref_done;
    wire fast_busy, fast_done;
    wire signed [OUT_W-1:0] ref_a, ref_b, fast_a, fast_b;

    integer seed;
    integer transaction_count;

    generate
        if (USE_MODULE_DEFAULTS) begin : gen_default_shape
            // This branch deliberately omits parameter overrides.  Its local
            // wires are 72x34/108, so elaboration also checks the RTL defaults.
            spu13_zphi_mul_serial u_ref (
                .clk(clk), .rst_n(rst_n), .start(start),
                .xa(xa), .xb(xb), .ya(ya), .yb(yb),
                .busy(ref_busy), .done(ref_done),
                .out_a(ref_a), .out_b(ref_b)
            );

            spu13_zphi_mul_serial_karatsuba u_fast (
                .clk(clk), .rst_n(rst_n), .start(start),
                .xa(xa), .xb(xb), .ya(ya), .yb(yb),
                .busy(fast_busy), .done(fast_done),
                .out_a(fast_a), .out_b(fast_b)
            );
        end else begin : gen_explicit_shape
            spu13_zphi_mul_serial #(
                .X_W(X_W), .Y_W(Y_W), .OUT_W(OUT_W)
            ) u_ref (
                .clk(clk), .rst_n(rst_n), .start(start),
                .xa(xa), .xb(xb), .ya(ya), .yb(yb),
                .busy(ref_busy), .done(ref_done),
                .out_a(ref_a), .out_b(ref_b)
            );

            spu13_zphi_mul_serial_karatsuba #(
                .X_W(X_W), .Y_W(Y_W), .OUT_W(OUT_W)
            ) u_fast (
                .clk(clk), .rst_n(rst_n), .start(start),
                .xa(xa), .xb(xb), .ya(ya), .yb(yb),
                .busy(fast_busy), .done(fast_done),
                .out_a(fast_a), .out_b(fast_b)
            );
        end
    endgenerate

    function signed [OUT_W-1:0] mul_ext;
        input signed [X_W-1:0] fx;
        input signed [Y_W-1:0] fy;
        reg signed [PRODUCT_W-1:0] raw;
        begin
            raw = fx * fy;
            mul_ext = {{(OUT_W-PRODUCT_W){raw[PRODUCT_W-1]}}, raw};
        end
    endfunction

    task fail;
        input [8*96-1:0] message;
        begin
            error_count = error_count + 1;
            $display("FAIL shape=%0d %0s", SHAPE_ID, message);
        end
    endtask

    task run_transaction;
        input signed [X_W-1:0] in_xa, in_xb;
        input signed [Y_W-1:0] in_ya, in_yb;
        input collide_and_mutate;
        input [8*48-1:0] label;
        integer cycles;
        reg saw_fast;
        reg signed [OUT_W-1:0] expected_a, expected_b;
        reg signed [OUT_W-1:0] saved_fast_a, saved_fast_b;
        reg signed [OUT_W-1:0] saved_ref_a, saved_ref_b;
        begin
            expected_a = mul_ext(in_xa, in_ya) + mul_ext(in_xb, in_yb);
            expected_b = mul_ext(in_xa, in_yb) + mul_ext(in_xb, in_ya)
                       + mul_ext(in_xb, in_yb);

            xa = in_xa;
            xb = in_xb;
            ya = in_ya;
            yb = in_yb;
            start = 1'b1;
            @(posedge clk); #1;
            transaction_count = transaction_count + 1;

            if (!ref_busy || !fast_busy || ref_done || fast_done)
                fail({label, ": idle start was not accepted cleanly"});

            // Change every external operand immediately after acceptance.  A
            // one-cycle start pulse on the first busy edge must be ignored.
            if (collide_and_mutate) begin
                xa = ~in_xa;
                xb = in_xa ^ in_xb;
                ya = ~in_ya;
                yb = in_ya ^ in_yb;
                start = 1'b1;
            end else begin
                start = 1'b0;
            end

            cycles = 0;
            saw_fast = 0;
            while (!ref_done && cycles < 8) begin
                @(posedge clk); #1;
                cycles = cycles + 1;

                if (cycles < 3 && (!fast_busy || fast_done))
                    fail({label, ": candidate busy dropped before evaluation"});
                if (cycles < 4 && (!ref_busy || ref_done))
                    fail({label, ": reference busy dropped before evaluation"});

                if (fast_done) begin
                    saw_fast = 1;
                    saved_fast_a = fast_a;
                    saved_fast_b = fast_b;
                    if (cycles != 3 || fast_busy)
                        fail({label, ": candidate latency/busy contract"});
                    if (fast_a !== expected_a || fast_b !== expected_b)
                        fail({label, ": candidate ignored captured operands"});
                end

                if (cycles == 1)
                    start = 1'b0;

                if (collide_and_mutate) begin
                    xa = {$random(seed), $random(seed), $random(seed)};
                    xb = {$random(seed), $random(seed), $random(seed)};
                    ya = {$random(seed), $random(seed), $random(seed)};
                    yb = {$random(seed), $random(seed), $random(seed)};
                end
            end

            if (!ref_done || ref_busy || cycles != 4)
                fail({label, ": reference latency/busy contract"});
            if (!saw_fast)
                fail({label, ": candidate done pulse missing"});
            if (ref_a !== expected_a || ref_b !== expected_b)
                fail({label, ": reference ignored captured operands"});
            if (saved_fast_a !== ref_a || saved_fast_b !== ref_b)
                fail({label, ": candidate/reference result mismatch"});

            saved_ref_a = ref_a;
            saved_ref_b = ref_b;
            @(posedge clk); #1;
            if (ref_done || fast_done || ref_busy || fast_busy)
                fail({label, ": done was not one cycle or idle not restored"});
            if (fast_a !== saved_fast_a || fast_b !== saved_fast_b ||
                ref_a !== saved_ref_a || ref_b !== saved_ref_b)
                fail({label, ": registered outputs were not stable after done"});
        end
    endtask

    task reset_in_flight_and_recover;
        begin
            xa = 17;
            xb = -9;
            ya = 11;
            yb = -3;
            start = 1'b1;
            @(posedge clk); #1;
            start = 1'b0;
            xa = X_MAX;
            xb = X_MIN;
            ya = Y_MIN;
            yb = Y_MAX;

            @(posedge clk); #1;
            if (!ref_busy || !fast_busy)
                fail("reset setup did not enter busy state");

            rst_n = 1'b0;
            @(posedge clk); #1;
            if (ref_busy || fast_busy || ref_done || fast_done)
                fail("in-flight reset did not clear handshake state");
            if (ref_a !== 0 || ref_b !== 0 || fast_a !== 0 || fast_b !== 0)
                fail("in-flight reset did not clear registered outputs");

            rst_n = 1'b1;
            repeat (5) begin
                @(posedge clk); #1;
                if (ref_busy || fast_busy || ref_done || fast_done)
                    fail("aborted transaction produced late activity");
            end

            run_transaction(-21, 8, 7, -4, 1'b1,
                            "post-reset independent recovery");
        end
    endtask

    integer i;
    initial begin
        rst_n = 0;
        start = 0;
        xa = 0;
        xb = 0;
        ya = 0;
        yb = 0;
        finished = 0;
        error_count = 0;
        transaction_count = 0;
        seed = 32'h13579bdf ^ SHAPE_ID;

        repeat (3) @(posedge clk);
        rst_n = 1;

        run_transaction(2, 3, 5, 7, 1'b0,
                        "first accepted transaction");
        run_transaction(-2, 3, 5, -7, 1'b1,
                        "busy collision and operand mutation");
        run_transaction(100000, -200000, -30000, 40000, 1'b1,
                        "second independent wide transaction");

        run_transaction(X_MAX, X_MAX, Y_MAX, Y_MAX, 1'b1,
                        "all positive maxima");
        run_transaction(X_MIN, X_MIN, Y_MIN, Y_MIN, 1'b1,
                        "all negative minima");
        run_transaction(X_MAX, X_MIN, Y_MIN, Y_MAX, 1'b1,
                        "cancelling extrema");
        run_transaction(X_MIN, X_MAX, Y_MAX, Y_MIN, 1'b1,
                        "opposed extrema");

        for (i = 0; i < 64; i = i + 1) begin
            run_transaction({$random(seed), $random(seed), $random(seed)},
                            {$random(seed), $random(seed), $random(seed)},
                            {$random(seed), $random(seed), $random(seed)},
                            {$random(seed), $random(seed), $random(seed)},
                            1'b1, "deterministic random equivalence");
        end

        reset_in_flight_and_recover();

        if (error_count == 0)
            $display("ZPHI_KARATSUBA_PHASE1_SHAPE: PASS shape=%0d X_W=%0d Y_W=%0d transactions=%0d candidate_cycles=3 reference_cycles=4",
                     SHAPE_ID, X_W, Y_W, transaction_count);
        else
            $display("ZPHI_KARATSUBA_PHASE1_SHAPE: FAIL shape=%0d errors=%0d",
                     SHAPE_ID, error_count);
        finished = 1'b1;
    end
endmodule

module spu13_zphi_mul_serial_karatsuba_tb;
    reg clk = 0;
    always #5 clk = ~clk;

    wire default_finished, equilibrium_finished;
    wire [31:0] default_errors, equilibrium_errors;

    zphi_karatsuba_shape_checker #(
        .X_W(72), .Y_W(34), .OUT_W(108),
        .USE_MODULE_DEFAULTS(1), .SHAPE_ID(72)
    ) u_default_72x34 (
        .clk(clk), .finished(default_finished), .error_count(default_errors)
    );

    zphi_karatsuba_shape_checker #(
        .X_W(39), .Y_W(39), .OUT_W(80),
        .USE_MODULE_DEFAULTS(0), .SHAPE_ID(39)
    ) u_equilibrium_39x39 (
        .clk(clk), .finished(equilibrium_finished),
        .error_count(equilibrium_errors)
    );

    initial begin
        wait (default_finished && equilibrium_finished);
        #1;
        if (default_errors == 0 && equilibrium_errors == 0)
            $display("SPU13_ZPHI_MUL_SERIAL_KARATSUBA_TB: PASS phase=1 shapes=default_72x34,explicit_39x39");
        else
            $display("SPU13_ZPHI_MUL_SERIAL_KARATSUBA_TB: FAIL default_errors=%0d equilibrium_errors=%0d",
                     default_errors, equilibrium_errors);
        $finish(default_errors != 0 || equilibrium_errors != 0);
    end
endmodule
