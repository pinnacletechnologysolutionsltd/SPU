// spu_depth_dispatch4.v — shared setup-time depth math for four primitives.
// One depth-math engine is retained; four one-deep pending slots serialize
// preparation without changing the per-pixel depth representation.
// CC0 1.0 Universal.

module spu_depth_dispatch4 (
    input wire clk, rst_n,
    input wire [3:0] depth_setup,
    input wire signed [63:0] a0_bus, b0_bus, a1_bus, b1_bus, a2_bus, b2_bus,
    input wire signed [127:0] c0_bus, c1_bus, c2_bus,
    input wire [63:0] z0_bus, z1_bus, z2_bus,
    output reg signed [55:0] A_z0, B_z0, C_z0,
    output reg [6:0] frac_bits0, output reg ready0,
    output reg signed [55:0] A_z1, B_z1, C_z1,
    output reg [6:0] frac_bits1, output reg ready1,
    output reg signed [55:0] A_z2, B_z2, C_z2,
    output reg [6:0] frac_bits2, output reg ready2,
    output reg signed [55:0] A_z3, B_z3, C_z3,
    output reg [6:0] frac_bits3, output reg ready3
);
    reg pending0, pending1, pending2, pending3;
    reg [1:0] active_unit;
    reg state;
    localparam S_IDLE = 1'b0, S_RUN = 1'b1;

    reg signed [15:0] a0_l[0:3], b0_l[0:3], a1_l[0:3], b1_l[0:3];
    reg signed [15:0] a2_l[0:3], b2_l[0:3];
    reg signed [31:0] c0_l[0:3], c1_l[0:3], c2_l[0:3];
    reg [15:0] z0_l[0:3], z1_l[0:3], z2_l[0:3];

    wire signed [15:0] a0_0 = a0_bus[15:0], a0_1 = a0_bus[31:16];
    wire signed [15:0] a0_2 = a0_bus[47:32], a0_3 = a0_bus[63:48];
    wire signed [15:0] b0_0 = b0_bus[15:0], b0_1 = b0_bus[31:16];
    wire signed [15:0] b0_2 = b0_bus[47:32], b0_3 = b0_bus[63:48];
    wire signed [15:0] a1_0 = a1_bus[15:0], a1_1 = a1_bus[31:16];
    wire signed [15:0] a1_2 = a1_bus[47:32], a1_3 = a1_bus[63:48];
    wire signed [15:0] b1_0 = b1_bus[15:0], b1_1 = b1_bus[31:16];
    wire signed [15:0] b1_2 = b1_bus[47:32], b1_3 = b1_bus[63:48];
    wire signed [15:0] a2_0 = a2_bus[15:0], a2_1 = a2_bus[31:16];
    wire signed [15:0] a2_2 = a2_bus[47:32], a2_3 = a2_bus[63:48];
    wire signed [15:0] b2_0 = b2_bus[15:0], b2_1 = b2_bus[31:16];
    wire signed [15:0] b2_2 = b2_bus[47:32], b2_3 = b2_bus[63:48];
    wire signed [31:0] c0_0 = c0_bus[31:0], c0_1 = c0_bus[63:32];
    wire signed [31:0] c0_2 = c0_bus[95:64], c0_3 = c0_bus[127:96];
    wire signed [31:0] c1_0 = c1_bus[31:0], c1_1 = c1_bus[63:32];
    wire signed [31:0] c1_2 = c1_bus[95:64], c1_3 = c1_bus[127:96];
    wire signed [31:0] c2_0 = c2_bus[31:0], c2_1 = c2_bus[63:32];
    wire signed [31:0] c2_2 = c2_bus[95:64], c2_3 = c2_bus[127:96];
    wire [15:0] z0_0 = z0_bus[15:0], z0_1 = z0_bus[31:16];
    wire [15:0] z0_2 = z0_bus[47:32], z0_3 = z0_bus[63:48];
    wire [15:0] z1_0 = z1_bus[15:0], z1_1 = z1_bus[31:16];
    wire [15:0] z1_2 = z1_bus[47:32], z1_3 = z1_bus[63:48];
    wire [15:0] z2_0 = z2_bus[15:0], z2_1 = z2_bus[31:16];
    wire [15:0] z2_2 = z2_bus[47:32], z2_3 = z2_bus[63:48];

    wire signed [15:0] a0 = active_unit == 2'd0 ? a0_l[0] : active_unit == 2'd1 ? a0_l[1] : active_unit == 2'd2 ? a0_l[2] : a0_l[3];
    wire signed [15:0] b0 = active_unit == 2'd0 ? b0_l[0] : active_unit == 2'd1 ? b0_l[1] : active_unit == 2'd2 ? b0_l[2] : b0_l[3];
    wire signed [15:0] a1 = active_unit == 2'd0 ? a1_l[0] : active_unit == 2'd1 ? a1_l[1] : active_unit == 2'd2 ? a1_l[2] : a1_l[3];
    wire signed [15:0] b1 = active_unit == 2'd0 ? b1_l[0] : active_unit == 2'd1 ? b1_l[1] : active_unit == 2'd2 ? b1_l[2] : b1_l[3];
    wire signed [15:0] a2 = active_unit == 2'd0 ? a2_l[0] : active_unit == 2'd1 ? a2_l[1] : active_unit == 2'd2 ? a2_l[2] : a2_l[3];
    wire signed [15:0] b2 = active_unit == 2'd0 ? b2_l[0] : active_unit == 2'd1 ? b2_l[1] : active_unit == 2'd2 ? b2_l[2] : b2_l[3];
    wire signed [31:0] c0 = active_unit == 2'd0 ? c0_l[0] : active_unit == 2'd1 ? c0_l[1] : active_unit == 2'd2 ? c0_l[2] : c0_l[3];
    wire signed [31:0] c1 = active_unit == 2'd0 ? c1_l[0] : active_unit == 2'd1 ? c1_l[1] : active_unit == 2'd2 ? c1_l[2] : c1_l[3];
    wire signed [31:0] c2 = active_unit == 2'd0 ? c2_l[0] : active_unit == 2'd1 ? c2_l[1] : active_unit == 2'd2 ? c2_l[2] : c2_l[3];
    wire [15:0] z0 = active_unit == 2'd0 ? z0_l[0] : active_unit == 2'd1 ? z0_l[1] : active_unit == 2'd2 ? z0_l[2] : z0_l[3];
    wire [15:0] z1 = active_unit == 2'd0 ? z1_l[0] : active_unit == 2'd1 ? z1_l[1] : active_unit == 2'd2 ? z1_l[2] : z1_l[3];
    wire [15:0] z2 = active_unit == 2'd0 ? z2_l[0] : active_unit == 2'd1 ? z2_l[1] : active_unit == 2'd2 ? z2_l[2] : z2_l[3];

    wire signed [55:0] A_z_m, B_z_m, C_z_m;
    wire [6:0] frac_bits_m;
    wire math_done;
    reg math_start_r;
    spu_depth_math u_math (.clk(clk), .rst_n(rst_n), .start(math_start_r),
        .a0(a0), .b0(b0), .a1(a1), .b1(b1), .a2(a2), .b2(b2),
        .c0(c0), .c1(c1), .c2(c2), .z0(z0), .z1(z1), .z2(z2),
        .A_z(A_z_m), .B_z(B_z_m), .C_z(C_z_m), .frac_bits(frac_bits_m),
        .done(math_done));

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pending0 <= 0; pending1 <= 0; pending2 <= 0; pending3 <= 0;
            active_unit <= 0; state <= S_IDLE; math_start_r <= 0;
            ready0 <= 0; ready1 <= 0; ready2 <= 0; ready3 <= 0;
            A_z0 <= 0; B_z0 <= 0; C_z0 <= 0; frac_bits0 <= 0;
            A_z1 <= 0; B_z1 <= 0; C_z1 <= 0; frac_bits1 <= 0;
            A_z2 <= 0; B_z2 <= 0; C_z2 <= 0; frac_bits2 <= 0;
            A_z3 <= 0; B_z3 <= 0; C_z3 <= 0; frac_bits3 <= 0;
        end else begin
            ready0 <= 0; ready1 <= 0; ready2 <= 0; ready3 <= 0;
            math_start_r <= 0;
            if (depth_setup[0]) begin
                a0_l[0]<=a0_0; b0_l[0]<=b0_0; a1_l[0]<=a1_0; b1_l[0]<=b1_0; a2_l[0]<=a2_0; b2_l[0]<=b2_0;
                c0_l[0]<=c0_0; c1_l[0]<=c1_0; c2_l[0]<=c2_0; z0_l[0]<=z0_0; z1_l[0]<=z1_0; z2_l[0]<=z2_0; pending0<=1;
            end
            if (depth_setup[1]) begin
                a0_l[1]<=a0_1; b0_l[1]<=b0_1; a1_l[1]<=a1_1; b1_l[1]<=b1_1; a2_l[1]<=a2_1; b2_l[1]<=b2_1;
                c0_l[1]<=c0_1; c1_l[1]<=c1_1; c2_l[1]<=c2_1; z0_l[1]<=z0_1; z1_l[1]<=z1_1; z2_l[1]<=z2_1; pending1<=1;
            end
            if (depth_setup[2]) begin
                a0_l[2]<=a0_2; b0_l[2]<=b0_2; a1_l[2]<=a1_2; b1_l[2]<=b1_2; a2_l[2]<=a2_2; b2_l[2]<=b2_2;
                c0_l[2]<=c0_2; c1_l[2]<=c1_2; c2_l[2]<=c2_2; z0_l[2]<=z0_2; z1_l[2]<=z1_2; z2_l[2]<=z2_2; pending2<=1;
            end
            if (depth_setup[3]) begin
                a0_l[3]<=a0_3; b0_l[3]<=b0_3; a1_l[3]<=a1_3; b1_l[3]<=b1_3; a2_l[3]<=a2_3; b2_l[3]<=b2_3;
                c0_l[3]<=c0_3; c1_l[3]<=c1_3; c2_l[3]<=c2_3; z0_l[3]<=z0_3; z1_l[3]<=z1_3; z2_l[3]<=z2_3; pending3<=1;
            end
            case (state)
                S_IDLE: begin
                    if (pending0) begin pending0<=0; active_unit<=0; math_start_r<=1; state<=S_RUN; end
                    else if (pending1) begin pending1<=0; active_unit<=1; math_start_r<=1; state<=S_RUN; end
                    else if (pending2) begin pending2<=0; active_unit<=2; math_start_r<=1; state<=S_RUN; end
                    else if (pending3) begin pending3<=0; active_unit<=3; math_start_r<=1; state<=S_RUN; end
                end
                S_RUN: if (math_done) begin
                    case (active_unit)
                        0: begin A_z0<=A_z_m; B_z0<=B_z_m; C_z0<=C_z_m; frac_bits0<=frac_bits_m; ready0<=1; end
                        1: begin A_z1<=A_z_m; B_z1<=B_z_m; C_z1<=C_z_m; frac_bits1<=frac_bits_m; ready1<=1; end
                        2: begin A_z2<=A_z_m; B_z2<=B_z_m; C_z2<=C_z_m; frac_bits2<=frac_bits_m; ready2<=1; end
                        default: begin A_z3<=A_z_m; B_z3<=B_z_m; C_z3<=C_z_m; frac_bits3<=frac_bits_m; ready3<=1; end
                    endcase
                    state <= S_IDLE;
                end
            endcase
        end
    end
endmodule
