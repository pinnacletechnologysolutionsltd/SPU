// SPU-13 Command Processor
// Objective: Stream incoming vertices into rasterization bounding boxes.

module spu_command_processor #(
    parameter RES_X = 240,
    parameter RES_Y = 240
)(
    input  wire         clk,
    input  wire         reset,

    // Vertex Buffer Interface
    input  wire         fifo_empty,
    output reg          fifo_rd_en,
    input  wire [63:0]  v0_abcd,
    input  wire [63:0]  v1_abcd,
    input  wire [63:0]  v2_abcd,
    input  wire [63:0]  v0_attr,
    input  wire [63:0]  v1_attr,
    input  wire [63:0]  v2_attr,

    // Rasterizer Interface
    output reg          rast_valid,
    output wire [63:0]  rast_v0,
    output wire [63:0]  rast_v1,
    output wire [63:0]  rast_v2,
    output wire [15:0]  rast_v0_z,
    output wire [15:0]  rast_v1_z,
    output wire [15:0]  rast_v2_z,
    output wire [31:0]  rast_px,
    output wire [31:0]  rast_py,
    
    // Memory Interface
    output reg          frame_done // Trigger swap
);

    localparam IDLE = 0, FETCH = 1, SETUP_BBOX = 2, RASTERIZE = 3, WAIT_SCAN = 4;
    reg [2:0] state;

    reg [31:0] min_x, max_x, min_y, max_y;
    reg [31:0] cur_x, cur_y;
    
    // Holding Registers
    reg [63:0] r_v0, r_v1, r_v2;
    reg [15:0] r_v0_z, r_v1_z, r_v2_z;
    
    assign rast_v0 = r_v0;
    assign rast_v1 = r_v1;
    assign rast_v2 = r_v2;
    assign rast_v0_z = r_v0_z;
    assign rast_v1_z = r_v1_z;
    assign rast_v2_z = r_v2_z;
    assign rast_px = cur_x;
    assign rast_py = cur_y;

    function [31:0] min3(input [31:0] a, b, c);
        begin min3 = (a < b) ? ((a < c) ? a : c) : ((b < c) ? b : c); end
    endfunction

    function [31:0] max3(input [31:0] a, b, c);
        begin max3 = (a > b) ? ((a > c) ? a : c) : ((b > c) ? b : c); end
    endfunction

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            state <= IDLE;
            fifo_rd_en <= 0;
            rast_valid <= 0;
            frame_done <= 0;
        end else begin
            fifo_rd_en <= 0;
            rast_valid <= 0;
            frame_done <= 0;
            
            case (state)
                IDLE: begin
                    if (!fifo_empty) begin
                        fifo_rd_en <= 1;
                        state <= FETCH;
                    end
                end
                
                FETCH: begin
                    // Latency cycle for FIFO read
                    r_v0 <= v0_abcd; r_v1 <= v1_abcd; r_v2 <= v2_abcd;
                    r_v0_z <= v0_attr[15:0]; r_v1_z <= v1_attr[15:0]; r_v2_z <= v2_attr[15:0];
                    state <= SETUP_BBOX;
                end
                
                SETUP_BBOX: begin
                    // v0_abcd mapping: y[63:32], x[31:0] (from spu_rasterizer.v)
                    min_x <= min3(r_v0[31:0], r_v1[31:0], r_v2[31:0]);
                    max_x <= max3(r_v0[31:0], r_v1[31:0], r_v2[31:0]);
                    min_y <= min3(r_v0[63:32], r_v1[63:32], r_v2[63:32]);
                    max_y <= max3(r_v0[63:32], r_v1[63:32], r_v2[63:32]);
                    
                    cur_x <= min3(r_v0[31:0], r_v1[31:0], r_v2[31:0]);
                    cur_y <= min3(r_v0[63:32], r_v1[63:32], r_v2[63:32]);
                    state <= RASTERIZE;
                end
                
                RASTERIZE: begin
                    rast_valid <= 1; // Pulse for rasterizer pipeline
                    if (cur_x >= max_x || cur_x >= RES_X - 1) begin
                        cur_x <= min_x;
                        if (cur_y >= max_y || cur_y >= RES_Y - 1) begin
                            state <= IDLE; // Triangle done
                            // Trigger frame_done if this is a sync primitive? Let's just do it manually for now.
                        end else begin
                            cur_y <= cur_y + 1;
                        end
                    end else begin
                        cur_x <= cur_x + 1;
                    end
                end
            endcase
        end
    end

endmodule
