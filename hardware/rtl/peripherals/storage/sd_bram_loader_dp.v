`timescale 1ns / 1ps

// sd_bram_loader_dp.v — FPGA-side SD bootloader (word-packed, DP RAM write interface)
// Reads N blocks from SD (SPI-mode) and emits 24-bit instruction words to a
// dual-clock boot RAM via a simple write interface (boot_wr_*).  The loader
// accumulates incoming bytes into 24-bit words (MSB first: {b0,b1,b2}).

module sd_bram_loader_dp #(
    parameter BOOT_BYTES = 16384,
    parameter BLOCK_SIZE = 512,
    parameter ADDR_WIDTH = 32,
    parameter CLK_DIV = 8,
    // Derived: number of 24-bit words
    parameter BOOT_WORDS = (BOOT_BYTES + 2) / 3,
    parameter BOOT_WORD_ADDR_WIDTH = (BOOT_WORDS <= 1) ? 1 : $clog2(BOOT_WORDS),
    parameter BOOT_START_BLOCK = 0
) (
    input  wire                       clk,
    input  wire                       rst_n,
    input  wire                       auto_boot,

    output reg                        boot_done,
    output reg                        boot_error,

    // Boot RAM write port (synchronous to clk)
    output reg                        boot_wr_en,
    output reg [BOOT_WORD_ADDR_WIDTH-1:0] boot_wr_addr,
    output reg [23:0]                 boot_wr_data,
    output reg [23:0]                 boot_head_word0,
    output reg [23:0]                 boot_head_word1,

    // SD SPI physical interface (Pmod pins)
    output wire                       sd_cs,
    output wire                       sd_sck,
    output wire                       sd_mosi,
    input  wire                       sd_miso
);

localparam NUM_BLOCKS = (BOOT_BYTES + BLOCK_SIZE - 1) / BLOCK_SIZE;

// Internal SD master control signals
reg                     sd_start_pulse;
reg [ADDR_WIDTH-1:0]    sd_block_addr;
wire                    sd_busy;
wire                    sd_data_valid;
wire [7:0]              sd_data_out;
wire                    sd_last;

// Word accumulation
reg [7:0] byte0, byte1;
reg [1:0] acc_cnt; // 0,1,2 bytes accumulated
reg [BOOT_WORD_ADDR_WIDTH-1:0] word_ptr;
reg [31:0] blocks_read;
reg [3:0] state;
localparam ST_IDLE      = 4'd0;
localparam ST_START     = 4'd1;
localparam ST_WAIT_BUSY = 4'd2;
localparam ST_STREAM    = 4'd3;
localparam ST_DONE      = 4'd4;
localparam ST_ERROR     = 4'd5;

integer i;

// Instantiate SD master (existing module)
sd_card_master #(.BLOCK_SIZE_BYTES(BLOCK_SIZE), .ADDR_WIDTH(ADDR_WIDTH), .CLK_DIV(CLK_DIV)) u_sd_card_master (
    .clk        (clk),
    .rst_n      (rst_n),
    .start_read (sd_start_pulse),
    .block_addr (sd_block_addr),
    .busy       (sd_busy),
    .data_valid (sd_data_valid),
    .data_out   (sd_data_out),
    .last       (sd_last),
    .sd_cs      (sd_cs),
    .sd_sck     (sd_sck),
    .sd_mosi    (sd_mosi),
    .sd_miso    (sd_miso)
);

initial begin
    // deterministic init for simulation
    boot_done = 1'b0;
    boot_error = 1'b0;
    boot_wr_en = 1'b0;
    boot_wr_addr = {BOOT_WORD_ADDR_WIDTH{1'b0}};
    boot_wr_data = 24'h0;
    sd_start_pulse = 1'b0;
    sd_block_addr = BOOT_START_BLOCK;
    acc_cnt = 0;
    byte0 = 8'h00; byte1 = 8'h00; word_ptr = 0; blocks_read = 0;
end

always @(posedge clk) begin
    if (!rst_n) begin
        boot_done <= 1'b0;
        boot_error <= 1'b0;
        boot_wr_en <= 1'b0;
        boot_wr_addr <= {BOOT_WORD_ADDR_WIDTH{1'b0}};
        boot_wr_data <= 24'h0;
        sd_start_pulse <= 1'b0;
        sd_block_addr <= BOOT_START_BLOCK;
        acc_cnt <= 0;
        byte0 <= 8'h00; byte1 <= 8'h00; word_ptr <= {BOOT_WORD_ADDR_WIDTH{1'b0}};
        blocks_read <= 32'd0;
        state <= ST_IDLE;
    end else begin
        // default single-cycle pulses
        sd_start_pulse <= 1'b0;
        boot_wr_en <= 1'b0;

        case (state)
            ST_IDLE: begin
                boot_done <= 1'b0;
                boot_error <= 1'b0;
                if (auto_boot) begin
                    sd_block_addr <= BOOT_START_BLOCK;
                    blocks_read <= 0;
                    word_ptr <= 0;
                    acc_cnt <= 0;
                    state <= ST_START;
                end
            end

            ST_START: begin
                // Pulse the SD master to begin reading the current block
                sd_start_pulse <= 1'b1;
                state <= ST_WAIT_BUSY;
            end

            ST_WAIT_BUSY: begin
                // Wait for master to assert busy
                if (sd_busy) begin
                    state <= ST_STREAM;
                end
            end

            ST_STREAM: begin
                // Stream bytes from SD master and pack into 24-bit words
                if (sd_data_valid) begin
                    if (acc_cnt == 2'b00) begin
                        byte0 <= sd_data_out;
                        acc_cnt <= 2'b01;
                    end else if (acc_cnt == 2'b01) begin
                        byte1 <= sd_data_out;
                        acc_cnt <= 2'b10;
                    end else begin
                        // third byte -> emit full word
                        boot_wr_data <= {byte0, byte1, sd_data_out};
                        boot_wr_addr <= word_ptr;
                        boot_wr_en <= 1'b1;
                        if (word_ptr == 0) boot_head_word0 <= {byte0, byte1, sd_data_out};
                        else if (word_ptr == 1) boot_head_word1 <= {byte0, byte1, sd_data_out};
                        word_ptr <= word_ptr + 1'b1;
                        acc_cnt <= 2'b00;
                    end

                    if (sd_last) begin
                        blocks_read <= blocks_read + 1;
                        if (blocks_read + 1 >= NUM_BLOCKS) begin
                            // final block: flush leftover bytes (pad to 24-bit word)
                            if (acc_cnt != 2'b00) begin
                                if (acc_cnt == 2'b01) begin
                                    // only byte0 present
                                    boot_wr_data <= {byte0, 16'h0};
                                end else if (acc_cnt == 2'b10) begin
                                    // byte0,byte1 present
                                    boot_wr_data <= {byte0, byte1, 8'h0};
                                end
                                boot_wr_addr <= word_ptr;
                                boot_wr_en <= 1'b1;
                                word_ptr <= word_ptr + 1'b1;
                                acc_cnt <= 2'b00;
                            end
                            state <= ST_DONE;
                        end else begin
                            // not final block: continue across block boundary (do not flush)
                            sd_block_addr <= sd_block_addr + 1'b1;
                            state <= ST_START;
                        end
                    end
                end
            end

            ST_DONE: begin
                boot_done <= 1'b1;
                // remain done
                state <= ST_DONE;
            end

            ST_ERROR: begin
                boot_error <= 1'b1;
                state <= ST_ERROR;
            end

            default: state <= ST_IDLE;
        endcase
    end
end

endmodule
