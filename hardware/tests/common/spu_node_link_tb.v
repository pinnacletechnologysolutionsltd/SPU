// spu_node_link_tb.v — satellite sync protocol tests
// Tests: TX frame packing, Davis XOR tag, consecutive failure counter,
//        sync_alert threshold, snap_alert clears counter
`timescale 1ns/1ps

module spu_node_link_tb;

    reg        clk, rst_n;
    reg [23:0] prime_anchor_in;
    reg [15:0] rx_frame;
    wire [31:0] tx_frame;
    wire        sync_alert;
    wire [7:0]  satellite_dissonance;

    spu_node_link #(.SYNC_FAIL_THRESH(3)) dut (
        .clk(clk), .rst_n(rst_n),
        .prime_anchor_in(prime_anchor_in),
        .rx_frame(rx_frame),
        .tx_frame(tx_frame),
        .sync_alert(sync_alert),
        .satellite_dissonance(satellite_dissonance)
    );

    always #20.833 clk = ~clk;
    integer fail = 0;

    // send one rx frame, wait one clock for registered output
    task send_rx;
        input [15:0] frame;
        begin
            rx_frame = frame;
            @(posedge clk); #1;
        end
    endtask

    initial begin
        clk = 0; rst_n = 0;
        prime_anchor_in = 24'hA1B2C3;
        rx_frame = 16'h8000;  // snap_alert=1 during warmup — keeps fail_cnt=0
        #200; rst_n = 1; #50;
        // One warmup clock with snap_alert=1 to confirm counter is zero
        @(posedge clk); #1;

        // --- T1: TX frame packing and Davis XOR tag ---
        // anchor=0xA1B2C3 → top16=0xA1B2, hi=0xA1, lo=0xB2, tag=0xA1^0xB2=0x13
        // tx_frame = {0xA1B2, 0x13, 0x00} = 0xA1B2_1300
        @(posedge clk); #1;
        begin : t1
            reg [7:0] b3, b2, b1, b0, xor_all;
            b3 = tx_frame[31:24]; b2 = tx_frame[23:16];
            b1 = tx_frame[15:8];  b0 = tx_frame[7:0];
            xor_all = b3 ^ b2 ^ b1 ^ b0;
            if (b3 === 8'hA1 && b2 === 8'hB2 && xor_all === 8'h00) begin
                $display("PASS T1: TX frame correct, XOR=%02h (anchor hi=%02h lo=%02h tag=%02h)",
                    xor_all, b3, b2, b1);
            end else begin
                $display("FAIL T1: tx=%08h xor=%02h (exp A1B21300)", tx_frame, xor_all);
                fail = fail + 1;
            end
        end

        // --- T2: satellite_dissonance extracted from rx_frame[14:7] ---
        rx_frame = 16'b0_10101010_0000000;  // dissonance = 0xAA, snap_alert=0
        @(posedge clk); #1;
        if (satellite_dissonance === 8'hAA) begin
            $display("PASS T2: dissonance=0xAA extracted correctly");
        end else begin
            $display("FAIL T2: dissonance=%02h (exp AA)", satellite_dissonance);
            fail = fail + 1;
        end

        // --- T3: No sync_alert on first snap_alert=0 frame ---
        send_rx(16'h0000);  // snap_alert=0
        if (sync_alert === 1'b0) begin
            $display("PASS T3: no alert after 1 failure");
        end else begin
            $display("FAIL T3: premature sync_alert after 1 failure");
            fail = fail + 1;
        end

        // --- T4: sync_alert after SYNC_FAIL_THRESH=3 consecutive failures ---
        send_rx(16'h0000);  // failure 2
        send_rx(16'h0000);  // failure 3 — threshold reached
        if (sync_alert === 1'b1) begin
            $display("PASS T4: sync_alert asserted after 3 consecutive failures");
        end else begin
            $display("FAIL T4: sync_alert not asserted after 3 failures");
            fail = fail + 1;
        end

        // --- T5: snap_alert=1 clears sync_alert and counter ---
        send_rx(16'h8000);  // snap_alert=1 (bit 15)
        if (sync_alert === 1'b0) begin
            $display("PASS T5: sync_alert cleared by snap_alert=1");
        end else begin
            $display("FAIL T5: sync_alert not cleared after snap_alert=1");
            fail = fail + 1;
        end

        // --- T6: Counter resets — need 3 more failures to re-alert ---
        send_rx(16'h0000);  // failure 1 post-clear
        send_rx(16'h0000);  // failure 2
        if (sync_alert === 1'b0) begin
            $display("PASS T6: no alert after 2 failures (counter reset)");
        end else begin
            $display("FAIL T6: premature alert (counter did not reset)");
            fail = fail + 1;
        end
        send_rx(16'h0000);  // failure 3 — should alert again
        if (sync_alert === 1'b1) begin
            $display("PASS T6b: sync_alert re-asserts after 3 more failures");
        end else begin
            $display("FAIL T6b: sync_alert should have re-asserted");
            fail = fail + 1;
        end

        // --- T7: TX frame updates when anchor changes ---
        prime_anchor_in = 24'hFF0000;
        @(posedge clk); #1;
        begin : t7
            reg [7:0] b3, b2, xor_all;
            b3 = tx_frame[31:24]; b2 = tx_frame[23:16];
            xor_all = tx_frame[31:24] ^ tx_frame[23:16] ^
                      tx_frame[15:8]  ^ tx_frame[7:0];
            if (b3 === 8'hFF && b2 === 8'h00 && xor_all === 8'h00) begin
                $display("PASS T7: anchor update, XOR still 0 (hi=%02h lo=%02h)", b3, b2);
            end else begin
                $display("FAIL T7: tx=%08h xor=%02h", tx_frame, xor_all);
                fail = fail + 1;
            end
        end

        if (fail == 0)
            $display("PASS");
        else
            $display("FAIL (%0d failures)", fail);
        $finish;
    end

    initial #1000000 begin $display("FAIL (timeout)"); $finish; end

endmodule
