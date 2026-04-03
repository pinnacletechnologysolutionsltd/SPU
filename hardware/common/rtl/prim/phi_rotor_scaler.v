// SPU-13 Phi-Rotor Scaling Extension (v4.0)
// Function: Exact Q(phi) scaling via Fibonacci basis recurrence.
//           Replaces the v3.x bit-shift approximation (1.609375 ≠ 1.618...)
//           which violated the Ultrafinite Constraint.
//
// Representation: in_vec = {fib_a[31:0], fib_b[31:0]}
//   Encodes the value  fib_a + fib_b * phi  in the Fibonacci basis.
//
// Exact recurrences (derived from phi^2 = phi + 1, no multipliers required):
//   Scale up   ×phi:   (a, b) → (b,   a+b)
//   Scale down ×1/phi: (a, b) → (b-a, a  )
//
// Both operations are single-cycle additions — zero approximation error,
// no multipliers, fully bit-exact in Q(phi).
//
// Usage note: the caller must initialise the lane in the Fibonacci basis.
//   A plain integer N should be loaded as {N, 0} (pure rational, zero phi part).
//   After k scale_up steps the result equals F(k)*N + F(k-1)*N*phi in integers.

module phi_rotor_scaler (
    input  wire [63:0] in_vec,   // {fib_a[31:0], fib_b[31:0]}  = fib_a + fib_b*phi
    input  wire        scale_up, // 1: multiply by phi  (Expand)
                                 // 0: multiply by 1/phi (Contract)
    output reg  [63:0] out_vec   // result in same Fibonacci basis
);

    wire signed [31:0] fib_a = $signed(in_vec[63:32]);
    wire signed [31:0] fib_b = $signed(in_vec[31:0]);

    always @(*) begin
        if (scale_up) begin
            // (a + b*phi) * phi = b + (a+b)*phi
            out_vec[63:32] = fib_b;           // new_a = b
            out_vec[31:0]  = fib_a + fib_b;   // new_b = a + b  (Fibonacci step)
        end else begin
            // (a + b*phi) * (1/phi) = (b-a) + a*phi
            out_vec[63:32] = fib_b - fib_a;   // new_a = b - a
            out_vec[31:0]  = fib_a;            // new_b = a
        end
    end

endmodule
