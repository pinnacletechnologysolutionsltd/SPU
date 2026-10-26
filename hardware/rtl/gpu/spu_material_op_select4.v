// Four-lane runtime material-op commit and winner selection.
// The selected opcode is registered on the same edge as winner-selected U/V.
// CC0 1.0 Universal.

module spu_material_op_select4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        enable,
    input  wire        activate_scene,
    input  wire [31:0] candidate_ops,
    input  wire [1:0]  winner_id,
    output reg  [31:0] active_ops,
    output reg  [7:0]  selected_op
);

    // Lane packing follows the scene wire format:
    //
    //   candidate_ops[ 7: 0] = primitive 0
    //   candidate_ops[15: 8] = primitive 1
    //   candidate_ops[23:16] = primitive 2
    //   candidate_ops[31:24] = primitive 3
    //
    // Activation commits all four bytes together. The selection register uses
    // candidate_ops on that edge because active_ops changes through the same
    // nonblocking clock update. Later pixels select only from active_ops.
    function [7:0] select_op;
        input [31:0] ops;
        input [1:0] id;
        begin
            case (id)
                2'd0: select_op = ops[7:0];
                2'd1: select_op = ops[15:8];
                2'd2: select_op = ops[23:16];
                default: select_op = ops[31:24];
            endcase
        end
    endfunction

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            active_ops <= 32'd0;
            selected_op <= 8'd0;
        end else if (enable) begin
            if (activate_scene) begin
                active_ops <= candidate_ops;
                selected_op <= select_op(candidate_ops, winner_id);
            end else begin
                selected_op <= select_op(active_ops, winner_id);
            end
        end
    end

endmodule
