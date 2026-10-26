`timescale 1ns / 1ps

// spu13_nsa_regfile_wrapper.v — Non-Standard Analysis Dual-Lane Register File
//
// Implements Finite Synthetic Differential Geometry (FSDG) over the dual ring
//   A_SPU = F_{p^4}[epsilon] / (epsilon^2)
// where epsilon is a nilpotent infinitesimal (epsilon^2 = 0).
//
// Each dual number R = A + epsilon·B maps to a register pair:
//   Real part A → reg[2n]    (position)
//   epsilon part B → reg[2n+1]  (velocity / exact derivative)
//
// When nsa_mode = 0: standard 16×32-bit register file (pass-through)
// When nsa_mode = 1: 8 dual-number slots, each 2×F_{p^4} = 8×32-bit
//
// Dual-lane write:
//   Writing to even address (2n):    updates real part A only
//   Writing to odd address  (2n+1):  updates epsilon part B only
//   Dual-write (nsa_pair_write):     updates both A and B simultaneously
//
// Dual-lane read:
//   Reading even address (2n):     returns real part A
//   Reading odd address  (2n+1):   returns epsilon part B
//   Dual-read (nsa_pair_read_en):  exposes both on nsa_real / nsa_eps ports
//
// Arithmetic semantics (performed by upstream ALU, not this wrapper):
//   (A+eB)+(C+eD) = (A+C)+e(B+D)     — 2 F_{p^4} adds
//   (A+eB)(C+eD) = AC + e(AD+BC)     — 3 F_{p^4} multiplies, 2 adds
//   (A+eB)^(-1) = A^(-1) - e·A^(-1)·B·A^(-1)  — 2 inversions, 2 multiplies

module spu13_nsa_regfile_wrapper (
    input  wire        clk,
    input  wire        rst_n,

    // ── NSA mode control ────────────────────────────────────────────
    input  wire        nsa_mode,           // 1 = dual-lane NSA, 0 = standard

    // ── Standard register interface (pass-through to inner regfile) ─
    input  wire [3:0]  alpha_srcA_addr,
    input  wire [3:0]  alpha_srcB_addr,
    output wire [31:0] alpha_srcA_data,
    output wire [31:0] alpha_srcB_data,
    input  wire [3:0]  alpha_dest_addr,
    input  wire [31:0] alpha_dest_data,
    input  wire        alpha_write_en,

    input  wire [3:0]  beta_srcA_addr,
    input  wire [3:0]  beta_srcB_addr,
    output wire [31:0] beta_srcA_data,
    output wire [31:0] beta_srcB_data,
    input  wire [3:0]  beta_dest_addr,
    input  wire [31:0] beta_dest_data,
    input  wire        beta_write_en,

    // ── NSA dual-lane write port ────────────────────────────────────
    // Writes both real (A) and epsilon (B) parts simultaneously to
    // the dual-number slot identified by nsa_slot[2:0] (8 slots).
    input  wire        nsa_pair_write_en,
    input  wire [2:0]  nsa_slot,
    // Each F_{p^4} element: 4 × 32-bit coefficients
    input  wire [31:0] nsa_real_z0, nsa_real_z1, nsa_real_z2, nsa_real_z3,
    input  wire [31:0] nsa_eps_z0,  nsa_eps_z1,  nsa_eps_z2,  nsa_eps_z3,

    // ── NSA dual-lane read port ─────────────────────────────────────
    input  wire        nsa_pair_read_en,
    input  wire [2:0]  nsa_read_slot,
    output wire [31:0] nsa_rd_real_z0, nsa_rd_real_z1, nsa_rd_real_z2, nsa_rd_real_z3,
    output wire [31:0] nsa_rd_eps_z0,  nsa_rd_eps_z1,  nsa_rd_eps_z2,  nsa_rd_eps_z3
);

    // ── Inner standard register file ─────────────────────────────────
    wire [31:0] inner_alpha_srcA_data;
    wire [31:0] inner_alpha_srcB_data;
    wire [31:0] inner_beta_srcA_data;
    wire [31:0] inner_beta_srcB_data;

    // NSA-mapped addresses: slot n maps to registers [4n : 4n+3] for real
    // and registers [4n+4 : 4n+7] for epsilon (within the 16-register file).
    // With 8 dual-number slots, we need 8×8=64 registers. The inner regfile
    // only has 16 registers, so in NSA mode we use slots 0-1 only (2 dual
    // numbers = 16 registers).
    //
    // Slot 0: real → reg[0..3],  eps → reg[4..7]
    // Slot 1: real → reg[8..11], eps → reg[12..15]

    // ── NSA dual-lane write: sequence into the inner regfile ─────────
    // We use the alpha write port for seqential 4-cycle write of the
    // 8 registers that compose one dual number.
    reg [2:0] nsa_write_seq;     // 0..7: which register in the dual-slot
    reg       nsa_write_active;

    // Slot 0 (real=0-3, eps=4-7), Slot 1 (real=8-11, eps=12-15)
    wire [3:0] nsa_real_base = nsa_slot[0] ? 4'd8  : 4'd0;
    wire [3:0] nsa_eps_base  = nsa_slot[0] ? 4'd12 : 4'd4;

    // Sequencer state machine for burst write
    localparam NSA_WR_IDLE = 1'b0;
    localparam NSA_WR_BUSY = 1'b1;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            nsa_write_seq    <= 3'd0;
            nsa_write_active <= NSA_WR_IDLE;
        end else begin
            if (nsa_mode && nsa_pair_write_en && !nsa_write_active) begin
                nsa_write_seq    <= 3'd0;
                nsa_write_active <= NSA_WR_BUSY;
            end else if (nsa_write_active) begin
                if (nsa_write_seq == 3'd7)
                    nsa_write_active <= NSA_WR_IDLE;
                else
                    nsa_write_seq <= nsa_write_seq + 3'd1;
            end
        end
    end

    // Map sequential write index to register address and data
    // seq 0→reg[real_base+0]=nsa_real_z0, 1→reg[real_base+1]=nsa_real_z1,
    // 2→reg[real_base+2]=nsa_real_z2, 3→reg[real_base+3]=nsa_real_z3,
    // 4→reg[eps_base+0] =nsa_eps_z0,  5→reg[eps_base+1] =nsa_eps_z1,
    // 6→reg[eps_base+2] =nsa_eps_z2,  7→reg[eps_base+3] =nsa_eps_z3,
    wire        nsa_seq_alpha_wr_en = nsa_write_active;
    wire [3:0]  nsa_seq_addr;
    wire [31:0] nsa_seq_data;

    assign nsa_seq_addr = (nsa_write_seq[2])
        ? (nsa_eps_base + {1'b0, nsa_write_seq[1:0]})
        : (nsa_real_base + {1'b0, nsa_write_seq[1:0]});

    // Mux data based on sequence position
    assign nsa_seq_data =
        (nsa_write_seq == 3'd0) ? nsa_real_z0 :
        (nsa_write_seq == 3'd1) ? nsa_real_z1 :
        (nsa_write_seq == 3'd2) ? nsa_real_z2 :
        (nsa_write_seq == 3'd3) ? nsa_real_z3 :
        (nsa_write_seq == 3'd4) ? nsa_eps_z0  :
        (nsa_write_seq == 3'd5) ? nsa_eps_z1  :
        (nsa_write_seq == 3'd6) ? nsa_eps_z2  :
                                  nsa_eps_z3;

    // ── NSA dual-lane read: combinational mux ────────────────────────
    // Real part: registers [slot_base + 0..3]
    // Epsilon part: registers [slot_base + 4..7]
    // Slot 0 (real=0-3, eps=4-7), Slot 1 (real=8-11, eps=12-15)
    wire [3:0] nsa_read_real_base = nsa_read_slot[0] ? 4'd8  : 4'd0;
    wire [3:0] nsa_read_eps_base  = nsa_read_slot[0] ? 4'd12 : 4'd4;

    // We multiplex the inner regfile read ports for NSA reads.
    // Alpha srcA, srcB and Beta srcA, srcB give us 4 concurrent reads.
    // For a dual-number read we need 8 concurrent reads (4 real + 4 eps).
    //
    // Strategy: when nsa_pair_read_en, steal alpha_srcA/B and beta_srcA/B
    // in a 2-cycle burst read (4 registers per cycle).
    reg [1:0] nsa_read_burst_ctr;
    reg       nsa_read_active;
    localparam NSA_RD_IDLE = 1'b0;
    localparam NSA_RD_BUSY = 1'b1;

    wire [3:0] nsa_rd_addr_0, nsa_rd_addr_1, nsa_rd_addr_2, nsa_rd_addr_3;

    // Read addresses switch between real (cycle 0) and eps (cycle 1)
    wire [3:0] nsa_rd_base = (nsa_read_burst_ctr == 2'd0) ? nsa_read_real_base : nsa_read_eps_base;

    assign nsa_rd_addr_0 = nsa_rd_base + 4'd0;
    assign nsa_rd_addr_1 = nsa_rd_base + 4'd1;
    assign nsa_rd_addr_2 = nsa_rd_base + 4'd2;
    assign nsa_rd_addr_3 = nsa_rd_base + 4'd3;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            nsa_read_burst_ctr <= 2'd0;
            nsa_read_active    <= NSA_RD_IDLE;
        end else if (nsa_mode && nsa_pair_read_en && !nsa_read_active) begin
            nsa_read_burst_ctr <= 2'd0;
            nsa_read_active    <= NSA_RD_BUSY;
        end else if (nsa_read_active) begin
            if (nsa_read_burst_ctr == 2'd1)
                nsa_read_active <= NSA_RD_IDLE;
            else
                nsa_read_burst_ctr <= nsa_read_burst_ctr + 2'd1;
        end
    end

    // Capture read data over the burst
    reg [31:0] int_rd_real_z0, int_rd_real_z1, int_rd_real_z2, int_rd_real_z3;
    reg [31:0] int_rd_eps_z0,  int_rd_eps_z1,  int_rd_eps_z2,  int_rd_eps_z3;

    always @(posedge clk) begin
        if (nsa_read_active && nsa_read_burst_ctr == 2'd0) begin
            int_rd_real_z0 <= inner_alpha_srcA_data;
            int_rd_real_z1 <= inner_alpha_srcB_data;
            int_rd_real_z2 <= inner_beta_srcA_data;
            int_rd_real_z3 <= inner_beta_srcB_data;
        end else if (nsa_read_active && nsa_read_burst_ctr == 2'd1) begin
            int_rd_eps_z0 <= inner_alpha_srcA_data;
            int_rd_eps_z1 <= inner_alpha_srcB_data;
            int_rd_eps_z2 <= inner_beta_srcA_data;
            int_rd_eps_z3 <= inner_beta_srcB_data;
        end
    end

    assign nsa_rd_real_z0 = int_rd_real_z0;
    assign nsa_rd_real_z1 = int_rd_real_z1;
    assign nsa_rd_real_z2 = int_rd_real_z2;
    assign nsa_rd_real_z3 = int_rd_real_z3;
    assign nsa_rd_eps_z0  = int_rd_eps_z0;
    assign nsa_rd_eps_z1  = int_rd_eps_z1;
    assign nsa_rd_eps_z2  = int_rd_eps_z2;
    assign nsa_rd_eps_z3  = int_rd_eps_z3;

    // ── Mux standard vs NSA address/demux for inner regfile ──────────
    wire [3:0]  mux_alpha_srcA_addr, mux_alpha_srcB_addr;
    wire [3:0]  mux_beta_srcA_addr,  mux_beta_srcB_addr;
    wire [3:0]  mux_alpha_dest_addr, mux_beta_dest_addr;
    wire [31:0] mux_alpha_dest_data, mux_beta_dest_data;
    wire        mux_alpha_write_en,  mux_beta_write_en;

    assign mux_alpha_srcA_addr = nsa_read_active ? nsa_rd_addr_0 : alpha_srcA_addr;
    assign mux_alpha_srcB_addr = nsa_read_active ? nsa_rd_addr_1 : alpha_srcB_addr;
    assign mux_beta_srcA_addr  = nsa_read_active ? nsa_rd_addr_2 : beta_srcA_addr;
    assign mux_beta_srcB_addr  = nsa_read_active ? nsa_rd_addr_3 : beta_srcB_addr;

    assign mux_alpha_dest_addr = nsa_seq_alpha_wr_en ? nsa_seq_addr   : alpha_dest_addr;
    assign mux_alpha_dest_data = nsa_seq_alpha_wr_en ? nsa_seq_data   : alpha_dest_data;
    assign mux_alpha_write_en  = nsa_seq_alpha_wr_en ? 1'b1           : alpha_write_en;
    assign mux_beta_dest_addr  = beta_dest_addr;
    assign mux_beta_dest_data  = beta_dest_data;
    assign mux_beta_write_en   = beta_write_en;

    // ── Inner register file instance ──────────────────────────────────
    spu13_multi_port_regfile u_regfile (
        .clk              (clk),
        .rst_n            (rst_n),
        .alpha_srcA_addr  (mux_alpha_srcA_addr),
        .alpha_srcB_addr  (mux_alpha_srcB_addr),
        .alpha_srcA_data  (inner_alpha_srcA_data),
        .alpha_srcB_data  (inner_alpha_srcB_data),
        .alpha_dest_addr  (mux_alpha_dest_addr),
        .alpha_dest_data  (mux_alpha_dest_data),
        .alpha_write_en   (mux_alpha_write_en),
        .beta_srcA_addr   (mux_beta_srcA_addr),
        .beta_srcB_addr   (mux_beta_srcB_addr),
        .beta_srcA_data   (inner_beta_srcA_data),
        .beta_srcB_data   (inner_beta_srcB_data),
        .beta_dest_addr   (mux_beta_dest_addr),
        .beta_dest_data   (mux_beta_dest_data),
        .beta_write_en    (mux_beta_write_en)
    );

    assign alpha_srcA_data = inner_alpha_srcA_data;
    assign alpha_srcB_data = inner_alpha_srcB_data;
    assign beta_srcA_data  = inner_beta_srcA_data;
    assign beta_srcB_data  = inner_beta_srcB_data;

endmodule
