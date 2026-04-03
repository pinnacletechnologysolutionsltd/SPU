// SPU-13 Lithic Command Overlay (v1.0)
// Objective: Dynamic geometry-based command rendering.
// Logic: Rasterizes 16-bit Quadray chords onto the VGA/Gram stream.

module spu_lithic_overlay #(
    parameter RES_X = 240,
    parameter RES_Y = 240
)(
    input  wire         clk,
    input  wire         reset,
    
    // Command Interface (from Command Processor)
    input  wire [63:0]  cmd_word,
    input  wire         cmd_valid,
    
    // Scanout Interface (from VGA HAL)
    input  wire [15:0]  cur_x,
    input  wire [15:0]  cur_y,
    
    // Overlay Output
    output reg          overlay_active,
    output reg  [7:0]   overlay_intensity,
    output reg  [23:0]  overlay_rgb
);

    // Opcode definitions
    localparam OP_SPROJ_P = 8'h41; // Project Point

    // Internal State for active geometry
    reg [15:0] target_x, target_y;
    reg [7:0]  target_intensity;
    reg        dot_visible;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            dot_visible <= 0;
            target_x <= 0; target_y <= 0;
            target_intensity <= 0;
        end else if (cmd_valid) begin
            if (cmd_word[63:56] == OP_SPROJ_P) begin
                // 1. Decode Chords (Simplistic projection for now)
                // Metal: float2 pos = float2((b - c) * 0.8660254f, a - (b + c) * 0.5f);
                // RTL conversion (Fixed point):
                // x = (mag_b - mag_c) * 221 >> 8 (approximating 0.866)
                // y = mag_a - (mag_b + mag_c) >> 1
                
                // mag_a = byte 5, mag_b = byte 4, mag_c = byte 1 (approx from Metal shift logic)
                // For simplicity, we use the middle bits
                target_x <= (RES_X/2) + ($signed({1'b0, cmd_word[39:32]}) - $signed({1'b0, cmd_word[19:12]}));
                target_y <= (RES_Y/2) + $signed({1'b0, cmd_word[51:44]});
                target_intensity <= cmd_word[31:24];
                dot_visible <= 1;
            end
        end
    end

    // Rasterization: Check if curr_x/y is within target dot radius
    wire [15:0] dx = (cur_x > target_x) ? (cur_x - target_x) : (target_x - cur_x);
    wire [15:0] dy = (cur_y > target_y) ? (cur_y - target_y) : (target_y - cur_y);
    
    always @(*) begin
        if (dot_visible && (dx < 2) && (dy < 2)) begin
            overlay_active = 1;
            overlay_intensity = target_intensity;
            overlay_rgb = 24'hFFFFFF; // Sovereign White
        end else begin
            overlay_active = 0;
            overlay_intensity = 0;
            overlay_rgb = 24'h0;
        end
    end

endmodule
