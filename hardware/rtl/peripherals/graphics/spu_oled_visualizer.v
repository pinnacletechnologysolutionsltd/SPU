// SPU-13 OLED Visualizer: Dual Hemisphere (v3.4.35)
// Implementation: Geometry (Left) and Scrolling Metabolism (Right).
// Objective: Visualize 'Deep Resonance' as a flat bit-perfect line.
// Result: 128x64 dual-display for SSD1306.

module spu_oled_visualizer (
    input  wire        clk,
    input  wire        reset,
    input  wire [31:0] manifold_a,
    input  wire [15:0] microwatts,
    output reg  [7:0]  pixel_data,
    output reg  [9:0]  pixel_idx,    // 0-1023 bytes
    output reg         frame_sync
);

    // Internal Page/Column Mapping
    wire [2:0] page;
    assign page = pixel_idx[9:7];
    wire [6:0] col;
    assign col = pixel_idx[6:0];

    // Strip Chart History (64 columns)
    reg [5:0] power_history [0:63];
    reg [5:0] write_ptr;
    reg [15:0] update_timer;

    // Power Mapping: 0-63 uW -> 0-63 Pixels (Vertical)
    wire [5:0] current_power;
    assign current_power = (microwatts > 16'd63) ? 6'd63 : microwatts[5:0];

    // Combinational helpers for right hemisphere indexing
    wire [5:0] h_idx;
    assign h_idx = col[5:0] + write_ptr;
    wire [5:0] p_val;
    assign p_val = power_history[h_idx];

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            write_ptr <= 0; update_timer <= 0;
            pixel_idx <= 0; frame_sync <= 0;
            pixel_data <= 8'h00;
        end else begin
            // 1. Telemetry Update (every ~100ms)
            if (update_timer == 16'hFFFF) begin
                power_history[write_ptr] <= current_power;
                write_ptr <= write_ptr + 1;
                update_timer <= 0;
            end else begin
                update_timer <= update_timer + 1;
            end

            // 2. Data Sequencing
            pixel_idx <= pixel_idx + 1;
            frame_sync <= (pixel_idx == 1023);

            // 3. Pixel Mapping (SSD1306 Horizontal Mode)
            if (col < 64) begin
                // LEFT HEMISPHERE: Geometry (Tetrahedral String)
                if (page == col[5:3])
                    pixel_data <= (8'h01 << col[2:0]);
                else
                    pixel_data <= 8'h00;
            end else begin
                // RIGHT HEMISPHERE: Metabolism (Scrolling Line Chart)
                if (p_val[5:3] == page)
                    pixel_data <= (8'h01 << p_val[2:0]);
                else
                    pixel_data <= 8'h00;
            end
        end
    end

endmodule
