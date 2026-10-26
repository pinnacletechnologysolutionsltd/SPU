// spu13_tang25k_mult35_probe.v — corrected shared-multiplier isolation probe
//
// Supersedes spu13_tang25k_mult42_probe.v's sizing, which was wrong: it
// sized the multiplier off A_z/B_z/C_z's OUTPUT width (~42-45 bits) rather
// than the actual operand widths feeding the final-scale multiply. The
// real widest multiply is |Sa| (35-bit magnitude, from summing three
// ~32-bit dot-product terms) x y1 (17-bit reciprocal output magnitude).
// Design is magnitude-only (unsigned) with sign handled separately outside
// the shared multiplier -- see spu_strategy/contract_gpu_depth_v2_shared_multiplier_arch_2026-08-25.md.
//
// Synthesis/PNR area measurement only, not a silicon claim. Non-constant
// operands so Yosys cannot fold the multiply away; output folded into
// led[2:0] every cycle to keep it live.

module spu13_tang25k_mult35_probe (
    input  wire       sys_clk,
    output wire [2:0] led
);

    reg [7:0] rst_cnt = 0;
    wire rst_n = (rst_cnt == 8'hFF);
    always @(posedge sys_clk) if (!rst_n) rst_cnt <= rst_cnt + 1;

    // Two independent, non-constant operand sources: 35-bit and 17-bit
    // unsigned, matching |Sa| x y1's actual widths.
    reg [34:0] ctr_a;
    reg [16:0] ctr_b;
    always @(posedge sys_clk or negedge rst_n) begin
        if (!rst_n) begin
            ctr_a <= 35'h0_0000_0001;
            ctr_b <= 17'h1_AAAA;
        end else begin
            ctr_a <= ctr_a + 35'h5_5555_5559;
            ctr_b <= ctr_b ^ {ctr_b[0], ctr_b[16:1]};
        end
    end

    wire [34:0] op_a = ctr_a;
    wire [16:0] op_b = ctr_b;
    wire [51:0] product = op_a * op_b;

    reg [51:0] acc = 52'd0;
    always @(posedge sys_clk) acc <= acc + product;

    reg [2:0] led_reg = 3'b0;
    always @(posedge sys_clk) led_reg <= led_reg ^ {acc[51], acc[25], acc[0]};
    assign led = led_reg;

endmodule
