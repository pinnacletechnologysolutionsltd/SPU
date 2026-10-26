`timescale 1ns / 1ps

// spu13_neuro_sidecar_adapter_tb.v — Testbench for SPI-visible adapter.

module spu13_neuro_sidecar_adapter_tb;
    reg clk = 1'b0;
    reg rst_n = 1'b0;
    reg inst_valid = 1'b0;
    reg [63:0] inst_word = 64'd0;

    wire inst_claimed;
    wire busy;
    wire error;
    wire qr_commit_valid;
    wire [3:0] qr_commit_lane;
    wire [63:0] qr_commit_A;
    wire [63:0] qr_commit_B;
    wire [63:0] qr_commit_C;
    wire [63:0] qr_commit_D;

    wire epoch_busy;
    wire epoch_done;
    wire accepted;
    wire rejected;
    wire norm_ok;
    wire overflow_fault;
    wire [1:0] epoch_token_mask;
    wire [15:0] epoch_spike_total;
    wire [9:0] epoch_norm_value;
    wire [9:0] epoch_commit_a;
    wire [9:0] epoch_commit_b;

    integer errors = 0;

    always #5 clk = ~clk;

    spu13_neuro_sidecar_adapter #(
        .NUM_NEURONS(2),
        .POT_WIDTH(8),
        .COUNT_WIDTH(4),
        .EPOCH_CYCLES(6),
        .EPOCH_COUNT_WIDTH(3),
        .LEAK(1),
        .RESET_VAL(0),
        .L_P(521),
        .L_P_BITS(10)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .inst_valid(inst_valid),
        .inst_word(inst_word),
        .inst_claimed(inst_claimed),
        .busy(busy),
        .error(error),
        .qr_commit_valid(qr_commit_valid),
        .qr_commit_lane(qr_commit_lane),
        .qr_commit_A(qr_commit_A),
        .qr_commit_B(qr_commit_B),
        .qr_commit_C(qr_commit_C),
        .qr_commit_D(qr_commit_D),
        .epoch_busy(epoch_busy),
        .epoch_done(epoch_done),
        .accepted(accepted),
        .rejected(rejected),
        .norm_ok(norm_ok),
        .overflow_fault(overflow_fault),
        .epoch_token_mask(epoch_token_mask),
        .epoch_spike_total(epoch_spike_total),
        .epoch_norm_value(epoch_norm_value),
        .epoch_commit_a(epoch_commit_a),
        .epoch_commit_b(epoch_commit_b)
    );

    // Issue one 64-bit SPI instruction word.
    // Delivers inst_valid for exactly 1 posedge of clk.
    task send_inst;
        input [7:0] op;
        input [3:0] n0;
        input [9:0] f1;
        input [9:0] f2;
        input [9:0] f3;
        input [9:0] f4;
        begin
            @(negedge clk);
            inst_valid <= 1'b1;
            inst_word <= {op, n0, f1, f2, f3, f4, 12'd0};
            @(posedge clk);
            @(negedge clk);
            inst_valid <= 1'b0;
            inst_word <= 64'd0;
        end
    endtask

    task cfg_neuron;
        input [3:0] idx;
        input [7:0] weight;
        input [7:0] threshold;
        begin
            send_inst(8'hE0, idx, {2'd0, weight}, {2'd0, threshold}, 10'd0, 10'd0);
            @(posedge clk);  // let config settle
        end
    endtask

    // Start epoch; initial_spike drives the first cycle's spike pattern.
    task start_epoch;
        input [9:0] exp_norm;
        input [9:0] fb_a;
        input [9:0] fb_b;
        input [9:0] initial_spike;
        begin
            send_inst(8'hE1, 4'd0, exp_norm, fb_a, fb_b, initial_spike);
        end
    endtask

    task send_spike;
        input [1:0] pattern;
        begin
            send_inst(8'hE2, 4'd0, 10'd0, 10'd0, {6'd0, pattern}, 10'd0);
        end
    endtask

    task read_result;
        input [3:0] lane;
        begin
            send_inst(8'hE3, lane, 10'd0, 10'd0, 10'd0, 10'd0);
            @(posedge clk);  // READY→IDLE, qr_commit_valid asserted (NB)
            @(negedge clk);  // Let NB settle; sample on negedge
        end
    endtask

    task wait_epoch;
        integer guard;
        begin
            guard = 0;
            while (!epoch_done && guard < 64) begin
                @(posedge clk);
                guard = guard + 1;
            end
            if (!epoch_done) begin
                $display("FAIL epoch timed out");
                errors = errors + 1;
            end
            // Do NOT add an extra clock; accepted/rejected/done are
            // valid only for the same cycle epoch_done is high.
        end
    endtask

    initial begin
        $display("=== spu13_neuro_sidecar_adapter_tb ===");
        repeat (4) @(posedge clk);
        rst_n = 1'b1;
        repeat (2) @(posedge clk);

        // ── Test 1: Accept path ───────────────────────────────────────
        // Config: neuron0 w=5 t=5, neuron1 w=3 t=5
        // EPOCH_CYCLES=6, spikes=2'b11 held for all cycles (from initial_spike).
        //
        // Neuron0 (w=5, t=5): fires every cycle → count=6
        // Neuron1 (w=3, t=5): fires on odd cycles (1,3,5) → count=3
        // sum_a = 6*1 + 3*2 = 12, sum_b = 6+3 = 9
        // norm(12,9) = 144+108-81 = 171
        // commit_a=12, commit_b=9, total=9
        $display("T1: accept path — expected_norm=171");
        cfg_neuron(4'd0, 8'd5, 8'd5);
        cfg_neuron(4'd1, 8'd3, 8'd5);

        start_epoch(10'd171, 10'd7, 10'd8, 10'd3);  // initial_spike=2'b11
        wait_epoch();

        if (!accepted || rejected || !norm_ok || overflow_fault) begin
            $display("FAIL T1 expected accept: accepted=%0d rejected=%0d norm_ok=%0d overflow=%0d",
                     accepted, rejected, norm_ok, overflow_fault);
            $display("  commit_a=%0d commit_b=%0d norm=%0d total=%0d",
                     epoch_commit_a, epoch_commit_b, epoch_norm_value, epoch_spike_total);
            errors = errors + 1;
        end else begin
            $display("T1 PASS: accept commit=(%0d,%0d) norm=%0d total=%0d",
                     epoch_commit_a, epoch_commit_b, epoch_norm_value, epoch_spike_total);
        end

        // Read back via NEURO_READ, lane 5
        // commit_a=12, commit_b=9 → qr_commit_A = {22'd0, 9, 22'd0, 12}
        read_result(4'd5);
        if (qr_commit_valid && qr_commit_lane == 4'd5 &&
            qr_commit_A[9:0] == 10'd12 && qr_commit_A[41:32] == 10'd9) begin
            $display("T1 READ PASS: lane=%0d A=%h B=%h", qr_commit_lane, qr_commit_A, qr_commit_B);
        end else begin
            $display("FAIL T1 READ: lane=%0d A=%h valid=%0d (expected lane5 A={9,12})",
                     qr_commit_lane, qr_commit_A, qr_commit_valid);
            errors = errors + 1;
        end

        // ── Test 2: Reject path (wrong expected_norm) ────────────────
        @(posedge clk);
        $display("T2: reject path — expected_norm=99 (wrong)");
        start_epoch(10'd99, 10'd7, 10'd8, 10'd3);
        wait_epoch();

        if (accepted || !rejected || norm_ok) begin
            $display("FAIL T2 expected reject: accepted=%0d rejected=%0d norm_ok=%0d",
                     accepted, rejected, norm_ok);
            errors = errors + 1;
        end else if (epoch_commit_a !== 10'd7 || epoch_commit_b !== 10'd8) begin
            $display("FAIL T2 fallback: commit_a=%0d commit_b=%0d (expected 7,8)",
                     epoch_commit_a, epoch_commit_b);
            errors = errors + 1;
        end else begin
            $display("T2 PASS: reject fallback=(%0d,%0d)", epoch_commit_a, epoch_commit_b);
        end

        // Read back — should show rejected bit in qr_commit_B[62]
        read_result(4'd0);
        if (qr_commit_valid && qr_commit_B[62]) begin
            $display("T2 READ PASS: rejected bit=1 B=%h", qr_commit_B);
        end else begin
            $display("FAIL T2 READ: rejected bit missing B=%h valid=%0d",
                     qr_commit_B, qr_commit_valid);
            errors = errors + 1;
        end

        // ── Test 3: Invalid opcode not claimed ───────────────────────
        @(posedge clk);
        $display("T3: invalid opcode");
        @(negedge clk);
        inst_valid <= 1'b1;
        inst_word <= {8'hFF, 60'd0};
        @(posedge clk);
        if (inst_claimed) begin
            $display("FAIL T3 unexpected claim for FF");
            errors = errors + 1;
        end else begin
            $display("T3 PASS: opcode FF not claimed");
        end
        @(negedge clk);
        inst_valid <= 1'b0;
        inst_word <= 64'd0;

        // ── Summary ──────────────────────────────────────────────────
        if (errors == 0) begin
            $display("PASS");
        end else begin
            $display("FAIL errors=%0d", errors);
        end
        $finish;
    end
endmodule
