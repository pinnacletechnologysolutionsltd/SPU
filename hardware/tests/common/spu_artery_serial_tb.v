// spu_artery_serial_tb.v — testbench for spu_artery_serial TX+RX pair
// Connects TX.tx directly to RX.rx (same-clock loopback).
// Tests: normal frames, back-to-back transmission, zero chord.
`timescale 1ns/1ps

module spu_artery_serial_tb;

    reg        clk, rst_n;
    reg [2:0]  t_node_id;
    reg [63:0] t_chord;
    reg        t_send;
    wire       tx_line;
    wire       tx_busy;
    wire [2:0]  rx_node_id;
    wire [63:0] rx_chord;
    wire        rx_valid, rx_error;

    spu_artery_serial_tx #(.CLK_PER_BIT(26)) u_tx (
        .clk(clk), .rst_n(rst_n),
        .node_id(t_node_id), .chord(t_chord), .send(t_send),
        .tx(tx_line), .busy(tx_busy)
    );

    spu_artery_serial_rx #(.CLK_PER_BIT(26)) u_rx (
        .clk(clk), .rst_n(rst_n),
        .rx(tx_line),
        .rx_node_id(rx_node_id), .rx_chord(rx_chord),
        .rx_valid(rx_valid), .rx_error(rx_error)
    );

    // 24 MHz clock
    initial clk = 0;
    always #20.833 clk = ~clk;

    // ---- Result capture registers ----
    integer   pass_count, fail_count;
    reg       rx_flag_valid, rx_flag_error;
    reg [2:0]  cap_node;
    reg [63:0] cap_chord;

    always @(posedge clk) begin
        if (rx_valid) begin
            rx_flag_valid <= 1'b1;
            cap_node      <= rx_node_id;
            cap_chord     <= rx_chord;
        end
        if (rx_error) rx_flag_error <= 1'b1;
    end

    // Wait up to 4000 cycles for an RX event
    task wait_rx;
        integer n;
        begin
            n = 0;
            while (!rx_flag_valid && !rx_flag_error && n < 4000) begin
                @(posedge clk);
                n = n + 1;
            end
        end
    endtask

    // Send one frame and wait for RX to finish
    task send_frame;
        input [2:0]  nid;
        input [63:0] ch;
        begin
            rx_flag_valid = 1'b0;
            rx_flag_error = 1'b0;
            t_node_id = nid;
            t_chord   = ch;
            @(posedge clk); #1;
            t_send = 1'b1;
            @(posedge clk); #1;
            t_send = 1'b0;
            wait_rx;
            // Also drain busy to avoid overlap with next test
            while (tx_busy) @(posedge clk);
            @(posedge clk);
        end
    endtask

    // Check and log result
    task check;
        input [2:0]  exp_node;
        input [63:0] exp_chord;
        input [63:0] test_num;
        begin
            if (rx_flag_valid && !rx_flag_error &&
                cap_node == exp_node && cap_chord == exp_chord) begin
                $display("T%0d PASS: node=%0d chord=%016h",
                    test_num, exp_node, exp_chord);
                pass_count = pass_count + 1;
            end else begin
                $display("T%0d FAIL: valid=%b error=%b got node=%0d chord=%016h  exp node=%0d chord=%016h",
                    test_num, rx_flag_valid, rx_flag_error,
                    cap_node, cap_chord, exp_node, exp_chord);
                fail_count = fail_count + 1;
            end
        end
    endtask

    initial begin
        rst_n = 0; t_send = 0; t_node_id = 0; t_chord = 0;
        pass_count = 0; fail_count = 0;
        rx_flag_valid = 0; rx_flag_error = 0;
        cap_node = 0; cap_chord = 0;
        #200; rst_n = 1; #200;

        // T1: standard frame
        send_frame(3'd3, 64'hDEAD_BEEF_CAFE_BABE);
        check(3'd3, 64'hDEAD_BEEF_CAFE_BABE, 1);

        // T2: max node_id, all-F chord
        send_frame(3'd7, 64'hFFFF_FFFF_FFFF_FFFF);
        check(3'd7, 64'hFFFF_FFFF_FFFF_FFFF, 2);

        // T3: zero chord (all bytes after 0xAA / node are 0)
        send_frame(3'd0, 64'h0000_0000_0000_0000);
        check(3'd0, 64'h0000_0000_0000_0000, 3);

        // T4: node_id=1, arbitrary chord
        send_frame(3'd1, 64'h0123_4567_89AB_CDEF);
        check(3'd1, 64'h0123_4567_89AB_CDEF, 4);

        if (fail_count == 0)
            $display("PASS");
        else
            $display("FAIL (%0d failures)", fail_count);
        $finish;
    end

    // Safety timeout: 4 frames × 3000 cycles + margin
    initial #1000000 begin $display("FAIL (timeout)"); $finish; end

endmodule
