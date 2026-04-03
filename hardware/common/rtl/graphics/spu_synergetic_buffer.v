// SPU-13 Synergetic Buffer: 3D State Persistence (v1.0)
// Objective: Manage Z-occlusion and manifold state in the 64MB SDRAM.

module spu_synergetic_buffer #(
    parameter RES_X = 240,
    parameter RES_Y = 240
)(
    input  wire         clk,
    input  wire         reset,
    
    // Rasterizer Interface (Z-Test)
    input  wire         test_en,
    input  wire [15:0]  test_x,
    input  wire [15:0]  test_y,
    input  wire [15:0]  test_z,     // Current fragment depth
    input  wire [7:0]   test_state, // Manifold state (e.g. stencil/layer)
    output reg          test_pass,  // High if fragment is closer/visible
    
    // SDRAM Interface (via VRAM Controller)
    output reg  [24:0]  sbuf_addr,
    output reg  [15:0]  sbuf_wr_data,
    input  wire [15:0]  sbuf_rd_data,
    output reg          sbuf_wr_en,
    input  wire         sbuf_ready
);

    // Memory Mapping Strategy:
    // Base Frame (0..240*240) = Cartesian Energy (BG)
    // Synergetic Buffer (Offset 64k) = Depth (16-bit)
    
    localparam SBUF_OFFSET = 25'h010000; // 64k word offset
    
    localparam IDLE = 0, FETCH = 1, COMPARE = 2, WRITE = 3;
    reg [1:0] state;
    
    reg [15:0] r_test_z;
    reg [7:0]  r_test_state;
    reg [24:0] r_addr;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            state <= IDLE;
            test_pass <= 0;
            sbuf_wr_en <= 0;
        end else begin
            sbuf_wr_en <= 0;
            
            case (state)
                IDLE: begin
                    if (test_en && sbuf_ready) begin
                        r_test_z <= test_z;
                        r_test_state <= test_state;
                        r_addr <= SBUF_OFFSET + (test_y * RES_X) + test_x;
                        
                        sbuf_addr <= SBUF_OFFSET + (test_y * RES_X) + test_x;
                        state <= FETCH;
                    end
                end
                
                FETCH: begin
                    // Wait for SDRAM read latency (VRAM controller handles the heavy lifting)
                    if (sbuf_ready) begin
                        state <= COMPARE;
                    end
                end
                
                COMPARE: begin
                    // Synergetic Depth Logic: Nearer pixels have smaller Z?
                    // Let's assume standard Z-buffer: test_z < sbuf_rd_data
                    if (r_test_z < sbuf_rd_data || sbuf_rd_data == 16'hFFFF) begin
                        test_pass <= 1;
                        state <= WRITE;
                    end else begin
                        test_pass <= 0;
                        state <= IDLE;
                    end
                end
                
                WRITE: begin
                    if (sbuf_ready) begin
                        sbuf_addr <= r_addr;
                        sbuf_wr_data <= r_test_z;
                        sbuf_wr_en <= 1;
                        state <= IDLE;
                    end
                end
            endcase
        end
    end
endmodule
