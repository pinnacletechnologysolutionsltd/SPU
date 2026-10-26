// Four-lane palette-pair commit and winner selection.
// Palette bytes follow the primitive order of the T1r scene packet.
// CC0 1.0 Universal.

module spu_material_palette_select4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        activate_scene,
    input  wire [31:0] candidate_palettes,
    input  wire [1:0]  winner_id,
    output reg  [31:0] active_palettes,
    output reg  [7:0]  selected_palette
);

    // Lane 0 is [7:0], through lane 3 in [31:24].
    function [7:0] select_palette;
        input [31:0] palettes;
        input [1:0] id;
        begin
            case (id)
                2'd0: select_palette = palettes[7:0];
                2'd1: select_palette = palettes[15:8];
                2'd2: select_palette = palettes[23:16];
                default: select_palette = palettes[31:24];
            endcase
        end
    endfunction

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            active_palettes <= 32'd0;
            selected_palette <= 8'd0;
        end else if (activate_scene) begin
            active_palettes <= candidate_palettes;
            selected_palette <= select_palette(candidate_palettes, winner_id);
        end else begin
            selected_palette <= select_palette(active_palettes, winner_id);
        end
    end

endmodule
