// Slice staging never modifies the architectural tuple before SLD succeeds.
module spu13_surd_load (
    input wire clk,rst,slice_en,commit_en,
    input wire [2:0] target,slice,
    input wire [31:0] payload,
    output wire slice_ok,commit_ok,
    output wire [191:0] tuple
);
    reg [191:0] staging;
    reg [5:0] received;
    reg [2:0] held_target;
    assign slice_ok=(received==0 || target==held_target);
    assign commit_ok=(received==6'b111111 && target==held_target && staging[191:128]!=0);
    assign tuple=staging;
    always @(posedge clk) begin
        if(rst) begin staging<=0;received<=0;held_target<=0;end
        else if(commit_en) begin received<=0;staging<=0;end
        else if(slice_en && slice_ok) begin
            staging[32*slice +:32]<=payload;
            received[slice]<=1;held_target<=target;
        end
    end
endmodule
