// psurd_imem.v — 256 x 64 instruction memory, synchronous read (RTL-0A).
// RTL-0A testbenches load `mem` directly ($readmemh via hierarchy); RTL-0B adds the SPUI loader path
// on the write port. The image is not execution state (frozen contract §2).
module psurd_imem (
    input  wire clk,
    input  wire [7:0] raddr,
    output reg  [63:0] rdata,
    input  wire we,
    input  wire [7:0] waddr,
    input  wire [63:0] wdata
);
    reg [63:0] mem [0:255];
    always @(posedge clk) begin
        rdata <= mem[raddr];
        if (we) mem[waddr] <= wdata;
    end
endmodule
