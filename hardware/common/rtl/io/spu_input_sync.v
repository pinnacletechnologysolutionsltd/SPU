// spu_input_sync.v — Physical Input Synchronizer  v1.1
// 2-stage D-FF metastability eliminator for async PMOD/GPIO inputs.
// One instance per physical signal line.

`default_nettype none

module spu_input_sync (
    input  wire clk,
    input  wire reset,
    input  wire async_in,
    output reg  sync_out
);

    reg stage1;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            stage1   <= 1'b0;
            sync_out <= 1'b0;
        end else begin
            stage1   <= async_in;
            sync_out <= stage1;
        end
    end

endmodule
`default_nettype wire
