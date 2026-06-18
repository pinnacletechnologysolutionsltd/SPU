// spu13_axiomatic_gatekeeper.v — Reverse-Mathematics Assertion Engine (v1.0)
//
// Monitors the SOM quadrance pipeline at every cycle and asserts that the
// computation stays within the bounds of the current Reverse-Math strength level.
//
// Levels (encoded on axiomatic_level[1:0]):
//   2'b00 = RCA₀  — Strictly constructive: no overflow, no fractional leakage
//   2'b01 = WKL₀  — Bounded choice: overflow traps, fractional OK (LUT-based)
//   2'b10 = ACA₀  — Full arithmetic: only hard physical faults trap
//   2'b11 = OFF   — Gatekeeper disabled (passthrough)
//
// Monitored signals (from spu_som_bmu quadrance pipeline):
//   delta_a, delta_b    — feature − weight (combinational)
//   quadrance_a, quadrance_b — accumulated Q_node (surd coefficients)
//   accum_overflow      — raised when acc[63:32] ≠ sign-extend of acc[31]
//
// Fault encoding:
//   FAULT_NONE          = 2'b00
//   FAULT_BIT_OVERFLOW  = 2'b01 — broke constructive integer bounds
//   FAULT_FRACTIONAL    = 2'b10 — non-dyadic fractional leakage detected
//
// CC0 1.0 Universal.

module spu13_axiomatic_gatekeeper #(
    parameter WIDTH = 18
)(
    input  wire        clk,
    input  wire        rst_n,

    input  wire [1:0]  axiomatic_level,   // 00=RCA₀ 01=WKL₀ 10=ACA₀ 11=OFF

    // ── Signals from quadrance pipeline ────────────────────────
    input  wire signed [WIDTH-1:0] quadrance_a,    // accumulated Q (rational part)
    input  wire signed [WIDTH-1:0] quadrance_b,    // accumulated Q (surd part)
    input  wire                    accum_overflow, // high bits lost in truncation
    input  wire                    pipeline_valid, // strobe: result is valid this cycle

    // ── Fault outputs ──────────────────────────────────────────
    output reg                     axiomatic_fault,
    output reg  [1:0]              fault_type,
    output reg  [15:0]             fault_count       // saturating counter
);

    // ── Fault type encoding ────────────────────────────────────
    localparam FAULT_NONE         = 2'b00;
    localparam FAULT_BIT_OVERFLOW = 2'b01;
    localparam FAULT_FRACTIONAL   = 2'b10;

    // ── Detection logic (combinational) ────────────────────────
    // Fractional leakage: reserved for future fixed-point SOM operations.
    // In pure integer Q(√3) arithmetic, small integer results like Q=1
    // have low bits set (0x0001) but are perfectly valid.  A blind
    // low-bit check would false-positive on every non-multiple-of-16.
    // Enable this check only when SHIFT > 0 (fixed-point mode) is active.
    wire is_fractional;
    assign is_fractional = 1'b0;  // reserved — integer-mode pipeline

    // ── Sequential assertion engine ────────────────────────────
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            axiomatic_fault <= 1'b0;
            fault_type      <= FAULT_NONE;
            fault_count     <= 16'd0;
        end else begin
            // Default: no fault this cycle
            axiomatic_fault <= 1'b0;
            fault_type      <= FAULT_NONE;

            if (pipeline_valid && axiomatic_level != 2'b11) begin

                case (axiomatic_level)

                    // ── RCA₀: Strictly Constructible ──────────
                    // Replayable arithmetic only.  Any overflow or fractional
                    // leakage means the computation exceeded the constructive
                    // bounds of the current hardware execution level.
                    2'b00: begin
                        if (accum_overflow) begin
                            axiomatic_fault <= 1'b1;
                            fault_type      <= FAULT_BIT_OVERFLOW;
                        end else if (is_fractional) begin
                            axiomatic_fault <= 1'b1;
                            fault_type      <= FAULT_FRACTIONAL;
                        end
                    end

                    // ── WKL₀: Bounded Choice ──────────────────
                    // LUT-based neighborhood operations are allowed.
                    // Fractional leakage tolerated; overflow still trapped.
                    2'b01: begin
                        if (accum_overflow) begin
                            axiomatic_fault <= 1'b1;
                            fault_type      <= FAULT_BIT_OVERFLOW;
                        end
                    end

                    // ── ACA₀: Arithmetical Comprehension ──────
                    // Full dynamic scale.  Gatekeeper backs off unless
                    // a hard physical fault is detected (not implemented
                    // at this level — reserved for future ECC/parity).
                    2'b10: begin
                        axiomatic_fault <= 1'b0;
                    end

                    default: begin
                        axiomatic_fault <= 1'b0;
                    end
                endcase

                // Increment fault counter (saturating)
                if (axiomatic_fault && fault_count != 16'hFFFF)
                    fault_count <= fault_count + 16'd1;

            end
        end
    end

endmodule
