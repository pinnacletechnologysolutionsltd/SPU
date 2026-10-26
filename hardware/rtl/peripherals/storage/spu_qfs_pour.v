// SPU-13 QFS Geometric Pour Controller (v1.0)
// Role: Streams 4D Quadray data from Storage (SD/Flash) into PSRAM.
// Logic: "Unfolds" geometric assets into the unified memory manifold.

module spu_qfs_pour (
    input  wire         clk,
    input  wire         reset,
    
    // Storage Interface (Skeleton for SPI/SD)
    input  wire         storage_ready,
    input  wire [127:0] storage_data, // One full Quadray (4 x 32-bit)
    input  wire         storage_valid,
    output reg          storage_rd_en,
    output reg  [31:0]  storage_addr,
    
    // PSRAM Interface (via DMA Manifold)
    output reg          psram_wr_en,
    output reg  [22:0]  psram_addr,
    output reg  [31:0]  psram_wr_data, // Writing 32-bit chunks
    input  wire         psram_ready,
    
    // Control
    input  wire         pour_trigger,
    input  wire [31:0]  pour_start_addr,
    input  wire [15:0]  pour_count, // Number of Quadrays to pour
    output reg          pour_busy
);

    reg [31:0] current_storage_addr;
    reg [22:0] current_psram_addr;
    reg [15:0] rem_quadrays;
    reg [1:0]  quad_lane; // 0=A, 1=B, 2=C, 3=D

    localparam IDLE = 0, REQ_STORAGE = 1, WAIT_STORAGE = 2, WRITE_PSRAM = 3;
    reg [1:0] state;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            state <= IDLE;
            storage_rd_en <= 0;
            psram_wr_en <= 0;
            pour_busy <= 0;
            quad_lane <= 0;
        end else begin
            psram_wr_en <= 0;
            storage_rd_en <= 0;
            
            case (state)
                IDLE: begin
                    if (pour_trigger && storage_ready && psram_ready) begin
                        current_storage_addr <= pour_start_addr;
                        current_psram_addr <= 23'h0; // Target PSRAM start
                        rem_quadrays <= pour_count;
                        pour_busy <= 1;
                        state <= REQ_STORAGE;
                    end else pour_busy <= 0;
                end
                
                REQ_STORAGE: begin
                    if (storage_ready) begin
                        storage_rd_en <= 1;
                        storage_addr <= current_storage_addr;
                        state <= WAIT_STORAGE;
                    end
                end
                
                WAIT_STORAGE: begin
                    if (storage_valid) begin
                        state <= WRITE_PSRAM;
                        quad_lane <= 0;
                    end
                end
                
                WRITE_PSRAM: begin
                    if (psram_ready) begin
                        psram_wr_en <= 1;
                        psram_addr <= current_psram_addr;
                        // Write one lane of the quadray at a time
                        case (quad_lane)
                            2'd0: psram_wr_data <= storage_data[31:0];
                            2'd1: psram_wr_data <= storage_data[63:32];
                            2'd2: psram_wr_data <= storage_data[95:64];
                            2'd3: psram_wr_data <= storage_data[127:96];
                        endcase
                        
                        current_psram_addr <= current_psram_addr + 1;
                        
                        if (quad_lane == 3) begin
                            if (rem_quadrays == 1) begin
                                state <= IDLE;
                            end else begin
                                rem_quadrays <= rem_quadrays - 1;
                                current_storage_addr <= current_storage_addr + 1;
                                state <= REQ_STORAGE;
                            end
                        end else begin
                            quad_lane <= quad_lane + 1;
                        end
                    end
                end
            endcase
        end
    end

endmodule
