// spu_mem_bridge_ddr3.v (v1.0)
// Sovereign Manifold Bus <-> MT41K128M16JT-125 DDR3 bridge
// Target : Tang Primer 20K, GW2A-18, 128 MB DDR3 @ 24 MHz sys clock
// Burst  : 52 x 16-bit words = 832-bit manifold (7 DDR3 BL8 bursts)
//
// Architecture note:
//   This module drives the DDR3 using a single-edge (SDR) timing model at
//   24 MHz.  All JEDEC DDR3 timing constraints are easily satisfied at this
//   frequency (41.67 ns/cycle vs. 13.75 ns minimums).  The CK/CK# outputs
//   are driven combinatorially; for real synthesis replace the assign with
//   an ODDR/OSER2 primitive to guarantee skew-free differential output.
//   Read data is sampled on the rising edge after CAS_LAT cycles (DQS-less
//   SDR capture).  LiteDRAM (GW2A target) will replace this module with a
//   proper DDR3 PHY when timing-accurate operation is required.
//
// Init sequence (JEDEC DDR3):
//   1. Assert reset_n=0, CKE=0 for T_RESET_CYCLES (≥200 µs, ~4800 cy @ 24 MHz)
//   2. Deassert reset_n=1, keep CKE=0 for T_INIT_CKE  (≥500 µs, ~12000 cy)
//   3. Assert CKE=1, wait tXPR (T_TXPR cycles)
//   4. Issue MRS: MR2 → MR3 → MR1 → MR0  (tMRD between each)
//   5. Issue ZQ Long Calibration (ZQCL), wait tZQinit (T_ZQINIT cycles)
//   6. Assert mem_ready = 1
//
// Burst read / write:
//   Activate → 52 single-word READ/WRITE commands → Precharge All
//   Read pipeline: data valid = (cmd cycle + CAS_LAT + 1)
//
// CC0 1.0 Universal.

