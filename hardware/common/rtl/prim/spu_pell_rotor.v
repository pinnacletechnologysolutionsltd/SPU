// spu_pell_rotor.v — Q(√3) Pell Step Unit
// CC0 1.0 Universal.
`timescale 1ns/1ps
//
// Applies one Pell step: multiply by the unit element (2 + 1·√3).
//
//   new_P = 2·P + 3·Q
//   new_Q = 1·P + 2·Q
//
// This is the fundamental algebraic rotation in Q(√3).  Every step scales
// the vector by (2+√3) while preserving the quadrance K = P²−3Q².
// The orbit is: (1,0)→(2,1)→(7,4)→(26,15)→(97,56)→…  K=1 throughout.
//
// Replaces the demoted phi_rotor_scaler (which used Fibonacci/φ — a
// transcendental approximation forbidden by the Ultrafinite Constraint).
//
// Format: packed {P[WIDTH-1:0], Q[WIDTH-1:0]} — same as spu_janus_mirror.
// Latency: 1 clock cycle.
//
// Depends on: nothing (standalone primitive).

module spu_pell_rotor #(
    parameter WIDTH = 16
)(
    input  wire                 clk,
    input  wire                 rst_n,
    input  wire [WIDTH*2-1:0]   surd_in,   // {Q, P} packed

    output reg  [WIDTH*2-1:0]   surd_out   // {Q_new, P_new} after one Pell step
);

    wire signed [WIDTH-1:0] P_in;
    assign P_in = $signed(surd_in[WIDTH-1:0]);
    wire signed [WIDTH-1:0] Q_in;
    assign Q_in = $signed(surd_in[WIDTH*2-1:WIDTH]);

    // new_P = 2P + 3Q  (shift-add — no multiply needed)
    // new_Q = P  + 2Q
    wire signed [WIDTH:0] P_new = (P_in <<< 1) + (Q_in <<< 1) + Q_in; // 2P + 3Q
    wire signed [WIDTH:0] Q_new = P_in + (Q_in <<< 1);                  // P  + 2Q

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            surd_out <= {WIDTH*2{1'b0}};
        end else begin
            surd_out <= {Q_new[WIDTH-1:0], P_new[WIDTH-1:0]};
        end
    end

endmodule
