// SPU-13 Sovereign Architecture Definitions (v2.3 - SQR v3.1)

`define SPURIOUS_WIDTH 18
`define DELTA_WIDTH    18
`define OPCODE_WIDTH   8

// 13-Axis Manifold Standard
`define MANIFOLD_AXES  13
`define CHORD_WIDTH    64
`define MANIFOLD_WIDTH (`MANIFOLD_AXES * `CHORD_WIDTH) // 832 bits

// Sovereign Memory Bus (Burst-Capable)
`define MEM_ADDR_WIDTH 24
`define MEM_DATA_WIDTH 16 // Legacy single-word
`define MANIFOLD_SIGS \
    input  wire                   mem_ready, \
    output reg                    mem_burst_rd, \
    output reg                    mem_burst_wr, \
    output reg [`MEM_ADDR_WIDTH-1:0] mem_addr, \
    input  wire [`MANIFOLD_WIDTH-1:0] mem_rd_manifold, \
    output reg [`MANIFOLD_WIDTH-1:0] mem_wr_manifold, \
    input  wire                   mem_burst_done