`include "spu_arch_defines.vh"

module spu_mem_bridge_ddr3 #(
    // Timing overrides (use small values in simulation testbenches)
    parameter T_RESET_CYCLES = 5001,  // ≥200 µs @ 24 MHz
    parameter T_INIT_CKE     = 12001, // ≥500 µs after reset_n deassert
    parameter T_TXPR         = 12,    // tXPR: CKE→first MRS (nCK)
    parameter T_MRD          = 4,     // tMRD: between MRS commands (nCK)
    parameter T_MOD          = 12,    // tMOD: last MRS → normal cmds (nCK)
    parameter T_ZQINIT       = 513,   // tZQinit: ZQCL duration (nCK)
    parameter T_REFI         = 187    // tREFI: auto-refresh interval (nCK @ 24 MHz = 7.8 µs)
)(
    input  wire         clk,
    input  wire         reset,    // active-high

    // ── Sovereign Manifold Bus ──────────────────────────────────────────── //
    output reg                              mem_ready,
    input  wire                             mem_burst_rd,
    input  wire                             mem_burst_wr,
    input  wire [`MEM_ADDR_WIDTH-1:0]       mem_addr,
    output reg  [`MANIFOLD_WIDTH-1:0]       mem_rd_manifold,
    input  wire [`MANIFOLD_WIDTH-1:0]       mem_wr_manifold,
    output reg                              mem_burst_done,

    // ── Physical DDR3 pins (MT41K128M16JT-125) ───────────────────────────  //
    output wire        ddr3_ck_p,
    output wire        ddr3_ck_n,
    output reg         ddr3_cke,
    output reg         ddr3_cs_n,
    output reg         ddr3_ras_n,
    output reg         ddr3_cas_n,
    output reg         ddr3_we_n,
    output reg         ddr3_odt,
    output reg         ddr3_reset_n,
    output reg [2:0]   ddr3_ba,
    output reg [13:0]  ddr3_addr,
    inout  wire [15:0] ddr3_dq,
    inout  wire [1:0]  ddr3_dqs_p,
    inout  wire [1:0]  ddr3_dqs_n,
    output reg [1:0]   ddr3_dm
);

    // -------------------------------------------------------------------------
    // DDR3 clock — combinatorial passthrough.
    // Synthesis: replace with ODDR / OSER2 for skew-free differential drive.
    // -------------------------------------------------------------------------
    assign ddr3_ck_p = clk;
    assign ddr3_ck_n = ~clk;

    // DQ tristate (driven only during write bursts)
    reg        dq_en;
    reg [15:0] dq_out;
    assign ddr3_dq = dq_en ? dq_out : 16'hzzzz;

    // DQS tristated — not used in this SDR capture model
    assign ddr3_dqs_p = 2'bzz;
    assign ddr3_dqs_n = 2'bzz;

    // -------------------------------------------------------------------------
    // Timing constants @ 24 MHz (41.67 ns / cycle)
    // -------------------------------------------------------------------------
    localparam BURST_LEN = `MANIFOLD_WIDTH / 16;  // 52 words
    localparam CAS_LAT   = 5;   // CL=5 programmed in MR0
    localparam CWL       = 5;   // CAS Write Latency (MR2)
    localparam T_RCD     = 2;   // tRCD ≥ 13.75 ns  → 2 × 41.67 ns = 83.3 ns
    localparam T_RP      = 2;   // tRP  ≥ 13.75 ns  → 2 × 41.67 ns
    localparam T_WR      = 2;   // tWR  ≥ 15 ns     → 2 cycles
    localparam T_RFC     = 3;   // tRFC ≥ 110 ns (1 Gb) → 3 × 41.67 ns = 125 ns
    // T_REFI is now a parameter (default 187 = 7.8 µs @ 24 MHz)

    // -------------------------------------------------------------------------
    // DDR3 Mode Register values
    //   MR0: BL=8 fixed (A1:0=00), BT=seq (A2=0), CL=5 (A6:4=001),
    //        DLL reset (A8=1), WR=6 (A11:9=010)
    //   MR1: DLL enable (A0=1), all other defaults 0
    //   MR2: CWL=5 (A5:3=000), all other defaults 0
    //   MR3: reserved — all zeros
    // -------------------------------------------------------------------------
    localparam MR0 = 14'h0510;  // CL=5|DLL_reset|WR=6
    localparam MR1 = 14'h0001;  // DLL enable
    localparam MR2 = 14'h0000;  // CWL=5 (000 encoding)
    localparam MR3 = 14'h0000;

    // -------------------------------------------------------------------------
    // DDR3 command encoding {CS_N, RAS_N, CAS_N, WE_N}
    // -------------------------------------------------------------------------
    localparam CMD_DESEL = 4'b1111;
    localparam CMD_NOP   = 4'b0111;
    localparam CMD_MRS   = 4'b0000;
    localparam CMD_REF   = 4'b0001;  // Auto Refresh
    localparam CMD_PRE   = 4'b0010;  // Precharge (A10=1 → all banks)
    localparam CMD_ACT   = 4'b0011;  // Activate
    localparam CMD_WRITE = 4'b0100;
    localparam CMD_READ  = 4'b0101;
    localparam CMD_ZQ    = 4'b0110;  // ZQ Calibration (A10=1 → long)

    // -------------------------------------------------------------------------
    // State machine
    // -------------------------------------------------------------------------
    localparam S_RST_HOLD    = 5'd0;   // hold DDR3 reset
    localparam S_RST_WAIT    = 5'd1;   // reset deasserted, CKE still low
    localparam S_CKE_ASSERT  = 5'd2;   // CKE raised, wait tXPR
    localparam S_MRS2        = 5'd3;
    localparam S_MRS2_W      = 5'd4;
    localparam S_MRS3        = 5'd5;
    localparam S_MRS3_W      = 5'd6;
    localparam S_MRS1        = 5'd7;
    localparam S_MRS1_W      = 5'd8;
    localparam S_MRS0        = 5'd9;
    localparam S_MRS0_W      = 5'd10;  // tMOD wait after MR0 (DLL lock)
    localparam S_ZQ          = 5'd11;
    localparam S_ZQ_W        = 5'd12;
    localparam S_IDLE        = 5'd13;
    localparam S_REFRESH     = 5'd14;
    localparam S_BURST_ACT   = 5'd15;
    localparam S_BURST_RD    = 5'd16;
    localparam S_BURST_WR    = 5'd17;
    localparam S_BURST_PRE   = 5'd18;

    // -------------------------------------------------------------------------
    // Address decomposition  {bank[1:0], row[12:0], col[8:0]} = 24 bits
    // -------------------------------------------------------------------------
    wire [1:0]  a_bank;
    assign a_bank = mem_addr[23:22];
    wire [12:0] a_row;
    assign a_row = mem_addr[21:9];
    wire [8:0]  a_col;
    assign a_col = mem_addr[8:0];

    // -------------------------------------------------------------------------
    // Registers
    // -------------------------------------------------------------------------
    reg  [4:0]  state;
    reg  [15:0] timer;
    reg  [8:0]  refi_cnt;
    reg          refresh_due;
    reg  [5:0]  rd_ptr;     // command pointer for burst phases
    reg          burst_is_rd;

    // Read-capture offset: cmd issued on cycle N, data valid on N + CAS_LAT + 1
    localparam WR_OFFSET = CAS_LAT + 1;
    wire [5:0] wr_ptr;
    assign wr_ptr = rd_ptr - WR_OFFSET[5:0];

    // -------------------------------------------------------------------------
    // Refresh counter (independent of main FSM)
    // -------------------------------------------------------------------------
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            refi_cnt    <= 0;
            refresh_due <= 0;
        end else if (state == S_REFRESH) begin
            refi_cnt    <= 0;
            refresh_due <= 0;
        end else if (refi_cnt == T_REFI - 1) begin
            refresh_due <= 1;
            refi_cnt    <= 0;
        end else begin
            refi_cnt <= refi_cnt + 1;
        end
    end

    // -------------------------------------------------------------------------
    // Helper task: drive DDR3 command bus
    // -------------------------------------------------------------------------
    task drive_cmd;
        input [3:0] cmd;
        input [2:0] ba;
        input [13:0] addr;
        begin
            {ddr3_cs_n, ddr3_ras_n, ddr3_cas_n, ddr3_we_n} <= cmd;
            ddr3_ba   <= ba;
            ddr3_addr <= addr;
        end
    endtask

    // -------------------------------------------------------------------------
    // Main FSM
    // -------------------------------------------------------------------------
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            state          <= S_RST_HOLD;
            timer          <= T_RESET_CYCLES[15:0];
            mem_ready      <= 0;
            mem_burst_done <= 0;
            dq_en          <= 0;
            ddr3_cke       <= 0;
            ddr3_odt       <= 0;
            ddr3_reset_n   <= 0;
            ddr3_dm        <= 2'b00;
            {ddr3_cs_n, ddr3_ras_n, ddr3_cas_n, ddr3_we_n} <= CMD_DESEL;
            ddr3_ba        <= 3'b0;
            ddr3_addr      <= 14'b0;
        end else begin
            // Pulsed outputs default low each cycle
            mem_burst_done <= 0;
            dq_en          <= 0;
            {ddr3_cs_n, ddr3_ras_n, ddr3_cas_n, ddr3_we_n} <= CMD_NOP;

            case (state)

                // -------------------------------------------------------------
                // Phase 0: hold DDR3 reset low for T_RESET_CYCLES
                // -------------------------------------------------------------
                S_RST_HOLD: begin
                    ddr3_cke     <= 0;
                    ddr3_reset_n <= 0;
                    {ddr3_cs_n, ddr3_ras_n, ddr3_cas_n, ddr3_we_n} <= CMD_DESEL;
                    if (timer == 0) begin
                        ddr3_reset_n <= 1;
                        state        <= S_RST_WAIT;
                        timer        <= T_INIT_CKE[15:0];
                    end else timer <= timer - 1;
                end

                // -------------------------------------------------------------
                // Phase 1: reset deasserted, CKE still low for T_INIT_CKE
                // -------------------------------------------------------------
                S_RST_WAIT: begin
                    {ddr3_cs_n, ddr3_ras_n, ddr3_cas_n, ddr3_we_n} <= CMD_NOP;
                    if (timer == 0) begin
                        ddr3_cke <= 1;
                        state    <= S_CKE_ASSERT;
                        timer    <= T_TXPR[15:0];
                    end else timer <= timer - 1;
                end

                // -------------------------------------------------------------
                // Phase 2: CKE asserted — wait tXPR before first MRS
                // -------------------------------------------------------------
                S_CKE_ASSERT: begin
                    if (timer == 0) begin
                        drive_cmd(CMD_MRS, 3'b010, {2'b0, MR2});
                        state <= S_MRS2;
                        timer <= T_MRD[15:0];
                    end else timer <= timer - 1;
                end

                // -------------------------------------------------------------
                // MRS sequence: MR2 → wait → MR3 → wait → MR1 → wait → MR0
                // -------------------------------------------------------------
                S_MRS2: begin
                    if (timer == 0) begin
                        drive_cmd(CMD_MRS, 3'b011, {2'b0, MR3});
                        state <= S_MRS3;
                        timer <= T_MRD[15:0];
                    end else timer <= timer - 1;
                end

                S_MRS3: begin
                    if (timer == 0) begin
                        drive_cmd(CMD_MRS, 3'b001, {2'b0, MR1});
                        state <= S_MRS1;
                        timer <= T_MRD[15:0];
                    end else timer <= timer - 1;
                end

                S_MRS1: begin
                    if (timer == 0) begin
                        drive_cmd(CMD_MRS, 3'b000, {2'b0, MR0});
                        state <= S_MRS0;
                        timer <= T_MOD[15:0];
                    end else timer <= timer - 1;
                end

                S_MRS0: begin
                    if (timer == 0) begin
                        // ZQCL: A10=1 selects long calibration
                        drive_cmd(CMD_ZQ, 3'b000, 14'h0400);
                        state <= S_ZQ;
                        timer <= T_ZQINIT[15:0];
                    end else timer <= timer - 1;
                end

                S_ZQ: begin
                    if (timer == 0) begin
                        mem_ready <= 1;
                        state     <= S_IDLE;
                    end else timer <= timer - 1;
                end

                // -------------------------------------------------------------
                // IDLE — service refresh or burst request
                // -------------------------------------------------------------
                S_IDLE: begin
                    if (refresh_due) begin
                        drive_cmd(CMD_REF, 3'b000, 14'b0);
                        state <= S_REFRESH;
                        timer <= T_RFC[15:0];
                    end else if (mem_burst_rd || mem_burst_wr) begin
                        burst_is_rd <= mem_burst_rd;
                        drive_cmd(CMD_ACT, {1'b0, a_bank}, {1'b0, a_row});
                        state   <= S_BURST_ACT;
                        timer   <= T_RCD[15:0] - 1;
                        rd_ptr  <= 0;
                    end
                end

                S_REFRESH: begin
                    if (timer == 0) state <= S_IDLE;
                    else            timer <= timer - 1;
                end

                S_BURST_ACT: begin
                    if (timer == 0) state <= burst_is_rd ? S_BURST_RD : S_BURST_WR;
                    else            timer <= timer - 1;
                end

                // -------------------------------------------------------------
                // Pipelined burst read
                //   Issue BURST_LEN READ commands; capture data with offset
                //   CAS_LAT+1 to account for registered-output SDRAM behaviour.
                //   Loop runs BURST_LEN + CAS_LAT + 1 cycles to drain fully.
                // -------------------------------------------------------------
                S_BURST_RD: begin
                    if (rd_ptr < BURST_LEN) begin
                        drive_cmd(CMD_READ,
                                  {1'b0, a_bank},
                                  {4'b0, a_col + {3'b0, rd_ptr[5:0]}});
                    end

                    if (wr_ptr < BURST_LEN)
                        mem_rd_manifold[wr_ptr * 16 +: 16] <= ddr3_dq;

                    if (rd_ptr == BURST_LEN + CAS_LAT) begin
                        drive_cmd(CMD_PRE, 3'b000, 14'h0400); // A10=1: all banks
                        state <= S_BURST_PRE;
                        timer <= T_RP[15:0];
                    end else begin
                        rd_ptr <= rd_ptr + 1;
                    end
                end

                // -------------------------------------------------------------
                // Sequential burst write
                //   Drive DQ on same cycle as WRITE command (SDR model).
                //   tWR enforced before PRECHARGE.
                // -------------------------------------------------------------
                S_BURST_WR: begin
                    if (rd_ptr < BURST_LEN) begin
                        drive_cmd(CMD_WRITE,
                                  {1'b0, a_bank},
                                  {4'b0, a_col + {3'b0, rd_ptr[5:0]}});
                        dq_out <= mem_wr_manifold[rd_ptr * 16 +: 16];
                        dq_en  <= 1;
                        ddr3_dm <= 2'b00; // all bytes enabled
                        rd_ptr  <= rd_ptr + 1;
                        if (rd_ptr == BURST_LEN - 1) timer <= T_WR[15:0];
                    end else begin
                        if (timer == 0) begin
                            drive_cmd(CMD_PRE, 3'b000, 14'h0400);
                            state <= S_BURST_PRE;
                            timer <= T_RP[15:0];
                        end else timer <= timer - 1;
                    end
                end

                S_BURST_PRE: begin
                    if (timer == 0) begin
                        mem_burst_done <= 1;
                        state          <= S_IDLE;
                    end else timer <= timer - 1;
                end

                default: state <= S_IDLE;
            endcase
        end
    end

endmodule
