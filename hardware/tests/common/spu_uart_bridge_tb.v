// spu_uart_bridge_tb.v — Testbench for spu_uart_bridge
// Sends 6-byte frames at 921600 baud (27 MHz clock) and checks SovereignBus output.
`timescale 1ns/1ps

module spu_uart_bridge_tb;
    // 27 MHz = 37.037... ns per cycle
    parameter CLK_PERIOD_NS = 37;
    parameter BAUD = 921_600;
    parameter CLK_FREQ = 27_000_000;
    parameter BIT_NS = 1_000_000_000 / BAUD;  // ~1085 ns

    reg        clk, reset;
    reg        uart_rx;
    wire [7:0] bus_addr;
    wire [31:0] bus_data;
    wire       bus_wen, bus_ren;
    reg        bus_ready;

    // Latch single-cycle strobes so we can check them after the frame
    reg        wen_seen, ren_seen;
    reg [7:0]  wen_addr, ren_addr;
    reg [31:0] wen_data;

    spu_uart_bridge #(
        .CLK_FREQ(CLK_FREQ),
        .BAUD_RATE(BAUD)
    ) dut (
        .clk(clk), .reset(reset),
        .uart_rx(uart_rx),
        .bus_addr(bus_addr), .bus_data(bus_data),
        .bus_wen(bus_wen), .bus_ren(bus_ren),
        .bus_ready(bus_ready)
    );

    initial clk = 0;
    always #(CLK_PERIOD_NS/2) clk = ~clk;

    // Capture single-cycle strobes
    always @(posedge clk) begin
        if (bus_wen) begin wen_seen <= 1; wen_addr <= bus_addr; wen_data <= bus_data; end
        if (bus_ren) begin ren_seen <= 1; ren_addr <= bus_addr; end
    end

    integer fail = 0;

    // Send a single byte over UART (LSB first)
    task send_byte;
        input [7:0] b;
        integer k;
        begin
            // Start bit
            uart_rx = 0; #(BIT_NS);
            // Data bits
            for (k = 0; k < 8; k = k + 1) begin
                uart_rx = b[k]; #(BIT_NS);
            end
            // Stop bit
            uart_rx = 1; #(BIT_NS);
        end
    endtask

    // Send a 6-byte frame
    task send_frame;
        input [7:0] cmd, addr;
        input [31:0] data;
        begin
            send_byte(cmd);
            send_byte(addr);
            send_byte(data[7:0]);
            send_byte(data[15:8]);
            send_byte(data[23:16]);
            send_byte(data[31:24]);
        end
    endtask

    initial begin
        reset = 1; uart_rx = 1; bus_ready = 0;
        wen_seen = 0; ren_seen = 0;
        wen_addr = 0; ren_addr = 0; wen_data = 0;
        #(CLK_PERIOD_NS * 4);
        reset = 0;
        #(CLK_PERIOD_NS * 4);

        // --- Test 1: WRITE frame ---
        send_frame(8'h00, 8'h42, 32'hDEADBEEF);
        // Wait for dispatch (a few clocks after last stop bit)
        repeat(20) @(posedge clk);
        bus_ready = 1; @(posedge clk); bus_ready = 0;
        repeat(5) @(posedge clk);

        if (!wen_seen) begin
            $display("FAIL: bus_wen never asserted for WRITE frame");
            fail = fail + 1;
        end
        if (wen_addr !== 8'h42) begin
            $display("FAIL: bus_addr=%h expected=42", wen_addr);
            fail = fail + 1;
        end
        if (wen_data !== 32'hDEADBEEF) begin
            $display("FAIL: bus_data=%h expected=DEADBEEF", wen_data);
            fail = fail + 1;
        end

        wen_seen = 0; ren_seen = 0;
        #(CLK_PERIOD_NS * 20);

        // --- Test 2: READ frame ---
        send_frame(8'h80, 8'h55, 32'h0);
        repeat(20) @(posedge clk);
        bus_ready = 1; @(posedge clk); bus_ready = 0;
        repeat(5) @(posedge clk);

        if (!ren_seen) begin
            $display("FAIL: bus_ren never asserted for READ frame");
            fail = fail + 1;
        end
        if (ren_addr !== 8'h55) begin
            $display("FAIL: bus_addr=%h expected=55", ren_addr);
            fail = fail + 1;
        end

        if (fail == 0)
            $display("PASS");
        else
            $display("FAIL (%0d errors)", fail);
        $finish;
    end
endmodule
