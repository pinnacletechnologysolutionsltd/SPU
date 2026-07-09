// spu13_satellite_aggregator_tb.v — Testbench: spu13_satellite_aggregator
//
// Drives two whisper v1 emitters into two of the aggregator's listener
// channels (loopback, same pattern as spu_whisper_v1_tb.v) and leaves the
// rest idle, then checks:
//   1. Per-satellite status_table packing (incoherent, som_valid,
//      som_label, snap, dissonance) matches the driven inputs exactly.
//   2. som_labels bus extracts the correct nibble per satellite.
//   3. worst_axis / worst_dissonance track the max across satellites and
//      update when a later frame changes the ranking.
//   4. incoherent_count rises only for satellites that never send a
//      frame, not for ones actively transmitting.
//   5. The command bus FSM shifts cmd_opcode out MSB-first on bus_mosi
//      with bus_cs == cmd_satellite while sending, and returns to the
//      idle (0xF) chip-select afterward.
//
// Oracle-driven: expected status fields come from the inputs fed to each
// emitter, never from re-deriving the RTL's internal bit layout.

`timescale 1ns/1ps

module spu13_satellite_aggregator_tb;

    localparam CLK_HZ    = 12000000;
    localparam BAUD      = 115200;
    // An 18-byte whisper frame takes ~18,700 cycles to transmit at this
    // BAUD/CLK_HZ regardless of the configured period, so PERIOD_CYCLES
    // must exceed that or the emitter never idles between frames and the
    // listener's 3-miss counter (which ticks on its own PERIOD_CYCLES,
    // independent of real frame arrival) falsely trips. 30,000 gives
    // ~60% margin over one frame's transmission time.
    localparam PERIOD_CYCLES = 30000;
    localparam NUM_SATELLITES = 4;

    reg clk;
    reg rst_n;

    // ── Two driven satellites (0, 1); 2 and 3 stay idle ─────────────
    reg        is_lam0, is_lam1;
    reg [3:0]  node0, node1;
    reg [2:0]  flags0, flags1;
    reg [7:0]  diss0, diss1;
    reg [7:0]  som0, som1;
    wire       tx0, tx1, busy0, busy1;

    spu_whisper_v1_emitter #(.CLK_HZ(CLK_HZ), .BAUD(BAUD), .PERIOD_CYCLES(PERIOD_CYCLES)) u_em0 (
        .clk(clk), .rst_n(rst_n),
        .is_laminar(is_lam0), .node_id(node0), .flags_in(flags0),
        .dissonance(diss0), .som_label(som0),
        .tx(tx0), .busy(busy0)
    );

    spu_whisper_v1_emitter #(.CLK_HZ(CLK_HZ), .BAUD(BAUD), .PERIOD_CYCLES(PERIOD_CYCLES)) u_em1 (
        .clk(clk), .rst_n(rst_n),
        .is_laminar(is_lam1), .node_id(node1), .flags_in(flags1),
        .dissonance(diss1), .som_label(som1),
        .tx(tx1), .busy(busy1)
    );

    wire [NUM_SATELLITES-1:0] whisper_rx;
    assign whisper_rx[0] = tx0;
    assign whisper_rx[1] = tx1;
    assign whisper_rx[2] = 1'b1;   // idle line (UART idle-high), never sends
    assign whisper_rx[3] = 1'b1;   // idle line, never sends

    // ── Command bus stimulus ─────────────────────────────────────────
    reg        cmd_valid;
    reg [3:0]  cmd_satellite;
    reg [7:0]  cmd_opcode;
    wire       cmd_done, cmd_error;
    wire [3:0] bus_cs;
    wire       bus_sck, bus_mosi;

    wire [NUM_SATELLITES*16-1:0] status_table;
    wire [3:0] worst_axis;
    wire [7:0] worst_dissonance;
    wire [3:0] incoherent_count;
    wire [51:0] som_labels;

    spu13_satellite_aggregator #(
        .NUM_SATELLITES(NUM_SATELLITES), .CLK_HZ(CLK_HZ), .BAUD(BAUD),
        .PERIOD_CYCLES(PERIOD_CYCLES)
    ) dut (
        .clk(clk), .rst_n(rst_n),
        .whisper_rx(whisper_rx),
        .bus_cs(bus_cs), .bus_sck(bus_sck), .bus_mosi(bus_mosi), .bus_miso(1'b0),
        .status_table(status_table),
        .worst_axis(worst_axis), .worst_dissonance(worst_dissonance),
        .incoherent_count(incoherent_count), .som_labels(som_labels),
        .cmd_valid(cmd_valid), .cmd_satellite(cmd_satellite), .cmd_opcode(cmd_opcode),
        .cmd_done(cmd_done), .cmd_error(cmd_error)
    );

    localparam HALF_CLK = 1_000_000_000 / (2 * CLK_HZ);
    always #(HALF_CLK) clk = ~clk;

    integer fail;

    // ── Oracle: expected 16-bit status field for one satellite ───────
    // Layout under test: incoherent(1) som_valid(1) reserved(1) som_label[3:0] snap(1) dissonance[7:0]
    function [15:0] oracle_status;
        input        incoherent;
        input        som_valid;
        input [3:0]  som_label;
        input        snap;
        input [7:0]  dissonance;
        begin
            oracle_status = {incoherent, som_valid, 1'b0, som_label, snap, dissonance};
        end
    endfunction

    task check_status;
        input [3:0]  sat;
        input [15:0] expected;
        input [127:0] msg;
        reg [15:0] got;
        begin
            got = status_table[sat*16 +: 16];
            if (got !== expected) begin
                $display("FAIL: %0s status_table[%0d] got=%h exp=%h", msg, sat, got, expected);
                fail = fail + 1;
            end
        end
    endtask

    task check_nibble;
        input [3:0]  sat;
        input [3:0]  expected;
        input [127:0] msg;
        reg [3:0] got;
        begin
            got = som_labels[sat*4 +: 4];
            if (got !== expected) begin
                $display("FAIL: %0s som_labels[%0d] got=%h exp=%h", msg, sat, got, expected);
                fail = fail + 1;
            end
        end
    endtask

    // ── Global watchdog ───────────────────────────────────────────────
    initial begin
        repeat (2000000) @(posedge clk);
        $display("FAIL: global watchdog timeout");
        $finish;
    end

    initial begin
        clk = 0; rst_n = 0; fail = 0;
        is_lam0 = 1; node0 = 4'h1; flags0 = 3'b001; diss0 = 8'h20; som0 = 8'h03;
        is_lam1 = 1; node1 = 4'h2; flags1 = 3'b000; diss1 = 8'h50; som1 = 8'h07;
        cmd_valid = 0; cmd_satellite = 0; cmd_opcode = 0;

        #(HALF_CLK * 4);
        rst_n = 1;

        // ── Test 1: first frames land, status_table matches inputs ───
        // First frame takes ~50,000 cycles (transmission + listener
        // pipeline delay at this BAUD/CLK_HZ); 80,000 gives margin.
        $display("── Test 1: status_table packing ──");
        repeat (80000) @(posedge clk);
        check_status(0, oracle_status(1'b0, 1'b1, som0[3:0], flags0[0], diss0), "T1 sat0");
        check_status(1, oracle_status(1'b0, 1'b1, som1[3:0], flags1[0], diss1), "T1 sat1");
        check_nibble(0, som0[3:0], "T1 nibble sat0");
        check_nibble(1, som1[3:0], "T1 nibble sat1");

        // ── Test 2: worst axis/dissonance track sat1 (higher diss) ───
        $display("── Test 2: worst_axis tracks max dissonance ──");
        if (worst_axis !== 4'd1 || worst_dissonance !== diss1) begin
            $display("FAIL: T2 worst_axis=%0d worst_diss=%h exp axis=1 diss=%h",
                      worst_axis, worst_dissonance, diss1);
            fail = fail + 1;
        end

        // ── Test 3: idle satellites 2,3 go incoherent, driven ones don't ──
        // Idle satellites trip the 3-miss timeout at 3*PERIOD_CYCLES=90,000
        // cycles post-reset. Waiting to ~130,000 total keeps sat0/sat1's
        // most recent real frame well under that same 90,000-cycle window
        // (steady-state period is ~29,600 cycles), so they must stay coherent.
        $display("── Test 3: incoherent_count for idle satellites ──");
        repeat (50000) @(posedge clk);
        if (incoherent_count !== 4'd2) begin
            $display("FAIL: T3 incoherent_count=%0d exp=2 (sats 2,3 idle)", incoherent_count);
            fail = fail + 1;
        end
        if (status_table[0*16+15] !== 1'b0 || status_table[1*16+15] !== 1'b0) begin
            $display("FAIL: T3 driven satellites 0/1 falsely marked incoherent");
            fail = fail + 1;
        end
        if (status_table[2*16+15] !== 1'b1 || status_table[3*16+15] !== 1'b1) begin
            $display("FAIL: T3 idle satellites 2/3 not marked incoherent");
            fail = fail + 1;
        end

        // ── Test 4: raise sat0's dissonance above sat1, worst_axis flips ──
        // One full period (~29,600 cycles) covers the next frame from em0.
        $display("── Test 4: worst_axis re-ranks on new frame ──");
        diss0 = 8'hAA;
        repeat (40000) @(posedge clk);
        check_status(0, oracle_status(1'b0, 1'b1, som0[3:0], flags0[0], diss0), "T4 sat0 updated");
        if (worst_axis !== 4'd0 || worst_dissonance !== 8'hAA) begin
            $display("FAIL: T4 worst_axis=%0d worst_diss=%h exp axis=0 diss=AA",
                      worst_axis, worst_dissonance);
            fail = fail + 1;
        end

        // ── Test 5: command bus shifts cmd_opcode out MSB-first ──────
        $display("── Test 5: command bus FSM ──");
        cmd_satellite = 4'd2;
        cmd_opcode    = 8'hB4;   // 1011_0100
        cmd_valid     = 1;
        @(posedge clk);
        cmd_valid = 0;

        // While sending, bus_cs must select the addressed satellite
        if (bus_cs !== 4'd2) begin
            $display("FAIL: T5 bus_cs=%h exp=2 during send", bus_cs);
            fail = fail + 1;
        end

        // bus_sck is held high for the whole 8-cycle transfer (no per-bit
        // toggle — see BUS_SEND in the DUT), so sample bus_mosi once per
        // clock for 8 cycles instead of on a clock edge that doesn't exist.
        @(posedge clk);   // BUS_IDLE -> BUS_SEND registers on this edge
        begin : capture
            reg [7:0] shifted;
            integer   i;
            shifted = 8'h00;
            for (i = 0; i < 8; i = i + 1) begin
                shifted = {shifted[6:0], bus_mosi};
                @(posedge clk);
            end
            if (shifted !== cmd_opcode) begin
                $display("FAIL: T5 shifted opcode=%h exp=%h", shifted, cmd_opcode);
                fail = fail + 1;
            end
        end

        // cmd_done should pulse and bus_cs should return to deselected (0xF)
        begin : wait_done
            integer guard;
            guard = 0;
            while (!cmd_done && guard < 1000) begin
                @(posedge clk);
                guard = guard + 1;
            end
            if (!cmd_done) begin
                $display("FAIL: T5 cmd_done never asserted");
                fail = fail + 1;
            end
        end
        @(posedge clk);
        if (bus_cs !== 4'hF) begin
            $display("FAIL: T5 bus_cs=%h exp=F after command completes", bus_cs);
            fail = fail + 1;
        end

        // ── Report ─────────────────────────────────────────────────────
        if (fail == 0)
            $display("\nPASS");
        else
            $display("\nFAIL (%0d failures)", fail);
        $finish;
    end

endmodule
