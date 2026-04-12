// sim_triage_stubs.v — minimal simulation stubs to satisfy unit tests during triage
// NOTE: These are non-functional placeholders. Remove or replace with real RTL for production.

module injection_gate (
    input clk,
    input rst_n,
    input start,
    input signed [15:0] pcm_in,
    input material_id,
    input [9:0] sector_addr,
    output reg signed [31:0] r_q16_out,
    output reg valid_out
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            r_q16_out <= 32'sd0;
            valid_out <= 1'b0;
        end else begin
            if (start) begin
                // Simple functional stub: scale PCM to Q16 and assert valid
                r_q16_out <= pcm_in << 16;
                valid_out <= 1'b1;
            end else begin
                valid_out <= 1'b0;
            end
        end
    end
endmodule

module spu_video_timing (
    input clk,
    input rst_n,
    output reg [9:0] x,
    output reg [9:0] y,
    output reg hsync,
    output reg vsync,
    output reg active
);
    localparam integer H_TOTAL = 800;
    localparam integer V_TOTAL = 525;

    initial begin
        x = 10'd0;
        y = 10'd0;
        hsync = 1'b1;
        vsync = 1'b1;
        active = 1'b0;
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            x = 10'd0;
            y = 10'd0;
            hsync = 1'b1;
            vsync = 1'b1;
            active = 1'b0;
        end else begin
            if (x == H_TOTAL - 1) begin
                x = 10'd0;
                if (y == V_TOTAL - 1) y = 10'd0; else y = y + 1;
            end else begin
                x = x + 1;
            end
            // Update active/hsync/vsync based on the new counters
            active = (x < 10'd640);
            hsync = (x >= 10'd656 && x < 10'd752) ? 1'b0 : 1'b1;
            vsync = (y >= 10'd490 && y < 10'd492) ? 1'b0 : 1'b1;
        end
    end
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
    // Coefficient memories (Q32 signed 64-bit)
    reg signed [63:0] num [0:4];
    reg signed [63:0] den [0:4];

    initial begin
        // Load coefficient ROMs (expected in repo); if missing, simulator will report but tests provide files
        $readmemh("hardware/common/rtl/gpu/pade_num_4_4_q32.mem", num);
        $readmemh("hardware/common/rtl/gpu/pade_den_4_4_q32.mem", den);
        exp_q16 = 32'sd0;
        done = 1'b1;
        busy = 1'b0;
    end

    reg signed [127:0] accn;
    reg signed [127:0] accd;
    reg signed [191:0] tmp;
    reg signed [255:0] numer;
    reg signed [255:0] quot;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            exp_q16 <= 32'sd0;
            done <= 1'b1;
            busy <= 1'b0;
            accn <= 128'sd0;
            accd <= 128'sd0;
            tmp <= 192'sd0;
            numer <= 256'sd0;
            quot <= 256'sd0;
        end else begin
            if (start && !busy) begin
                busy <= 1'b1;
                done <= 1'b0;

                // Horner evaluation for numerator (Q32)
                accn = num[4];
                tmp = accn * x_q32;
                accn = (tmp >>> 32) + num[3];
                tmp = accn * x_q32;
                accn = (tmp >>> 32) + num[2];
                tmp = accn * x_q32;
                accn = (tmp >>> 32) + num[1];
                tmp = accn * x_q32;
                accn = (tmp >>> 32) + num[0];

                // Horner evaluation for denominator (Q32)
                accd = den[4];
                tmp = accd * x_q32;
                accd = (tmp >>> 32) + den[3];
                tmp = accd * x_q32;
                accd = (tmp >>> 32) + den[2];
                tmp = accd * x_q32;
                accd = (tmp >>> 32) + den[1];
                tmp = accd * x_q32;
                accd = (tmp >>> 32) + den[0];

                if (accd == 0) begin
                    exp_q16 <= 32'sd0;
                end else begin
                    // Scale numerator to Q16 and divide
                    numer = accn <<< 16;
                    quot = numer / accd;
                    exp_q16 <= quot[31:0];
                end

                done <= 1'b1;
                busy <= 1'b0;
            end
        end
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
