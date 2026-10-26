// spu_a7_uart_loopback_tb.v — bench for the T1 gate-step-1 F3 loopback probe.
//
// The probe's whole job on silicon is to make three outcomes distinguishable:
// no banner / banner but no echo / banner and echo. This bench must therefore
// prove that the banner and the echo are INDEPENDENT -- a probe that emitted
// the banner only when a byte arrived, or echoed spontaneously, would report
// a working RX path that does not exist.
//
// Small timing parameters: BIT_CYC = 8 rather than 434, so a byte is tens of
// cycles instead of tens of thousands. The behaviour under test is the
// sequencing, not the divisor.
//
// CC0 1.0 Universal.

`timescale 1ns/1ps

module spu_a7_uart_loopback_tb;

    localparam CLK_HZ     = 1_000_000;
    localparam BAUD       = 125_000;      // BIT_CYC = 8
    localparam BIT_CYC    = CLK_HZ / BAUD;
    localparam BANNER_DIV = 4000;

    reg clk = 1'b0, rst_n = 1'b0, rx = 1'b1;
    always #1 clk = ~clk;
    wire tx;

    spu_a7_uart_loopback_top #(
        .CLK_HZ(CLK_HZ), .BAUD(BAUD), .BANNER_DIV(BANNER_DIV),
        .DEBOUNCE_BITS(4)
    ) dut (.sys_clk(clk), .rst_n(rst_n), .uart_rx(rx), .uart_tx(tx));

    integer errors = 0;

    // ── Receive whatever the DUT transmits ───────────────────────────────
    reg [7:0] seen [0:255];
    integer   n_seen = 0;

    task capture_bytes(input integer max_cycles);
        integer c, b;
        reg [7:0] acc;
        begin
            c = 0;
            while (c < max_cycles) begin
                if (tx == 1'b0) begin                     // start bit
                    repeat (BIT_CYC + BIT_CYC/2) @(posedge clk);
                    acc = 8'd0;
                    for (b = 0; b < 8; b = b + 1) begin
                        acc[b] = tx;
                        repeat (BIT_CYC) @(posedge clk);
                    end
                    seen[n_seen] = acc;
                    n_seen = n_seen + 1;
                    c = c + 10 * BIT_CYC;
                end else begin
                    @(posedge clk);
                    c = c + 1;
                end
            end
        end
    endtask

    task send_byte(input [7:0] v);
        integer b;
        begin
            rx = 1'b0;                                    // start
            repeat (BIT_CYC) @(posedge clk);
            for (b = 0; b < 8; b = b + 1) begin
                rx = v[b];
                repeat (BIT_CYC) @(posedge clk);
            end
            rx = 1'b1;                                    // stop
            repeat (BIT_CYC) @(posedge clk);
        end
    endtask

    integer i, found;

    initial begin
        repeat (8) @(posedge clk);
        rst_n = 1'b1;
        repeat (40) @(posedge clk);   // let the debounce release

        // ── CONTROL 1: the banner appears with NO input at all. ──────────
        // This is what makes "no banner" a usable diagnosis on the bench.
        // Without it, a dead TX and a dead RX would look identical.
        n_seen = 0;
        // The window must span the banner PERIOD plus the banner's own
        // transmission time: 16 bytes x 10 bits x BIT_CYC cycles. Sizing it
        // to the period alone truncates the banner mid-way, and the tail
        // then shows up in the next window looking like spontaneous output.
        capture_bytes(BANNER_DIV + 16 * 10 * BIT_CYC + 20 * BIT_CYC);
        $display("CONTROL 1 -- banner with rx held idle: %0d bytes seen", n_seen);
        if (n_seen < 16) begin
            $display("FAIL: expected the 16-byte banner, saw %0d", n_seen);
            errors = errors + 1;
        end else begin
            $write("   banner text: \"");
            for (i = 0; i < 14; i = i + 1) $write("%0s", seen[i]);
            $display("\"");
            if (seen[0] !== "U" || seen[8] !== ":" || seen[14] !== 8'h0D) begin
                $display("FAIL: banner content wrong");
                errors = errors + 1;
            end
        end

        // ── CONTROL 2: NOTHING is emitted when nothing is sent. ──────────
        // The one that matters. A probe echoing spontaneously would report a
        // working receive path that does not exist. Run immediately after
        // CONTROL 1, so the banner has just finished and its period has
        // restarted -- this window is deliberately far shorter than
        // BANNER_DIV, so the line must be silent throughout.
        n_seen = 0;
        capture_bytes(BANNER_DIV / 4);
        $display("CONTROL 2 -- bytes emitted with rx idle, inside one banner period: %0d", n_seen);
        if (n_seen != 0) begin
            $display("FAIL: %0d spontaneous bytes -- echo is not caused by input", n_seen);
            errors = errors + 1;
        end

        // ── The actual test: a sent byte comes back. ─────────────────────
        n_seen = 0;
        fork
            send_byte(8'h5A);
            capture_bytes(30 * BIT_CYC);
        join
        found = 0;
        for (i = 0; i < n_seen; i = i + 1) if (seen[i] === 8'h5A) found = 1;
        $display("TEST -- sent 0x5A, echoed: %0s (%0d bytes seen)",
                 found ? "YES" : "NO", n_seen);
        if (!found) begin
            $display("FAIL: 0x5A was not echoed");
            errors = errors + 1;
        end

        // A second, different byte -- so a stuck echo register cannot pass.
        n_seen = 0;
        fork
            send_byte(8'hA5);
            capture_bytes(30 * BIT_CYC);
        join
        found = 0;
        for (i = 0; i < n_seen; i = i + 1) if (seen[i] === 8'hA5) found = 1;
        $display("TEST -- sent 0xA5, echoed: %0s", found ? "YES" : "NO");
        if (!found) begin
            $display("FAIL: 0xA5 was not echoed (a stuck echo register would do this)");
            errors = errors + 1;
        end

        if (errors == 0)
            $display("PASS: banner is independent of input, and input is echoed");
        else
            $display("FAILED with %0d error(s)", errors);
        $finish;
    end

endmodule
