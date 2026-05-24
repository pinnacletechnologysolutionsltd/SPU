`timescale 1ns / 1ps

module spu_tang25k_blink #(
    parameter CLK_FREQ = 50000000 // 50 MHz clock
)(
    input  wire clk,
    output reg  led = 1'b1 // Explicitly initialized to OFF for active-low LED
);

    reg [24:0] counter = 0;
    localparam MAX_COUNT = CLK_FREQ / 2; // Toggle every 0.5 seconds

    always @(posedge clk) begin
        if (counter == MAX_COUNT - 1) begin
            counter <= 0;
            led <= ~led; // Toggle LED
        end else begin
            counter <= counter + 1;
        end
    end

endmodule
