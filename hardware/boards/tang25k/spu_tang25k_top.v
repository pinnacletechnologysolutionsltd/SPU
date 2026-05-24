module spu_tang25k_top (
    input  wire sys_clk,
    output wire [2:0] led,
    output wire uart_tx
);
    // 1. Simple counter for heartbeat
    reg [25:0] count = 0;
    always @(posedge sys_clk) count <= count + 1;
    assign led = ~{count[25], 1'b0, 1'b0};

    // 2. Delayed UART output
    // Give the bridge chip 2 seconds of silence (Idle High)
    // to negotiate "UART mode" before we start toggling the line.
    reg [27:0] boot_delay = 0;
    always @(posedge sys_clk) begin
        if (boot_delay < 28'd100_000_000)
            boot_delay <= boot_delay + 1;
    end
    wire tx_allowed = (boot_delay == 28'd100_000_000);

    // Toggle TX only after delay
    assign uart_tx = tx_allowed ? count[20] : 1'b1;
endmodule
