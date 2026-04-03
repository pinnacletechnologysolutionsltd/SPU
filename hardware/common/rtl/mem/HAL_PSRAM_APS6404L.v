// SPU-13 HAL: PSRAM Controller (AP Memory APS6404L)
// Status: Laminar Domain Implementation (v1.0)
// Objective: 8MB Zero-Lag Paging for WAD/LUT Streaming.

module HAL_PSRAM_APS6404L (
    input  wire         clk,        // System Clock (e.g., 50 MHz)
    input  wire         reset,
    
    // Memory Interface (Internal)
    input  wire         rd_en,
    input  wire         wr_en,
    input  wire [22:0]  addr,       // Byte address (8MB = 2^23)
    input  wire [7:0]   wr_data,
    output reg  [7:0]   rd_data,
    output reg          ready,
    
    // PSRAM Physical Interface (QPI)
    output wire         psram_ce_n,
    output wire         psram_clk,
    inout  wire [3:0]   psram_dq
);

    // --- State Machine ---
    localparam S_INIT_WAIT  = 0;
    localparam S_INIT_RESET = 1;
    localparam S_INIT_QPI   = 2;
    localparam S_IDLE       = 3;
    localparam S_READ_CMD   = 4;
    localparam S_READ_ADDR  = 5;
    localparam S_READ_DUMMY = 6;
    localparam S_READ_DATA  = 7;
    localparam S_WRITE_CMD  = 8;
    localparam S_WRITE_ADDR = 9;
    localparam S_WRITE_DATA = 10;

    reg [3:0]  state;
    reg [15:0] timer;
    reg [5:0]  bit_cnt;
    
    // Command Constants
    localparam CMD_RST_EN   = 8'h66;
    localparam CMD_RST      = 8'h99;
    localparam CMD_ENTER_QPI = 8'h35;
    localparam CMD_FAST_READ = 8'hEB;
    localparam CMD_WRITE     = 8'h02;

    reg        ce_n;
    reg [3:0]  dq_out;
    reg        dq_oe;
    reg [31:0] shift_reg;
    
    assign psram_ce_n = ce_n;
    assign psram_clk  = ce_n ? 1'b0 : clk;
    assign psram_dq   = dq_oe ? dq_out : 4'bzzzz;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            state <= S_INIT_WAIT;
            timer <= 16'd10000; // ~200us wait
            ce_n  <= 1'b1;
            dq_oe <= 1'b0;
            ready <= 1'b0;
        end else begin
            case (state)
                S_INIT_WAIT: begin
                    if (timer == 0) state <= S_INIT_RESET;
                    else timer <= timer - 1;
                end

                S_INIT_RESET: begin
                    // 150us wait done, issue Reset Enable & Reset
                    ce_n <= 1'b0;
                    dq_oe <= 1'b1;
                    dq_out[0] <= 1'b0; // SPI MOSI
                    shift_reg <= 32'h66990000; // Reset Enable + Reset commands
                    bit_cnt <= 16;
                    state <= S_INIT_QPI; 
                end

                S_INIT_QPI: begin
                    if (bit_cnt == 0) begin
                        ce_n <= 1'b1;
                        // Next command: Enter QPI (0x35)
                        if (shift_reg[31:24] == 8'h00) begin
                            state <= S_IDLE;
                            ready <= 1'b1;
                        end else begin
                            ce_n <= 1'b0;
                            shift_reg <= 32'h35000000;
                            bit_cnt <= 8;
                        end
                    end else begin
                        dq_out[0] <= shift_reg[31];
                        shift_reg <= {shift_reg[30:0], 1'b0};
                        bit_cnt <= bit_cnt - 1;
                    end
                end

                S_IDLE: begin
                    ce_n <= 1'b1;
                    dq_oe <= 1'b0;
                    if (rd_en) begin
                        ce_n <= 1'b0;
                        dq_oe <= 1'b1;
                        shift_reg <= {CMD_FAST_READ, addr, 1'b0}; // 8-bit CMD + 24-bit ADDR
                        bit_cnt <= 8; // 2 cycles for CMD + 6 cycles for ADDR in QPI
                        state <= S_READ_CMD;
                    end
                end

                S_READ_CMD: begin
                    if (bit_cnt == 0) begin
                        state <= S_READ_DUMMY;
                        timer <= 6; // 6 dummy cycles for EB command
                        dq_oe <= 1'b0;
                    end else begin
                        dq_out <= shift_reg[31:28];
                        shift_reg <= {shift_reg[27:0], 4'h0};
                        bit_cnt <= bit_cnt - 1;
                    end
                end

                S_READ_DUMMY: begin
                    if (timer == 0) begin
                        state <= S_READ_DATA;
                        bit_cnt <= 2; // 2 cycles per byte
                    end else timer <= timer - 1;
                end

                S_READ_DATA: begin
                    if (bit_cnt == 0) begin
                        state <= S_IDLE;
                        ce_n <= 1'b1;
                    end else begin
                        rd_data <= {rd_data[3:0], psram_dq};
                        bit_cnt <= bit_cnt - 1;
                    end
                end

                default: state <= S_IDLE;
            endcase
        end
    end
endmodule
