`timescale 1ns / 1ps

// spu13_m31_inverter.v — Binary Extended Euclidean Algorithm over M31
//
// Computes inv = X^(-1) mod P where P = 2^31 - 1.
// Uses division-free BEEA: shifts, subtractions, conditional P-add for even handling.
//
// Registers: u, v (values), a, c (coefficients). When u==1, inv=a.
// The trick: when a value is even and needs right-shift, if the corresponding
// coefficient is odd, add P first to make it even (since P is odd, P + odd = even).
//
// States: IDLE → INIT → REDUCE_U → REDUCE_V → STEP → DONE → IDLE
// REDUCE_U: while u is even, shift right
// REDUCE_V: while v is even, shift right
// STEP:    u>=v ? (u=u-v, a=a-c) : (v=v-u, c=c-a)

module spu13_m31_inverter (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         start,
    input  wire [31:0]  x_in,       // Value to invert (must be non-zero)
    output reg  [31:0]  inv_out,    // Modular inverse result
    output reg          done,
    output reg          busy
);

    localparam [31:0] P = 32'h7FFFFFFF;  // M31

    // Registers for BEEA state
    reg [31:0] u, v;
    reg [31:0] a, c;

    // State machine
    localparam S_IDLE     = 3'd0;
    localparam S_INIT     = 3'd1;
    localparam S_REDUCE_U = 3'd2;
    localparam S_REDUCE_V = 3'd3;
    localparam S_STEP     = 3'd4;
    localparam S_DONE     = 3'd5;

    reg [2:0] state, next_state;

    // ── Next-state logic ───────────────────────────────────────────
    always @(*) begin
        case (state)
            S_IDLE:     next_state = start  ? S_INIT     : S_IDLE;
            S_INIT:     next_state = S_REDUCE_U;
            S_REDUCE_U: next_state = (u[0] == 1'b0) ? S_REDUCE_U : S_REDUCE_V;
            S_REDUCE_V: next_state = (v[0] == 1'b0) ? S_REDUCE_V : S_STEP;
            S_STEP: begin
                if (u == 32'd1)       next_state = S_DONE;
                else if (v == 32'd1)  next_state = S_DONE;
                else                  next_state = S_REDUCE_U;
            end
            S_DONE:     next_state = S_IDLE;
            default:    next_state = S_IDLE;
        endcase
    end

    // ── Sequential datapath ────────────────────────────────────────
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state   <= S_IDLE;
            u       <= 32'd0;
            v       <= 32'd0;
            a       <= 32'd0;
            c       <= 32'd0;
            inv_out <= 32'd0;
            done    <= 1'b0;
            busy    <= 1'b0;
        end else begin
            state   <= next_state;
            done    <= 1'b0;

            case (state)
                S_IDLE: begin
                    busy <= 1'b0;
                end

                S_INIT: begin
                    busy <= 1'b1;
                    u    <= x_in;
                    v    <= P;
                    a    <= 32'd1;
                    c    <= 32'd0;
                end

                S_REDUCE_U: begin
                    if (u[0] == 1'b0) begin
                        u <= u >> 1;
                        a <= (a[0] == 1'b0) ? (a >> 1) : ((a + P) >> 1);
                    end
                end

                S_REDUCE_V: begin
                    if (v[0] == 1'b0) begin
                        v <= v >> 1;
                        c <= (c[0] == 1'b0) ? (c >> 1) : ((c + P) >> 1);
                    end
                end

                S_STEP: begin
                    if (u >= v) begin
                        u <= u - v;
                        a <= (a >= c) ? (a - c) : (a + P - c);
                    end else begin
                        v <= v - u;
                        c <= (c >= a) ? (c - a) : (c + P - a);
                    end
                end

                S_DONE: begin
                    inv_out <= (u == 32'd1) ? a : c;
                    done    <= 1'b1;
                    busy    <= 1'b0;
                end
            endcase
        end
    end

endmodule
