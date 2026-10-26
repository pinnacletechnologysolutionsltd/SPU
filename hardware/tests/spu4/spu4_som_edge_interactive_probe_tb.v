`timescale 1ns / 1ps

// spu4_som_edge_interactive_probe_tb.v -- end-to-end UART-in/UART-out test
// for spu13_tang25k_spu4_som_edge_interactive_probe.v. Reuses the mock
// flash SPI slave and oracle-fixture weight tables verbatim from
// spu4_som_edge_full_chain_tb.v (same 8 oracle-checked queries), but
// drives them as host-framed UART query lines instead of hardcoded bus
// assignments, and receives results by decoding the probe's own UART TX
// output through a second spu4_uart_rx_bitsync instance acting as a
// receive harness -- proving the RX core in a real role, not just its
// own standalone TB. Also proves 3 malformed-line cases resync correctly.

module spu4_som_edge_interactive_probe_tb #(
    parameter BENCH25 = 0,
    parameter DIAGNOSTIC = 0,
    parameter FROZEN_CASE = 0
);

    // Bench25 uses the real wire rate: 217 divided-clock cycles = 434 source cycles.
    localparam integer CLKS_PER_BIT = BENCH25 ? 434 : 8;
    // Real-rate reply alone takes 40*10*434 source clocks. Preserve the
    // original 60,000-cycle startup margin, doubled for half-speed fabric.
    localparam integer REPLY_LIMIT = BENCH25 ? 120000 + 400*CLKS_PER_BIT : 60000;

    reg clk = 0, rst_n = 0;
    reg  uart_rx_line = 1;
    wire uart_tx_line;
    wire [2:0] led;
    wire flash_sck, flash_cs, flash_mosi;
    reg  flash_miso = 0;
    wire probe_clk, probe_start, probe_busy, probe_done, probe_completion_armed;
    wire [2:0] probe_dispatch_state;

    generate if (BENCH25) begin : bench25
        spu4_ina226_bench25_top #(.DIAGNOSTIC(DIAGNOSTIC)) dut (
            .sys_clk(clk), .led(led), .uart_tx(uart_tx_line), .uart_rx(uart_rx_line),
            .flash_cs(flash_cs), .flash_sck(flash_sck),
            .flash_mosi(flash_mosi), .flash_miso(flash_miso)
        );
        time previous_edge = 0;
        always @(posedge dut.clk_25) begin
            if (previous_edge != 0 && $time - previous_edge != 40)
                $fatal(1, "bench25 clock is not 25 MHz");
            previous_edge = $time;
        end
        assign probe_start = dut.u_probe.start;
        assign probe_clk = dut.clk_25;
        assign probe_busy = dut.u_probe.busy;
        assign probe_done = dut.u_probe.done;
        assign probe_completion_armed = dut.u_probe.completion_armed;
        assign probe_dispatch_state = dut.u_probe.dispatch_state;
    end else begin : original
    spu13_tang25k_spu4_som_edge_interactive_probe #(
        .CLK_FREQ(50000000), .CLKS_PER_BIT(CLKS_PER_BIT),
        .DIAGNOSTIC(DIAGNOSTIC)
    ) dut (
        .sys_clk(clk), .led(led),
        .uart_tx(uart_tx_line), .uart_rx(uart_rx_line),
        .flash_cs(flash_cs), .flash_sck(flash_sck),
        .flash_mosi(flash_mosi), .flash_miso(flash_miso)
    );
        assign probe_start = dut.start;
        assign probe_clk = clk;
        assign probe_busy = dut.busy;
        assign probe_done = dut.done;
        assign probe_completion_armed = dut.completion_armed;
        assign probe_dispatch_state = dut.dispatch_state;
    end endgenerate

    // Receive harness: decode the DUT's own TX line the same way a real
    // host would.
    wire       resp_byte_valid;
    wire [7:0] resp_byte;
    spu4_uart_rx_bitsync #(.CLKS_PER_BIT(CLKS_PER_BIT)) u_resp_rx (
        .clk(clk), .rst_n(rst_n), .rx(uart_tx_line),
        .rx_byte_valid(resp_byte_valid), .rx_byte(resp_byte)
    );

    always #10 clk = ~clk;

    integer pass = 0, fail = 0;
    integer accepted_queries = 0, fresh_completions = 0, stale_done_blocks = 0;
    always @(posedge probe_clk) begin
        if (probe_start && !probe_busy) accepted_queries = accepted_queries + 1;
        if (probe_dispatch_state == 3'd3 && probe_completion_armed && probe_done)
            fresh_completions = fresh_completions + 1;
        if (probe_dispatch_state == 3'd3 && !probe_completion_armed && probe_done)
            stale_done_blocks = stale_done_blocks + 1;
    end
    task ok;  input [1023:0] m; begin $display("PASS: %0s", m); pass = pass + 1; end endtask
    task bad; input [1023:0] m; begin $display("FAIL: %0s", m); fail = fail + 1; end endtask

    // ── Mock flash: identical fixture to spu4_som_edge_full_chain_tb.v ──
    localparam integer NUM_FEATURES = 4;
    localparam integer TOTAL_BYTES  = 4 * NUM_FEATURES * 4;

    reg signed [15:0] exp_p [0:3][0:NUM_FEATURES-1];
    reg signed [15:0] exp_q [0:3][0:NUM_FEATURES-1];

    initial begin
        if (FROZEN_CASE) begin
            exp_p[0][0]=25385; exp_q[0][0]=0; exp_p[0][1]=14190; exp_q[0][1]=0;
            exp_p[0][2]=8574;  exp_q[0][2]=0; exp_p[0][3]=11169; exp_q[0][3]=0;
            exp_p[1][0]=29735; exp_q[1][0]=0; exp_p[1][1]=2945;  exp_q[1][1]=0;
            exp_p[1][2]=938;   exp_q[1][2]=0; exp_p[1][3]=1242;  exp_q[1][3]=0;
            exp_p[2][0]=7832;  exp_q[2][0]=0; exp_p[2][1]=20489; exp_q[2][1]=0;
            exp_p[2][2]=15449; exp_q[2][2]=0; exp_p[2][3]=22881; exp_q[2][3]=0;
            exp_p[3][0]=0;     exp_q[3][0]=0; exp_p[3][1]=6338;  exp_q[3][1]=0;
            exp_p[3][2]=2000;  exp_q[3][2]=0; exp_p[3][3]=5294;  exp_q[3][3]=0;
        end else begin
        exp_p[0][0]=100; exp_q[0][0]=0;  exp_p[0][1]=0; exp_q[0][1]=0;
        exp_p[0][2]=0;   exp_q[0][2]=0;  exp_p[0][3]=0; exp_q[0][3]=0;
        exp_p[1][0]=0;   exp_q[1][0]=0;  exp_p[1][1]=0; exp_q[1][1]=40;
        exp_p[1][2]=0;   exp_q[1][2]=0;  exp_p[1][3]=0; exp_q[1][3]=0;
        exp_p[2][0]=-30; exp_q[2][0]=0;  exp_p[2][1]=-30; exp_q[2][1]=0;
        exp_p[2][2]=60;  exp_q[2][2]=0;  exp_p[2][3]=0;   exp_q[2][3]=0;
        exp_p[3][0]=0;   exp_q[3][0]=0;  exp_p[3][1]=0; exp_q[3][1]=0;
        exp_p[3][2]=0;   exp_q[3][2]=0;  exp_p[3][3]=50; exp_q[3][3]=50;
        end
    end

    reg [7:0] spi_mem [0:TOTAL_BYTES-1];
    integer n, f, idx;
    initial begin
        #1;
        idx = 0;
        for (n = 0; n < 4; n = n + 1) begin
            for (f = 0; f < NUM_FEATURES; f = f + 1) begin
                spi_mem[idx] = exp_p[n][f][15:8]; idx = idx + 1;
                spi_mem[idx] = exp_p[n][f][7:0];  idx = idx + 1;
                spi_mem[idx] = exp_q[n][f][15:8]; idx = idx + 1;
                spi_mem[idx] = exp_q[n][f][7:0];  idx = idx + 1;
            end
        end
    end

    integer total_bits, sbn, sbyt;
    always @(negedge flash_cs) total_bits = 0;
    always @(negedge flash_sck) begin
        if (!flash_cs) begin
            total_bits = total_bits + 1;
            if (total_bits >= 32) begin
                idx  = total_bits - 32;
                sbn  = idx % 8;
                sbyt = idx / 8;
                flash_miso = (sbyt < TOTAL_BYTES) ? spi_mem[sbyt][7-sbn] : 1'b0;
            end
        end
    end

    // ── UART byte-level send helper (mirrors spu4_uart_rx_bitsync_tb.v) ─
    task send_byte;
        input [7:0] b;
        integer i;
        begin
            uart_rx_line = 1'b0;                          // start bit
            repeat (CLKS_PER_BIT) @(posedge clk);
            for (i = 0; i < 8; i = i + 1) begin
                uart_rx_line = b[i];                       // LSB first
                repeat (CLKS_PER_BIT) @(posedge clk);
            end
            uart_rx_line = 1'b1;                           // stop bit
            repeat (CLKS_PER_BIT) @(posedge clk);
        end
    endtask

    function [7:0] hexch;
        input [3:0] nib;
        begin hexch = (nib < 10) ? ("0" + nib) : ("A" + nib - 10); end
    endfunction

    function [3:0] ascii_to_nibble;
        input [7:0] c;
        begin
            if (c >= "0" && c <= "9")      ascii_to_nibble = c - "0";
            else if (c >= "A" && c <= "F") ascii_to_nibble = c - "A" + 4'd10;
            else                            ascii_to_nibble = 4'hX;  // unexpected
        end
    endfunction

    // Send a well-formed query line for the 8 oracle fixtures below.
    task send_query_line;
        input signed [15:0] p0, q0, p1, q1, p2, q2, p3, q3;
        integer k;
        reg signed [15:0] vals [0:7];
        begin
            vals[0]=p0; vals[1]=q0; vals[2]=p1; vals[3]=q1;
            vals[4]=p2; vals[5]=q2; vals[6]=p3; vals[7]=q3;
            send_byte("Q");
            for (k = 0; k < 8; k = k + 1) begin
                send_byte(hexch(vals[k][15:12]));
                send_byte(hexch(vals[k][11:8]));
                send_byte(hexch(vals[k][7:4]));
                send_byte(hexch(vals[k][3:0]));
            end
            send_byte(8'h0A);
        end
    endtask

    // ── Response capture: decode the harness RX's byte stream into one
    // 40-byte line at a time ──────────────────────────────────────────
    reg [7:0] resp_bytes [0:39];
    integer   resp_idx = 0;
    always @(posedge clk) begin
        if (resp_byte_valid && resp_idx < 40) begin
            resp_bytes[resp_idx] = resp_byte;
            resp_idx = resp_idx + 1;
        end
    end

    task recv_line;
        output [7:0]  ch;
        output [1:0]  node;
        output [31:0] quad;
        output [7:0]  stat;
        output [11:0] lat;
        output [15:0] rid;
        integer t;
        begin
            resp_idx = 0;
            t = 0;
            while (resp_idx < 40 && t < REPLY_LIMIT) begin @(posedge clk); t = t + 1; end
            if (resp_idx < 40) begin
                bad("response line never completed (timeout)");
                ch = "?"; node = 2'bxx; quad = 32'hxxxxxxxx;
                stat = 8'hxx; lat = 12'hxxx; rid = 16'hxxxx;
            end else begin
                ch   = resp_bytes[4];
                node = ascii_to_nibble(resp_bytes[8]) & 2'b11;
                quad = {ascii_to_nibble(resp_bytes[12]), ascii_to_nibble(resp_bytes[13]),
                        ascii_to_nibble(resp_bytes[14]), ascii_to_nibble(resp_bytes[15]),
                        ascii_to_nibble(resp_bytes[16]), ascii_to_nibble(resp_bytes[17]),
                        ascii_to_nibble(resp_bytes[18]), ascii_to_nibble(resp_bytes[19])};
                stat = {ascii_to_nibble(resp_bytes[23]), ascii_to_nibble(resp_bytes[24])};
                lat  = {ascii_to_nibble(resp_bytes[28]), ascii_to_nibble(resp_bytes[29]),
                        ascii_to_nibble(resp_bytes[30])};
                rid  = {ascii_to_nibble(resp_bytes[34]), ascii_to_nibble(resp_bytes[35]),
                        ascii_to_nibble(resp_bytes[36]), ascii_to_nibble(resp_bytes[37])};
            end
        end
    endtask

    // Drive one query over UART and check the oracle-computed verdict.
    task run_uart_query;
        input [255:0] label;
        input signed [15:0] p0, q0, p1, q1, p2, q2, p3, q3;
        input [1:0]  exp_node;
        input [31:0] exp_quad;
        reg [7:0]  ch;
        reg [1:0]  node;
        reg [31:0] quad;
        reg [7:0]  stat;
        reg [11:0] lat;
        reg [15:0] rid;
        integer dline;
        reg [7:0] expected_code;
        begin
            send_query_line(p0, q0, p1, q1, p2, q2, p3, q3);
            if (DIAGNOSTIC) begin
                for (dline = 1; dline <= 11; dline = dline + 1) begin
                    recv_line(ch, node, quad, stat, lat, rid);
                    case (dline)
                        1: expected_code = "I";
                        2: expected_code = "A";
                        3: expected_code = "B";
                        4: expected_code = "C";
                        5: expected_code = "D";
                        6: expected_code = "0";
                        7: expected_code = "1";
                        8: expected_code = "2";
                        9: expected_code = "3";
                        10: expected_code = "R";
                        default: expected_code = "C";
                    endcase
                    if (resp_bytes[0] !== "D" || resp_bytes[1] !== "B" ||
                        resp_bytes[2] !== "G" || resp_bytes[3] !== ":" ||
                        ch !== expected_code || resp_bytes[5] !== "=")
                        bad({label, ": malformed diagnostic line"});
                    else ok({label, ": ordered diagnostic line"});
                end
            end
            recv_line(ch, node, quad, stat, lat, rid);
            if (ch !== "D") bad({label, ": expected 'D' response char"});
            else             ok({label, ": got 'D' response char"});
            if (node !== exp_node) bad({label, ": best_node mismatch vs oracle"});
            else                    ok({label, ": best_node matches oracle"});
            if (quad !== exp_quad) bad({label, ": best_quadrance mismatch vs oracle"});
            else                    ok({label, ": best_quadrance matches oracle exactly"});
            $display("INFO: %0s latency=%0d", label, lat);
            if (lat !== 12'd6) bad({label, ": latency is stale or not six accepted-to-done clocks"});
            else               ok({label, ": fresh latency is six clocks"});
        end
    endtask

    function [127:0] frozen_diag_payload;
        input integer line;
        begin
            case (line)
                1: frozen_diag_payload = 128'h4BD40000520800003EB800001B250000;
                2: frozen_diag_payload = 128'h2BA10000217E0000376E000063290000;
                3: frozen_diag_payload = 128'h04DA000003AA00000B81000074270000;
                4: frozen_diag_payload = 128'h596100003C590000500900001E980000;
                5: frozen_diag_payload = 128'h14AE000007D0000018C2000000000000;
                6: frozen_diag_payload = 128'h00000000000000000000000021B83601;
                7: frozen_diag_payload = 128'h00000000000000000000000054DC707D;
                8: frozen_diag_payload = 128'h00000000000000000000000003C58E94;
                9: frozen_diag_payload = 128'h00000000000000000000000029E7A1A1;
                10: frozen_diag_payload = 128'h00000000000000000000000203C58E94;
                default: frozen_diag_payload = 128'h00000000000000000000000203C58E94;
            endcase
        end
    endfunction

    reg [7:0]  ch;
    reg [1:0]  node;
    reg [31:0] quad;
    reg [7:0]  stat;
    reg [11:0] lat;
    reg [15:0] rid;
    reg [127:0] frozen_observed_payload;
    integer frozen_line, frozen_digit;

    initial begin
        #100 rst_n = 1;

        // ── Boot hydration line ('H'), consumed before any query ──────
        recv_line(ch, node, quad, stat, lat, rid);
        if (ch !== "H") bad("expected 'H' boot-hydration line first");
        else             ok("received 'H' boot-hydration line");

        if (FROZEN_CASE) begin
            if (!DIAGNOSTIC) bad("frozen case requires diagnostic output");
            send_query_line(6949, 0, 16056, 0, 21000, 0, 19412, 0);
            for (frozen_line = 1; frozen_line <= 11; frozen_line = frozen_line + 1) begin
                recv_line(ch, node, quad, stat, lat, rid);
                frozen_observed_payload = 128'd0;
                for (frozen_digit = 6; frozen_digit <= 37; frozen_digit = frozen_digit + 1)
                    frozen_observed_payload = {frozen_observed_payload[123:0],
                                               ascii_to_nibble(resp_bytes[frozen_digit])};
                if (frozen_observed_payload !== frozen_diag_payload(frozen_line))
                    bad("frozen diagnostic payload differs from oracle");
                else ok("frozen diagnostic payload matches oracle");
            end
            recv_line(ch, node, quad, stat, lat, rid);
            if (ch !== "D" || node !== 2'd2 || quad !== 32'h03C58E94)
                bad("frozen terminal result differs from oracle");
            else ok("frozen terminal result matches oracle");
            if (accepted_queries !== 1 || fresh_completions !== 1)
                bad("frozen query did not produce exactly one fresh completion");
            else ok("frozen query produced exactly one fresh completion");
            $display("%0d checks, %0d passed, %0d failed", pass + fail, pass, fail);
            if (fail == 0) $display("PASS"); else $display("FAIL");
            $finish;
        end

        // Every (best_node, best_quadrance) pair below is the same oracle
        // output spu4_som_edge_full_chain_tb.v checks against
        // find_bmu_edge() -- see software/tests/test_spu4_som_edge_oracle.py.
        run_uart_query("exact match node 0",           100, 0,   0, 0,   0, 0,   0, 0,    2'd0, 32'd0);
        run_uart_query("exact match node 1",             0, 0,   0, 40,  0, 0,   0, 0,    2'd1, 32'd0);
        run_uart_query("exact match node 2",           -30, 0, -30, 0,  60, 0,   0, 0,    2'd2, 32'd0);
        run_uart_query("exact match node 3",             0, 0,   0, 0,   0, 0,  50, 50,   2'd3, 32'd0);
        run_uart_query("near node 1, Q-dominated delta",  0, 0,   0, 45,  0, 0,   0, 0,    2'd1, 32'd75);
        run_uart_query("negative deltas near node 2",   -40, 0, -25, 0,  55, 0,   0, 0,    2'd2, 32'd150);
        run_uart_query("exact tie node 0 / node 1",      50, 0,   0, 20,  0, 0,   0, 0,    2'd0, 32'd3700);
        run_uart_query("far from all nodes, mixed sign", -5, 5,   5, -5, -5, 5,   5, -5,   2'd1, 32'd6400);

        // ── Malformed line 1: garbage prefix (not 'Q') is silently
        // absorbed, no response line at all -- then a valid query
        // straight after proves the resync. ──────────────────────────
        send_byte("X"); send_byte("!"); send_byte("9");
        run_uart_query("resync after garbage prefix",
                        100, 0, 0, 0, 0, 0, 0, 0, 2'd0, 32'd0);

        // ── Malformed line 2: non-hex byte mid-field aborts with 'F',
        // no wrapper interaction -- then a valid query proves recovery. ─
        send_byte("Q"); send_byte("0"); send_byte("0");
        send_byte("Z");                                  // not a hex digit
        recv_line(ch, node, quad, stat, lat, rid);
        if (ch !== "F") bad("non-hex mid-field byte: expected 'F' response");
        else             ok("non-hex mid-field byte: got 'F' response");
        run_uart_query("recovery after nibble abort",
                        0, 0, 0, 40, 0, 0, 0, 0, 2'd1, 32'd0);

        // ── Malformed line 3: short line (terminator arrives before all
        // 32 nibbles) also aborts with 'F' via the same non-hex-byte
        // path, since '\n' isn't a hex digit -- then a valid query
        // proves recovery. ─────────────────────────────────────────────
        send_byte("Q"); send_byte("0"); send_byte("0");
        send_byte(8'h0A);                                 // early terminator
        recv_line(ch, node, quad, stat, lat, rid);
        if (ch !== "F") bad("short line: expected 'F' response");
        else             ok("short line: got 'F' response");
        run_uart_query("recovery after short-line abort",
                        -30, 0, -30, 0, 60, 0, 0, 0, 2'd2, 32'd0);

        if (accepted_queries !== 11) bad("expected exactly eleven accepted queries");
        else                         ok("exactly eleven queries accepted");
        if (fresh_completions !== accepted_queries)
            bad("fresh completion count differs from accepted query count");
        else ok("exactly one fresh completion recognized per accepted query");
        if (stale_done_blocks < 3)
            bad("held done was not exercised across three consecutive queries");
        else ok("held done from prior queries was blocked before re-arming");

        $display("%0d checks, %0d passed, %0d failed", pass + fail, pass, fail);
        if (fail == 0) $display("PASS");
        else            $display("FAIL");
        $finish;
    end

    initial begin
        #(20_000_000 * (BENCH25 ? 60 : 1));
        $display("FAIL: timeout");
        $display("FAIL");
        $finish;
    end

endmodule
