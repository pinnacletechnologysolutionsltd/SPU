// spu_vram_controller.v — Rational VRAM bridge stub (Simulation model)
// Buffers pixel writes and provides streaming read to the display HAL.
// Synthesis target: ECP5/GW2A SDRAM. Simulation: BRAM model.

module spu_vram_controller #(
    parameter RES_X = 240,
    parameter RES_Y = 240
)(
    input  wire        clk,
    input  wire        reset,

    // Fragment write path (from rasterizer)
    input  wire        pixel_inside,
    input  wire [15:0] lambda0, lambda1, lambda2,
    input  wire [15:0] interpolated_energy,
    input  wire [15:0] wr_x, wr_y,
    input  wire [15:0] wr_z,
    input  wire        z_test_pass,

    // Read path (to display HAL / VGA)
    input  wire        rd_clk,
    input  wire [15:0] rd_x, rd_y,
    output reg  [15:0] out_qa, out_qb, out_qc, out_qd,
    output reg  [15:0] out_energy,

    // SDRAM interface (passthrough stub)
    output wire [24:0] sdram_addr,
    output wire [15:0] sdram_wr_data,
    input  wire [15:0] sdram_rd_data,
    output wire        sdram_wr_en,
    input  wire        sdram_ready,

    output wire        frame_done
);
    // Sim-only flat BRAM: store energy per pixel
    reg [15:0] fb_energy [0:RES_X*RES_Y-1];

    wire [15:0] addr_w = wr_y * RES_X + wr_x;
    wire [15:0] addr_r = rd_y * RES_X + rd_x;

    integer ii;
    initial for (ii = 0; ii < RES_X*RES_Y; ii = ii+1) fb_energy[ii] = 0;

    always @(posedge clk) begin
        if (pixel_inside && z_test_pass && wr_x < RES_X && wr_y < RES_Y)
            fb_energy[addr_w] <= interpolated_energy;
    end

    always @(posedge rd_clk) begin
        out_energy <= (rd_x < RES_X && rd_y < RES_Y) ? fb_energy[addr_r] : 16'h0;
        out_qa     <= lambda0;
        out_qb     <= lambda1;
        out_qc     <= lambda2;
        out_qd     <= 16'h0;
    end

    assign sdram_addr    = 25'h0;
    assign sdram_wr_data = 16'h0;
    assign sdram_wr_en   = 1'b0;
    assign frame_done    = 1'b0;
endmodule
