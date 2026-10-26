// spu13_tang25k_mult42_probe.v — shared-multiplier isolation area probe
//
// Synthesis/place-route AREA MEASUREMENT ONLY, not a silicon claim. Tests
// exactly one thing: what does a single 42x42 signed multiplier (the
// shape contract_gpu_depth_v2_shared_multiplier_arch_2026-08-25.md
// proposes reusing across ~14 FSM states) cost on this Tang 25K /
// nextpnr-himbaechel flow -- the flow that produced series_stream_probe's
// proven 305% blowup from a single combinational M31 multiplier
// (docs/hardware_evidence.md §3.6g). See
// spu_strategy/contract_gpu_mult42_isolation_probe_2026-08-25.md.
//
// Operands are free-running, non-constant counters so Yosys cannot
// constant-fold the multiply away and under-report its cost. Output is
// folded into led[2:0] every cycle to keep the multiplier's result live.

module spu13_tang25k_mult42_probe (
    input  wire       sys_clk,
    output wire [2:0] led
);

    reg [7:0] rst_cnt = 0;
    wire rst_n = (rst_cnt == 8'hFF);
    always @(posedge sys_clk) if (!rst_n) rst_cnt <= rst_cnt + 1;

    // Two independent, non-constant 42-bit operand sources.
    reg [41:0] ctr_a, ctr_b;
    always @(posedge sys_clk or negedge rst_n) begin
        if (!rst_n) begin
            ctr_a <= 42'h00000_00001;
            ctr_b <= 42'h2AAAA_AAAAA;
        end else begin
            ctr_a <= ctr_a + 42'h2AAAA_AAAA9;          // odd increment, full period
            ctr_b <= ctr_b ^ {ctr_b[0], ctr_b[41:1]};  // rotate-xor, non-constant
        end
    end

    wire signed [41:0] op_a = ctr_a;
    wire signed [41:0] op_b = ctr_b;
    wire signed [83:0] product = op_a * op_b;

    // Registered accumulator -- same shape one shared-multiplier FSM
    // state (e.g. M_SCALE_A) would need: combinational multiply feeding
    // a register on the same clock edge.
    reg signed [83:0] acc = 84'sd0;
    always @(posedge sys_clk) acc <= acc + product;

    reg [2:0] led_reg = 3'b0;
    always @(posedge sys_clk) led_reg <= led_reg ^ {acc[83], acc[41], acc[0]};
    assign led = led_reg;

endmodule
