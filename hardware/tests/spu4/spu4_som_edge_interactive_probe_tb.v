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

module spu4_som_edge_interactive_probe_tb;

    localparam integer CLKS_PER_BIT = 8;   // small value, fast sim only

    reg clk = 0, rst_n = 0;
    reg  uart_rx_line = 1;
    wire uart_tx_line;
    wire [2:0] led;
    wire flash_sck, flash_cs, flash_mosi;
    reg  flash_miso = 0;

    spu13_tang25k_spu4_som_edge_interactive_probe #(
        .CLK_FREQ(50000000), .CLKS_PER_BIT(CLKS_PER_BIT)
    ) dut (
        .sys_clk(clk), .led(led),
        .uart_tx(uart_tx_line), .uart_rx(uart_rx_line),
        .flash_cs(flash_cs), .flash_sck(flash_sck),
        .flash_mosi(flash_mosi), .flash_miso(flash_miso)
    );

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
    task ok;  input [1023:0] m; begin $display("PASS: %0s", m); pass = pass + 1; end endtask
    task bad; input [1023:0] m; begin $display("FAIL: %0s", m); fail = fail + 1; end endtask

    // ── Mock flash: identical fixture to spu4_som_edge_full_chain_tb.v ──
    localparam integer NUM_FEATURES = 4;
    localparam integer TOTAL_BYTES  = 4 * NUM_FEATURES * 4;

    reg signed [15:0] exp_p [0:3][0:NUM_FEATURES-1];
    reg signed [15:0] exp_q [0:3][0:NUM_FEATURES-1];

    initial begin
        exp_p[0][0]=100; exp_q[0][0]=0;  exp_p[0][1]=0; exp_q[0][1]=0;
        exp_p[0][2]=0;   exp_q[0][2]=0;  exp_p[0][3]=0; exp_q[0][3]=0;
        exp_p[1][0]=0;   exp_q[1][0]=0;  exp_p[1][1]=0; exp_q[1][1]=40;
        exp_p[1][2]=0;   exp_q[1][2]=0;  exp_p[1][3]=0; exp_q[1][3]=0;
        exp_p[2][0]=-30; exp_q[2][0]=0;  exp_p[2][1]=-30; exp_q[2][1]=0;
        exp_p[2][2]=60;  exp_q[2][2]=0;  exp_p[2][3]=0;   exp_q[2][3]=0;
        exp_p[3][0]=0;   exp_q[3][0]=0;  exp_p[3][1]=0; exp_q[3][1]=0;
        exp_p[3][2]=0;   exp_q[3][2]=0;  exp_p[3][3]=50; exp_q[3][3]=50;
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
            while (resp_idx < 40 && t < 60000) begin @(posedge clk); t = t + 1; end
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
        begin
            send_query_line(p0, q0, p1, q1, p2, q2, p3, q3);
            recv_line(ch, node, quad, stat, lat, rid);
            if (ch !== "D") bad({label, ": expected 'D' response char"});
            else             ok({label, ": got 'D' response char"});
            if (node !== exp_node) bad({label, ": best_node mismatch vs oracle"});
            else                    ok({label, ": best_node matches oracle"});
            if (quad !== exp_quad) bad({label, ": best_quadrance mismatch vs oracle"});
            else                    ok({label, ": best_quadrance matches oracle exactly"});
        end
    endtask

    reg [7:0]  ch;
    reg [1:0]  node;
    reg [31:0] quad;
    reg [7:0]  stat;
    reg [11:0] lat;
    reg [15:0] rid;

    initial begin
        #100 rst_n = 1;

        // ── Boot hydration line ('H'), consumed before any query ──────
        recv_line(ch, node, quad, stat, lat, rid);
        if (ch !== "H") bad("expected 'H' boot-hydration line first");
        else             ok("received 'H' boot-hydration line");

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

        $display("%0d checks, %0d passed, %0d failed", pass + fail, pass, fail);
        if (fail == 0) $display("PASS");
        else            $display("FAIL");
        $finish;
    end

    initial begin
        #20_000_000;
        $display("FAIL: timeout");
        $display("FAIL");
        $finish;
    end

endmodule
