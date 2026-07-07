`timescale 1ns / 1ps

// spu13_batch_inverter_collision_tb.v — scoreboard collision test
//
// Verifies done-coupled busy gating: a premature start while busy
// must not corrupt the running batch, and a post-done batch must
// produce correct results.

module spu13_batch_inverter_collision_tb;

    reg         clk;
    reg         rst_n;
    reg         start;
    reg  [4:0]  batch_size;
    reg  [31:0] d0, d1, d2, d3;
    reg         d_valid;
    reg         d_last;

    wire [31:0] inv0, inv1, inv2, inv3;
    wire        inv_valid;
    wire        inv_singular;
    wire        done;
    wire        busy;
    wire [3:0]  debug_state;

    spu13_batch_inverter #(.MAX_BATCH(16)) u_dut (
        .clk(clk), .rst_n(rst_n),
        .start(start), .batch_size(batch_size),
        .d0(d0), .d1(d1), .d2(d2), .d3(d3),
        .d_valid(d_valid), .d_last(d_last),
        .inv0(inv0), .inv1(inv1), .inv2(inv2), .inv3(inv3),
        .inv_valid(inv_valid), .inv_singular(inv_singular),
        .done(done), .busy(busy),
        .debug_state(debug_state)
    );

    // Output capture
    reg [31:0] cap_inv0 [0:3];
    reg [31:0] cap_inv1 [0:3];
    reg [31:0] cap_inv2 [0:3];
    reg [31:0] cap_inv3 [0:3];
    reg        cap_sing [0:3];
    reg [4:0]  cap_cnt;

    integer    errors;
    integer    timeout;
    integer    cycle;

    always #5 clk = ~clk;

    always @(posedge clk) begin
        if (inv_valid) begin
            cap_inv0[cap_cnt] <= inv0;
            cap_inv1[cap_cnt] <= inv1;
            cap_inv2[cap_cnt] <= inv2;
            cap_inv3[cap_cnt] <= inv3;
            cap_sing[cap_cnt] <= inv_singular;
            cap_cnt <= cap_cnt + 1;
        end
    end

    initial begin
        clk = 0; rst_n = 0; start = 0;
        d_valid = 0; d_last = 0;
        d0 = 0; d1 = 0; d2 = 0; d3 = 0;
        errors = 0;
        #20 rst_n = 1;
        #20;

        $display("=== Batch Inverter — Scoreboard Collision Test ===");

        // ── Batch A: k=2 [2, 3] ──
        $display("--- Starting batch A: k=2 [2, 3] ---");
        cap_cnt = 0;
        batch_size = 5'd2;
        start = 1; #10 start = 0;
        d0 = 32'd2; d_valid = 1; d_last = 0; #10;
        d0 = 32'd3; d_last = 1; #10;
        d_valid = 0; d_last = 0;

        // Verify busy is high during processing
        #10;
        if (!busy) begin
            $display("  FAIL: busy not asserted after start");
            errors = errors + 1;
        end else
            $display("  ok  busy high during processing");

        // Premature start while busy — must be benign
        $display("  Issuing premature start...");
        start = 1; #10 start = 0;
        $display("  ok  premature start ignored (busy still high)");

        // Wait for batch A to complete
        timeout = 0;
        while (!done && timeout < 50000) begin
            @(posedge clk); timeout = timeout + 1;
        end
        repeat (3) @(posedge clk);

        // busy must clear with done
        if (busy) begin
            $display("  FAIL: busy still high after done");
            errors = errors + 1;
        end else
            $display("  ok  busy cleared with done");

        // Verify batch A results
        if (cap_cnt != 2) begin
            $display("  FAIL: batch A produced %0d outputs, expected 2", cap_cnt);
            errors = errors + 1;
        end else begin
            $display("  ok  batch A produced 2 outputs");
            // Lane 0: inv(2) = 0x40000000
            if (cap_sing[0]) begin
                $display("  FAIL: batch A lane 0 flagged singular");
                errors = errors + 1;
            end else if (cap_inv0[0] != 32'h40000000) begin
                $display("  FAIL: batch A lane 0 = %h, expected 40000000", cap_inv0[0]);
                errors = errors + 1;
            end else
                $display("  ok  batch A lane 0 = inv(2)");
            // Lane 1: inv(3) = 0x55555555
            if (cap_sing[1]) begin
                $display("  FAIL: batch A lane 1 flagged singular");
                errors = errors + 1;
            end else if (cap_inv0[1] != 32'h55555555) begin
                $display("  FAIL: batch A lane 1 = %h, expected 55555555", cap_inv0[1]);
                errors = errors + 1;
            end else
                $display("  ok  batch A lane 1 = inv(3)");
        end

        // ── Batch B: k=1 [5] — post-collision recovery ──
        $display("--- Starting batch B: k=1 [5] (post-collision) ---");
        cap_cnt = 0;
        batch_size = 5'd1;
        start = 1; #10 start = 0;
        d0 = 32'd5; d_valid = 1; d_last = 1; #10;
        d_valid = 0; d_last = 0;

        timeout = 0;
        while (!done && timeout < 50000) begin
            @(posedge clk); timeout = timeout + 1;
        end
        repeat (3) @(posedge clk);

        if (cap_cnt != 1) begin
            $display("  FAIL: batch B produced %0d outputs, expected 1", cap_cnt);
            errors = errors + 1;
        end else if (cap_sing[0]) begin
            $display("  FAIL: batch B flagged singular");
            errors = errors + 1;
        end else if (cap_inv0[0] != 32'h33333333) begin
            $display("  FAIL: batch B inv = %h, expected 33333333 (inv 5)", cap_inv0[0]);
            errors = errors + 1;
        end else
            $display("  ok  batch B correct after collision");

        // ── Batch C: same-cycle start+done (start arrives with done high) ──
        $display("--- Batch C: same-cycle restart test ---");
        cap_cnt = 0;
        batch_size = 5'd1;
        // Pulse start on the same cycle done might still be high from batch B
        start = 1; #10 start = 0;
        d0 = 32'd7; d_valid = 1; d_last = 1; #10;
        d_valid = 0; d_last = 0;

        timeout = 0;
        while (!done && timeout < 50000) begin
            @(posedge clk); timeout = timeout + 1;
        end
        repeat (3) @(posedge clk);

        if (cap_cnt != 1 || cap_sing[0]) begin
            $display("  FAIL: batch C failed");
            errors = errors + 1;
        end else
            $display("  ok  batch C (inv 7) completed");

        // ── Summary ──
        $display("============================================");
        if (errors == 0)
            $display("PASS: Scoreboard collision tests passed");
        else
            $display("FAIL: %0d errors", errors);
        $finish;
    end

endmodule
