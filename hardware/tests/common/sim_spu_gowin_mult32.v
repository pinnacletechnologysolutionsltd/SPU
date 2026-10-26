module spu_gowin_mult32 #(parameter DEVICE = "GW5A") (
    input clk, input reset, input [31:0] a, input [31:0] b, output [63:0] p
);
    reg [63:0] p_reg;
    always @(posedge clk or posedge reset) begin
        if (reset) p_reg <= 64'd0;
        else p_reg <= a * b;
    end
    assign p = p_reg;
endmodule
