// v0.3 production register bank (RF-B from RF-COMP-0, adopted 2026-11-11): LUTRAM register bank, same interface as the shared
// spu13_surd_bank. Only the 8-bit initialized mask resets (frozen contract §2 permits unspecified storage);
// tuple storage is not reset so it can map to distributed RAM. Two asynchronous reads, one synchronous write.
module psurd_bank_lutram (
    input wire clk, rst,
    input wire [2:0] ra, rb, wa,
    output wire [191:0] qa, qb,
    output wire valid_a, valid_b,
    input wire we, input wire [191:0] wd
);
    (* ram_style = "distributed" *) reg [191:0] tuples [0:7];
    reg [7:0] initialized;
    assign qa = tuples[ra]; assign qb = tuples[rb];
    assign valid_a = initialized[ra]; assign valid_b = initialized[rb];
    always @(posedge clk) if (we) tuples[wa] <= wd;
    always @(posedge clk) begin
        if (rst) initialized <= 8'd0;
        else if (we) initialized[wa] <= 1'b1;
    end
endmodule
