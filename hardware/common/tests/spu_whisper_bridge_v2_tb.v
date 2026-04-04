// spu_whisper_bridge_v2_tb.v — tests for spu_whisper_bridge v2.0
// Tests: normal Whisper 4-byte packet, full 13-axis snap dump, snap_busy flag
`timescale 1ns/1ps

module spu_whisper_bridge_v2_tb;

    reg        clk, rst_n;
    reg [12:0] whisper_frame;
    reg        strike_pulse, snap_req;
    reg [831:0] manifold_state;

    wire [7:0]  uart_tx_byte;
    wire        uart_tx_en;
    wire        snap_busy;

    spu_whisper_bridge dut (
        .clk(clk), .rst_n(rst_n),
        .whisper_frame(whisper_frame),
        .strike_pulse(strike_pulse),
        .snap_req(snap_req),
        .manifold_state(manifold_state),
        .uart_tx_byte(uart_tx_byte),
        .uart_tx_en(uart_tx_en),
        .snap_busy(snap_busy)
    );

    always #20.833 clk = ~clk;

    integer fail = 0;

    // Collect N bytes emitted while uart_tx_en pulses
    reg [831:0] collect_buf;
    task collect_bytes;
        input  integer n;
        integer        i, timeout;
        begin
            collect_buf = 0;
            for (i = 0; i < n; i = i + 1) begin
                timeout = 0;
                while (!uart_tx_en && timeout < 100000) begin
                    @(posedge clk); timeout = timeout + 1;
                end
                if (!uart_tx_en) begin
                    $display("FAIL: byte %0d timeout", i);
                    fail = fail + 1;
                end else begin
                    collect_buf = (collect_buf << 8) | uart_tx_byte;
                end
                @(posedge clk); #1;
            end
        end
    endtask

    // ── Whisper normal packet test ─────────────────────────────────────────
    task test_normal_packet;
        input [12:0] frame;
        reg [7:0]    b0, b1, b2, b3;
        begin
            whisper_frame = frame;
            @(posedge clk); #1;
            strike_pulse = 1; @(posedge clk); #1; strike_pulse = 0;
            collect_bytes(4);
            b0 = collect_buf[31:24]; b1 = collect_buf[23:16];
            b2 = collect_buf[15:8];  b3 = collect_buf[7:0];
            if (b0 === 8'hAA &&
                b1 === {3'b0, frame[12:8]} &&
                b2 === frame[7:0] &&
                b3 === (b1 ^ b2)) begin
                $display("PASS normal_packet: [%02h %02h %02h %02h]", b0, b1, b2, b3);
            end else begin
                $display("FAIL normal_packet: [%02h %02h %02h %02h]", b0, b1, b2, b3);
                fail = fail + 1;
            end
        end
    endtask

    integer i;
    reg [831:0] snap_buf;
    reg [7:0]   snap_bytes [0:103];
    reg [7:0]   xor_check;

    initial begin
        clk = 0; rst_n = 0;
        strike_pulse = 0; snap_req = 0;
        whisper_frame = 13'h0;
        manifold_state = 832'h0;
        #200; rst_n = 1; #100;

        // Build a recognisable manifold: axis N gets A = N*0x1000, B = N*0x0100
        begin : build_manifest
            integer n;
            for (n = 0; n < 13; n = n + 1) begin
                manifold_state[n*64+63 -: 32] = n * 32'h0000_1000;
                manifold_state[n*64+31 -: 32] = n * 32'h0000_0100;
            end
        end

        // --- T1: Normal Whisper frame ---
        test_normal_packet(13'h01A5);

        // --- T2: snap_busy low when idle ---
        @(posedge clk); #1;
        if (snap_busy === 1'b0)
            $display("PASS T2: snap_busy=0 in idle");
        else begin
            $display("FAIL T2: snap_busy should be 0");
            fail = fail + 1;
        end

        // --- T3: Full snap dump — collect 13 × 8 = 104 bytes ---
        @(posedge clk); #1;
        snap_req = 1; @(posedge clk); #1; snap_req = 0;

        // snap_busy should rise on the cycle after snap_req
        if (snap_busy === 1'b1)
            $display("PASS T3a: snap_busy asserted");
        else begin
            $display("FAIL T3a: snap_busy not asserted");
            fail = fail + 1;
        end

        // Collect all 104 bytes one at a time
        for (i = 0; i < 104; i = i + 1) begin : collect_snap
            integer timeout;
            timeout = 0;
            while (!uart_tx_en && timeout < 200000) begin
                @(posedge clk); timeout = timeout + 1;
            end
            if (!uart_tx_en) begin
                $display("FAIL T3b: snap byte %0d timeout", i);
                fail = fail + 1;
            end else
                snap_bytes[i] = uart_tx_byte;
            @(posedge clk); #1;
        end

        // Verify packet structure for each axis
        begin : verify_snap
            integer ax;
            reg [7:0] crc_check;
            reg [7:0] exp_A_hi, exp_A_lo, exp_B_hi, exp_B_lo;
            integer   ok;
            ok = 1;
            for (ax = 0; ax < 13; ax = ax + 1) begin
                // XOR all 8 bytes of this packet — must equal 0
                crc_check = snap_bytes[ax*8+0] ^ snap_bytes[ax*8+1] ^
                            snap_bytes[ax*8+2] ^ snap_bytes[ax*8+3] ^
                            snap_bytes[ax*8+4] ^ snap_bytes[ax*8+5] ^
                            snap_bytes[ax*8+6] ^ snap_bytes[ax*8+7];
                if (crc_check !== 8'h00) begin
                    $display("FAIL T3c: axis %0d CRC error (XOR=%02h)", ax, crc_check);
                    fail = fail + 1; ok = 0;
                end
                // Header must be 0xFE
                if (snap_bytes[ax*8+0] !== 8'hFE) begin
                    $display("FAIL T3d: axis %0d bad header %02h", ax, snap_bytes[ax*8+0]);
                    fail = fail + 1; ok = 0;
                end
                // Axis index byte
                if (snap_bytes[ax*8+1] !== ax[7:0]) begin
                    $display("FAIL T3e: axis %0d idx mismatch %02h", ax, snap_bytes[ax*8+1]);
                    fail = fail + 1; ok = 0;
                end
            end
            if (ok) $display("PASS T3: all 13 snap packets valid (header + CRC)");
        end

        // --- T4: snap_busy deasserts after dump ---
        @(posedge clk); #1;
        if (snap_busy === 1'b0)
            $display("PASS T4: snap_busy cleared after full dump");
        else begin
            $display("FAIL T4: snap_busy still set after dump");
            fail = fail + 1;
        end

        // --- T5: Normal frame still works after snap ---
        test_normal_packet(13'h07FF);

        if (fail == 0)
            $display("PASS");
        else
            $display("FAIL (%0d failures)", fail);
        $finish;
    end

    initial #50000000 begin $display("FAIL (timeout)"); $finish; end

endmodule
