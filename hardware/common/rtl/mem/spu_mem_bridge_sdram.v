// spu_mem_bridge_sdram.v (v1.0)
// Sovereign Manifold Bus <-> W9825G6KH-6 SDR-SDRAM bridge
// Target : Tang Primer 25K, 32 MB SDRAM @ 50 MHz (clk_fast)
// Burst  : 52 x 16-bit words = 832-bit manifold
// Timing : tRCD=2cy, CAS=3, tRP=2cy, tRFC=7cy, tREFI=390cy (~7.8 us)
// Reads  : pipelined — 52 READs issued back-to-back, drain 3-cy CAS
//          Total burst latency: tRCD + BURST_LEN + CAS_LAT + tRP = ~60 cy
//
// Note: DQM tied internally to 0 (always enable all byte lanes).
//       DQ tristate: use IOBUF primitives for physical synthesis.
//
// CC0 1.0 Universal.

`include "spu_arch_defines.vh"

module spu_mem_bridge_sdram #(
    parameter T_INIT = 10001  // 200 us at 50 MHz; override to small value in TB
)(
    input  wire         clk,
    input  wire         reset,

    // Sovereign Manifold Bus
    output reg                            mem_ready,
    input  wire                           mem_burst_rd,
    input  wire                           mem_burst_wr,
    input  wire [`MEM_ADDR_WIDTH-1:0]     mem_addr,       // {bank[1:0], row[12:0], col[8:0]}
    output reg  [`MANIFOLD_WIDTH-1:0]     mem_rd_manifold,
    input  wire [`MANIFOLD_WIDTH-1:0]     mem_wr_manifold,
    output reg                            mem_burst_done,

    // Physical SDRAM pins (W9825G6KH-6)
    output wire         sdram_clk,
    output wire         sdram_cke,
    output reg          sdram_cs_n,
    output reg          sdram_ras_n,
    output reg          sdram_cas_n,
    output reg          sdram_we_n,
    output reg  [1:0]   sdram_ba,
    output reg  [12:0]  sdram_addr,
    inout  wire [15:0]  sdram_dq
);

    // -------------------------------------------------------------------------
    // Timing constants (50 MHz = 20 ns/cycle)
    // -------------------------------------------------------------------------
    localparam BURST_LEN = `MANIFOLD_WIDTH / 16;   // 52 words
    localparam CAS_LAT   = 3;
    localparam T_RCD     = 2;   // tRCD >= 15 ns  → 2 x 20 ns = 40 ns
    localparam T_RP      = 2;   // tRP  >= 15 ns  → 2 x 20 ns = 40 ns
    localparam T_WR      = 2;   // write-recovery before PRECHARGE
    localparam T_RFC     = 7;   // tRFC >= 66 ns  → 7 x 20 ns = 140 ns
    localparam T_REFI    = 390; // 64 ms / 8192 rows / 20 ns = 390 cy

    // -------------------------------------------------------------------------
    // State encoding
    // -------------------------------------------------------------------------
    localparam S_INIT_WAIT = 4'd0,  S_INIT_PRE  = 4'd1;
    localparam S_INIT_REF1 = 4'd2,  S_INIT_REF2 = 4'd3;
    localparam S_INIT_MRS  = 4'd4,  S_IDLE      = 4'd5;
    localparam S_REFRESH   = 4'd6,  S_BURST_ACT = 4'd7;
    localparam S_BURST_RD  = 4'd8,  S_BURST_WR  = 4'd9;
    localparam S_BURST_PRE = 4'd10;

    // -------------------------------------------------------------------------
    // SDRAM commands {RAS_N, CAS_N, WE_N} (CS_N driven separately)
    // -------------------------------------------------------------------------
    localparam CMD_NOP   = 3'b111;
    localparam CMD_PALL  = 3'b010;  // Precharge All (requires A10=1)
    localparam CMD_REF   = 3'b001;  // Auto Refresh
    localparam CMD_MRS   = 3'b000;  // Mode Register Set
    localparam CMD_ACT   = 3'b011;  // Bank Activate
    localparam CMD_READ  = 3'b101;  // Read  (A10=0: no auto-precharge)
    localparam CMD_WRITE = 3'b100;  // Write (A10=0: no auto-precharge)

    // Mode register: CAS=3, BL=1, Sequential
    // A[2:0]=000(BL1) A[3]=0(seq) A[6:4]=011(CAS3) A[9:7]=0 A[12:10]=0
    localparam MRS_VAL = 13'b000_0_00_011_0_000;  // = 13'h0030

    // -------------------------------------------------------------------------
    // Address decomposition  {bank[1:0], row[12:0], col[8:0]} = 24 bits
    // -------------------------------------------------------------------------
    wire [1:0]  a_bank = mem_addr[23:22];
    wire [12:0] a_row  = mem_addr[21:9];
    wire [8:0]  a_col  = mem_addr[8:0];

    // -------------------------------------------------------------------------
    // DQ tristate (replace with IOBUF primitives in FPGA synthesis flow)
    // -------------------------------------------------------------------------
    reg        dq_en;
    reg [15:0] dq_out;
    assign sdram_dq  = dq_en ? dq_out : 16'hzzzz;
    assign sdram_clk = clk;
    assign sdram_cke = 1'b1;
    // DQM tied to 0 internally — all byte lanes always enabled

    // -------------------------------------------------------------------------
    // Registers
    // -------------------------------------------------------------------------
    reg  [3:0]  state;
    reg  [13:0] timer;
    reg  [9:0]  refi_cnt;
    reg          refresh_due;
    reg  [5:0]  rd_ptr;      // command pointer (0 .. BURST_LEN + CAS_LAT)
    reg          burst_is_rd;

    // wr_ptr: which manifold word the arriving data maps to.
    // Commands are driven as registered outputs; the SDRAM device latches
    // them on the NEXT posedge, adding 1 implicit cycle to the CAS pipeline.
    // Effective capture offset = CAS_LAT + 1 = 4.
    // Unsigned 6-bit wrap when rd_ptr < 4 keeps wr_ptr >= BURST_LEN, so
    // the guard `wr_ptr < BURST_LEN` alone is sufficient.
    wire [5:0] wr_ptr = rd_ptr - 6'd4;  // effective CAS offset = CAS_LAT + 1

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
    // Main FSM
    // -------------------------------------------------------------------------
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            state          <= S_INIT_WAIT;
            timer          <= T_INIT;
            mem_ready      <= 0;
            mem_burst_done <= 0;
            dq_en          <= 0;
            sdram_cs_n     <= 1;
            {sdram_ras_n, sdram_cas_n, sdram_we_n} <= CMD_NOP;
            sdram_ba       <= 0;
            sdram_addr     <= 0;
        end else begin
            // Defaults overridden per-state below
            mem_burst_done <= 0;
            sdram_cs_n     <= 0;
            {sdram_ras_n, sdram_cas_n, sdram_we_n} <= CMD_NOP;
            dq_en          <= 0;

            case (state)

                // -----------------------------------------------------------------
                // Initialisation sequence (JEDEC SDR-SDRAM)
                // -----------------------------------------------------------------
                S_INIT_WAIT: begin
                    sdram_cs_n <= 1;
                    if (timer == 0) begin
                        {sdram_ras_n, sdram_cas_n, sdram_we_n} <= CMD_PALL;
                        sdram_cs_n     <= 0;
                        sdram_addr[10] <= 1;    // A10=1: precharge all banks
                        state          <= S_INIT_PRE;
                        timer          <= T_RP;
                    end else timer <= timer - 1;
                end

                S_INIT_PRE: begin
                    if (timer == 0) begin
                        {sdram_ras_n, sdram_cas_n, sdram_we_n} <= CMD_REF;
                        state <= S_INIT_REF1;
                        timer <= T_RFC;
                    end else timer <= timer - 1;
                end

                S_INIT_REF1: begin
                    if (timer == 0) begin
                        {sdram_ras_n, sdram_cas_n, sdram_we_n} <= CMD_REF;
                        state <= S_INIT_REF2;
                        timer <= T_RFC;
                    end else timer <= timer - 1;
                end

                S_INIT_REF2: begin
                    if (timer == 0) begin
                        {sdram_ras_n, sdram_cas_n, sdram_we_n} <= CMD_MRS;
                        sdram_ba   <= 2'b00;
                        sdram_addr <= MRS_VAL;
                        state      <= S_INIT_MRS;
                        timer      <= 2;
                    end else timer <= timer - 1;
                end

                S_INIT_MRS: begin
                    if (timer == 0) begin
                        mem_ready <= 1;
                        state     <= S_IDLE;
                    end else timer <= timer - 1;
                end

                // -----------------------------------------------------------------
                // Idle: serve refresh or burst request
                // -----------------------------------------------------------------
                S_IDLE: begin
                    if (refresh_due) begin
                        {sdram_ras_n, sdram_cas_n, sdram_we_n} <= CMD_REF;
                        state <= S_REFRESH;
                        timer <= T_RFC;
                    end else if (mem_burst_rd || mem_burst_wr) begin
                        burst_is_rd <= mem_burst_rd;
                        {sdram_ras_n, sdram_cas_n, sdram_we_n} <= CMD_ACT;
                        sdram_ba   <= a_bank;
                        sdram_addr <= a_row;
                        state      <= S_BURST_ACT;
                        timer      <= T_RCD - 1;
                        rd_ptr     <= 0;
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

                // -----------------------------------------------------------------
                // Pipelined burst read
                // Commands are registered so SDRAM latches them 1 cycle late.
                // Effective pipeline offset = CAS_LAT + 1 = 4.
                // Loop runs BURST_LEN + CAS_LAT + 1 = 56 cycles to drain fully.
                // -----------------------------------------------------------------
                S_BURST_RD: begin
                    if (rd_ptr < BURST_LEN) begin
                        {sdram_ras_n, sdram_cas_n, sdram_we_n} <= CMD_READ;
                        sdram_ba   <= a_bank;
                        sdram_addr <= {4'b0000, a_col + {3'b0, rd_ptr}};
                    end

                    // Capture: wr_ptr = rd_ptr - 4 (unsigned 6-bit wraps when < 4,
                    // keeping wr_ptr >= BURST_LEN so the guard rejects those cycles)
                    if (wr_ptr < BURST_LEN) begin
                        mem_rd_manifold[wr_ptr * 16 +: 16] <= sdram_dq;
                    end

                    if (rd_ptr == BURST_LEN + CAS_LAT) begin  // = 55
                        {sdram_ras_n, sdram_cas_n, sdram_we_n} <= CMD_PALL;
                        sdram_addr[10] <= 1;
                        state          <= S_BURST_PRE;
                        timer          <= T_RP;
                    end else begin
                        rd_ptr <= rd_ptr + 1;
                    end
                end

                // -----------------------------------------------------------------
                // Sequential burst write
                // Issue BURST_LEN WRITEs, wait tWR, then PRECHARGE
                // -----------------------------------------------------------------
                S_BURST_WR: begin
                    if (rd_ptr < BURST_LEN) begin
                        {sdram_ras_n, sdram_cas_n, sdram_we_n} <= CMD_WRITE;
                        sdram_ba   <= a_bank;
                        sdram_addr <= {4'b0000, a_col + {3'b0, rd_ptr}};
                        dq_out     <= mem_wr_manifold[rd_ptr * 16 +: 16];
                        dq_en      <= 1;
                        rd_ptr     <= rd_ptr + 1;
                        if (rd_ptr == BURST_LEN - 1) timer <= T_WR;
                    end else begin
                        // tWR wait before PRECHARGE
                        if (timer == 0) begin
                            {sdram_ras_n, sdram_cas_n, sdram_we_n} <= CMD_PALL;
                            sdram_addr[10] <= 1;
                            state          <= S_BURST_PRE;
                            timer          <= T_RP;
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
