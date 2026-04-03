// SPU_ARTERY_FIFO.v (v1.1 - 64-Deep Burst Hardened)
// Objective: High-throughput 133 MHz (RP2040) to 61.44 kHz (SPU) Bridge.
// Architecture: 64-bit Wide Dual-Port FIFO (Depth 64).

module SPU_ARTERY_FIFO (
    // Write Domain (133 MHz)
    input  wire        wr_clk,
    input  wire        wr_rst_n,
    input  wire        wr_en,
    input  wire [63:0] wr_data,
    output wire        full,

    // Read Domain (61.44 kHz)
    input  wire        rd_clk,
    input  wire        rd_rst_n,
    input  wire        rd_en,
    output wire [63:0] rd_data,
    output wire        empty
);

    // 64-deep 64-bit Manifold Storage (4,096 bits total)
    reg [63:0] mem [63:0];
    initial begin : init_mem
        integer j;
        for (j = 0; j < 64; j = j + 1) mem[j] = 64'h0;
    end
    
    // 6-bit Pointers for 64 locations
    reg [5:0]  wr_ptr, rd_ptr;
    initial begin wr_ptr = 0; rd_ptr = 0; end

    always @(posedge wr_clk) begin
        if (!wr_rst_n) begin
            wr_ptr <= 6'h0;
        end else if (wr_en && !full) begin
            mem[wr_ptr] <= wr_data;
            wr_ptr <= wr_ptr + 6'd1;
        end
    end

    always @(posedge rd_clk) begin
        if (!rd_rst_n) begin
            rd_ptr <= 6'h0;
        end else if (rd_en && !empty) begin
            rd_ptr <= rd_ptr + 6'd1;
        end
    end

    assign rd_data = mem[rd_ptr];

    // Laminar Occupancy logic
    // Using simple pointer comparison for pulse-locked domain crossing
    assign empty = (wr_ptr == rd_ptr);
    assign full  = (wr_ptr + 6'd1 == rd_ptr);

endmodule
