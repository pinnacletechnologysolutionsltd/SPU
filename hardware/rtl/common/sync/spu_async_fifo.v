// spu_async_fifo.v
// Standard Asynchronous FIFO using Gray-code pointers for safe CDC.
// Used to bridge SPU fast-clock/SPI domains into slower piranha domains.
//
// CC0 1.0 Universal.

module spu_async_fifo #(
    parameter DATA_WIDTH = 78,
    parameter ADDR_WIDTH = 4   // Depth = 16
) (
    // Write Domain
    input  wire                  wr_clk,
    input  wire                  wr_rst_n,
    input  wire                  wr_en,
    input  wire [DATA_WIDTH-1:0] wr_data,
    output wire                  full,

    // Read Domain
    input  wire                  rd_clk,
    input  wire                  rd_rst_n,
    input  wire                  rd_en,
    output wire [DATA_WIDTH-1:0] rd_data,
    output wire                  empty
);

    localparam DEPTH = (1 << ADDR_WIDTH);

    // --- Dual-Port Memory ---
    reg [DATA_WIDTH-1:0] mem [0:DEPTH-1];

    // --- Pointers ---
    // N+1 bit pointers where MSB is used to distinguish empty from full.
    reg [ADDR_WIDTH:0] wr_ptr_bin, wr_ptr_gray;
    reg [ADDR_WIDTH:0] rd_ptr_bin, rd_ptr_gray;

    // --- Synchronizers ---
    reg [ADDR_WIDTH:0] wr_ptr_gray_sync0, wr_ptr_gray_sync1;
    reg [ADDR_WIDTH:0] rd_ptr_gray_sync0, rd_ptr_gray_sync1;

    // 1. Write Logic
    always @(posedge wr_clk or negedge wr_rst_n) begin
        if (!wr_rst_n) begin
            wr_ptr_bin  <= 0;
            wr_ptr_gray <= 0;
        end else if (wr_en && !full) begin
            mem[wr_ptr_bin[ADDR_WIDTH-1:0]] <= wr_data;
            wr_ptr_bin  <= wr_ptr_bin + 1;
            wr_ptr_gray <= (wr_ptr_bin + 1) ^ ((wr_ptr_bin + 1) >> 1);
        end
    end

    // Sync read pointer into write domain
    always @(posedge wr_clk or negedge wr_rst_n) begin
        if (!wr_rst_n) begin
            rd_ptr_gray_sync0 <= 0;
            rd_ptr_gray_sync1 <= 0;
        end else begin
            rd_ptr_gray_sync0 <= rd_ptr_gray;
            rd_ptr_gray_sync1 <= rd_ptr_gray_sync0;
        end
    end

    // Full condition: Gray code MSB & MSB-1 inverted, rest match
    wire [ADDR_WIDTH:0] wr_ptr_gray_next = wr_ptr_bin ^ (wr_ptr_bin >> 1);
    assign full = (wr_ptr_gray_next == {~rd_ptr_gray_sync1[ADDR_WIDTH:ADDR_WIDTH-1], 
                                         rd_ptr_gray_sync1[ADDR_WIDTH-2:0]});

    // 2. Read Logic
    always @(posedge rd_clk or negedge rd_rst_n) begin
        if (!rd_rst_n) begin
            rd_ptr_bin  <= 0;
            rd_ptr_gray <= 0;
        end else if (rd_en && !empty) begin
            rd_ptr_bin  <= rd_ptr_bin + 1;
            rd_ptr_gray <= (rd_ptr_bin + 1) ^ ((rd_ptr_bin + 1) >> 1);
        end
    end

    assign rd_data = mem[rd_ptr_bin[ADDR_WIDTH-1:0]];

    // Sync write pointer into read domain
    always @(posedge rd_clk or negedge rd_rst_n) begin
        if (!rd_rst_n) begin
            wr_ptr_gray_sync0 <= 0;
            wr_ptr_gray_sync1 <= 0;
        end else begin
            wr_ptr_gray_sync0 <= wr_ptr_gray;
            wr_ptr_gray_sync1 <= wr_ptr_gray_sync0;
        end
    end

    // Empty condition: pointers match exactly
    assign empty = (rd_ptr_gray == wr_ptr_gray_sync1);

endmodule
