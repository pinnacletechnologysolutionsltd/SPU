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

    // Padé [4/4] coeffs (Q16.16)
    reg signed [31:0] pade_num [0:4];
    reg signed [31:0] pade_den [0:4];
    initial begin
        $readmemh("hardware/common/rtl/gpu/pade_num_4_4.mem", pade_num);
        $readmemh("hardware/common/rtl/gpu/pade_den_4_4.mem", pade_den);
    end

    reg signed [31:0] a_q16, re_q16;
    reg [31:0] De_q16;

    // pipeline registers
    reg signed [31:0] r_reg;
    reg signed [31:0] delta_q16;
    reg signed [63:0] x_q32;
    reg [7:0] idx;
    reg signed [31:0] exp_q16;
    reg signed [31:0] t_q16;
    reg signed [63:0] t2_q32;
    reg signed [63:0] v_q32;

    reg signed [47:0] x_q16_temp;
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
                // compute x_q16 from x_q32>>16
                x_q16_temp = x_q32 >>> 16;
                // Evaluate Padé [4/4] via Horner (coeffs Q16.16)
                reg signed [63:0] acc_num;
                reg signed [63:0] acc_den;
                // numerator Horner: p4*x + p3 ... -> start from highest
                acc_num = $signed(pade_num[4]);
                acc_num = (($signed(acc_num) * x_q16_temp) >>> 16) + $signed(pade_num[3]);
                acc_num = (($signed(acc_num) * x_q16_temp) >>> 16) + $signed(pade_num[2]);
                acc_num = (($signed(acc_num) * x_q16_temp) >>> 16) + $signed(pade_num[1]);
                acc_num = (($signed(acc_num) * x_q16_temp) >>> 16) + $signed(pade_num[0]);
                // denominator Horner
                acc_den = $signed(pade_den[4]);
                acc_den = (($signed(acc_den) * x_q16_temp) >>> 16) + $signed(pade_den[3]);
                acc_den = (($signed(acc_den) * x_q16_temp) >>> 16) + $signed(pade_den[2]);
                acc_den = (($signed(acc_den) * x_q16_temp) >>> 16) + $signed(pade_den[1]);
                acc_den = (($signed(acc_den) * x_q16_temp) >>> 16) + $signed(pade_den[0]);
                // perform division (acc_num/acc_den) in Q16.16: (acc_num << 16) / acc_den
                if (acc_den == 0) begin
                    exp_q16 = 32'sd0;
                end else begin
                    exp_q16 = ($signed(acc_num <<< 16) / $signed(acc_den));
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
