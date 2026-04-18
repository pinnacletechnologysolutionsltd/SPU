// spu_gowin_prim.v — SPU Primitives for Gowin GW2A-LV18
// Objective: Standardize SPU multipliers and BRAM for the Tang Primer 20K.

`timescale 1ns / 1ps

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
            // Registered assignment allows Yosys to infer MULT18X18D
            always @(posedge clk) begin
                p <= a * b;
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
