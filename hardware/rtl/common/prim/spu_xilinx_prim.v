// spu_xilinx_prim.v — SPU primitives for Xilinx Artix-7 devices.
// Drop-in replacement for spu_gowin_prim.v — same module names,
// Xilinx-native implementations.  Used with DEVICE="A7_35T"|"A7_100T"|"A7_200T".
//
// synth_xilinx maps behavioral multiplies to DSP48E1 blocks.
// synth_xilinx maps behavioral dual-port RAM to RAMB18E1.
// Behavioral approach lets Yosys optimize across device families.

module spu_gowin_mult32 #(
    parameter DEVICE = "A7_100T"
) (
    input  wire                 clk,
    input  wire                 reset,
    input  wire signed [31:0]   a,
    input  wire signed [31:0]   b,
    output reg  signed [63:0]   p
);
    always @(posedge clk or posedge reset) begin
        if (reset) p <= 64'sd0;
        else       p <= a * b;
    end
endmodule


module spu_gowin_multiplier #(
    parameter DEVICE = "A7_100T"
) (
    input  wire                 clk,
    input  wire signed [17:0]   a,
    input  wire signed [17:0]   b,
    output reg  signed [35:0]   p
);
    always @(posedge clk) begin
        p <= a * b;
    end
endmodule


module spu_gowin_bram #(
    parameter ADDR_WIDTH = 10,
    parameter DATA_WIDTH = 16
) (
    input  wire                     clk,
    input  wire [ADDR_WIDTH-1:0]    addr_a,
    input  wire [DATA_WIDTH-1:0]    din_a,
    input  wire                      we_a,
    output wire [DATA_WIDTH-1:0]    dout_a,
    input  wire [ADDR_WIDTH-1:0]    addr_b,
    input  wire [DATA_WIDTH-1:0]    din_b,
    input  wire                      we_b,
    output wire [DATA_WIDTH-1:0]    dout_b
);
    reg [DATA_WIDTH-1:0] mem [(1 << ADDR_WIDTH)-1:0];

    always @(posedge clk) begin
        if (we_a) mem[addr_a] <= din_a;
    end
    assign dout_a = mem[addr_a];

    always @(posedge clk) begin
        if (we_b) mem[addr_b] <= din_b;
    end
    assign dout_b = mem[addr_b];
endmodule
