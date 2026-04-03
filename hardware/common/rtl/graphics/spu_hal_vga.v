// SPU-13 HAL: VGA Display Translator (v1.0)
// Objective: Standard 640x480 @ 60Hz VGA signal generation.
// This requires a ~25.175 MHz pixel clock (or 25 MHz on typical FPGAs).
// Generates a ~31.5 kHz horizontal sync line rate.

module spu_hal_vga #(
    parameter RES_X = 240,
    parameter RES_Y = 240
)(
    input  wire        clk_25mhz, // VGA Pixel Clock
    input  wire        reset,
    
    // VRAM Interface
    output wire [15:0] rd_x,
    output wire [15:0] rd_y,
    input  wire [7:0]  in_energy, // Intensity from VRAM
    input  wire [23:0] in_rgb,    // NEW: RGB color from compositor
    
    // VGA Physical Pins
    output reg         vga_hsync,
    output reg         vga_vsync,
    output reg  [3:0]  vga_r,
    output reg  [3:0]  vga_g,
    output reg  [3:0]  vga_b
);

    // --- VGA 640x480@60Hz Timing Constants ---
    localparam H_VISIBLE = 640;
    localparam H_FRONT   = 16;
    localparam H_SYNC    = 96;
    localparam H_BACK    = 48;
    localparam H_TOTAL   = 800;
    
    localparam V_VISIBLE = 480;
    localparam V_FRONT   = 10;
    localparam V_SYNC    = 2;
    localparam V_BACK    = 33;
    localparam V_TOTAL   = 525;

    // --- Counters ---
    reg [9:0] h_cnt;
    reg [9:0] v_cnt;
    
    always @(posedge clk_25mhz or posedge reset) begin
        if (reset) begin
            h_cnt <= 0;
            v_cnt <= 0;
        end else begin
            if (h_cnt == H_TOTAL - 1) begin
                h_cnt <= 0;
                if (v_cnt == V_TOTAL - 1)
                    v_cnt <= 0;
                else
                    v_cnt <= v_cnt + 1;
            end else begin
                h_cnt <= h_cnt + 1;
            end
        end
    end

    // --- Sync Generators (Active Low for 640x480) ---
    always @(posedge clk_25mhz or posedge reset) begin
        if (reset) begin
            vga_hsync <= 1'b1;
            vga_vsync <= 1'b1;
        end else begin
            vga_hsync <= ~((h_cnt >= (H_VISIBLE + H_FRONT)) && (h_cnt < (H_VISIBLE + H_FRONT + H_SYNC)));
            vga_vsync <= ~((v_cnt >= (V_VISIBLE + V_FRONT)) && (v_cnt < (V_VISIBLE + V_FRONT + V_SYNC)));
        end
    end

    // --- Active Display Region ---
    wire active = (h_cnt < H_VISIBLE) && (v_cnt < V_VISIBLE);

    // --- Resolution Scaling & Centering ---
    // The internal SPU memory is (RES_X x RES_Y), typically 240x240.
    // We pixel-double the 240x240 to 480x480 to fit the 480 vertical lines perfectly.
    // We center the 480 wide image horizontally inside the 640 wide screen.
    // X Offset = (640 - 480) / 2 = 80
    wire inside_frame = (h_cnt >= 80) && (h_cnt < 80 + (RES_X * 2)) && (v_cnt < (RES_Y * 2));
    
    assign rd_x = (h_cnt - 80) >> 1; // Divide by 2 for pixel doubling
    assign rd_y = v_cnt >> 1;        // Divide by 2 for pixel doubling

    // --- Color Output ---
    always @(posedge clk_25mhz or posedge reset) begin
        if (reset) begin
            vga_r <= 4'b0; vga_g <= 4'b0; vga_b <= 4'b0;
        end else begin
            if (active && inside_frame) begin
                // Use the input RGB, scaled for 4-bit DAC (24-bit to 12-bit)
                vga_r <= in_rgb[23:20];
                vga_g <= in_rgb[15:12];
                vga_b <= in_rgb[7:4];
            end else begin
                // Blanking / Outside bounds
                vga_r <= 4'b0; vga_g <= 4'b0; vga_b <= 4'b0;
            end
        end
    end

endmodule
