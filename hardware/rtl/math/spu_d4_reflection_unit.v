// Fixed D4 simple-root reflections for four signed 16-bit lanes.
// root_sel: 0=(e0-e1), 1=(e1-e2), 2=(e2-e3), 3=(e2+e3).
module spu_d4_reflection_unit (
    input  wire [63:0] in_v,
    input  wire [1:0]  root_sel,
    output reg  [63:0] out_v,
    output reg         invalid_flag
);
    wire signed [15:0] v0 = in_v[63:48];
    wire signed [15:0] v1 = in_v[47:32];
    wire signed [15:0] v2 = in_v[31:16];
    wire signed [15:0] v3 = in_v[15:0];

    always @* begin
        out_v = in_v;
        invalid_flag = 1'b0;
        case (root_sel)
            2'd0: out_v = {v1, v0, v2, v3};
            2'd1: out_v = {v0, v2, v1, v3};
            2'd2: out_v = {v0, v1, v3, v2};
            2'd3: begin
                // The only signed-16 overflow for these negations is -32768.
                invalid_flag = (v2 == -16'sd32768) || (v3 == -16'sd32768);
                out_v = {v0, v1, -v3, -v2};
            end
        endcase
    end
endmodule
