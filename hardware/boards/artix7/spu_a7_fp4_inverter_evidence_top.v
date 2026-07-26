`timescale 1ns / 1ps

// P&R evidence harness for matched v1/v2 Fp4 inverter measurements.  This
// deliberately omits the unrelated SPI response mux whose current Yosys-0.63
// netlist is rejected by nextpnr's timing-graph construction.  A free-running
// operand source and live result reduction prevent the inverter or multiplier
// from being optimized away.
module spu_a7_fp4_inverter_evidence_top #(
    parameter USE_STRUCTURED = 0,
    parameter SEQUENTIAL = 0
) (
    input  wire       clk_100mhz,
    input  wire       rst_n,
    output wire       fault_led,
    output wire [3:0] led_out
);
    reg [127:0] stimulus;
    reg start;
    wire [31:0] z0 = {1'b0, stimulus[30:0]};
    wire [31:0] z1 = {1'b0, stimulus[62:32]};
    wire [31:0] z2 = {1'b0, stimulus[94:64]};
    wire [31:0] z3 = {1'b0, stimulus[126:96]};

    wire [31:0] inv0, inv1, inv2, inv3;
    wire done, busy, flags_v;
    wire mult_start, mult_done, mult_busy, mult_rns_error;
    wire [2:0] mult_op;
    wire [31:0] mult_a0, mult_a1, mult_a2, mult_a3;
    wire [31:0] mult_b0, mult_b1, mult_b2, mult_b3;
    wire [31:0] mult_r0, mult_r1, mult_r2, mult_r3;
    wire [3:0] debug_state;

    always @(posedge clk_100mhz or negedge rst_n) begin
        if (!rst_n) begin
            stimulus <= 128'h1;
            start <= 1'b0;
        end else begin
            stimulus <= {stimulus[126:0],
                         stimulus[127] ^ stimulus[125] ^
                         stimulus[100] ^ stimulus[98]};
            start <= !busy && !start;
        end
    end

    generate
        if (USE_STRUCTURED) begin : gen_candidate
            spu13_fp4_inverter_structured u_inv (
                .clk(clk_100mhz), .rst_n(rst_n), .start(start),
                .z0(z0), .z1(z1), .z2(z2), .z3(z3),
                .inv0(inv0), .inv1(inv1), .inv2(inv2), .inv3(inv3),
                .done(done), .busy(busy), .flags_v(flags_v),
                .mult_start(mult_start), .mult_op(mult_op),
                .mult_a0(mult_a0), .mult_a1(mult_a1),
                .mult_a2(mult_a2), .mult_a3(mult_a3),
                .mult_b0(mult_b0), .mult_b1(mult_b1),
                .mult_b2(mult_b2), .mult_b3(mult_b3),
                .mult_r0(mult_r0), .mult_r1(mult_r1),
                .mult_r2(mult_r2), .mult_r3(mult_r3),
                .mult_done(mult_done), .mult_busy(mult_busy),
                .debug_state(debug_state), .debug_start_accept()
            );
            if (SEQUENTIAL) begin : gen_seq
                spu13_m31_multiplier_seq_structured u_mult (
                    .clk(clk_100mhz), .rst_n(rst_n), .start(mult_start),
                    .op(mult_op),
                    .a0(mult_a0), .a1(mult_a1), .a2(mult_a2), .a3(mult_a3),
                    .b0(mult_b0), .b1(mult_b1), .b2(mult_b2), .b3(mult_b3),
                    .r0(mult_r0), .r1(mult_r1), .r2(mult_r2), .r3(mult_r3),
                    .done(mult_done), .busy(mult_busy),
                    .rns_error(mult_rns_error), .logical_products()
                );
            end else begin : gen_parallel
                spu13_m31_multiplier_structured u_mult (
                    .clk(clk_100mhz), .rst_n(rst_n), .start(mult_start),
                    .op(mult_op),
                    .a0(mult_a0), .a1(mult_a1), .a2(mult_a2), .a3(mult_a3),
                    .b0(mult_b0), .b1(mult_b1), .b2(mult_b2), .b3(mult_b3),
                    .r0(mult_r0), .r1(mult_r1), .r2(mult_r2), .r3(mult_r3),
                    .done(mult_done), .busy(mult_busy),
                    .rns_error(mult_rns_error), .logical_products()
                );
            end
        end else begin : gen_reference
            assign mult_op = 3'd0;
            spu13_fp4_inverter u_inv (
                .clk(clk_100mhz), .rst_n(rst_n), .start(start),
                .z0(z0), .z1(z1), .z2(z2), .z3(z3),
                .inv0(inv0), .inv1(inv1), .inv2(inv2), .inv3(inv3),
                .done(done), .busy(busy), .flags_v(flags_v),
                .mult_start(mult_start),
                .mult_a0(mult_a0), .mult_a1(mult_a1),
                .mult_a2(mult_a2), .mult_a3(mult_a3),
                .mult_b0(mult_b0), .mult_b1(mult_b1),
                .mult_b2(mult_b2), .mult_b3(mult_b3),
                .mult_r0(mult_r0), .mult_r1(mult_r1),
                .mult_r2(mult_r2), .mult_r3(mult_r3),
                .mult_done(mult_done), .mult_busy(mult_busy),
                .debug_state(debug_state), .debug_start_accept()
            );
            if (SEQUENTIAL) begin : gen_seq
                spu13_m31_multiplier_seq u_mult (
                    .clk(clk_100mhz), .rst_n(rst_n), .start(mult_start),
                    .a0(mult_a0), .a1(mult_a1), .a2(mult_a2), .a3(mult_a3),
                    .b0(mult_b0), .b1(mult_b1), .b2(mult_b2), .b3(mult_b3),
                    .r0(mult_r0), .r1(mult_r1), .r2(mult_r2), .r3(mult_r3),
                    .done(mult_done), .busy(mult_busy),
                    .rns_error(mult_rns_error)
                );
            end else begin : gen_parallel
                spu13_m31_multiplier u_mult (
                    .clk(clk_100mhz), .rst_n(rst_n), .start(mult_start),
                    .a0(mult_a0), .a1(mult_a1), .a2(mult_a2), .a3(mult_a3),
                    .b0(mult_b0), .b1(mult_b1), .b2(mult_b2), .b3(mult_b3),
                    .r0(mult_r0), .r1(mult_r1), .r2(mult_r2), .r3(mult_r3),
                    .done(mult_done), .busy(mult_busy),
                    .rns_error(mult_rns_error)
                );
            end
        end
    endgenerate

    assign fault_led = flags_v | mult_rns_error;
    assign led_out = {done, busy, debug_state[0],
                      ^inv0 ^ ^inv1 ^ ^inv2 ^ ^inv3};
endmodule
