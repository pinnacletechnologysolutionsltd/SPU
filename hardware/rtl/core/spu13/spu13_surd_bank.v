// Eight explicit-denominator tuples, independent of scalar and Quadray state.
module spu13_surd_bank (
    input wire clk,rst,
    input wire [2:0] ra,rb,wa,
    output wire [191:0] qa,qb,
    output wire valid_a,valid_b,
    input wire we, input wire [191:0] wd
);
    reg [191:0] tuples [0:7];
    reg [7:0] initialized;
    integer i;
    assign qa=tuples[ra]; assign qb=tuples[rb];
    assign valid_a=initialized[ra]; assign valid_b=initialized[rb];
    always @(posedge clk) begin
        if(rst) begin
            initialized<=0;
            for(i=0;i<8;i=i+1) tuples[i]<={64'd1,128'd0};
        end else if(we) begin tuples[wa]<=wd; initialized[wa]<=1; end
    end
endmodule
