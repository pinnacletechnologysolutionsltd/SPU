// spu_texture_dma.v — Simple texture read DMA for external SDRAM
// Periodically issues read bursts to the ext SDRAM bridge to exercise the
// interface and provide a template for later GPU/texture-cache integration.

`include "spu_arch_defines.vh"

module spu_texture_dma (
    input  wire                         clk,
    input  wire                         reset,

    // SDRAM bridge interface
    input  wire                         mem_ready,
    output reg                          mem_burst_rd,
    output reg                          mem_burst_wr,
    output reg  [`MEM_ADDR_WIDTH-1:0]   mem_addr,
    input  wire [`MANIFOLD_WIDTH-1:0]   mem_rd_manifold,
    output reg  [`MANIFOLD_WIDTH-1:0]   mem_wr_manifold,
    input  wire                         mem_burst_done
);

    // Simple periodic reader: wait until mem_ready, then issue a 1-cycle burst
    // request every WAIT_CYCLES cycles. On burst completion increment address.
    parameter WAIT_CYCLES = 24'd1000000;

    reg [23:0] timer;
    reg        busy;

    always @(posedge clk) begin
        if (reset) begin
            timer         <= 24'd0;
            busy          <= 1'b0;
            mem_burst_rd  <= 1'b0;
            mem_burst_wr  <= 1'b0;
            mem_addr      <= {`MEM_ADDR_WIDTH{1'b0}};
            mem_wr_manifold <= {`MANIFOLD_WIDTH{1'b0}};
        end else begin
            // Default: no request
            mem_burst_rd <= 1'b0;
            mem_burst_wr <= 1'b0;

            if (!mem_ready) begin
                timer <= 24'd0;
                busy  <= 1'b0;
            end else begin
                if (busy) begin
                    // wait for burst to complete
                    if (mem_burst_done) begin
                        busy <= 1'b0;
                        mem_addr <= mem_addr + 1'b1; // advance to next block
                    end
                end else begin
                    if (timer >= WAIT_CYCLES) begin
                        // start a read burst
                        mem_burst_rd <= 1'b1;
                        busy <= 1'b1;
                        timer <= 24'd0;
                    end else begin
                        timer <= timer + 1'b1;
                    end
                end
            end
        end
    end

    // mem_wr_manifold stays zero (read-only DMA for now)

endmodule
