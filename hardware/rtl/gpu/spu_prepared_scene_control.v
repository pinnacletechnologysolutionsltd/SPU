// spu_prepared_scene_control.v -- two-triangle candidate preparation state.
// Captures the shared dispatcher's results, isolates the active derived state,
// and emits one qualified activation pulse at frame_start. CC0 1.0 Universal.

module spu_prepared_scene_control (
    input  wire clk, rst_n,
    input  wire commit_pending, frame_start,
    input  wire ready0, ready1,
    input  wire signed [55:0] candidate_A_z0, candidate_B_z0, candidate_C_z0,
    input  wire [6:0] candidate_frac_bits0,
    input  wire signed [55:0] candidate_A_z1, candidate_B_z1, candidate_C_z1,
    input  wire [6:0] candidate_frac_bits1,
    output reg  prepare0, prepare1,
    output wire activate_scene,
    output reg  ready0_seen, ready1_seen,
    output wire generation_matches,
    output reg  signed [55:0] active_A_z0, active_B_z0, active_C_z0,
    output reg  [6:0] active_frac_bits0,
    output reg  signed [55:0] active_A_z1, active_B_z1, active_C_z1,
    output reg  [6:0] active_frac_bits1
);

    localparam IDLE = 1'b0, PREPARING = 1'b1;
    reg state;
    reg candidate_generation, result_generation0, result_generation1;

    assign generation_matches = ready0_seen && ready1_seen &&
        (result_generation0 == candidate_generation) &&
        (result_generation1 == candidate_generation);
    assign activate_scene = (state == PREPARING) && commit_pending &&
        generation_matches && frame_start;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            candidate_generation <= 1'b0;
            result_generation0 <= 1'b0;
            result_generation1 <= 1'b0;
            prepare0 <= 1'b0;
            prepare1 <= 1'b0;
            ready0_seen <= 1'b0;
            ready1_seen <= 1'b0;
            active_A_z0 <= 56'sd0; active_B_z0 <= 56'sd0; active_C_z0 <= 56'sd0;
            active_frac_bits0 <= 7'd0;
            active_A_z1 <= 56'sd0; active_B_z1 <= 56'sd0; active_C_z1 <= 56'sd0;
            active_frac_bits1 <= 7'd0;
        end else begin
            prepare0 <= 1'b0;
            prepare1 <= 1'b0;
            if (state == IDLE && commit_pending) begin
                candidate_generation <= ~candidate_generation;
                ready0_seen <= 1'b0;
                ready1_seen <= 1'b0;
                prepare0 <= 1'b1;
                prepare1 <= 1'b1;
                state <= PREPARING;
            end else if (state == PREPARING) begin
                if (ready0) begin
                    ready0_seen <= 1'b1;
                    result_generation0 <= candidate_generation;
                end
                if (ready1) begin
                    ready1_seen <= 1'b1;
                    result_generation1 <= candidate_generation;
                end
                if (activate_scene) begin
                    active_A_z0 <= candidate_A_z0;
                    active_B_z0 <= candidate_B_z0;
                    active_C_z0 <= candidate_C_z0;
                    active_frac_bits0 <= candidate_frac_bits0;
                    active_A_z1 <= candidate_A_z1;
                    active_B_z1 <= candidate_B_z1;
                    active_C_z1 <= candidate_C_z1;
                    active_frac_bits1 <= candidate_frac_bits1;
                    ready0_seen <= 1'b0;
                    ready1_seen <= 1'b0;
                    state <= IDLE;
                end
            end
        end
    end

endmodule
