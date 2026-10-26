// SU(3) Taylor-series matrix exponential accelerator (prototype)
// Multi-cycle, fixed-point Q16 implementation with scaling-and-squaring
// This is a simulation-first prototype; optimisations and Padé upgrade can follow.

module su3_taylor_accel (
    input  wire clk,
    input  wire rst_n,
    input  wire start,

    input  wire signed [31:0] g00, g01, g02,
    input  wire signed [31:0] g10, g11, g12,
    input  wire signed [31:0] g20, g21, g22,

    output reg  signed [31:0] e00, e01, e02,
    output reg  signed [31:0] e10, e11, e12,
    output reg  signed [31:0] e20, e21, e22,

    output reg done,
    output reg busy
);

// Fixed-point: inputs and outputs are Q16 (1.0 == 65536)
// Simple multi-cycle FSM computing: scale -> A2 -> A3 -> polynomial (I + A + A2/2 + A3/6) -> square s times

localparam IDLE = 3'd0, LATCH = 3'd1, SCALE = 3'd2, A2 = 3'd3, A3 = 3'd4, POLY = 3'd5, SQR = 3'd6, DONE = 3'd7;
reg [2:0] state, next_state;

// Latched inputs
reg signed [31:0] A00, A01, A02, A10, A11, A12, A20, A21, A22;
// Scaled matrix
reg signed [31:0] S00, S01, S02, S10, S11, S12, S20, S21, S22;
// Powers
reg signed [31:0] A2_00, A2_01, A2_02, A2_10, A2_11, A2_12, A2_20, A2_21, A2_22;
reg signed [31:0] A3_00, A3_01, A3_02, A3_10, A3_11, A3_12, A3_20, A3_21, A3_22;
// Accumulator / result (Q16)
reg signed [31:0] R00, R01, R02, R10, R11, R12, R20, R21, R22;

// internal
reg [4:0] s_count; // squaring count
reg [4:0] s_remaining;
integer i;

// helpers for absolute value and max
function [31:0] abs32;
    input signed [31:0] v;
    begin
        abs32 = v[31] ? -v : v;
    end
endfunction

