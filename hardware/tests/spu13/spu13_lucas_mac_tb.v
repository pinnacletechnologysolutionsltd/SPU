`timescale 1ns / 1ps

// spu13_lucas_mac_tb.v — Zero-Drift Bit-Pattern Test
//
// Proves that phi-multiplication in Z[phi]/L_521 is exact and periodic.
// After 26 PSCALE operations (the phi period mod 521), any seed value
// must return to its exact starting bit-pattern.
//
// This is the phinary analogue of the M31 2^31 ≡ 1 bit-wrap: structural
// exactness from algebraic structure, not numerical approximation.

module spu13_lucas_mac_tb;

    // ── Parameters ────────────────────────────────────────────────────
    localparam L_P      = 521;
    localparam L_P_BITS = 10;
    localparam PERIOD   = 26;     // phi_order(521)
    localparam CLK_HALF = 10;     // 50 MHz

    // ── Signals ───────────────────────────────────────────────────────
    reg         clk = 1'b0;
    reg         rst_n = 1'b0;
    reg         start;
    reg  [2:0]  opcode;
    reg  [9:0]  op_a, op_b, op_c, op_d;
    wire        busy, done, error;
    wire [9:0]  result_a, result_b;

    // ── Test state ────────────────────────────────────────────────────
    reg [9:0]   seed_a, seed_b;       // starting value
    reg [9:0]   current_a, current_b; // running value
    reg [9:0]   next_a, next_b;       // next PSCALE result
    reg [15:0]  step;                 // PSCALE step counter
    reg [31:0]  periods_completed;
    integer     errors;
    reg         test_active;
    reg         phi_order_verified;

    // ── DUT ───────────────────────────────────────────────────────────
    spu13_lucas_mac #(
        .L_P(L_P),
        .L_P_BITS(L_P_BITS)
    ) uut (
        .clk(clk),
        .rst_n(rst_n),
        .start(start),
        .opcode(opcode),
        .op_a(op_a),
        .op_b(op_b),
        .op_c(op_c),
        .op_d(op_d),
        .busy(busy),
        .done(done),
        .result_a(result_a),
        .result_b(result_b),
        .error(error)
    );

    // ── Clock ─────────────────────────────────────────────────────────
    always #CLK_HALF clk = ~clk;

    // ── Test orchestrator ─────────────────────────────────────────────
    initial begin
        $display("=== Lucas MAC Zero-Drift Test ===");
        $display("Modulus: L_13 = %0d", L_P);
        $display("Phi period: %0d", PERIOD);
        $display();

        // Reset
        rst_n = 1'b0;
        start = 1'b0;
        opcode = 3'd0;
        op_a = 0; op_b = 0; op_c = 0; op_d = 0;
        errors = 0;
        test_active = 0;
        phi_order_verified = 0;
        periods_completed = 0;
        step = 0;

        #100 rst_n = 1'b1;
        #50;

        // ─── Phase 1: Sanity checks on PSCALE and PCHIRAL ─────────
        $display("── Phase 1: Opcode sanity ──");

        // PSCALE: φ·(3+5φ) should be (5+8φ)
        run_pscale(10'd3, 10'd5, 10'd5, 10'd8, "PSCALE φ·(3+5φ)");

        // PSCALE: φ·(0+1φ) should be (1+1φ)   [φ² = φ+1]
        run_pscale(10'd0, 10'd1, 10'd1, 10'd1, "PSCALE φ·φ = φ+1");

        // PSCALE: φ·(1+0φ) should be (0+1φ)   [φ·1 = φ]
        run_pscale(10'd1, 10'd0, 10'd0, 10'd1, "PSCALE φ·1 = φ");

        // PCHIRAL: conj(3+5φ) = (8+516φ) mod 521
        run_pchiral(10'd3, 10'd5, 10'd8, (L_P - 5) % L_P, "PCHIRAL conj(3+5φ)");

        // PMUL: (3+5φ)(2+7φ) = (41+66φ)
        run_pmul(10'd3, 10'd5, 10'd2, 10'd7, 10'd41, 10'd66, "PMUL (3+5φ)(2+7φ)");

        // PINV: 1^-1 = 1, and (3+5φ)^-1 = (513+5φ)
        run_pinv(10'd1, 10'd0, 10'd1, 10'd0, "PINV 1^-1");
        run_pinv(10'd3, 10'd5, 10'd513, 10'd5, "PINV (3+5φ)^-1");

        // ─── Phase 2: Phi-order verification ──────────────────────
        $display();
        $display("── Phase 2: Phi-order verification ──");

        // Start from φ^0 = 1, apply PSCALE until φ^PERIOD returns to 1.
        current_a = 1;
        current_b = 0;
        phi_order_verified = 0;

        for (step = 1; step <= PERIOD * 2; step = step + 1) begin
            step_pscale(current_a, current_b, next_a, next_b);
            current_a = next_a;
            current_b = next_b;

            if (current_a == 1 && current_b == 0) begin
                if (!phi_order_verified) begin
                    $display("  phi^%0d ≡ 1 (mod %0d)  ✓", step, L_P);
                    if (step != PERIOD) begin
                        $display("  WARNING: Expected period %0d, got %0d", PERIOD, step);
                        errors = errors + 1;
                    end
                    phi_order_verified = 1;
                end
            end
        end

        if (!phi_order_verified) begin
            $display("  FAIL: phi period not found within %0d steps", PERIOD * 2);
            errors = errors + 1;
        end

        // ─── Phase 3: Zero-Drift Marathon ──────────────────────────
        $display();
        $display("── Phase 3: Zero-Drift Marathon (10,000 PSCALE steps) ──");

        // Seed: (3+5φ)
        seed_a = 3;
        seed_b = 5;
        current_a = seed_a;
        current_b = seed_b;
        periods_completed = 0;

        test_active = 1;
        for (step = 0; step < 10000; step = step + 1) begin
            step_pscale(current_a, current_b, next_a, next_b);
            current_a = next_a;
            current_b = next_b;

            // Check period closure
            if ((step + 1) % PERIOD == 0) begin
                periods_completed = periods_completed + 1;
                if (current_a != seed_a || current_b != seed_b) begin
                    $display("  DRIFT at step %0d (period %0d): got (%0d+%0dphi), expected (%0d+%0dphi)",
                             step + 1, periods_completed,
                             current_a, current_b,
                             seed_a, seed_b);
                    errors = errors + 1;
                end
            end

            // Progress report
            if ((step + 1) % 1000 == 0) begin
                $display("  ... %0d steps, %0d periods, current = (%0d+%0dφ)",
                         step + 1, periods_completed,
                         current_a, current_b);
            end
        end
        test_active = 0;

        // ─── Results ───────────────────────────────────────────────
        $display();
        if (errors == 0) begin
            $display("=== ZERO-DRIFT: PASS ===");
            $display("    %0d periods completed, bit-exact closure every time",
                     periods_completed);
        end else begin
            $display("=== ZERO-DRIFT: FAIL (%0d errors) ===", errors);
        end

        $finish;
    end

    // ── Helper tasks ──────────────────────────────────────────────────

    task run_pscale;
        input [9:0] a_in, b_in;
        input [9:0] exp_a, exp_b;
        input [8*32:0] desc;
        begin
            @(negedge clk);
            start = 1;
            opcode = 3'd0;
            op_a = a_in;
            op_b = b_in;
            @(negedge clk);
            start = 0;
            wait(done);
            @(negedge clk);
            if (result_a == exp_a && result_b == exp_b) begin
                $display("  PASS: %0s → (%0d+%0dφ)", desc, result_a, result_b);
            end else begin
                $display("  FAIL: %0s  exp (%0d+%0dφ)  got (%0d+%0dφ)",
                         desc, exp_a, exp_b, result_a, result_b);
                errors = errors + 1;
            end
        end
    endtask

    task run_pchiral;
        input [9:0] a_in, b_in;
        input [9:0] exp_a, exp_b;
        input [8*32:0] desc;
        begin
            @(negedge clk);
            start = 1;
            opcode = 3'd1;
            op_a = a_in;
            op_b = b_in;
            @(negedge clk);
            start = 0;
            wait(done);
            @(negedge clk);
            if (result_a == exp_a && result_b == exp_b) begin
                $display("  PASS: %0s → (%0d+%0dφ)", desc, result_a, result_b);
            end else begin
                $display("  FAIL: %0s  exp (%0d+%0dφ)  got (%0d+%0dφ)",
                         desc, exp_a, exp_b, result_a, result_b);
                errors = errors + 1;
            end
        end
    endtask

    task run_pmul;
        input [9:0] a_in, b_in, c_in, d_in;
        input [9:0] exp_a, exp_b;
        input [8*40:0] desc;
        begin
            @(negedge clk);
            start = 1;
            opcode = 3'd2;
            op_a = a_in;
            op_b = b_in;
            op_c = c_in;
            op_d = d_in;
            @(negedge clk);
            start = 0;
            wait(done || error);
            @(negedge clk);
            if (!error && result_a == exp_a && result_b == exp_b) begin
                $display("  PASS: %0s → (%0d+%0dφ)", desc, result_a, result_b);
            end else begin
                $display("  FAIL: %0s  exp (%0d+%0dφ)  got (%0d+%0dφ), error=%0d",
                         desc, exp_a, exp_b, result_a, result_b, error);
                errors = errors + 1;
            end
        end
    endtask

    task run_pinv;
        input [9:0] a_in, b_in;
        input [9:0] exp_a, exp_b;
        input [8*40:0] desc;
        begin
            @(negedge clk);
            start = 1;
            opcode = 3'd3;
            op_a = a_in;
            op_b = b_in;
            op_c = 0;
            op_d = 0;
            @(negedge clk);
            start = 0;
            wait(done || error);
            @(negedge clk);
            if (!error && result_a == exp_a && result_b == exp_b) begin
                $display("  PASS: %0s → (%0d+%0dφ)", desc, result_a, result_b);
            end else begin
                $display("  FAIL: %0s  exp (%0d+%0dφ)  got (%0d+%0dφ), error=%0d",
                         desc, exp_a, exp_b, result_a, result_b, error);
                errors = errors + 1;
            end
        end
    endtask

    task step_pscale;
        input  [9:0] a_in, b_in;
        output [9:0] a_out, b_out;
        begin
            @(negedge clk);
            start = 1;
            opcode = 3'd0;
            op_a = a_in;
            op_b = b_in;
            op_c = 0;
            op_d = 0;
            @(negedge clk);
            start = 0;
            wait(done || error);
            a_out = result_a;
            b_out = result_b;
            @(negedge clk);
            if (error) begin
                $display("  FAIL: PSCALE step produced error for (%0d+%0dφ)", a_in, b_in);
                errors = errors + 1;
            end
        end
    endtask

endmodule
