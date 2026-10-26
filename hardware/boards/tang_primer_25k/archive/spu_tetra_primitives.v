// SPU-13 Tetrahedral Primitives (v1.0)
`define LAMINAR_MUX(sel, a, b, width) (({width{sel}} & (a)) ^ ({width{~sel}} & (b)))

module t_and_gate (input [3:0] quad_in, input [17:0] delta, output y_out, output snap_locked);
    assign y_out = &quad_in; assign snap_locked = 1;
endmodule

module t_xor_gate (input a, b, output y_out);
    assign y_out = a ^ b;
endmodule

module t_majority_gate (input [3:0] bits_in, output y_out, output snap_locked);
    assign y_out = ^bits_in;
    assign snap_locked = 1'b1;
endmodule
