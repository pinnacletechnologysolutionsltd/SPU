// spu_depth_compare4.v — deterministic four-input prepared-scene reduction.
// Smaller signed depth is nearer; equal depth selects the lower primitive ID.
// CC0 1.0 Universal.

module spu_depth_compare4 (
    input wire cov0, cov1, cov2, cov3,
    input wire signed [55:0] depth0, depth1, depth2, depth3,
    input wire [3:0] r0, g0, b0, r1, g1, b1,
    input wire [3:0] r2, g2, b2, r3, g3, b3,
    output reg [3:0] pixel_r, pixel_g, pixel_b,
    output reg [1:0] pixel_id,
    output reg pixel_valid
);
    reg best_valid;
    reg [1:0] best_id;
    reg signed [55:0] best_depth;
    reg [3:0] best_r, best_g, best_b;

    always @(*) begin
        best_valid = 1'b0;
        best_id = 2'd0;
        best_depth = 56'sd0;
        best_r = 4'd0; best_g = 4'd0; best_b = 4'd0;

        if (cov0) begin
            best_valid = 1'b1; best_id = 2'd0; best_depth = depth0;
            best_r = r0; best_g = g0; best_b = b0;
        end
        if (cov1 && (!best_valid || depth1 < best_depth ||
                     (depth1 == best_depth && 2'd1 < best_id))) begin
            best_valid = 1'b1; best_id = 2'd1; best_depth = depth1;
            best_r = r1; best_g = g1; best_b = b1;
        end
        if (cov2 && (!best_valid || depth2 < best_depth ||
                     (depth2 == best_depth && 2'd2 < best_id))) begin
            best_valid = 1'b1; best_id = 2'd2; best_depth = depth2;
            best_r = r2; best_g = g2; best_b = b2;
        end
        if (cov3 && (!best_valid || depth3 < best_depth ||
                     (depth3 == best_depth && 2'd3 < best_id))) begin
            best_valid = 1'b1; best_id = 2'd3; best_depth = depth3;
            best_r = r3; best_g = g3; best_b = b3;
        end

        if (best_valid) begin
            pixel_r = best_r; pixel_g = best_g; pixel_b = best_b;
            pixel_id = best_id;
            pixel_valid = 1'b1;
        end else begin
            pixel_r = 4'd0; pixel_g = 4'd0; pixel_b = 4'd0;
            pixel_id = 2'd0;
            pixel_valid = 1'b0;
        end
    end
endmodule
