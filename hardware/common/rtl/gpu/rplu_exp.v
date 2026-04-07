// RPLU exp-approx pipeline (normalized units Q16.16)
// Inputs: r_q16, material select -> use params ROM for a_q16,re_q16, De normalized=1.0
module rplu_exp (
    input wire clk,
    input wire rst_n,
    input wire start,
    input wire [9:0] addr,
    input wire material_id,
    input wire signed [31:0] r_q16,
    output reg signed [31:0] v_q16,
    output reg dissoc,
    output reg done
);

    // params ROMs (small text files produced by generator)
    reg [31:0] params_carbon [0:2];
    reg [31:0] params_iron   [0:2];
    initial begin
        // file format: a_q16, re_q16, De_q16 (each 32-bit hex per line)
        $readmemh("hardware/common/rtl/gpu/params_carbon.hex", params_carbon);
        $readmemh("hardware/common/rtl/gpu/params_iron.hex", params_iron);
    end

    // Padé [4/4] coeffs (Q32 and improved Q16 available)
    reg signed [63:0] pade_num_q32 [0:4];
    reg signed [63:0] pade_den_q32 [0:4];
    // keep Q16 mems for fallback compatibility
    reg signed [31:0] pade_num_q16 [0:4];
    reg signed [31:0] pade_den_q16 [0:4];
    initial begin
        // read Q32 coeffs (preferred)
        $readmemh("hardware/common/rtl/gpu/pade_num_4_4_q32.mem", pade_num_q32);
        $readmemh("hardware/common/rtl/gpu/pade_den_4_4_q32.mem", pade_den_q32);
        // also read Q16 for tools that expect them
        $readmemh("hardware/common/rtl/gpu/pade_num_4_4.mem", pade_num_q16);
        $readmemh("hardware/common/rtl/gpu/pade_den_4_4.mem", pade_den_q16);
    end

    reg signed [31:0] a_q16, re_q16;
    reg [31:0] De_q16;

    // pipeline registers
    reg signed [31:0] r_reg;
    reg signed [31:0] delta_q16;
    reg signed [63:0] x_q32;          // Q32.32 (a_q16 * delta_q16 -> Q32)
    reg signed [127:0] acc_num128;    // accumulator in Q32 represented in 128 bits
    reg signed [127:0] acc_den128;
    reg signed [127:0] mult128;
    reg signed [127:0] numer128;
    reg signed [127:0] quot128;
    reg [7:0] idx;
    reg signed [31:0] exp_q16;
    reg signed [31:0] t_q16;
    reg signed [63:0] t2_q32;
    reg signed [63:0] v_q32;

    reg signed [63:0] x_q32_temp;
    reg signed [55:0] idx_temp;

    localparam integer XMAX_SCALED = 262144; // XMAX(4.0) * 2^16

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            v_q16 <= 0; dissoc <= 0; done <= 0;
            r_reg <= 0; delta_q16 <= 0; x_q32 <= 0; idx <= 0; exp_q16 <= 0; t_q16 <= 0; t2_q32 <= 0; v_q32 <= 0;
            a_q16 <= 0; re_q16 <= 0; De_q16 <= 32'sd65536;
        end else begin
            done <= 1'b0;
            if (start) begin
                // load params (three-word files)
                if (material_id == 1'b0) begin
                    a_q16  = $signed(params_carbon[0]);
                    re_q16 = $signed(params_carbon[1]);
                    De_q16 = params_carbon[2];
                end else begin
                    a_q16  = $signed(params_iron[0]);
                    re_q16 = $signed(params_iron[1]);
                    De_q16 = params_iron[2];
                end
                r_reg = r_q16;
                // stage1: delta = re - r (Q16.16)
                delta_q16 = re_q16 - r_q16;
                // compute x = a * delta (Q32.32 in x_q32)
                x_q32 = a_q16 * delta_q16; // signed 64-bit
                // Use Q32 Padé evaluation: x_q32 is Q32 (a_q16 * delta_q16)
                x_q32_temp = x_q32; // Q32
                // numerator Horner (Q32 arithmetic), using 128-bit intermediates
                acc_num128 = {{64{pade_num_q32[4][63]}}, pade_num_q32[4]}; // sign-extend 64->128
                mult128 = acc_num128 * x_q32_temp; // Q32*Q32 => Q64 in mult128 (scaled by 2^64)
                acc_num128 = (mult128 >>> 32) + {{64{pade_num_q32[3][63]}}, pade_num_q32[3]};
                mult128 = acc_num128 * x_q32_temp;
                acc_num128 = (mult128 >>> 32) + {{64{pade_num_q32[2][63]}}, pade_num_q32[2]};
                mult128 = acc_num128 * x_q32_temp;
                acc_num128 = (mult128 >>> 32) + {{64{pade_num_q32[1][63]}}, pade_num_q32[1]};
                mult128 = acc_num128 * x_q32_temp;
                acc_num128 = (mult128 >>> 32) + {{64{pade_num_q32[0][63]}}, pade_num_q32[0]};
                // denominator Horner
                acc_den128 = {{64{pade_den_q32[4][63]}}, pade_den_q32[4]};
                mult128 = acc_den128 * x_q32_temp;
                acc_den128 = (mult128 >>> 32) + {{64{pade_den_q32[3][63]}}, pade_den_q32[3]};
                mult128 = acc_den128 * x_q32_temp;
                acc_den128 = (mult128 >>> 32) + {{64{pade_den_q32[2][63]}}, pade_den_q32[2]};
                mult128 = acc_den128 * x_q32_temp;
                acc_den128 = (mult128 >>> 32) + {{64{pade_den_q32[1][63]}}, pade_den_q32[1]};
                mult128 = acc_den128 * x_q32_temp;
                acc_den128 = (mult128 >>> 32) + {{64{pade_den_q32[0][63]}}, pade_den_q32[0]};
                // perform division: exp_q16 = (acc_num128 << 16) / acc_den128  -> result Q16.16
                if (acc_den128 == 0) begin
                    exp_q16 = 32'sd0;
                end else begin
                    // compute  (acc_num128 * 2^16) / acc_den128
                    reg signed [127:0] numer128;
                    numer128 = acc_num128 <<< 16;
                    reg signed [127:0] quot128;
                    quot128 = numer128 / acc_den128; // Q16.16 in lower 64 bits
                    exp_q16 = quot128[31:0];
                end
                // compute t = 1 - exp
                t_q16 = 32'sd65536 - exp_q16;
                // t^2 (Q16.16)
                t2_q32 = (t_q16 * t_q16) >>> 16;
                // v = De * t2 >> 16 (result Q16.16)
                v_q32 = (De_q16 * t2_q32) >>> 16;
                v_q16 = v_q32[31:0];
                // dissoc if v >= De (normalized De=1<<16)
                dissoc = (v_q16 >= 32'sd65536) ? 1'b1 : 1'b0;
                // debug print
                $display("DBG idx=%0d x_q16=%0d exp=%0d t=%0d t2=%0d v=%0d De=%0d", idx, x_q16_temp, exp_q16, t_q16, t2_q32, v_q16, De_q16);
                done = 1'b1;
            end
        end
    end
endmodule
