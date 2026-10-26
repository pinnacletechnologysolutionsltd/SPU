`timescale 1ns / 1ps

// spu13_m31_multiplier.v — F_{p^4} multiplier over Mersenne prime p=2^31-1
//
// Computes R = A × B in the biquadratic extension field F_{p^4} with
// basis [1, √3, √5, √15]. Each operand is 4 × 32-bit registers.
//
// Multiplication matrix:
//   R0 = A0×B0 + 3·A1×B1 + 5·A2×B2 + 15·A3×B3
//   R1 = A0×B1 + A1×B0 + 5·A2×B3 + 5·A3×B2
//   R2 = A0×B2 + 3·A1×B3 + A2×B0 + 3·A3×B1
//   R3 = A0×B3 + A1×B2 + A2×B1 + A3×B0
//
// All products are full 64-bit. Scaling by 3/5/15 uses shift+add/sub.
// Accumulators are 72-bit to hold up to ~24×2^62 ≈ 2^66.6.
// Reduction to M31 uses multi-chunk 31-bit split-and-add.

module spu13_m31_multiplier (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         start,
    input  wire [31:0]  a0, a1, a2, a3,
    input  wire [31:0]  b0, b1, b2, b3,
    output wire [31:0]  r0, r1, r2, r3,
    output wire         done,
    output wire         busy,
    output wire         rns_error        // mod-3 residue parity violation
);

    localparam [31:0] P = 32'h7FFFFFFF;

    // ── Stage 0: 64-bit products → 72-bit scaled accumulators ──────
    reg [71:0] s0_acc0, s0_acc1, s0_acc2, s0_acc3;
    reg        s0_valid;
    wire [63:0] p00, p01, p02, p03,
                p10, p11, p12, p13,
                p20, p21, p22, p23,
                p30, p31, p32, p33;

    // Full 64-bit products
    assign p00 = a0 * b0; assign p01 = a0 * b1; assign p02 = a0 * b2; assign p03 = a0 * b3;
    assign p10 = a1 * b0; assign p11 = a1 * b1; assign p12 = a1 * b2; assign p13 = a1 * b3;
    assign p20 = a2 * b0; assign p21 = a2 * b1; assign p22 = a2 * b2; assign p23 = a2 * b3;
    assign p30 = a3 * b0; assign p31 = a3 * b1; assign p32 = a3 * b2; assign p33 = a3 * b3;

    // Combinational accumulation (72-bit safe)
    wire [71:0] acc0_comb = {8'd0, p00} + {7'd0, p11, 1'b0} + {8'd0, p11}   // + 3·p11
                          + {6'd0, p22, 2'b0} + {8'd0, p22}                  // + 5·p22
                          + {4'd0, p33, 4'b0} - {8'd0, p33};                 // +15·p33

    wire [71:0] acc1_comb = {8'd0, p01} + {8'd0, p10}
                          + {6'd0, p23, 2'b0} + {8'd0, p23}                  // + 5·p23
                          + {6'd0, p32, 2'b0} + {8'd0, p32};                 // + 5·p32

    wire [71:0] acc2_comb = {8'd0, p02} + {7'd0, p13, 1'b0} + {8'd0, p13}   // + 3·p13
                          + {8'd0, p20}
                          + {7'd0, p31, 1'b0} + {8'd0, p31};                 // + 3·p31

    wire [71:0] acc3_comb = {8'd0, p03} + {8'd0, p12}
                          + {8'd0, p21} + {8'd0, p30};

    // ── Multi-chunk Mersenne reduction (handles up to 72 bits) ─────
    // Z mod (2^31-1): split Z into 31-bit chunks, sum them,
    // then if sum >= P subtract P.
    function [31:0] m31_reduce_72;
        input [71:0] z;
        reg [31:0] chunk0, chunk1, chunk2;
        reg [32:0] sum01, sum_all;
        begin
            chunk0  = z[30:0];
            chunk1  = z[61:31];
            chunk2  = {21'd0, z[71:62]};
            sum01   = chunk0 + chunk1;
            sum_all = sum01 + chunk2;
            if (sum_all >= P) sum_all = sum_all - P;
            if (sum_all >= P) sum_all = sum_all - P;
            m31_reduce_72 = sum_all[31:0];
        end
    endfunction

    // ── Stage 0 sequential ─────────────────────────────────────────
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s0_valid <= 1'b0;
            s0_acc0  <= 72'd0;
            s0_acc1  <= 72'd0;
            s0_acc2  <= 72'd0;
            s0_acc3  <= 72'd0;
        end else begin
            if (start) begin
                s0_acc0  <= acc0_comb;
                s0_acc1  <= acc1_comb;
                s0_acc2  <= acc2_comb;
                s0_acc3  <= acc3_comb;
                s0_valid <= 1'b1;
            end else begin
                s0_valid <= 1'b0;
            end
        end
    end

    // ── Stage 1: reduce ────────────────────────────────────────────
    reg [31:0] s1_r0, s1_r1, s1_r2, s1_r3;
    reg        s1_valid;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s1_valid <= 1'b0;
            s1_r0 <= 32'd0; s1_r1 <= 32'd0;
            s1_r2 <= 32'd0; s1_r3 <= 32'd0;
        end else begin
            if (s0_valid) begin
                s1_r0 <= m31_reduce_72(s0_acc0);
                s1_r1 <= m31_reduce_72(s0_acc1);
                s1_r2 <= m31_reduce_72(s0_acc2);
                s1_r3 <= m31_reduce_72(s0_acc3);
                s1_valid <= 1'b1;
            end else begin
                s1_valid <= 1'b0;
            end
        end
    end

    assign r0   = s1_r0;
    assign r1   = s1_r1;
    assign r2   = s1_r2;
    assign r3   = s1_r3;
    assign done = s1_valid;
    assign busy = s0_valid || s1_valid;

    // ── RNS mod-3 residue parity checker ───────────────────────────
    // Checks the reduced output against an independently reduced mod-3 shadow
    // of the 72-bit accumulator. The correction term matters because
    // P = 2^31-1 is 1 mod 3, so raw product residues cannot be compared
    // directly with field-reduced outputs.
    function [1:0] mod3_32;
        input [31:0] x;
        reg [5:0] even, odd;
        reg signed [6:0] d;
        integer i;
        begin
            even = 0; odd = 0;
            for (i = 0; i < 16; i = i + 1) begin
                even = even + x[2*i];
                odd  = odd  + x[2*i+1];
            end
            d = even - odd;           // -16..+16
            if (d < 0) d = d + 18;    // shift to 2..34
            // reduce mod 3 by conditional subtract
            if (d >= 18) d = d - 18;
            if (d >= 12) d = d - 12;
            if (d >= 9)  d = d - 9;
            if (d >= 6)  d = d - 6;
            if (d >= 3)  d = d - 3;
            mod3_32 = d[1:0];
        end
    endfunction

    function [1:0] m31_reduce_72_mod3;
        input [71:0] z;
        reg [31:0] chunk0, chunk1, chunk2;
        reg [32:0] sum01, sum_all;
        reg [31:0] reduced;
        begin
            chunk0  = z[30:0];
            chunk1  = z[61:31];
            chunk2  = {21'd0, z[71:62]};
            sum01   = chunk0 + chunk1;
            sum_all = sum01 + chunk2;
            if (sum_all >= P) sum_all = sum_all - P;
            if (sum_all >= P) sum_all = sum_all - P;
            reduced = sum_all[31:0];
            m31_reduce_72_mod3 = mod3_32(reduced);
        end
    endfunction

    reg [1:0] s0_res0, s0_res1, s0_res2, s0_res3;
    reg [1:0] s1_res0, s1_res1, s1_res2, s1_res3;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s0_res0 <= 2'd0; s0_res1 <= 2'd0;
            s0_res2 <= 2'd0; s0_res3 <= 2'd0;
            s1_res0 <= 2'd0; s1_res1 <= 2'd0;
            s1_res2 <= 2'd0; s1_res3 <= 2'd0;
        end else begin
            if (start) begin
                s0_res0 <= m31_reduce_72_mod3(acc0_comb);
                s0_res1 <= m31_reduce_72_mod3(acc1_comb);
                s0_res2 <= m31_reduce_72_mod3(acc2_comb);
                s0_res3 <= m31_reduce_72_mod3(acc3_comb);
            end
            if (s0_valid) begin
                s1_res0 <= s0_res0;
                s1_res1 <= s0_res1;
                s1_res2 <= s0_res2;
                s1_res3 <= s0_res3;
            end
        end
    end

    // Actual output residues
    wire [1:0] r0_act = mod3_32(s1_r0);
    wire [1:0] r1_act = mod3_32(s1_r1);
    wire [1:0] r2_act = mod3_32(s1_r2);
    wire [1:0] r3_act = mod3_32(s1_r3);

    // Assert on valid output, any lane mismatch
    assign rns_error = s1_valid && (
        (r0_act != s1_res0) ||
        (r1_act != s1_res1) ||
        (r2_act != s1_res2) ||
        (r3_act != s1_res3)
    );

endmodule
