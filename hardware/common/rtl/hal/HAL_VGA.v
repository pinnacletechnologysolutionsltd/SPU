// HAL_VGA.v — VGA PMOD output driver
// Digilent PmodVGA layout: R[3:0], G[3:0], B[3:0], HSYNC, VSYNC (14 pins).
// Blanks RGB to zero outside the active display area.
// CC0 1.0 Universal.

module HAL_VGA (
    input  wire [3:0] r,
    input  wire [3:0] g,
    input  wire [3:0] b,
    input  wire       hsync,
    input  wire       vsync,
    input  wire       active,

    output wire [3:0] vga_r,
    output wire [3:0] vga_g,
    output wire [3:0] vga_b,
    output wire       vga_hsync,
    output wire       vga_vsync
);

    assign vga_r     = active ? r : 4'h0;
    assign vga_g     = active ? g : 4'h0;
    assign vga_b     = active ? b : 4'h0;
    assign vga_hsync = hsync;
    assign vga_vsync = vsync;

endmodule
