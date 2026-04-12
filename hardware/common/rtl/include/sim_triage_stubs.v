// sim_triage_stubs.v — minimal simulation stubs to satisfy unit tests during triage
// NOTE: These are non-functional placeholders. Remove or replace with real RTL for production.

module injection_gate (
    input clk, input reset
);
endmodule

module spu_video_timing (
    input clk, input reset, input [7:0] pix_in, output reg disp_ready
);
    always @(*) disp_ready = 1'b0;
endmodule

module spu_raster_unit (
    input clk, input reset
);
endmodule

module rational_sine_provider #(
    parameter DEPTH = 4096,
    parameter HIGH_PRECISION = 0
) (
    input clk,
    input reset,
    input [$clog2(DEPTH)-1:0] addr,
    output reg signed [31:0] pout,
    output reg signed [31:0] qout
);
    always @(*) begin
        pout = 32'sd0;
        qout = 32'sd0;
    end
endmodule

module pade_eval_4_4 (
    input clk,
    input rst_n,
    input start,
    input signed [63:0] x_q32,
    input cfg_wr_en,
    input [2:0] cfg_wr_sel,
    input [2:0] cfg_wr_addr,
    input [63:0] cfg_wr_data,
    output reg signed [31:0] exp_q16,
    output reg done,
    output reg busy
);
    initial begin
        exp_q16 = 32'sd0;
        done = 1'b1;
        busy = 1'b0;
    end
endmodule

module davis_to_rplu (
    input clk, input reset
);
endmodule

module rational_sine_rom (
    input clk, input [15:0] addr, output reg [31:0] data
);
    always @(*) data = 32'd0;
endmodule

module laminar_detector (
    input clk, input reset
);
endmodule

module rplu_skel (
    input clk, input reset
);
endmodule

module simple_lau (
    input clk,
    input rst_n,
    input start,
    input signed [15:0] pcm_in,
    output reg signed [31:0] vout_q16,
    output reg valid_out
);
    always @(*) begin
        vout_q16 = 32'sd0;
        valid_out = 1'b0;
    end
endmodule

module rplu_exp (
    input clk, input reset
);
endmodule
