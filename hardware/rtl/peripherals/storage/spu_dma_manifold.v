// SPU-13 Laminar DMA Manifold (v1.0)
// Objective: Stream PSRAM (WAD/Textures) into local BRAM caches for the rasterizer.

module spu_dma_manifold #(
    parameter ADDR_WIDTH = 23
)(
    input  wire         clk,
    input  wire         reset,
    
    // PSRAM Interface
    output reg          psram_rd_en,
    output reg  [22:0]  psram_addr,
    input  wire [7:0]   psram_rd_data,
    input  wire         psram_ready,
    
    // Internal Cache/DMA Interface
    input  wire         dma_trigger,
    input  wire [22:0]  dma_start_addr,
    input  wire [15:0]  dma_length,
    output reg          dma_busy,
    
    // Output to Fragment Pipe (Texture Stream)
    output reg  [7:0]   stream_data,
    output reg          stream_valid
);

    reg [22:0] current_addr;
    reg [15:0] rem_len;
    
    localparam IDLE = 0, FETCH = 1, STREAM = 2;
    reg [1:0] state;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            state <= IDLE;
            psram_rd_en <= 0;
            dma_busy <= 0;
            stream_valid <= 0;
        end else begin
            stream_valid <= 0;
            psram_rd_en <= 0;
            
            case (state)
                IDLE: begin
                    if (dma_trigger && psram_ready) begin
                        current_addr <= dma_start_addr;
                        rem_len <= dma_length;
                        dma_busy <= 1;
                        state <= FETCH;
                    end else dma_busy <= 0;
                end
                
                FETCH: begin
                    if (psram_ready) begin
                        psram_rd_en <= 1;
                        psram_addr <= current_addr;
                        state <= STREAM;
                    end
                end
                
                STREAM: begin
                    // HAL provides data in the next cycle(s) depending on latency
                    // For now, assume 1-cycle latency from HAL_PSRAM
                    stream_data <= psram_rd_data;
                    stream_valid <= 1;
                    
                    if (rem_len == 1) begin
                        state <= IDLE;
                    end else begin
                        rem_len <= rem_len - 1;
                        current_addr <= current_addr + 1;
                        state <= FETCH;
                    end
                end
            endcase
        end
    end
endmodule
