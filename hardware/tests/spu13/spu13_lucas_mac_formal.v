// spu13_lucas_mac_formal.v — Formal proof for Lucas MAC PSCALE.
//
// Uses standard reset pattern: rst_n low at step 0 to initialize DUT,
// then high for all subsequent steps.

`define ASSERT assert

module spu13_lucas_mac_formal (
    input wire clk,
    input wire rst_n
);
    localparam L_P = 521;
    localparam L_P_BITS = 10;
    localparam [2:0] OP_PSCALE = 0;

    reg [L_P_BITS-1:0] op_a, op_b;
    reg start, ce;
    reg [2:0] opcode;

    wire done, error;
    wire [L_P_BITS-1:0] result_a, result_b;
    wire norm_violation;

    spu13_lucas_mac #(
        .L_P(L_P), .L_P_BITS(L_P_BITS),
        .FAST_ONLY(0), .PINV_MAX_ITERS(64)
    ) u_dut (
        .clk(clk), .rst_n(rst_n), .ce(ce), .start(start),
        .opcode(opcode), .op_a(op_a), .op_b(op_b),
        .op_c(op_a), .op_d(op_b),
        .phslk_n2_a(op_a), .phslk_n2_b(op_b),
        .phslk_d2_a(op_a), .phslk_d2_b(op_b),
        .busy(), .done(done), .error(error),
        .result_a(result_a), .result_b(result_b),
        .phslk_coherent(), .phslk_zero_divisor(),
        .norm_violation(norm_violation)
    );

    reg f_past_valid;
    initial f_past_valid = 0;
    always @(posedge clk) f_past_valid <= 1;

    // Standard reset sequence:
    //   Step 0: rst_n=0 (DUT reset initializes state and registers)
    //   After step 0: rst_n=1 always
    always @(posedge clk) begin
        if (!f_past_valid) begin
            assume(!rst_n);  // reset at step 0
            assume(!start);  // no start during reset
        end else begin
            assume(rst_n);   // out of reset after step 0
        end
    end

    // No consecutive start pulses
    reg start_q;
    always @(posedge clk) start_q <= start;
    always @(*) begin
        if (f_past_valid) assume(!start || !start_q);
    end

    always @(*) assume(ce);
    always @(*) begin
        assume(op_a < L_P); assume(op_b < L_P);
        assume(opcode == 0);  // PSCALE only
        assume(!busy || !start);  // never start while DUT is busy
    end

    // At step N: $past(start) was the start value at transition N-1→N.
    // If it was PSCALE, done reflects the result of that processing.
    always @(posedge clk) begin
        if (f_past_valid && $past(start) && $past(opcode) == OP_PSCALE) begin
            `ASSERT(done);
            `ASSERT(!error);
            `ASSERT(result_b < L_P);
            `ASSERT(!norm_violation);
        end
    end

endmodule
