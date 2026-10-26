// Four-lane predicate-selector commit and winner selection.
// Low nibble selects U bit; high nibble selects V bit.
// CC0 1.0 Universal.

module spu_material_predicate_select4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        activate_scene,
    input  wire [31:0] candidate_selectors,
    input  wire [1:0]  winner_id,
    output reg  [31:0] active_selectors,
    output reg  [7:0]  selected_selector
);

    // Each byte follows the primitive order of the scene packet:
    //
    //   candidate_selectors[ 7: 0] = primitive 0
    //   candidate_selectors[15: 8] = primitive 1
    //   candidate_selectors[23:16] = primitive 2
    //   candidate_selectors[31:24] = primitive 3
    //
    // For every byte, bits [3:0] select U and bits [7:4] select V.
    // On the activation edge use candidate bytes, because active_selectors
    // updates through the same nonblocking assignment. On every later edge
    // use the active tuple. This is the same edge and winner ID as U/V.
    function [7:0] select_byte;
        input [31:0] selectors;
        input [1:0] id;
        begin
            case (id)
                2'd0: select_byte = selectors[7:0];
                2'd1: select_byte = selectors[15:8];
                2'd2: select_byte = selectors[23:16];
                default: select_byte = selectors[31:24];
            endcase
        end
    endfunction

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            active_selectors <= 32'd0;
            selected_selector <= 8'd0;
        end else if (activate_scene) begin
            active_selectors <= candidate_selectors;
            selected_selector <= select_byte(candidate_selectors, winner_id);
        end else begin
            selected_selector <= select_byte(active_selectors, winner_id);
        end
    end

endmodule
