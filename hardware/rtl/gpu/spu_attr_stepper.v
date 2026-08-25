// spu_attr_stepper.v — per-pixel incremental attribute accumulator.
// Same accumulation shape as spu_edge_stepper.v's f/f_row (seed at row
// start, += A per step_x, += B per step_y), but outputs a wide signed
// value instead of a boolean inside-test. Used for depth-v2's affine-
// interpolated depth: A_z/B_z/C_z are computed once at triangle setup
// by spu_depth_setup.v (setup-time only reciprocal, see
// spu_strategy/contract_gpu_depth_v2_scoping_2026-08-25.md), and this
// module does the per-pixel work with pure incremental add -- no
// multiply, no divide in the hot path.
//
// 56-bit accumulator: measured peak magnitude across a full 640x480
// scan is ~52 bits (contract_gpu_depth_v2_shared_multiplier_arch_2026-08-25.md
// §1), rounded up for margin.
//
// No floating point, no division. CC0 1.0 Universal.

module spu_attr_stepper (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        setup,
    input  wire signed [55:0] a_coef,
    input  wire signed [55:0] b_coef,
    input  wire signed [55:0] c_coef,
    input  wire        step_x,
    input  wire        step_y,
    input  wire [6:0]  frac_bits,     // right-shift amount at readout,
                                       // matches spu_reciprocal_core.v's
                                       // exp_out width (up to ~49; a
                                       // narrower port here would wrap
                                       // silently -- a real bug this
                                       // module's own testbench caught
                                       // when it was [4:0])
    output wire signed [55:0] value_out
);

    reg signed [55:0] acc;
    reg signed [55:0] acc_row;
    reg signed [55:0] a_r, b_r;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            acc     <= 56'sd0;
            acc_row <= 56'sd0;
            a_r     <= 56'sd0;
            b_r     <= 56'sd0;
        end else if (setup) begin
            a_r     <= a_coef;
            b_r     <= b_coef;
            acc     <= c_coef;
            acc_row <= c_coef;
        end else if (step_y) begin
            acc_row <= acc_row + b_r;
            acc     <= acc_row + b_r;
        end else if (step_x) begin
            acc <= acc + a_r;
        end
    end

    // Readout is the accumulated value shifted right by frac_bits --
    // truncation happens explicitly here, at this one consuming point,
    // per the shared-multiplier contract's "no hidden precision
    // decisions" invariant (spu_shared_mult35.v never truncates either).
    assign value_out = acc >>> frac_bits;

endmodule
