// T1h four-lane scalar setup, frame-boundary state, and pixel interpolation.
// Scalar results are selected with the existing depth winner identity.
// CC0 1.0 Universal.

module spu_prepared_scalar_attribute4 (
    input wire clk, rst_n, enable,
    input wire [3:0] prepare,
    input wire signed [63:0] a0_bus, b0_bus, a1_bus, b1_bus, a2_bus, b2_bus,
    input wire signed [127:0] c0_bus, c1_bus, c2_bus,
    input wire [63:0] attr0_bus, attr1_bus, attr2_bus,
    input wire [3:0] depth_ready,
    input wire activate_scene, frame_start, step_x, step_y,
    input wire [1:0] pixel_id,
    input wire pixel_valid,
    output wire [3:0] attr_ready,
    output wire [3:0] joined_ready,
    output wire signed [55:0] fragment_scalar,
    output wire fragment_scalar_valid
);
    wire [3:0] attr_setup = enable ? prepare : 4'b0000;
    assign joined_ready = depth_ready & attr_ready;

    wire signed [55:0] candidate_A_attr0, candidate_B_attr0, candidate_C_attr0;
    wire signed [55:0] candidate_A_attr1, candidate_B_attr1, candidate_C_attr1;
    wire signed [55:0] candidate_A_attr2, candidate_B_attr2, candidate_C_attr2;
    wire signed [55:0] candidate_A_attr3, candidate_B_attr3, candidate_C_attr3;
    wire [6:0] candidate_frac_attr0, candidate_frac_attr1;
    wire [6:0] candidate_frac_attr2, candidate_frac_attr3;

    spu_depth_dispatch4 u_attribute_dispatch4 (
        .clk(clk), .rst_n(rst_n), .depth_setup(attr_setup),
        .a0_bus(a0_bus), .b0_bus(b0_bus), .a1_bus(a1_bus), .b1_bus(b1_bus),
        .a2_bus(a2_bus), .b2_bus(b2_bus), .c0_bus(c0_bus), .c1_bus(c1_bus), .c2_bus(c2_bus),
        .z0_bus(attr0_bus), .z1_bus(attr1_bus), .z2_bus(attr2_bus),
        .A_z0(candidate_A_attr0), .B_z0(candidate_B_attr0), .C_z0(candidate_C_attr0),
        .frac_bits0(candidate_frac_attr0), .ready0(attr_ready[0]),
        .A_z1(candidate_A_attr1), .B_z1(candidate_B_attr1), .C_z1(candidate_C_attr1),
        .frac_bits1(candidate_frac_attr1), .ready1(attr_ready[1]),
        .A_z2(candidate_A_attr2), .B_z2(candidate_B_attr2), .C_z2(candidate_C_attr2),
        .frac_bits2(candidate_frac_attr2), .ready2(attr_ready[2]),
        .A_z3(candidate_A_attr3), .B_z3(candidate_B_attr3), .C_z3(candidate_C_attr3),
        .frac_bits3(candidate_frac_attr3), .ready3(attr_ready[3]));

    reg signed [55:0] active_A_attr0, active_B_attr0, active_C_attr0;
    reg signed [55:0] active_A_attr1, active_B_attr1, active_C_attr1;
    reg signed [55:0] active_A_attr2, active_B_attr2, active_C_attr2;
    reg signed [55:0] active_A_attr3, active_B_attr3, active_C_attr3;
    reg [6:0] active_frac_attr0, active_frac_attr1;
    reg [6:0] active_frac_attr2, active_frac_attr3;
    reg scalar_armed;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            scalar_armed<=1'b0;
            active_A_attr0<=0; active_B_attr0<=0; active_C_attr0<=0; active_frac_attr0<=0;
            active_A_attr1<=0; active_B_attr1<=0; active_C_attr1<=0; active_frac_attr1<=0;
            active_A_attr2<=0; active_B_attr2<=0; active_C_attr2<=0; active_frac_attr2<=0;
            active_A_attr3<=0; active_B_attr3<=0; active_C_attr3<=0; active_frac_attr3<=0;
        end else if (enable && activate_scene) begin
            scalar_armed<=1'b1;
            active_A_attr0<=candidate_A_attr0; active_B_attr0<=candidate_B_attr0;
            active_C_attr0<=candidate_C_attr0; active_frac_attr0<=candidate_frac_attr0;
            active_A_attr1<=candidate_A_attr1; active_B_attr1<=candidate_B_attr1;
            active_C_attr1<=candidate_C_attr1; active_frac_attr1<=candidate_frac_attr1;
            active_A_attr2<=candidate_A_attr2; active_B_attr2<=candidate_B_attr2;
            active_C_attr2<=candidate_C_attr2; active_frac_attr2<=candidate_frac_attr2;
            active_A_attr3<=candidate_A_attr3; active_B_attr3<=candidate_B_attr3;
            active_C_attr3<=candidate_C_attr3; active_frac_attr3<=candidate_frac_attr3;
        end
    end

    wire scalar_setup = enable && (activate_scene || (frame_start && scalar_armed));
    wire signed [55:0] value0, value1, value2, value3;
    spu_attr_stepper u_scalar0 (.clk(clk), .rst_n(rst_n), .setup(scalar_setup),
        .a_coef(activate_scene ? candidate_A_attr0 : active_A_attr0),
        .b_coef(activate_scene ? candidate_B_attr0 : active_B_attr0),
        .c_coef(activate_scene ? candidate_C_attr0 : active_C_attr0),
        .step_x(step_x), .step_y(step_y),
        .frac_bits(activate_scene ? candidate_frac_attr0 : active_frac_attr0), .value_out(value0));
    spu_attr_stepper u_scalar1 (.clk(clk), .rst_n(rst_n), .setup(scalar_setup),
        .a_coef(activate_scene ? candidate_A_attr1 : active_A_attr1),
        .b_coef(activate_scene ? candidate_B_attr1 : active_B_attr1),
        .c_coef(activate_scene ? candidate_C_attr1 : active_C_attr1),
        .step_x(step_x), .step_y(step_y),
        .frac_bits(activate_scene ? candidate_frac_attr1 : active_frac_attr1), .value_out(value1));
    spu_attr_stepper u_scalar2 (.clk(clk), .rst_n(rst_n), .setup(scalar_setup),
        .a_coef(activate_scene ? candidate_A_attr2 : active_A_attr2),
        .b_coef(activate_scene ? candidate_B_attr2 : active_B_attr2),
        .c_coef(activate_scene ? candidate_C_attr2 : active_C_attr2),
        .step_x(step_x), .step_y(step_y),
        .frac_bits(activate_scene ? candidate_frac_attr2 : active_frac_attr2), .value_out(value2));
    spu_attr_stepper u_scalar3 (.clk(clk), .rst_n(rst_n), .setup(scalar_setup),
        .a_coef(activate_scene ? candidate_A_attr3 : active_A_attr3),
        .b_coef(activate_scene ? candidate_B_attr3 : active_B_attr3),
        .c_coef(activate_scene ? candidate_C_attr3 : active_C_attr3),
        .step_x(step_x), .step_y(step_y),
        .frac_bits(activate_scene ? candidate_frac_attr3 : active_frac_attr3), .value_out(value3));

    assign fragment_scalar_valid = enable && pixel_valid;
    assign fragment_scalar = !fragment_scalar_valid ? 56'sd0 :
        (pixel_id==2'd0 ? value0 : pixel_id==2'd1 ? value1 :
         pixel_id==2'd2 ? value2 : value3);
endmodule
