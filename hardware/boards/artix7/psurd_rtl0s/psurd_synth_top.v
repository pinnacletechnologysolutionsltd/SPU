// psurd_synth_top.v — RTL-0S synthesis-feasibility wrapper for the v0.3 RTL-0A core (synthesis only).
// Not a board top: no UART, no record packetizer, no pin constraints (out-of-context synthesis).
// Instruction memory contents come only from the top-level write port, so synthesis cannot treat the
// program as constant and optimize the core away. All ports are registered so the out-of-context timing
// estimate has register-to-register boundaries. No functional change to the core.
module psurd_synth_top (
    input  wire clk, rst,
    input  wire start_i,
    input  wire [31:0] budget_i,
    input  wire [8:0]  img_len_i,
    input  wire imem_we_i,
    input  wire [7:0]  imem_waddr_i,
    input  wire [63:0] imem_wdata_i,
    output reg  done_o,
    output reg  [2:0]  cause_o,
    output reg  [8:0]  pc_o,
    output reg  [31:0] retired_o,
    output reg  [5:0]  flags_o,                 // {RS, R, CV, P, N, Z}
    output reg  [1:0]  status_o
);
    reg start, imem_we; reg [31:0] budget; reg [8:0] img_len; reg [7:0] imem_waddr; reg [63:0] imem_wdata;
    wire done, Z, N, P, CV, R, RS; wire [2:0] cause; wire [8:0] pc; wire [31:0] retired; wire [1:0] status;
    always @(posedge clk) begin
        start <= start_i; budget <= budget_i; img_len <= img_len_i;
        imem_we <= imem_we_i; imem_waddr <= imem_waddr_i; imem_wdata <= imem_wdata_i;
        done_o <= done; cause_o <= cause; pc_o <= pc; retired_o <= retired;
        flags_o <= {RS, R, CV, P, N, Z}; status_o <= status;
    end
    psurd_core core (.clk(clk), .rst(rst), .start(start), .budget(budget), .img_len(img_len),
        .imem_we(imem_we), .imem_waddr(imem_waddr), .imem_wdata(imem_wdata),
        .dump_ra(3'd0), .dump_q(), .dump_valid(),          // RTL-0B register-dump port, unused in this wrapper
        .done(done), .cause(cause), .pc(pc), .retired(retired),
        .Z(Z), .N(N), .P(P), .CV(CV), .R(R), .RS(RS), .status(status));
endmodule
