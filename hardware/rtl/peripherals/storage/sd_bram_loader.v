`timescale 1ns / 1ps

// sd_bram_loader.v — simple FPGA-side SD bootloader
// Streams a configurable number of 512-byte blocks from the SD (SPI-mode)
// into a block-RAM array (boot_mem). Designed as a synthesis-friendly
// scaffold; consumers may read boot_mem hierarchically or a read-port
// accessor can be added later.

module sd_bram_loader #(
    parameter BOOT_BYTES = 16384,    // total bytes to load
    parameter BLOCK_SIZE = 512,       // SD block size
    parameter ADDR_WIDTH = 32,
    parameter CLK_DIV = 8,
    parameter BOOT_START_BLOCK = 0
)(
    input  wire                   clk,
    input  wire                   rst_n,
    input  wire                   auto_boot,   // when 1, start loading after reset

    output reg                    boot_done,
    output reg                    boot_error,

    // SD SPI physical interface (Pmod)
    output wire                   sd_cs,
    output wire                   sd_sck,
    output wire                   sd_mosi,
    input  wire                   sd_miso
);

localparam NUM_BLOCKS = (BOOT_BYTES + BLOCK_SIZE - 1) / BLOCK_SIZE;
localparam DEPTH = BOOT_BYTES;

integer i;
(* ram_style = "block", keep = "true", dont_touch = "true" *) reg [7:0] boot_mem [0:DEPTH-1];

// Signals to/from sd_card_master
wire                    sd_busy;
wire                    sd_data_valid;
wire [7:0]              sd_data_out;
wire                    sd_last;
reg                     sd_start_pulse;
reg [ADDR_WIDTH-1:0]    sd_block_addr;

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

reg [31:0] write_ptr;
reg [31:0] blocks_read;
reg [3:0]  state;
localparam ST_IDLE      = 4'd0;
localparam ST_START     = 4'd1;
localparam ST_WAIT_BUSY = 4'd2;
localparam ST_STREAM    = 4'd3;
localparam ST_DONE      = 4'd4;
localparam ST_ERROR     = 4'd5;

// Simulation helper: zero memory at start for deterministic sim
initial begin
    for (i = 0; i < DEPTH; i = i + 1) begin
        boot_mem[i] = 8'h00;
    end
end

always @(posedge clk) begin
    if (!rst_n) begin
        sd_start_pulse <= 1'b0;
        sd_block_addr <= {ADDR_WIDTH{1'b0}};
        write_ptr <= 32'd0;
        blocks_read <= 32'd0;
        boot_done <= 1'b0;
        boot_error <= 1'b0;
        state <= ST_IDLE;
    end else begin
        case (state)
            ST_IDLE: begin
                boot_done <= 1'b0;
                boot_error <= 1'b0;
                if (auto_boot) begin
                    sd_block_addr <= BOOT_START_BLOCK;
                    write_ptr <= 32'd0;
                    blocks_read <= 32'd0;
                    state <= ST_START;
                end
            end

            ST_START: begin
                // Issue a one-cycle start pulse
                sd_start_pulse <= 1'b1;
                state <= ST_WAIT_BUSY;
            end

            ST_WAIT_BUSY: begin
                // deassert pulse next cycle
                sd_start_pulse <= 1'b0;
                // wait for master to assert busy
                if (sd_busy) begin
                    state <= ST_STREAM;
                end
            end

            ST_STREAM: begin
                if (sd_data_valid) begin
                    if (write_ptr < DEPTH) begin
                        boot_mem[write_ptr] <= sd_data_out;
                        write_ptr <= write_ptr + 1;
                    end else begin
                        // overflow
                        boot_error <= 1'b1;
                        state <= ST_ERROR;
                    end

                    if (sd_last) begin
                        blocks_read <= blocks_read + 1;
                        if (blocks_read + 1 >= NUM_BLOCKS) begin
                            state <= ST_DONE;
                        end else begin
                            // start next block
                            sd_block_addr <= sd_block_addr + 1;
                            state <= ST_START;
                        end
                    end
                end
            end

            ST_DONE: begin
                boot_done <= 1'b1;
                // stay here until reset
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
