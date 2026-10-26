// rational_surd5_scale_manager.v - Store per-axis normalization shifts and overflow flags
// Parameterised NODES (default 13). Write interface: on write_en, write_shift and
// write_overflow are stored at write_idx.

module rational_surd5_scale_manager #(
    parameter NODES = 13
)(
    input  wire               clk,
    input  wire               rst_n,
    input  wire               write_en,
    input  wire [3:0]         write_idx,      // supports up to 16 indices
    input  wire [3:0]         write_shift,
    input  wire               write_overflow,

    output reg [NODES*4-1:0]  scale_table,
    output reg [NODES-1:0]    overflow_table
);

integer i;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        scale_table <= {NODES*4{1'b0}};
        overflow_table <= {NODES{1'b0}};
    end else begin
        if (write_en) begin
            // bounds check: only write if index < NODES
            if (write_idx < NODES) begin
                scale_table[write_idx*4 +: 4] <= write_shift;
                overflow_table[write_idx] <= write_overflow;
            end
        end
    end
end

endmodule
