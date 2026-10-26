module spu_tang_top (
    input  wire        clk_in,
    input  wire        rst_n,
    output wire        led_out,
    output wire        smoke_ok,
    output wire        uart_tx
);
    // BUFG was here, but it's not needed/recognized in some OSS flows
    wire clk = clk_in;
    
    // Explicitly drive GSR high (inactive) using the primitive
    GSR i_gsr (.GSRI(1'b1));

    // Reset logic: use rst_n (active-low)
    wire reset = ~rst_n;

    // Counter for heartbeat (~1Hz given 50MHz clock)
    reg [25:0] counter = 0;
    always @(posedge clk or posedge reset) begin
        if (reset)
            counter <= 0;
        else
            counter <= counter + 1'b1;
    end

    // Map heartbeat to led_out (active-low, so 0 is ON)
    assign led_out = ~counter[25];
    assign smoke_ok = 1'b1; // Keep LED1 off for now
    assign uart_tx = counter[25];
endmodule
