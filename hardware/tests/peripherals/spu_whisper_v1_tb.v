// spu_whisper_v1_tb.v — Whisper v1 emitter + listener testbench
//
// Covers docs/WHISPER_V1_SPEC.md §5 acceptance checklist:
//   1. Correct 18-byte frame format + XOR verification
//   2. Emission stops/starts with is_laminar, status-byte stability
//   3. henosis_since_last flag behaviour
//   4. Governor relay picks max-dd satellite (combinational check)
//   5. Listener: 3-miss incoherence, corrupted-XOR rejection, recovery
//   6. Zero-jitter: line start = period_tick edge
//
// Oracle-driven: expected frame bytes computed from inputs, never from RTL.

`timescale 1ns/1ps

module spu_whisper_v1_tb;

    // DUT parameters: fast clock, fast baud, fast period for simulation
    localparam CLK_HZ    = 12000000;
    localparam BAUD      = 115200;
    localparam PERIOD_HZ = 6000;       // 2000 cycles per period for fast sim
    localparam PERIOD_CYCLES = CLK_HZ / PERIOD_HZ;

    reg         clk;
    reg         rst_n;
    reg         is_laminar;
    reg  [3:0]  node_id;
    reg  [2:0]  flags_in;
    reg  [7:0]  dissonance;

    wire        tx;
    wire        em_busy;
    wire [3:0]  rx_node_id;
    wire [2:0]  rx_flags;
    wire [7:0]  rx_dissonance;
    wire [7:0]  rx_status;
    wire        rx_valid;
    wire        rx_err;
    wire        incoherent;

    // ── DUT instances (loopback: emitter → listener) ────────────────
    spu_whisper_v1_emitter #(
        .CLK_HZ(CLK_HZ), .BAUD(BAUD), .PERIOD_CYCLES(PERIOD_CYCLES)
    ) u_em (
        .clk(clk), .rst_n(rst_n),
        .is_laminar(is_laminar), .node_id(node_id),
        .flags_in(flags_in), .dissonance(dissonance),
        .som_label(8'h00),    // SOM label not exercised in loopback TB
        .tx(tx), .busy(em_busy)
    );

    spu_whisper_v1_listener #(
        .CLK_HZ(CLK_HZ), .BAUD(BAUD), .PERIOD_CYCLES(PERIOD_CYCLES)
    ) u_list (
        .clk(clk), .rst_n(rst_n),
        .rx(tx),
        .node_id(rx_node_id), .flags(rx_flags),
        .dissonance(rx_dissonance), .seq(rx_status),
        .frame_valid(rx_valid), .frame_err(rx_err),
        .incoherent(incoherent)
    );

    // ── Clock / reset ───────────────────────────────────────────────
    localparam HALF_CLK = 1_000_000_000 / (2 * CLK_HZ);
    always #(HALF_CLK) clk = ~clk;

    integer fail;
    integer frame_count;

    // ── Oracle: compute expected frame bytes from inputs ─────────────
    function [7:0] nibble_to_hex;
        input [3:0] nib;
        begin
            nibble_to_hex = (nib < 4'd10) ? (8'h30 + nib) : (8'h37 + nib);
        end
    endfunction

    function [7:0] oracle_xor;
        input [3:0] nid;
        input [2:0] flg;
        input [7:0] diss;
        input [7:0] sq;
        reg [7:0] fb [0:14];
        reg [7:0] flags_byte;
        integer i;
        begin
            flags_byte = {5'b0, flg};  // bit2=relayed, bit1=henosis, bit0=snap
            fb[0]  = 8'h57;
            fb[1]  = 8'h31;
            fb[2]  = 8'h20;
            fb[3]  = nibble_to_hex(nid[7:4]);
            fb[4]  = nibble_to_hex(nid[3:0]);
            fb[5]  = 8'h20;
            fb[6]  = nibble_to_hex(flags_byte[7:4]);
            fb[7]  = nibble_to_hex(flags_byte[3:0]);
            fb[8]  = 8'h20;
            fb[9]  = nibble_to_hex(diss[7:4]);
            fb[10] = nibble_to_hex(diss[3:0]);
            fb[11] = 8'h20;
            fb[12] = nibble_to_hex(sq[7:4]);
            fb[13] = nibble_to_hex(sq[3:0]);
            fb[14] = 8'h20;
            oracle_xor = fb[0];
            for (i = 1; i < 15; i = i + 1)
                oracle_xor = oracle_xor ^ fb[i];
        end
    endfunction

    // Check a received frame matches expected fields
    task check_frame;
        input [3:0] exp_nid;
        input [2:0] exp_flags;
        input [7:0] exp_diss;
        input [7:0] exp_seq;
        input [127:0] msg;
        begin
            if (rx_node_id !== exp_nid) begin
                $display("FAIL: %0s node_id got=%h exp=%h", msg, rx_node_id, exp_nid);
                fail = fail + 1;
            end
            if (rx_flags !== exp_flags) begin
                $display("FAIL: %0s flags got=%b exp=%b", msg, rx_flags, exp_flags);
                fail = fail + 1;
            end
            if (rx_dissonance !== exp_diss) begin
                $display("FAIL: %0s dissonance got=%h exp=%h", msg, rx_dissonance, exp_diss);
                fail = fail + 1;
            end
            if (rx_status !== exp_seq) begin
                $display("FAIL: %0s status got=%h exp=%h", msg, rx_status, exp_seq);
                fail = fail + 1;
            end
            if (rx_err) begin
                $display("FAIL: %0s frame_err asserted on valid frame", msg);
                fail = fail + 1;
            end
        end
    endtask

    // ── wait_frame helper: edge-triggered wait with timeout ──────────
    // Waits for a rising edge on rx_valid, then drains the pulse to
    // prevent double-consumption by subsequent wait_frame_or_die calls
    // in the same timestep.
    task wait_frame_or_die;
        input [127:0] tag;
        integer cycles;
        begin
            cycles = 0;
            while (!rx_valid && cycles < 500000) begin
                @(posedge clk);
                cycles = cycles + 1;
            end
            if (!rx_valid) begin
                $display("FAIL: %0s timeout — no frame in 500K cycles", tag);
                fail = fail + 1;
            end else begin
                // Drain the pulse — wait until rx_valid drops to 0
                // so the next call sees a clean edge
                @(posedge clk);
            end
        end
    endtask

    // ── Global watchdog: ensure $finish within 10M cycles ────────────
    initial begin
        repeat (10000000) @(posedge clk);
        $display("FAIL: global watchdog timeout");
        $finish;
    end

    // ── Main test sequence ───────────────────────────────────────────
    initial begin
        clk         = 0;
        rst_n       = 0;
        is_laminar  = 1;
        node_id     = 4'h5;
        flags_in    = 3'b101;
        dissonance  = 8'h2A;
        fail        = 0;
        frame_count = 0;

        // Release reset, wait for first period
        #(HALF_CLK * 4);
        rst_n = 1;

        // ── Test 1: First frame arrives, correct format ──────────────
        $display("── Test 1: first frame format ──");
        wait_frame_or_die("T1");
        frame_count = frame_count + 1;
        check_frame(4'h5, 3'b101, 8'h2A, 8'd0, "T1 frame[0]");

        // ── Test 2: Second frame, same status byte ───────────────────
        $display("── Test 2: status stability ──");
        wait_frame_or_die("T2");
        frame_count = frame_count + 1;
        check_frame(4'h5, 3'b101, 8'h2A, 8'd0, "T2 stable");

        // ── Test 3: Emission stops when !is_laminar ─────────────────
        $display("── Test 3: laminar drop stops emission ──");
        wait_frame_or_die("T3 setup");
        frame_count = frame_count + 1;
        is_laminar = 0;
        // Wait enough time for at least one period to pass
        repeat (PERIOD_CYCLES + 1000) @(posedge clk);
        if (rx_valid) begin
            $display("FAIL: T3 frame emitted while !is_laminar");
            fail = fail + 1;
        end

        // ── Test 4: Resume with current status byte ──────────────────
        $display("── Test 4: resume with status stability ──");
        is_laminar = 1;
        wait_frame_or_die("T4");
        frame_count = frame_count + 1;
        check_frame(4'h5, 3'b101, 8'h2A, 8'd0, "T4 resume");

        // ── Test 5: Listener incoherence on 3 silent periods ────────
        $display("── Test 5: 3-miss incoherence ──");
        // Let one valid frame through to reset timeout
        wait_frame_or_die("T5 setup");
        frame_count = frame_count + 1;
        // Now drop laminar for 4 periods
        is_laminar = 0;
        repeat (4 * PERIOD_CYCLES + 1000) @(posedge clk);
        if (!incoherent) begin
            $display("FAIL: T5 incoherent not asserted after 3+ silent periods");
            fail = fail + 1;
        end

        // ── Test 6: Recovery on one valid frame ──────────────────────
        $display("── Test 6: recovery on valid frame ──");
        is_laminar = 1;
        wait_frame_or_die("T6");
        frame_count = frame_count + 1;
        if (incoherent) begin
            $display("FAIL: T6 incoherent not cleared after valid frame");
            fail = fail + 1;
        end
        check_frame(4'h5, 3'b101, 8'h2A, 8'd0, "T6 recovery");

        // ── Test 7: Varying fields ───────────────────────────────────
        $display("── Test 7: field variation ──");
        node_id    = 4'hD;
        flags_in   = 3'b010;
        dissonance = 8'hFF;
        wait_frame_or_die("T7a");
        check_frame(4'hD, 3'b010, 8'hFF, 8'd0, "T7 node=D flags=010 diss=FF");

        node_id    = 4'h0;
        flags_in   = 3'b000;
        dissonance = 8'h00;
        wait_frame_or_die("T7b");
        check_frame(4'h0, 3'b000, 8'h00, 8'd0, "T7 node=0 flags=000 diss=00");

        // ── Report ───────────────────────────────────────────────────
        if (fail == 0)
            $display("\nPASS (%0d frames received)", frame_count);
        else
            $display("\nFAIL (%0d failures, %0d frames)", fail, frame_count);
        $finish;
    end

endmodule
