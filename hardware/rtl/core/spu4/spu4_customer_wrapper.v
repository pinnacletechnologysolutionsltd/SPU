`timescale 1ns / 1ps

// spu4_customer_wrapper.v — the SPU-4 product contract layer (ABI v1.0)
//
// This is the module a customer integrates against. It is deliberately NOT
// `spu4_standalone_top`: that module is a development and bring-up vehicle,
// and its port list carries research-era concepts, an unclosed programmable
// datapath, and two outputs that are not driven at all. See
// docs/SPU4_ABI.md for the full contract and the reasoning behind every
// inclusion and omission.
//
// ── What this wrapper guarantees ─────────────────────────────────────
//  1. Every declared output is driven. No port reads X or Z, ever.
//  2. Operands and coefficients are CAPTURED on an accepted `start`. The
//     customer may change their inputs on the very next cycle without
//     corrupting an operation in flight.
//  3. Results are REGISTERED and held stable from `done` until the next
//     accepted `start`. They do not flicker mid-operation.
//  4. `start` asserted while `busy` is ignored, and the violation is
//     reported in `status` rather than silently corrupting state.
//  5. Latency is fixed and bounded. See SPU4_LATENCY_CYCLES below; the
//     bound is asserted every operation by spu4_customer_wrapper_tb.
//  6. `rst_n` may be driven asynchronously. It is synchronised here.
//
// ── Deliberately NOT in this contract ────────────────────────────────
//  * Program memory / the sequencer. The programmable path is not closed
//    in this design -- the register file's read ports are dangling and the
//    ALU always reads the input pins -- so freezing an ABI over it would
//    freeze a defect. One operation per `start` is the smallest useful
//    contract, which is what the product ladder asks for.
//  * `sentinel_mode`, `piranha_pulse`. Research-era concepts.
//  * UART and cluster-link ports. Those are ADAPTERS layered on this
//    wrapper, not part of the base contract -- and in the standalone top
//    both are undriven outputs today.
//
// ── Compatibility promise ────────────────────────────────────────────
// Within ABI v1.x: ports are added only at the end of the list, reserved
// status bits read 0 and may gain meaning, and the meaning of an existing
// port never changes. A breaking change is v2.0 and a new module name.
//
// This module is ADDITIVE. It does not modify spu4_standalone_top, so no
// existing bitstream or silicon-evidence hash moves because of it.

module spu4_customer_wrapper #(
    // Operand width. Informational for v1.0 -- the datapath below is 16-bit
    // and the parameter exists so a customer sees the width is a stated
    // property of the contract rather than an accident.
    parameter integer OPERAND_W = 16
) (
    // ── Clock and reset ──────────────────────────────────────────────
    input  wire                     clk,
    // Active-low. May be driven asynchronously: released synchronously here.
    input  wire                     rst_n,

    // ── Operation handshake ──────────────────────────────────────────
    // Assert `start` for one cycle to begin. Ignored while `busy`.
    input  wire                     start,
    output wire                     busy,
    // Level, not a pulse: asserted when results are valid, held until the
    // next accepted `start`. Low from reset until the first result.
    output wire                     done,

    // ── Operands, captured on an accepted start ──────────────────────
    input  wire signed [OPERAND_W-1:0] a_in,
    input  wire signed [OPERAND_W-1:0] b_in,
    input  wire signed [OPERAND_W-1:0] c_in,
    input  wire signed [OPERAND_W-1:0] d_in,

    // ── Coefficients, captured on an accepted start ──────────────────
    // Held stable internally for the whole operation, which the bare ALU
    // requires and does not itself enforce.
    input  wire signed [OPERAND_W-1:0] coeff_f,
    input  wire signed [OPERAND_W-1:0] coeff_g,
    input  wire signed [OPERAND_W-1:0] coeff_h,

    // ── Results, registered, valid while `done` ──────────────────────
    output wire signed [OPERAND_W-1:0] a_out,
    output wire signed [OPERAND_W-1:0] b_out,
    output wire signed [OPERAND_W-1:0] c_out,
    output wire signed [OPERAND_W-1:0] d_out,

    // ── Telemetry ────────────────────────────────────────────────────
    // Saturating |a+b+c+d| for the completed operation. Telemetry, NOT a
    // fault flag -- see docs/SPU4_FAULT_REPORTING_CONTRACT.md.
    output wire [7:0]               dissonance,

    // status[0] busy
    // status[1] done
    // status[2] henosis      -- a Phi-fold normalisation fired during the op
    // status[3] saturated    -- dissonance read 0xFF for the op
    // status[4] start_ignored-- a start arrived while busy (handshake misuse)
    // status[7:5] reserved, read 0
    output wire [7:0]               status
);

    // Cycle budget for one operation, measured not assumed. The testbench
    // asserts every operation completes within this and fails if it does not,
    // so this constant cannot drift away from the hardware silently.
    localparam integer SPU4_LATENCY_CYCLES = 200;

    // ── Reset synchroniser ───────────────────────────────────────────
    // A raw asynchronous reset pad driving internal resets cost this project
    // a three-week board outage (docs/hardware_evidence.md, A7 reset
    // post-mortem). A customer must not be able to reproduce that by wiring
    // a button or a power-supervisor output straight to rst_n.
    reg rst_meta, rst_sync_n;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rst_meta   <= 1'b0;
            rst_sync_n <= 1'b0;
        end else begin
            rst_meta   <= 1'b1;
            rst_sync_n <= rst_meta;
        end
    end

    // ── Captured inputs ──────────────────────────────────────────────
    reg signed [15:0] a_q, b_q, c_q, d_q;
    reg signed [15:0] f_q, g_q, h_q;

    // ── Control ──────────────────────────────────────────────────────
    reg        busy_q, done_q, start_ignored_q, henosis_q;
    reg        alu_start_q;
    wire       accept = start && !busy_q;

    // ── Result registers ─────────────────────────────────────────────
    reg signed [15:0] a_r, b_r, c_r, d_r;

    // ── ALU ──────────────────────────────────────────────────────────
    wire signed [15:0] alu_a, alu_b, alu_c, alu_d;
    wire               alu_done, alu_henosis;

    spu4_euclidean_alu u_alu (
        .clk(clk),
        .reset(!rst_sync_n),
        .start(alu_start_q),
        .bloom_intensity(8'hFF),        // identity scaling; see spu4_euclidean_alu
        .mode_autonomous(1'b0),         // operands come from the captured registers
        .A_in(a_q), .B_in(b_q), .C_in(c_q), .D_in(d_q),
        .F(f_q),    .G(g_q),   .H(h_q),
        .A_out(alu_a), .B_out(alu_b), .C_out(alu_c), .D_out(alu_d),
        .done(alu_done),
        .henosis_pulse(alu_henosis)
    );

    // Residual over the REGISTERED results, so `dissonance` describes the
    // completed operation and not whatever the ALU is midway through.
    wire [7:0] dissonance_live;
    spu4_dissonance u_dissonance (
        .A(a_r), .B(b_r), .C(c_r), .D(d_r),
        .dissonance(dissonance_live)
    );

    always @(posedge clk) begin
        if (!rst_sync_n) begin
            a_q <= 16'sd0; b_q <= 16'sd0; c_q <= 16'sd0; d_q <= 16'sd0;
            f_q <= 16'sd0; g_q <= 16'sd0; h_q <= 16'sd0;
            a_r <= 16'sd0; b_r <= 16'sd0; c_r <= 16'sd0; d_r <= 16'sd0;
            busy_q          <= 1'b0;
            done_q          <= 1'b0;
            alu_start_q     <= 1'b0;
            henosis_q       <= 1'b0;
            start_ignored_q <= 1'b0;
        end else begin
            alu_start_q <= 1'b0;

            // Handshake misuse is reported, never silently absorbed.
            if (start && busy_q)
                start_ignored_q <= 1'b1;

            if (accept) begin
                a_q <= a_in; b_q <= b_in; c_q <= c_in; d_q <= d_in;
                f_q <= coeff_f; g_q <= coeff_g; h_q <= coeff_h;
                alu_start_q     <= 1'b1;
                busy_q          <= 1'b1;
                done_q          <= 1'b0;
                henosis_q       <= 1'b0;
                start_ignored_q <= 1'b0;
            end else if (busy_q) begin
                if (alu_henosis)
                    henosis_q <= 1'b1;
                if (alu_done) begin
                    a_r    <= alu_a; b_r <= alu_b; c_r <= alu_c; d_r <= alu_d;
                    busy_q <= 1'b0;
                    done_q <= 1'b1;
                end
            end
        end
    end

    assign busy       = busy_q;
    assign done       = done_q;
    assign a_out      = a_r;
    assign b_out      = b_r;
    assign c_out      = c_r;
    assign d_out      = d_r;
    assign dissonance = dissonance_live;

    assign status = {3'b000,                       // reserved, read 0
                     start_ignored_q,
                     (dissonance_live == 8'hFF),
                     henosis_q,
                     done_q,
                     busy_q};

endmodule
