// rplu_cfg_cdc.v
// Wrapper for spu_async_fifo to handle RPLU config writes across clock domains.
// Transfers a single 78-bit payload: {sel[2:0], material[0], addr[9:0], data[63:0]}
// from src clock domain into dst clock domain. Provides a single-cycle wr_dst
// pulse in the destination domain when a word is popped from the FIFO.
//
// V2.0: Upgraded to Async FIFO for high-throughput bulk ROM streaming.

module rplu_cfg_cdc(
    input  wire        clk_src,
    input  wire        rst_n_src,
    input  wire        wr_src,
    input  wire [2:0]  sel_src,
    input  wire        material_src,
    input  wire [9:0]  addr_src,
    input  wire [63:0] data_src,

    input  wire        clk_dst,
    input  wire        rst_n_dst,
    output reg         wr_dst,
    output reg  [2:0]  sel_dst,
    output reg         material_dst,
    output reg  [9:0]  addr_dst,
    output reg  [63:0] data_dst
);

    localparam WPAY = 78; // 3 + 1 + 10 + 64

    wire [WPAY-1:0] wr_data = {sel_src, material_src, addr_src, data_src};
    wire [WPAY-1:0] rd_data;
    wire empty;
    wire full;

    spu_async_fifo #(
        .DATA_WIDTH(WPAY),
        .ADDR_WIDTH(4) // Depth 16 (sufficient for buffered bursts)
    ) u_fifo (
        .wr_clk(clk_src),
        .wr_rst_n(rst_n_src),
        .wr_en(wr_src & ~full),   // Protection against overflow
        .wr_data(wr_data),
        .full(full),

        .rd_clk(clk_dst),
        .rd_rst_n(rst_n_dst),
        .rd_en(~empty),           // Auto-pop whenever not empty
        .rd_data(rd_data),
        .empty(empty)
    );

    // Dst Domain Output Latch
    // The FIFO automatically presents the next data word on rd_data.
    // Since we assert rd_en dynamically when !empty, it takes 1 cycle to pop.
    // We register the popped data and pulse wr_dst for the RPLU.
    always @(posedge clk_dst or negedge rst_n_dst) begin
        if (!rst_n_dst) begin
            wr_dst       <= 1'b0;
            sel_dst      <= 3'd0;
            material_dst <= 1'b0;
            addr_dst     <= 10'd0;
            data_dst     <= 64'd0;
        end else begin
            // If the FIFO was not empty this cycle, we pop it and assert write pulse
            if (!empty) begin
                wr_dst       <= 1'b1;
                sel_dst      <= rd_data[WPAY-1:WPAY-3];    // [77:75]
                material_dst <= rd_data[WPAY-4];             // [74]
                addr_dst     <= rd_data[WPAY-5:WPAY-14];   // [73:64]
                data_dst     <= rd_data[63:0];               // [63:0]
            end else begin
                wr_dst       <= 1'b0;
            end
        end
    end

endmodule
