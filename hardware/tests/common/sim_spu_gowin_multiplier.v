module spu_gowin_multiplier #(parameter DEVICE = "GW5A") (
    input clk, input [17:0] a, input [17:0] b, output [35:0] p
);
    reg [35:0] p_reg;
    always @(posedge clk) p_reg <= a * b;
    assign p = p_reg;
endmodule
