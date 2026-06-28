// Minimal southbridge blinky — same module name, same CST, no core
module spu13_tang25k_southbridge_top (
    input  wire        sys_clk,
    output wire [2:0]  led,
    input  wire        spi_cs_n,
    input  wire        spi_sck,
    input  wire        spi_mosi,
    output wire        spi_miso
);
    wire clk_50m;
    BUFG u_bufg (.I(sys_clk), .O(clk_50m));

    reg [25:0] cnt = 0;
    always @(posedge clk_50m) cnt <= cnt + 1;
    assign led[0] = ~cnt[24];
    assign led[1] = ~cnt[23];
    assign led[2] = ~cnt[22];
    assign spi_miso = 1'b0;
endmodule

(* blackbox *)
module BUFG (input wire I, output wire O);
endmodule
