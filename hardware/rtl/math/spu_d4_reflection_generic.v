// Generic integer reflection formula for matched P2 cost comparison.
// This is deliberately distinct from the fixed swap/sign-swap specialization.
module spu_d4_reflection_generic (
    input  wire [63:0] in_v,
    input  wire [1:0]  root_sel,
    output reg  [63:0] out_v,
    output reg         invalid_flag
);
    wire signed [15:0] v0 = in_v[63:48];
    wire signed [15:0] v1 = in_v[47:32];
    wire signed [15:0] v2 = in_v[31:16];
    wire signed [15:0] v3 = in_v[15:0];
    reg signed [1:0] a0, a1, a2, a3;
    wire signed [17:0] e0 = {{2{v0[15]}}, v0};
    wire signed [17:0] e1 = {{2{v1[15]}}, v1};
    wire signed [17:0] e2 = {{2{v2[15]}}, v2};
    wire signed [17:0] e3 = {{2{v3[15]}}, v3};
    wire signed [17:0] aw0 = {{16{a0[1]}}, a0};
    wire signed [17:0] aw1 = {{16{a1[1]}}, a1};
    wire signed [17:0] aw2 = {{16{a2[1]}}, a2};
    wire signed [17:0] aw3 = {{16{a3[1]}}, a3};
    reg signed [17:0] dot;
    reg signed [17:0] r0, r1, r2, r3;

    always @* begin
        a0 = 0; a1 = 0; a2 = 0; a3 = 0;
        case (root_sel)
            2'd0: begin a0 = 1; a1 = -1; end
            2'd1: begin a1 = 1; a2 = -1; end
            2'd2: begin a2 = 1; a3 = -1; end
            2'd3: begin a2 = 1; a3 = 1; end
        endcase
        dot = e0 * aw0 + e1 * aw1 + e2 * aw2 + e3 * aw3;
        r0 = e0 - dot * aw0;
        r1 = e1 - dot * aw1;
        r2 = e2 - dot * aw2;
        r3 = e3 - dot * aw3;
        invalid_flag = (r0 < -18'sd32768) || (r0 > 18'sd32767) ||
                       (r1 < -18'sd32768) || (r1 > 18'sd32767) ||
                       (r2 < -18'sd32768) || (r2 > 18'sd32767) ||
                       (r3 < -18'sd32768) || (r3 > 18'sd32767);
        out_v = {r0[15:0], r1[15:0], r2[15:0], r3[15:0]};
    end
endmodule
