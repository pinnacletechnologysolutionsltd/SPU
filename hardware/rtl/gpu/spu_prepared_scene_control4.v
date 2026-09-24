// spu_prepared_scene_control4.v — four-result prepared-scene activation.
// All derived depth planes must match one candidate generation before the
// raw scene and derived state activate together at frame_start.
// CC0 1.0 Universal.

module spu_prepared_scene_control4 (
    input wire clk, rst_n,
    input wire commit_pending, frame_start,
    input wire [3:0] ready,
    input wire signed [55:0] candidate_A0, candidate_B0, candidate_C0,
    input wire [6:0] candidate_frac0,
    input wire signed [55:0] candidate_A1, candidate_B1, candidate_C1,
    input wire [6:0] candidate_frac1,
    input wire signed [55:0] candidate_A2, candidate_B2, candidate_C2,
    input wire [6:0] candidate_frac2,
    input wire signed [55:0] candidate_A3, candidate_B3, candidate_C3,
    input wire [6:0] candidate_frac3,
    output reg [3:0] prepare,
    output wire activate_scene,
    output wire generation_matches,
    output reg [3:0] ready_seen,
    output reg signed [55:0] active_A0, active_B0, active_C0,
    output reg [6:0] active_frac0,
    output reg signed [55:0] active_A1, active_B1, active_C1,
    output reg [6:0] active_frac1,
    output reg signed [55:0] active_A2, active_B2, active_C2,
    output reg [6:0] active_frac2,
    output reg signed [55:0] active_A3, active_B3, active_C3,
    output reg [6:0] active_frac3
);
    localparam IDLE = 1'b0, PREPARING = 1'b1;
    reg state, candidate_generation;
    reg [3:0] result_generation;

    assign generation_matches = (ready_seen == 4'b1111) &&
        (result_generation == {4{candidate_generation}});
    assign activate_scene = (state == PREPARING) && commit_pending &&
        generation_matches && frame_start;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE; candidate_generation <= 0; result_generation <= 0;
            prepare <= 0; ready_seen <= 0;
            active_A0<=0; active_B0<=0; active_C0<=0; active_frac0<=0;
            active_A1<=0; active_B1<=0; active_C1<=0; active_frac1<=0;
            active_A2<=0; active_B2<=0; active_C2<=0; active_frac2<=0;
            active_A3<=0; active_B3<=0; active_C3<=0; active_frac3<=0;
        end else begin
            prepare <= 0;
            if (state == IDLE && commit_pending) begin
                candidate_generation <= ~candidate_generation;
                ready_seen <= 0;
                prepare <= 4'b1111;
                state <= PREPARING;
            end else if (state == PREPARING) begin
                if (ready[0]) begin ready_seen[0]<=1; result_generation[0]<=candidate_generation; end
                if (ready[1]) begin ready_seen[1]<=1; result_generation[1]<=candidate_generation; end
                if (ready[2]) begin ready_seen[2]<=1; result_generation[2]<=candidate_generation; end
                if (ready[3]) begin ready_seen[3]<=1; result_generation[3]<=candidate_generation; end
                if (activate_scene) begin
                    active_A0<=candidate_A0; active_B0<=candidate_B0; active_C0<=candidate_C0; active_frac0<=candidate_frac0;
                    active_A1<=candidate_A1; active_B1<=candidate_B1; active_C1<=candidate_C1; active_frac1<=candidate_frac1;
                    active_A2<=candidate_A2; active_B2<=candidate_B2; active_C2<=candidate_C2; active_frac2<=candidate_frac2;
                    active_A3<=candidate_A3; active_B3<=candidate_B3; active_C3<=candidate_C3; active_frac3<=candidate_frac3;
                    ready_seen <= 0;
                    state <= IDLE;
                end
            end
        end
    end
endmodule
