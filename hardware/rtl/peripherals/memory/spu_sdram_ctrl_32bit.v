// spu_sdram_ctrl_32bit.v (v1.0 — ESMT M12L64322A)
// Objective: 32-bit SDRAM controller for Colorlight 5A-75B V8.2.
// Architecture: FSM-based with Auto-Refresh and Precharge logic.
// Optimized for 832-bit manifold bursts (13 words of 64 bits).

module spu_sdram_ctrl_32bit (
    input  wire        clk,        // System clock (e.g., 100MHz)
    input  wire        rst_n,

    // SPU Memory Interface
    input  wire        rd_en,
    input  wire        wr_en,
    input  wire [23:0] addr,       // Byte address
    input  wire [31:0] wr_data,
    output reg  [31:0] rd_data,
    output reg         ready,
    output reg         rd_valid,

    // Physical SDRAM Interface (ESMT M12L64322A)
    output reg         sdram_clk,
    output reg         sdram_ras_n,
    output reg         sdram_cas_n,
    output reg         sdram_we_n,
    output reg  [1:0]  sdram_ba,
    output reg  [10:0] sdram_addr,
    inout  wire [31:0] sdram_dq
);

    // Timing parameters for M12L64322A @ 100MHz
    localparam T_RP  = 3;  // Precharge to Active (20ns)
    localparam T_RC  = 7;  // Active to Active (60ns)
    localparam T_RCD = 3;  // Active to Read/Write (20ns)
    localparam T_CAS = 3;  // CAS Latency

    localparam IDLE         = 4'd0;
    localparam INIT_PRE     = 4'd1;
    localparam INIT_REF     = 4'd2;
    localparam INIT_MRS     = 4'd3;
    localparam ACTIVE       = 4'd4;
    localparam READ         = 4'd5;
    localparam WRITE        = 4'd6;
    localparam PRECHARGE    = 4'd7;
    localparam REFRESH      = 4'd8;

    reg [3:0]  state;
    reg [15:0] timer;
    reg [3:0]  refresh_cnt;
    reg [15:0] refresh_timer;

    // Tristate control for DQ bus
    reg        dq_out_en;
    reg [31:0] dq_out_reg;
    assign sdram_dq = dq_out_en ? dq_out_reg : 32'bz;

    // Shift registers for CAS latency
    reg [3:0]  valid_shifter;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= INIT_PRE;
            timer <= 16'd20000; // 200us power-on delay
            sdram_ras_n <= 1'b1;
            sdram_cas_n <= 1'b1;
            sdram_we_n  <= 1'b1;
            ready <= 1'b0;
            refresh_timer <= 16'd0;
            dq_out_en <= 1'b0;
            valid_shifter <= 4'b0;
        end else begin
            // Default command: NOP
            {sdram_ras_n, sdram_cas_n, sdram_we_n} <= 3'b111;
            rd_valid <= valid_shifter[0];
            valid_shifter <= {1'b0, valid_shifter[3:1]};
            
            if (timer > 0) timer <= timer - 16'd1;
            
            // Refresh timer (7.8us @ 100MHz = ~780 cycles)
            if (refresh_timer < 750) refresh_timer <= refresh_timer + 16'd1;

            case (state)
                // --- Initial Power-on Precharge All ---
                INIT_PRE: begin
                    if (timer == 0) begin
                        {sdram_ras_n, sdram_cas_n, sdram_we_n} <= 3'b010; // PRECHARGE
                        sdram_addr[10] <= 1'b1; // ALL banks
                        timer <= T_RP;
                        state <= INIT_REF;
                        refresh_cnt <= 4'd8;
                    end
                end

                // --- Initial Auto-Refresh Cycles (8x) ---
                INIT_REF: begin
                    if (timer == 0) begin
                        if (refresh_cnt > 0) begin
                            {sdram_ras_n, sdram_cas_n, sdram_we_n} <= 3'b001; // REFRESH
                            refresh_cnt <= refresh_cnt - 4'd1;
                            timer <= T_RC;
                        end else begin
                            state <= INIT_MRS;
                        end
                    end
                end

                // --- Load Mode Register ---
                INIT_MRS: begin
                    {sdram_ras_n, sdram_cas_n, sdram_we_n} <= 3'b000; // MRS
                    // Mode: Burst Length 1, Sequential, CAS 3
                    sdram_addr <= 11'b000_0_011_0_000; 
                    timer <= T_RP;
                    state <= IDLE;
                end

                // --- Functional States ---
                IDLE: begin
                    ready <= 1'b1;
                    if (refresh_timer >= 750) begin
                        state <= REFRESH;
                        ready <= 1'b0;
                    end else if (rd_en || wr_en) begin
                        {sdram_ras_n, sdram_cas_n, sdram_we_n} <= 3'b011; // ACTIVE
                        sdram_ba <= addr[22:21];
                        sdram_addr <= addr[20:10]; // Row
                        timer <= T_RCD;
                        state <= (rd_en) ? READ : WRITE;
                        ready <= 1'b0;
                    end
                end

                READ: begin
                    if (timer == 0) begin
                        {sdram_ras_n, sdram_cas_n, sdram_we_n} <= 3'b101; // READ
                        sdram_addr[10] <= 1'b1; // Auto-precharge
                        sdram_addr[9:0] <= {2'b0, addr[9:2]}; // Column
                        valid_shifter[T_CAS-1] <= 1'b1;
                        timer <= T_RC; // Wait for auto-precharge to clear
                        state <= PRECHARGE;
                    end
                end

                WRITE: begin
                    if (timer == 0) begin
                        {sdram_ras_n, sdram_cas_n, sdram_we_n} <= 3'b100; // WRITE
                        sdram_addr[10] <= 1'b1; // Auto-precharge
                        sdram_addr[9:0] <= {2'b0, addr[9:2]};
                        dq_out_en <= 1'b1;
                        dq_out_reg <= wr_data;
                        timer <= T_RC;
                        state <= PRECHARGE;
                    end
                end

                PRECHARGE: begin
                    dq_out_en <= 1'b0;
                    if (timer == 0) state <= IDLE;
                end

                REFRESH: begin
                    {sdram_ras_n, sdram_cas_n, sdram_we_n} <= 3'b001; // REFRESH
                    refresh_timer <= 16'd0;
                    timer <= T_RC;
                    state <= PRECHARGE;
                end

                default: state <= IDLE;
            endcase
        end
    end

    // Clock output logic (usually mirrored for better phase)
    always @(*) sdram_clk = clk;

    // Capture read data
    always @(posedge clk) begin
        if (valid_shifter[0]) rd_data <= sdram_dq;
    end

endmodule
