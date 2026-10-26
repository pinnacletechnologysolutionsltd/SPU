// spu13_lattice.v - simple SPU-13 lattice that instantiates 13 laminar_node primitives
// and provides a basic "stitcher" prototype. This is intentionally minimal and
// serves as a hook for floorplanner instance naming (u_spu13/node_X).

module spu13_lattice #(
    parameter NODES = 13,
    parameter WIDTH = 64
)(
    input  wire                     clk,
    input  wire                     rst_n,
    input  wire                     enable,
    input  wire [NODES*WIDTH-1:0]   manifold_in,
    output wire [NODES*WIDTH-1:0]   manifold_out,
    output wire [NODES*4-1:0]       scale_shifts,
    output wire [NODES-1:0]         scale_overflows
);

    // Individual node outputs
    wire [WIDTH-1:0] node_out0;  wire [WIDTH-1:0] node_out1;  wire [WIDTH-1:0] node_out2;
    wire [WIDTH-1:0] node_out3;  wire [WIDTH-1:0] node_out4;  wire [WIDTH-1:0] node_out5;
    wire [WIDTH-1:0] node_out6;  wire [WIDTH-1:0] node_out7;  wire [WIDTH-1:0] node_out8;
    wire [WIDTH-1:0] node_out9;  wire [WIDTH-1:0] node_out10; wire [WIDTH-1:0] node_out11;
    wire [WIDTH-1:0] node_out12;

    // Instantiate laminar_node primitives (explicit names for floorplanner hooks)
    laminar_node #(.WIDTH(WIDTH)) node_0  (.clk(clk), .rst_n(rst_n), .enable(enable), .surd_in(manifold_in[0*WIDTH +: WIDTH]),  .surd_out(node_out0));
    laminar_node #(.WIDTH(WIDTH)) node_1  (.clk(clk), .rst_n(rst_n), .enable(enable), .surd_in(manifold_in[1*WIDTH +: WIDTH]),  .surd_out(node_out1));
    laminar_node #(.WIDTH(WIDTH)) node_2  (.clk(clk), .rst_n(rst_n), .enable(enable), .surd_in(manifold_in[2*WIDTH +: WIDTH]),  .surd_out(node_out2));
    laminar_node #(.WIDTH(WIDTH)) node_3  (.clk(clk), .rst_n(rst_n), .enable(enable), .surd_in(manifold_in[3*WIDTH +: WIDTH]),  .surd_out(node_out3));
    laminar_node #(.WIDTH(WIDTH)) node_4  (.clk(clk), .rst_n(rst_n), .enable(enable), .surd_in(manifold_in[4*WIDTH +: WIDTH]),  .surd_out(node_out4));
    laminar_node #(.WIDTH(WIDTH)) node_5  (.clk(clk), .rst_n(rst_n), .enable(enable), .surd_in(manifold_in[5*WIDTH +: WIDTH]),  .surd_out(node_out5));
    laminar_node #(.WIDTH(WIDTH)) node_6  (.clk(clk), .rst_n(rst_n), .enable(enable), .surd_in(manifold_in[6*WIDTH +: WIDTH]),  .surd_out(node_out6));
    laminar_node #(.WIDTH(WIDTH)) node_7  (.clk(clk), .rst_n(rst_n), .enable(enable), .surd_in(manifold_in[7*WIDTH +: WIDTH]),  .surd_out(node_out7));
    laminar_node #(.WIDTH(WIDTH)) node_8  (.clk(clk), .rst_n(rst_n), .enable(enable), .surd_in(manifold_in[8*WIDTH +: WIDTH]),  .surd_out(node_out8));
    laminar_node #(.WIDTH(WIDTH)) node_9  (.clk(clk), .rst_n(rst_n), .enable(enable), .surd_in(manifold_in[9*WIDTH +: WIDTH]),  .surd_out(node_out9));
    laminar_node #(.WIDTH(WIDTH)) node_10 (.clk(clk), .rst_n(rst_n), .enable(enable), .surd_in(manifold_in[10*WIDTH +: WIDTH]), .surd_out(node_out10));
    laminar_node #(.WIDTH(WIDTH)) node_11 (.clk(clk), .rst_n(rst_n), .enable(enable), .surd_in(manifold_in[11*WIDTH +: WIDTH]), .surd_out(node_out11));
    laminar_node #(.WIDTH(WIDTH)) node_12 (.clk(clk), .rst_n(rst_n), .enable(enable), .surd_in(manifold_in[12*WIDTH +: WIDTH]), .surd_out(node_out12));

    // Phinary stitcher: use rational_surd5_mul64 + rational_surd5_add to
    // combine neighbouring nodes in a simple chordal synthesis, then normalize outputs.

    // Multiply pairs
    wire [WIDTH-1:0] mul_01; rational_surd5_mul64 u_mul_01 (.a(node_out0),  .b(node_out1),  .out(mul_01));
    wire [WIDTH-1:0] mul_12; rational_surd5_mul64 u_mul_12 (.a(node_out1),  .b(node_out2),  .out(mul_12));
    wire [WIDTH-1:0] mul_23; rational_surd5_mul64 u_mul_23 (.a(node_out2),  .b(node_out3),  .out(mul_23));
    wire [WIDTH-1:0] mul_34; rational_surd5_mul64 u_mul_34 (.a(node_out3),  .b(node_out4),  .out(mul_34));
    wire [WIDTH-1:0] mul_45; rational_surd5_mul64 u_mul_45 (.a(node_out4),  .b(node_out5),  .out(mul_45));
    wire [WIDTH-1:0] mul_56; rational_surd5_mul64 u_mul_56 (.a(node_out5),  .b(node_out6),  .out(mul_56));
    wire [WIDTH-1:0] mul_67; rational_surd5_mul64 u_mul_67 (.a(node_out6),  .b(node_out7),  .out(mul_67));
    wire [WIDTH-1:0] mul_78; rational_surd5_mul64 u_mul_78 (.a(node_out7),  .b(node_out8),  .out(mul_78));
    wire [WIDTH-1:0] mul_89; rational_surd5_mul64 u_mul_89 (.a(node_out8),  .b(node_out9),  .out(mul_89));
    wire [WIDTH-1:0] mul_9a; rational_surd5_mul64 u_mul_9a (.a(node_out9),  .b(node_out10), .out(mul_9a));
    wire [WIDTH-1:0] mul_ab; rational_surd5_mul64 u_mul_ab (.a(node_out10), .b(node_out11), .out(mul_ab));
    wire [WIDTH-1:0] mul_bc; rational_surd5_mul64 u_mul_bc (.a(node_out11), .b(node_out12), .out(mul_bc));
    wire [WIDTH-1:0] mul_c0; rational_surd5_mul64 u_mul_c0 (.a(node_out12), .b(node_out0),  .out(mul_c0));

    // Add with local node to form the stitched chord (raw)
    wire [WIDTH-1:0] post0_raw;  rational_surd5_add u_add_0  (.a(node_out0),  .b(mul_01), .out(post0_raw));
    wire [WIDTH-1:0] post1_raw;  rational_surd5_add u_add_1  (.a(node_out1),  .b(mul_12), .out(post1_raw));
    wire [WIDTH-1:0] post2_raw;  rational_surd5_add u_add_2  (.a(node_out2),  .b(mul_23), .out(post2_raw));
    wire [WIDTH-1:0] post3_raw;  rational_surd5_add u_add_3  (.a(node_out3),  .b(mul_34), .out(post3_raw));
    wire [WIDTH-1:0] post4_raw;  rational_surd5_add u_add_4  (.a(node_out4),  .b(mul_45), .out(post4_raw));
    wire [WIDTH-1:0] post5_raw;  rational_surd5_add u_add_5  (.a(node_out5),  .b(mul_56), .out(post5_raw));
    wire [WIDTH-1:0] post6_raw;  rational_surd5_add u_add_6  (.a(node_out6),  .b(mul_67), .out(post6_raw));
    wire [WIDTH-1:0] post7_raw;  rational_surd5_add u_add_7  (.a(node_out7),  .b(mul_78), .out(post7_raw));
    wire [WIDTH-1:0] post8_raw;  rational_surd5_add u_add_8  (.a(node_out8),  .b(mul_89), .out(post8_raw));
    wire [WIDTH-1:0] post9_raw;  rational_surd5_add u_add_9  (.a(node_out9),  .b(mul_9a), .out(post9_raw));
    wire [WIDTH-1:0] post10_raw; rational_surd5_add u_add_10 (.a(node_out10), .b(mul_ab), .out(post10_raw));
    wire [WIDTH-1:0] post11_raw; rational_surd5_add u_add_11 (.a(node_out11), .b(mul_bc), .out(post11_raw));
    wire [WIDTH-1:0] post12_raw; rational_surd5_add u_add_12 (.a(node_out12), .b(mul_c0), .out(post12_raw));

    // Normalize each stitched output
    wire [WIDTH-1:0] post0; wire [3:0] post0_shift; wire post0_oflow; rational_surd5_norm u_norm_0 (.in(post0_raw), .out(post0), .scale_shift(post0_shift), .overflow(post0_oflow));
    wire [WIDTH-1:0] post1; wire [3:0] post1_shift; wire post1_oflow; rational_surd5_norm u_norm_1 (.in(post1_raw), .out(post1), .scale_shift(post1_shift), .overflow(post1_oflow));
    wire [WIDTH-1:0] post2; wire [3:0] post2_shift; wire post2_oflow; rational_surd5_norm u_norm_2 (.in(post2_raw), .out(post2), .scale_shift(post2_shift), .overflow(post2_oflow));
    wire [WIDTH-1:0] post3; wire [3:0] post3_shift; wire post3_oflow; rational_surd5_norm u_norm_3 (.in(post3_raw), .out(post3), .scale_shift(post3_shift), .overflow(post3_oflow));
    wire [WIDTH-1:0] post4; wire [3:0] post4_shift; wire post4_oflow; rational_surd5_norm u_norm_4 (.in(post4_raw), .out(post4), .scale_shift(post4_shift), .overflow(post4_oflow));
    wire [WIDTH-1:0] post5; wire [3:0] post5_shift; wire post5_oflow; rational_surd5_norm u_norm_5 (.in(post5_raw), .out(post5), .scale_shift(post5_shift), .overflow(post5_oflow));
    wire [WIDTH-1:0] post6; wire [3:0] post6_shift; wire post6_oflow; rational_surd5_norm u_norm_6 (.in(post6_raw), .out(post6), .scale_shift(post6_shift), .overflow(post6_oflow));
    wire [WIDTH-1:0] post7; wire [3:0] post7_shift; wire post7_oflow; rational_surd5_norm u_norm_7 (.in(post7_raw), .out(post7), .scale_shift(post7_shift), .overflow(post7_oflow));
    wire [WIDTH-1:0] post8; wire [3:0] post8_shift; wire post8_oflow; rational_surd5_norm u_norm_8 (.in(post8_raw), .out(post8), .scale_shift(post8_shift), .overflow(post8_oflow));
    wire [WIDTH-1:0] post9; wire [3:0] post9_shift; wire post9_oflow; rational_surd5_norm u_norm_9 (.in(post9_raw), .out(post9), .scale_shift(post9_shift), .overflow(post9_oflow));
    wire [WIDTH-1:0] post10; wire [3:0] post10_shift; wire post10_oflow; rational_surd5_norm u_norm_10 (.in(post10_raw), .out(post10), .scale_shift(post10_shift), .overflow(post10_oflow));
    wire [WIDTH-1:0] post11; wire [3:0] post11_shift; wire post11_oflow; rational_surd5_norm u_norm_11 (.in(post11_raw), .out(post11), .scale_shift(post11_shift), .overflow(post11_oflow));
    wire [WIDTH-1:0] post12; wire [3:0] post12_shift; wire post12_oflow; rational_surd5_norm u_norm_12 (.in(post12_raw), .out(post12), .scale_shift(post12_shift), .overflow(post12_oflow));

    // Pack normalized outputs back into manifold_out using the same ordering
    assign manifold_out[0*WIDTH +: WIDTH]  = post0;
    assign manifold_out[1*WIDTH +: WIDTH]  = post1;
    assign manifold_out[2*WIDTH +: WIDTH]  = post2;
    assign manifold_out[3*WIDTH +: WIDTH]  = post3;
    assign manifold_out[4*WIDTH +: WIDTH]  = post4;
    assign manifold_out[5*WIDTH +: WIDTH]  = post5;
    assign manifold_out[6*WIDTH +: WIDTH]  = post6;
    assign manifold_out[7*WIDTH +: WIDTH]  = post7;
    assign manifold_out[8*WIDTH +: WIDTH]  = post8;
    assign manifold_out[9*WIDTH +: WIDTH]  = post9;
    assign manifold_out[10*WIDTH +: WIDTH] = post10;
    assign manifold_out[11*WIDTH +: WIDTH] = post11;
    assign manifold_out[12*WIDTH +: WIDTH] = post12;

    // Export per-node scale shifts and overflow flags
    assign scale_shifts = {post12_shift, post11_shift, post10_shift, post9_shift, post8_shift, post7_shift, post6_shift, post5_shift, post4_shift, post3_shift, post2_shift, post1_shift, post0_shift};
    assign scale_overflows = {post12_oflow, post11_oflow, post10_oflow, post9_oflow, post8_oflow, post7_oflow, post6_oflow, post5_oflow, post4_oflow, post3_oflow, post2_oflow, post1_oflow, post0_oflow};

endmodule
