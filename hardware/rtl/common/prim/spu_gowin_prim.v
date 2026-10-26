// spu_gowin_prim.v — SPU primitives for Gowin devices.
// Objective: Standardize SPU multipliers and BRAM for Tang boards.

`timescale 1ns / 1ps

module spu_gowin_mult32 #(
    parameter DEVICE = "SIM"
) (
    input  wire        clk,
    input  wire        reset,
    input  wire signed [31:0] a,
    input  wire signed [31:0] b,
    output reg  signed [63:0] p
);
    generate
        if (DEVICE == "GW5A") begin : gen_gw5a_mult27x36
            // GW5A exposes 27x36 DSP blocks. The SPU-13 bring-up operands are
            // Q12 seed/Pell values that fit signed 27x36 while math is staged.
            wire [62:0] dsp_p;
            MULT27X36 u_mult (
                .DOUT(dsp_p),
                .A(a[26:0]),
                .B({{4{b[31]}}, b}),
                .D(26'd0),
                .CLK({1'b0, clk}),
                .CE(2'b01),
                .RESET({1'b0, reset}),
                .PSEL(1'b0),
                .PADDSUB(1'b0)
            );

            always @(posedge clk or posedge reset) begin
                if (reset) begin
                    p <= 64'sd0;
                end else begin
                    p <= {{1{dsp_p[62]}}, dsp_p};
                end
            end
        end else begin : gen_inferred_mult32
            always @(posedge clk or posedge reset) begin
                if (reset) begin
                    p <= 64'sd0;
                end else begin
                    p <= a * b;
                end
            end
        end
    endgenerate
endmodule

module spu_gowin_multiplier #(
    parameter DEVICE = "GW5A"
) (
    input  wire        clk,
    input  wire signed [17:0] a,
    input  wire signed [17:0] b,
    output reg  signed [35:0] p
);
    generate
        if (DEVICE == "GW5A") begin : gen_gw5a
            wire [62:0] dsp_p;
            MULT27X36 u_mult (
                .DOUT(dsp_p),
                .A({{9{a[17]}}, a}),
                .B({{18{b[17]}}, b}),
                .D(26'd0),
                .CLK({1'b0, clk}),
                .CE(2'b01),
                .RESET(2'b00),
                .PSEL(1'b0),
                .PADDSUB(1'b0)
            );

            always @(posedge clk) begin
                p <= dsp_p[35:0];
            end
        end else begin : gen_gw2a
            // Explicit instantiation of Gowin MULT18X18 primitive for GW2A
            MULT18X18 #(
                .ASIGN(1), // Signed
                .BSIGN(1)  // Signed
            ) u_mult (
                .A(a),
                .B(b),
                .P(p)
            );
        end
    endgenerate
endmodule

module spu_gowin_bram #(
    parameter ADDR_WIDTH = 10,
    parameter DATA_WIDTH = 16
) (
    input  wire                   clk,
    input  wire [ADDR_WIDTH-1:0]  addr_a,
    input  wire [DATA_WIDTH-1:0]  din_a,
    input  wire                   we_a,
    output wire [DATA_WIDTH-1:0]  dout_a,

    input  wire [ADDR_WIDTH-1:0]  addr_b,
    input  wire [DATA_WIDTH-1:0]  din_b,
    input  wire                   we_b,
    output wire [DATA_WIDTH-1:0]  dout_b
);
    // Semi-Dual Port B-SRAM (SDPB) instantiation for Gowin.
    // GW2A uses 18Kbit BRAM blocks.
    SDPB #(
        .BIT_WIDTH_0(DATA_WIDTH),
        .BIT_WIDTH_1(DATA_WIDTH)
    ) u_bsram (
        .CLKA(clk),
        .CEA(we_a),
        .RESETA(1'b0),
        .ADA(addr_a),
        .DIA(din_a),
        
        .CLKB(clk),
        .CEB(1'b1),
        .RESETB(1'b0),
        .ADB(addr_b),
        .DOB(dout_b)
    );
endmodule
