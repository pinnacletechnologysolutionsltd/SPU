// SPU-13 HAL: SDRAM Controller (Winbond W9864G6KH-6)
// Status: Laminar Domain Implementation (v1.0)
// Objective: Phase-Locked SDR-SDRAM Access for 640x480 Framebuffer.

module HAL_SDRAM_Winbond (
    input  wire         clk,        // System Clock (e.g., 50 MHz)
    input  wire         reset,
    
    // Memory Interface (Internal)
    input  wire         wr_en,
    input  wire [24:0]  addr,       // {Bank[1:0], Row[12:0], Column[9:0]}
    input  wire [15:0]  wr_data,
    output reg  [15:0]  rd_data,
    output reg          ready,
    
    // SDRAM Physical Interface
    output wire         sdram_clk,
    output wire         sdram_cke,
    output wire         sdram_cs_n,
    output wire         sdram_ras_n,
    output wire         sdram_cas_n,
    output wire         sdram_we_n,
    output wire [1:0]   sdram_ba,
    output wire [12:0]  sdram_addr,
    output wire [1:0]   sdram_dqm,
    inout  wire [15:0]  sdram_dq
);

    // --- State Machine ---
    localparam S_INIT_WAIT  = 0;
    localparam S_INIT_PRE   = 1;
    localparam S_INIT_REFA1 = 2;
    localparam S_INIT_REFA2 = 3;
    localparam S_INIT_MODE  = 4;
    localparam S_IDLE       = 5;
    localparam S_READ_ACT   = 6;
    localparam S_READ_WAIT  = 7;
    localparam S_WRITE      = 8;
    localparam S_REFRESH    = 9;

    reg [3:0]  state;
    reg [15:0] timer;
    reg [3:0]  refresh_cnt;

    // --- Commands (RAS_N, CAS_N, WE_N) ---
    localparam CMD_PALL   = 3'b010; // Precharge All
    localparam CMD_REF    = 3'b001; // Auto Refresh
    localparam CMD_MRS    = 3'b000; // Mode Register Set
    localparam CMD_ACT    = 3'b011; // Bank Activate
    localparam CMD_READ   = 3'b101; // Read
    localparam CMD_WRITE  = 3'b100; // Write
    localparam CMD_NOP    = 3'b111; // No Operation

    reg [2:0] cmd;
    reg [12:0] a_reg;
    reg [1:0]  ba_reg;
    reg        dq_en;
    reg [15:0] dq_out;

    assign sdram_clk   = clk; // Direct phase-lock
    assign sdram_cke   = 1'b1;
    assign sdram_cs_n  = 1'b0; // Always selected for simplicity
    assign {sdram_ras_n, sdram_cas_n, sdram_we_n} = cmd;
    assign sdram_ba    = ba_reg;
    assign sdram_addr  = a_reg;
    assign sdram_dqm   = 2'b00;
    assign sdram_dq    = dq_en ? dq_out : 16'hzzzz;

    // --- Refresh Timer (e.g. 64ms for 4096 rows @ 50MHz = 781 clocks per refresh) ---
    reg [9:0] ref_timer;
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            ref_timer <= 0;
            refresh_cnt <= 0;
        end else begin
            if (ref_timer == 781) begin
                ref_timer <= 0;
                if (refresh_cnt < 8) refresh_cnt <= refresh_cnt + 1;
            end else ref_timer <= ref_timer + 1;
        end
    end

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            state <= S_INIT_WAIT;
            timer <= 16'd5000; // ~100us wait at 50MHz
            cmd <= CMD_NOP;
            ready <= 0;
            dq_en <= 0;
        end else begin
            case (state)
                S_INIT_WAIT: begin
                    if (timer == 0) state <= S_INIT_PRE;
                    else timer <= timer - 1;
                end
                
                S_INIT_PRE: begin
                    cmd <= CMD_PALL;
                    a_reg[10] <= 1'b1; // All banks
                    state <= S_INIT_REFA1;
                    timer <= 4;
                end
                
                S_INIT_REFA1: begin
                    if (timer == 0) {cmd, state, timer} <= {CMD_REF, S_INIT_REFA2, 4'd8};
                    else {cmd, timer} <= {CMD_NOP, timer - 1'b1};
                end
                
                S_INIT_REFA2: begin
                    if (timer == 0) {cmd, state, timer} <= {CMD_MRS, S_INIT_MODE, 4'd4};
                    else {cmd, timer} <= {CMD_NOP, timer - 1'b1};
                end
                
                S_INIT_MODE: begin
                    // CAS 3, Sequential, Burst 1
                    a_reg <= 13'b000_0_00_011_0_000; 
                    state <= S_IDLE;
                    ready <= 1;
                end
                
                S_IDLE: begin
                    cmd <= CMD_NOP;
                    dq_en <= 0;
                    if (timer > 0) timer <= timer - 1;
                    else if (refresh_cnt > 0) begin
                        state <= S_REFRESH;
                        cmd <= CMD_REF;
                        timer <= 8;
                        refresh_cnt <= refresh_cnt - 1;
                    end else if (wr_en) begin
                        state <= S_WRITE;
                        cmd <= CMD_ACT;
                        ba_reg <= addr[24:23];
                        a_reg <= addr[22:10];
                    end else begin
                        // Always check for read or other ops here
                        state <= S_READ_ACT;
                        cmd <= CMD_ACT;
                        ba_reg <= addr[24:23];
                        a_reg <= addr[22:10];
                    end
                end
                
                S_READ_ACT: begin
                    cmd <= CMD_READ;
                    state <= S_READ_WAIT;
                    a_reg[10] <= 1'b1; // Auto precharge
                    a_reg[9:0] <= addr[9:0]; // 10-bit column mapping
                    timer <= 3; // CAS latency 3
                end

                S_READ_WAIT: begin
                    cmd <= CMD_NOP;
                    if (timer == 0) begin
                        rd_data <= sdram_dq;
                        state <= S_IDLE;
                    end else timer <= timer - 1;
                end
                
                S_WRITE: begin
                    cmd <= CMD_WRITE;
                    a_reg[10] <= 1'b1; // Auto precharge
                    a_reg[9:0] <= addr[9:0]; // 10-bit column mapping
                    dq_out <= wr_data;
                    dq_en <= 1;
                    state <= S_IDLE;
                    timer <= 2;
                end

                S_REFRESH: begin
                    if (timer == 0) state <= S_IDLE;
                    else {cmd, timer} <= {CMD_NOP, timer - 1'b1};
                end
                
                default: state <= S_IDLE;
            endcase
        end
    end
endmodule