// synchronous FSM
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        state <= IDLE;
        busy <= 1'b0;
        done <= 1'b0;
        // clear outputs
        e00 <= 32'sd0; e01 <= 32'sd0; e02 <= 32'sd0;
        e10 <= 32'sd0; e11 <= 32'sd0; e12 <= 32'sd0;
        e20 <= 32'sd0; e21 <= 32'sd0; e22 <= 32'sd0;
        R00 <= 32'sd0; R01 <= 32'sd0; R02 <= 32'sd0;
        R10 <= 32'sd0; R11 <= 32'sd0; R12 <= 32'sd0;
        R20 <= 32'sd0; R21 <= 32'sd0; R22 <= 32'sd0;
        A00 <= 32'sd0; A01 <= 32'sd0; A02 <= 32'sd0;
        A10 <= 32'sd0; A11 <= 32'sd0; A12 <= 32'sd0;
        A20 <= 32'sd0; A21 <= 32'sd0; A22 <= 32'sd0;
        S00 <= 32'sd0; S01 <= 32'sd0; S02 <= 32'sd0;
        S10 <= 32'sd0; S11 <= 32'sd0; S12 <= 32'sd0;
        S20 <= 32'sd0; S21 <= 32'sd0; S22 <= 32'sd0;
    end else begin
        case (state)
            IDLE: begin
                done <= 1'b0;
                busy <= 1'b0;
                if (start) begin
                    // latch inputs
                    A00 <= g00; A01 <= g01; A02 <= g02;
                    A10 <= g10; A11 <= g11; A12 <= g12;
                    A20 <= g20; A21 <= g21; A22 <= g22;
                    state <= LATCH;
                    busy <= 1'b1;
                end else state <= IDLE;
            end
            LATCH: begin
                // estimate norm (max absolute element) and compute s_count such that |A/2^s| <= 1.0 (Q16=65536)
                // use max absolute element of A
                begin : compute_norm
                    reg [31:0] m00,m01,m02,m10,m11,m12,m20,m21,m22;
                    reg [31:0] mx;
                    m00 = abs32(A00);
                    m01 = abs32(A01);
                    m02 = abs32(A02);
                    m10 = abs32(A10);
                    m11 = abs32(A11);
                    m12 = abs32(A12);
                    m20 = abs32(A20);
                    m21 = abs32(A21);
                    m22 = abs32(A22);
                    mx = m00;
                    if (m01 > mx) mx = m01;
                    if (m02 > mx) mx = m02;
                    if (m10 > mx) mx = m10;
                    if (m11 > mx) mx = m11;
                    if (m12 > mx) mx = m12;
                    if (m20 > mx) mx = m20;
                    if (m21 > mx) mx = m21;
                    if (m22 > mx) mx = m22;
                    // compute s_count = max(0, ceil(log2(mx/65536))) using shifts
                    s_count = 0;
                    if (mx <= 32'sd65536) begin
                        s_count = 0;
                    end else begin
                        reg [63:0] tmp;
                        tmp = mx;
                        while (tmp > 32'sd65536 && s_count < 20) begin
                            tmp = tmp >> 1;
                            s_count = s_count + 1;
                        end
                    end
                end
                s_remaining <= s_count;
                state <= SCALE;
            end
            SCALE: begin
                // arithmetic right shift by s_count for each element to get S = A / 2^s_count
                if (s_count == 0) begin
                    S00 <= A00; S01 <= A01; S02 <= A02;
                    S10 <= A10; S11 <= A11; S12 <= A12;
                    S20 <= A20; S21 <= A21; S22 <= A22;
                end else begin
                    S00 <= A00 >>> s_count; S01 <= A01 >>> s_count; S02 <= A02 >>> s_count;
                    S10 <= A10 >>> s_count; S11 <= A11 >>> s_count; S12 <= A12 >>> s_count;
                    S20 <= A20 >>> s_count; S21 <= A21 >>> s_count; S22 <= A22 >>> s_count;
                end
                state <= A2;
            end
            A2: begin
                // compute S * S -> A2 (Q16)
                // do products in 64-bit then shift >>16 to keep Q16
                reg signed [63:0] p0,p1,p2;
                // A2_00 = (S00*S00 + S01*S10 + S02*S20) >> 16
                p0 = $signed(S00) * $signed(S00);
                p1 = $signed(S01) * $signed(S10);
                p2 = $signed(S02) * $signed(S20);
                A2_00 <= $signed((p0 + p1 + p2) >>> 16);
                // A2_01
                p0 = $signed(S00) * $signed(S01);
                p1 = $signed(S01) * $signed(S11);
                p2 = $signed(S02) * $signed(S21);
                A2_01 <= $signed((p0 + p1 + p2) >>> 16);
                // A2_02
                p0 = $signed(S00) * $signed(S02);
                p1 = $signed(S01) * $signed(S12);
                p2 = $signed(S02) * $signed(S22);
                A2_02 <= $signed((p0 + p1 + p2) >>> 16);
                // row1
                p0 = $signed(S10) * $signed(S00);
                p1 = $signed(S11) * $signed(S10);
                p2 = $signed(S12) * $signed(S20);
                A2_10 <= $signed((p0 + p1 + p2) >>> 16);
                p0 = $signed(S10) * $signed(S01);
                p1 = $signed(S11) * $signed(S11);
                p2 = $signed(S12) * $signed(S21);
                A2_11 <= $signed((p0 + p1 + p2) >>> 16);
                p0 = $signed(S10) * $signed(S02);
                p1 = $signed(S11) * $signed(S12);
                p2 = $signed(S12) * $signed(S22);
                A2_12 <= $signed((p0 + p1 + p2) >>> 16);
                // row2
                p0 = $signed(S20) * $signed(S00);
                p1 = $signed(S21) * $signed(S10);
                p2 = $signed(S22) * $signed(S20);
                A2_20 <= $signed((p0 + p1 + p2) >>> 16);
                p0 = $signed(S20) * $signed(S01);
                p1 = $signed(S21) * $signed(S11);
                p2 = $signed(S22) * $signed(S21);
                A2_21 <= $signed((p0 + p1 + p2) >>> 16);
                p0 = $signed(S20) * $signed(S02);
                p1 = $signed(S21) * $signed(S12);
                p2 = $signed(S22) * $signed(S22);
                A2_22 <= $signed((p0 + p1 + p2) >>> 16);

                state <= A3;
            end
            A3: begin
                // compute A3 = A2 * S
                reg signed [63:0] p0,p1,p2;
                p0 = $signed(A2_00) * $signed(S00);
                p1 = $signed(A2_01) * $signed(S10);
                p2 = $signed(A2_02) * $signed(S20);
                A3_00 <= $signed((p0 + p1 + p2) >>> 16);

                p0 = $signed(A2_00) * $signed(S01);
                p1 = $signed(A2_01) * $signed(S11);
                p2 = $signed(A2_02) * $signed(S21);
                A3_01 <= $signed((p0 + p1 + p2) >>> 16);

                p0 = $signed(A2_00) * $signed(S02);
                p1 = $signed(A2_01) * $signed(S12);
                p2 = $signed(A2_02) * $signed(S22);
                A3_02 <= $signed((p0 + p1 + p2) >>> 16);

                p0 = $signed(A2_10) * $signed(S00);
                p1 = $signed(A2_11) * $signed(S10);
                p2 = $signed(A2_12) * $signed(S20);
                A3_10 <= $signed((p0 + p1 + p2) >>> 16);

                p0 = $signed(A2_10) * $signed(S01);
                p1 = $signed(A2_11) * $signed(S11);
                p2 = $signed(A2_12) * $signed(S21);
                A3_11 <= $signed((p0 + p1 + p2) >>> 16);

                p0 = $signed(A2_10) * $signed(S02);
                p1 = $signed(A2_11) * $signed(S12);
                p2 = $signed(A2_12) * $signed(S22);
                A3_12 <= $signed((p0 + p1 + p2) >>> 16);

                p0 = $signed(A2_20) * $signed(S00);
                p1 = $signed(A2_21) * $signed(S10);
                p2 = $signed(A2_22) * $signed(S20);
                A3_20 <= $signed((p0 + p1 + p2) >>> 16);

                p0 = $signed(A2_20) * $signed(S01);
                p1 = $signed(A2_21) * $signed(S11);
                p2 = $signed(A2_22) * $signed(S21);
                A3_21 <= $signed((p0 + p1 + p2) >>> 16);

                p0 = $signed(A2_20) * $signed(S02);
                p1 = $signed(A2_21) * $signed(S12);
                p2 = $signed(A2_22) * $signed(S22);
                A3_22 <= $signed((p0 + p1 + p2) >>> 16);

                state <= POLY;
            end
            POLY: begin
                // compute R = I + S + A2/2 + A3/6  (all Q16)
                R00 <= 32'sd65536 + S00 + (A2_00 >>> 1) + ($signed(A3_00) / 6);
                R01 <= S01 + (A2_01 >>> 1) + ($signed(A3_01) / 6);
                R02 <= S02 + (A2_02 >>> 1) + ($signed(A3_02) / 6);

                R10 <= S10 + (A2_10 >>> 1) + ($signed(A3_10) / 6);
                R11 <= 32'sd65536 + S11 + (A2_11 >>> 1) + ($signed(A3_11) / 6);
                R12 <= S12 + (A2_12 >>> 1) + ($signed(A3_12) / 6);

                R20 <= S20 + (A2_20 >>> 1) + ($signed(A3_20) / 6);
                R21 <= S21 + (A2_21 >>> 1) + ($signed(A3_21) / 6);
                R22 <= 32'sd65536 + S22 + (A2_22 >>> 1) + ($signed(A3_22) / 6);

                state <= SQR;
            end
            SQR: begin
                // if no squaring required, finish; otherwise square R s_remaining times
                if (s_remaining == 0) begin
                    state <= DONE;
                end else begin
                    // compute R = R * R
                    reg signed [63:0] p0,p1,p2;
                    // temp registers to hold next R
                    reg signed [31:0] T00,T01,T02,T10,T11,T12,T20,T21,T22;

                    p0 = $signed(R00) * $signed(R00);
                    p1 = $signed(R01) * $signed(R10);
                    p2 = $signed(R02) * $signed(R20);
                    T00 = $signed((p0 + p1 + p2) >>> 16);

                    p0 = $signed(R00) * $signed(R01);
                    p1 = $signed(R01) * $signed(R11);
                    p2 = $signed(R02) * $signed(R21);
                    T01 = $signed((p0 + p1 + p2) >>> 16);

                    p0 = $signed(R00) * $signed(R02);
                    p1 = $signed(R01) * $signed(R12);
                    p2 = $signed(R02) * $signed(R22);
                    T02 = $signed((p0 + p1 + p2) >>> 16);

                    p0 = $signed(R10) * $signed(R00);
                    p1 = $signed(R11) * $signed(R10);
                    p2 = $signed(R12) * $signed(R20);
                    T10 = $signed((p0 + p1 + p2) >>> 16);

                    p0 = $signed(R10) * $signed(R01);
                    p1 = $signed(R11) * $signed(R11);
                    p2 = $signed(R12) * $signed(R21);
                    T11 = $signed((p0 + p1 + p2) >>> 16);

                    p0 = $signed(R10) * $signed(R02);
                    p1 = $signed(R11) * $signed(R12);
                    p2 = $signed(R12) * $signed(R22);
                    T12 = $signed((p0 + p1 + p2) >>> 16);

                    p0 = $signed(R20) * $signed(R00);
                    p1 = $signed(R21) * $signed(R10);
                    p2 = $signed(R22) * $signed(R20);
                    T20 = $signed((p0 + p1 + p2) >>> 16);

                    p0 = $signed(R20) * $signed(R01);
                    p1 = $signed(R21) * $signed(R11);
                    p2 = $signed(R22) * $signed(R21);
                    T21 = $signed((p0 + p1 + p2) >>> 16);

                    p0 = $signed(R20) * $signed(R02);
                    p1 = $signed(R21) * $signed(R12);
                    p2 = $signed(R22) * $signed(R22);
                    T22 = $signed((p0 + p1 + p2) >>> 16);

                    // write back
                    R00 <= T00; R01 <= T01; R02 <= T02;
                    R10 <= T10; R11 <= T11; R12 <= T12;
                    R20 <= T20; R21 <= T21; R22 <= T22;

                    s_remaining <= s_remaining - 1'b1;
                    // stay in SQR until s_remaining == 0
                end
            end
            DONE: begin
                // drive outputs
                e00 <= R00; e01 <= R01; e02 <= R02;
                e10 <= R10; e11 <= R11; e12 <= R12;
                e20 <= R20; e21 <= R21; e22 <= R22;
                done <= 1'b1;
                busy <= 1'b0;
                state <= IDLE;
            end
            default: state <= IDLE;
        endcase
    end
end

endmodule
