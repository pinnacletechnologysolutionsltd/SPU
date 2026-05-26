// spu_bio_stubs.v — Empty stubs for bio/I2S/torus modules
// Used when building minimal configs that don't need these modules.

module spu_annealer(input clk, reset, enable, input [831:0] reg_in, output [831:0] reg_out);
    assign reg_out = reg_in;
endmodule

module spu_active_inference(input clk, reset, input [127:0] prior_state, input [15:0] prior_precision,
    input [127:0] sensory_in, input sensory_valid, output [127:0] posterior_state,
    output [127:0] prediction_error, output is_dissonant);
    assign posterior_state = prior_state;
    assign prediction_error = 0;
    assign is_dissonant = 0;
endmodule

module spu_viscosity_monitor(input clk, reset, input [127:0] abcd_vector, output [7:0] laminar_flow_index);
    assign laminar_flow_index = 8'h80;
endmodule

module spu_proprioception(input clk, reset, input [831:0] manifold_state,
    output [31:0] thermal_pressure, output damping_active);
    assign thermal_pressure = 0;
    assign damping_active = 0;
endmodule

module spu_i2s_out(input clk, rst_n, input [1:0] mode, input [15:0] lfi,
    input [23:0] left_data, right_data, output i2s_bclk, i2s_lrclk, i2s_dout);
    assign i2s_bclk = 0; assign i2s_lrclk = 0; assign i2s_dout = 0;
endmodule

module toroidal_regfile #(parameter WIDTH = 832, NUM = 8)
   (input clk, rst_n, wr_en, input [2:0] wr_addr, input [831:0] wr_data,
    input rd_en, input [2:0] rd_addr, output [831:0] rd_data,
    input rotate_start, input [31:0] rotate_amount, input [2:0] rotate_idx,
    input rotate_dir, method_sel, output rotate_done);
    assign rd_data = 0; assign rotate_done = 0;
endmodule

module spu_soul_metabolism #(parameter CLK_HZ = 12000000)
   (input clk, reset, input [127:0] q_state, input fault_pulse, is_idle,
    output [31:0] adaptive_tau_q, output [31:0] tuck_count, cycle_count,
    output flash_we, output [23:0] flash_addr, output [255:0] soul_page, input flash_ready);
    assign adaptive_tau_q = 32'h0100_0000;
    assign tuck_count = 0; assign cycle_count = 0;
    assign flash_we = 0; assign flash_addr = 0; assign soul_page = 0;
endmodule

