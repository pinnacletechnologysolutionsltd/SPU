// Auto-generated minimal stubs to unblock simulation triage
// Place: hardware/common/rtl/include/auto_stubs.v
`timescale 1ns/1ps

// Simple, conservative-width stubs.  These implement no behaviour
// other than safe default outputs so the testbench can elaborate.


module spu_gram_controller(
    input clk,
    input reset,
    input [15:0] addr,
    input [15:0] data_in,
    input write_en,
    output [15:0] data_out,
    output ready
);
    assign data_out = 16'h0;
    assign ready = 1'b1;
endmodule

module spu_fractal_bypass(
    input [255:0] q_in,
    input [1:0] phase,
    output [255:0] q_out
);
    assign q_out = q_in;
endmodule

module spu_permute(
    input clk,
    input reset,
    input [255:0] q_in,
    input [1:0] prime_phase,
    input sign_flip,
    output [255:0] q_out
);
    assign q_out = q_in;
endmodule

module spu_smul_13(
    input clk,
    input reset,
    input [15:0] a1,
    input [15:0] b1,
    input [15:0] a2,
    input [15:0] b2,
    output [15:0] res_a,
    output [15:0] res_b,
    output ready
);
    assign res_a = a1;
    assign res_b = b1;
    assign ready = 1'b1;
endmodule

module spu_validator(
    input clk,
    input reset,
    input [831:0] manifold_state,
    input [31:0] current_quadrance,
    output fault_detected
);
    assign fault_detected = 1'b0;
endmodule

module spu_laminar_gate(
    input clk,
    input reset,
    input [63:0] data_in,
    input janus_flip,
    output [63:0] data_out,
    output laminar_valid
);
    assign data_out = data_in;
    assign laminar_valid = 1'b1;
endmodule

module spu_laminar_buffer(
    input clk,
    input reset,
    input [15:0] microwatts_in,
    output [15:0] microwatts_out,
    output reservoir_full
);
    assign microwatts_out = microwatts_in;
    assign reservoir_full = 1'b0;
endmodule

module spu_harmonic_transducer(
    input clk,
    input reset,
    input [7:0] ascii_in,
    input data_valid,
    output [127:0] ripple_out,
    output membrane_lock
);
    assign ripple_out = 128'h0;
    assign membrane_lock = 1'b0;
endmodule

module spu_manifold_bus(
    input clk,
    input reset,
    input [7:0] bus_addr,
    input [31:0] bus_data,
    input bus_wen,
    input bus_ren,
    output bus_ready,
    input exec_valid
);
    assign bus_ready = 1'b1;
endmodule

module spu_vertex_buffer #(
    parameter DEPTH = 16
)(
    input clk,
    input reset,
    input wr_en,
    input [63:0] wr_v0, wr_v1, wr_v2,
    input [63:0] wr_attr_v0, wr_attr_v1, wr_attr_v2,
    input rd_en,
    output [63:0] rd_v0, rd_v1, rd_v2,
    output [63:0] rd_attr_v0, rd_attr_v1, rd_attr_v2,
    output empty,
    output full
);
    assign rd_v0 = 64'h0;
    assign rd_v1 = 64'h0;
    assign rd_v2 = 64'h0;
    assign rd_attr_v0 = 64'h0;
    assign rd_attr_v1 = 64'h0;
    assign rd_attr_v2 = 64'h0;
    assign empty = 1'b1;
    assign full = 1'b0;
endmodule

module spu_phase_switch(
    input clk,
    input reset,
    input [1:0] target_phase,
    input switch_trigger,
    input [22:0] logical_addr,
    output [22:0] physical_addr,
    output [1:0] current_phase
);
    assign physical_addr = logical_addr;
    assign current_phase = target_phase;
endmodule

module spu_lattice_13(
    input clk,
    input reset,
    input enable,
    input [831:0] manifold_in,
    output [831:0] manifold_out,
    output [51:0] scale_shifts,
    output [12:0] scale_overflows
);
    assign manifold_out = manifold_in;
    assign scale_shifts = 52'b0;
    assign scale_overflows = 13'b0;
endmodule
