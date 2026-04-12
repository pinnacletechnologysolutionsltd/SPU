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

module rational_sine_provider (
    input clk, input reset, input [15:0] addr, output reg [31:0] data
);
    always @(*) data = 32'd0;
endmodule

module pade_eval_4_4 (
    input clk, input reset
);
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
    input clk, input reset
);
endmodule

module rplu_exp (
    input clk, input reset
);
endmodule
