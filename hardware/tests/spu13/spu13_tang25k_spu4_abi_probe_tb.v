// spu13_tang25k_spu4_abi_probe_tb.v — decode the ABI probe's UART line
//
// The probe under test is the first thing that puts `spu4_customer_wrapper`
// -- the SPU-4 ABI v1.0 contract layer -- into a board top. Until this
// existed, the ABI was verified only against its own testbench and reached no
// build at all, which is the same shape as the defects it was written to
// prevent: a product surface asserted in a document and never exercised.
//
// This decodes the serial stream byte-for-byte off `uart_tx` rather than
// peeking at internal state, so it fails the way a bench would fail.
//
// The status byte `S` is DECODED AND REPORTED, not predicted. `henosis`
// depends on whether the ALU's phi-fold fires for this fixture, and guessing
// it and asserting the guess would be a fabricated expectation. The bits this
// file does assert are the ones the contract fixes: done set, busy clear,
// start_ignored clear, saturated set.

`timescale 1ns / 1ps

module spu13_tang25k_spu4_abi_probe_tb;

    reg sys_clk = 0;
    wire [2:0] led;
    wire uart_tx;

    // Small timing constants so the line arrives in a few ms of sim time
    // rather than the ~200 ms the board uses.
    localparam CLKS_PER_BIT = 8;

    spu13_tang25k_spu4_abi_probe #(
        .CLK_FREQ(50000000),
        .CLKS_PER_BIT(CLKS_PER_BIT),
        .START_DELAY(400),
        .LINE_PERIOD(6000)
    ) dut (
        .sys_clk(sys_clk), .led(led), .uart_tx(uart_tx)
    );

    always #10 sys_clk = ~sys_clk;      // 50 MHz

    integer pass = 0, fail = 0;
    task ok;  input [1023:0] m; begin $display("PASS: %0s", m); pass = pass + 1; end endtask
    task bad; input [1023:0] m; begin $display("FAIL: %0s", m); fail = fail + 1; end endtask

    // ── UART receiver ────────────────────────────────────────────────
    localparam BIT_TIME = CLKS_PER_BIT * 20;    // ns per bit

    reg [7:0] line [0:127];
    integer   line_len;
    integer   lines_seen;

    task recv_byte(output [7:0] b);
        integer i;
        begin
            @(negedge uart_tx);                 // start bit
            #(BIT_TIME * 3 / 2);                // centre of bit 0
            for (i = 0; i < 8; i = i + 1) begin
                b[i] = uart_tx;
                #(BIT_TIME);
            end
        end
    endtask

    task recv_line;
        reg [7:0] b;
        begin
            line_len = 0;
            forever begin
                recv_byte(b);
                line[line_len] = b;
                line_len = line_len + 1;
                if (b == 8'h0A || line_len == 127) disable recv_line;
            end
        end
    endtask

    // Returns 4 bits, so callers never part-select a function result --
    // which Verilog-2001 does not allow. Non-hex input maps to 0; the
    // framing and label checks above run first and catch a malformed line.
    function [3:0] unhex;
        input [7:0] c;
        begin
            if (c >= "0" && c <= "9")      unhex = c - "0";
            else if (c >= "A" && c <= "F") unhex = c - "A" + 10;
            else                           unhex = 4'd0;
        end
    endfunction

    function [15:0] hex4;
        input integer at;
        begin
            hex4 = {unhex(line[at]), unhex(line[at+1]),
                    unhex(line[at+2]), unhex(line[at+3])};
        end
    endfunction

    integer i;
    reg [7:0] status_byte;
    reg [11:0] latency;
    reg pass_seen;

    initial begin
        pass_seen = 1'b0;
        lines_seen = 0;

        // Take several lines: the first ones legitimately carry the
        // in-progress '.' verdict, and a probe that never settles would
        // otherwise look identical to one that settles correctly.
        while (lines_seen < 6 && !pass_seen) begin
            recv_line;
            lines_seen = lines_seen + 1;
            if (line_len == 44 && line[4] == "P") pass_seen = 1'b1;
        end

        if (!pass_seen) begin
            bad("probe never emitted a PASS line");
            $write("last line seen: ");
            for (i = 0; i < line_len; i = i + 1)
                if (line[i] >= 32 && line[i] < 127) $write("%c", line[i]);
            $display("");
        end else begin
            ok("probe emitted a PASS line");

            // ── Framing ──────────────────────────────────────────────
            if (line_len == 44) ok("line is 44 bytes (42 visible + CRLF)");
            else                bad("line length wrong");
            if (line[42] == 8'h0D && line[43] == 8'h0A) ok("line ends CR LF");
            else                                        bad("line terminator wrong");

            if (line[0] == "A" && line[1] == "B" && line[2] == "I" &&
                line[3] == ":" && line[4] == "P")
                ok("prefix is ABI:P");
            else
                bad("prefix wrong");

            // ── Field labels, so a silently reordered line fails ──────
            if (line[6] == "B" && line[13] == "C" && line[20] == "D" &&
                line[27] == "R" && line[32] == "S" && line[37] == "L")
                ok("field labels B C D R S L in order");
            else
                bad("field labels wrong or reordered");

            // ── Values ───────────────────────────────────────────────
            if (hex4(8)  == 16'h0155) ok("B = 0155");  else bad("B wrong");
            if (hex4(15) == 16'h0155) ok("C = 0155");  else bad("C wrong");
            if (hex4(22) == 16'h0155) ok("D = 0155");  else bad("D wrong");

            // R must be FF, not 00. The QROT fixture's residual is 0x3FF and
            // saturates; 00 is what a stripped or stuck-at-zero port reads,
            // so asserting FF is what distinguishes a live signal from a dead
            // one. This is the same reasoning as §3.2j's R field.
            if (unhex(line[29]) == 4'hF && unhex(line[30]) == 4'hF)
                ok("R = FF, the saturated residual, not a laminar 00");
            else
                bad("R wrong");

            // ── ABI status byte ──────────────────────────────────────
            status_byte = {unhex(line[34]), unhex(line[35])};
            $display("INFO: ABI status byte S = %02h", status_byte);
            if (status_byte[1] == 1'b1) ok("status.done set");
            else                        bad("status.done clear on a PASS line");
            if (status_byte[0] == 1'b0) ok("status.busy clear");
            else                        bad("status.busy set on a PASS line");
            if (status_byte[3] == 1'b1) ok("status.saturated set, agreeing with R=FF");
            else                        bad("status.saturated disagrees with R");
            // The probe drives one start and never re-asserts it. A set bit
            // here would mean the PROBE violated the handshake, not the ABI.
            if (status_byte[4] == 1'b0) ok("status.start_ignored clear -- probe drove the handshake correctly");
            else                        bad("status.start_ignored set -- the probe double-started");
            if (status_byte[7:5] == 3'b000) ok("reserved status bits read 0");
            else                            bad("reserved status bits are not 0");

            // ── Measured latency ─────────────────────────────────────
            latency = {unhex(line[39]), unhex(line[40]), unhex(line[41])};
            $display("INFO: measured latency L = %0d clocks", latency);
            // SPU4_ABI.md §4: bounded, not fixed. 180-183 measured in
            // simulation over 124 operations, contract bound 200.
            if (latency > 0 && latency <= 200)
                ok("latency within the 200-clock ABI bound");
            else
                bad("latency outside the ABI bound");
            if (latency >= 175 && latency <= 190)
                ok("latency agrees with the simulated 180-183 range");
            else
                bad("latency disagrees with simulation -- investigate before trusting either");
        end

        $display("%0d checks, %0d passed, %0d failed", pass + fail, pass, fail);
        if (fail == 0) $display("PASS: spu13_tang25k_spu4_abi_probe_tb");
        else           $display("FAIL");
        $finish;
    end

    // Guard: a mute UART must fail loudly rather than hang the suite.
    initial begin
        #20_000_000;
        $display("FAIL: timeout -- no complete UART line");
        $display("FAIL");
        $finish;
    end

endmodule
