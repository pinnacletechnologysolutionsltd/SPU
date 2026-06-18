// spu_trajectory_correct.v — RPLU Trajectory Correction Engine (v1.0)
//
// Closes the robotics control loop:
//   1. Compute error = commanded − actual
//   2. Compute error quadrance = Σ (a² − 3b²) per component
//   3. Hash quadrance → RPLU address
//   4. Correction = RPLU table lookup
//   5. Corrected = commanded + correction
//
// The RPLU table is pre-loaded at boot (16 entries × 64-bit correction
// vectors, fits in one BRAM18).  The hash maps quadrance magnitude
// to a bin address via arithmetic right-shift.
//
// Pipeline: 3 cycles (subtract → quadrance → lookup+apply)
//
// CC0 1.0 Universal.

module spu_trajectory_correct #(
    parameter WIDTH        = 18,     // surd coefficient width
    parameter RPLU_DEPTH   = 16,     // RPLU table entries
    parameter Q_BITS       = 4       // quadrance hash shift (bin width)
)(
    input  wire        clk,
    input  wire        rst_n,

    // ── Control ──────────────────────────────────────────────
    input  wire        correct_start,   // pulse to begin correction
    output reg         correct_done,    // pulses when complete

    // ── Position vectors (commanded / actual from QR regfile) ─
    input  wire [63:0] commanded_A, commanded_B, commanded_C, commanded_D,
    input  wire [63:0] actual_A, actual_B, actual_C, actual_D,

    // ── RPLU table interface (read-only, pre-loaded at boot) ──
    output reg  [$clog2(RPLU_DEPTH)-1:0] rplu_addr,
    input  wire [63:0]                    rplu_data,  // correction vector

    // ── Corrected output ─────────────────────────────────────
    output reg  [63:0] corrected_A, corrected_B, corrected_C, corrected_D,
    output reg  [31:0] error_quadrance    // for debug / gatekeeper
);

    // ── FSM ──────────────────────────────────────────────────
    localparam S_IDLE      = 0;
    localparam S_SUBTRACT  = 1;   // compute error = commanded - actual
    localparam S_QUADRANCE = 2;   // compute Σ (a² − 3b²), hash → address
    localparam S_CORRECT   = 3;   // rplu lookup + apply correction

    reg [1:0] state;

    // ── Error vector (registered) ────────────────────────────
    reg signed [WIDTH-1:0] err_A_a, err_A_b;
    reg signed [WIDTH-1:0] err_B_a, err_B_b;
    reg signed [WIDTH-1:0] err_C_a, err_C_b;
    reg signed [WIDTH-1:0] err_D_a, err_D_b;

    // ── RPLU correction (from table) ─────────────────────────
    wire signed [WIDTH-1:0] corr_A_a = rplu_data[WIDTH-1:0];
    wire signed [WIDTH-1:0] corr_A_b = rplu_data[2*WIDTH-1:WIDTH];
    wire signed [WIDTH-1:0] corr_B_a = rplu_data[3*WIDTH-1:2*WIDTH];
    wire signed [WIDTH-1:0] corr_B_b = rplu_data[4*WIDTH-1:3*WIDTH];

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state          <= S_IDLE;
            correct_done   <= 0;
            rplu_addr      <= 0;
            corrected_A    <= 0; corrected_B <= 0;
            corrected_C    <= 0; corrected_D <= 0;
            error_quadrance <= 0;
            err_A_a <= 0; err_A_b <= 0;
            err_B_a <= 0; err_B_b <= 0;
            err_C_a <= 0; err_C_b <= 0;
            err_D_a <= 0; err_D_b <= 0;
        end else begin
            correct_done <= 0;

            case (state)
                S_IDLE: begin
                    if (correct_start) begin
                        // Truncate 64-bit surds to WIDTH bits
                        err_A_a <= commanded_A[WIDTH-1:0] - actual_A[WIDTH-1:0];
                        err_A_b <= commanded_A[2*WIDTH-1:WIDTH] - actual_A[2*WIDTH-1:WIDTH];
                        err_B_a <= commanded_B[WIDTH-1:0] - actual_B[WIDTH-1:0];
                        err_B_b <= commanded_B[2*WIDTH-1:WIDTH] - actual_B[2*WIDTH-1:WIDTH];
                        err_C_a <= commanded_C[WIDTH-1:0] - actual_C[WIDTH-1:0];
                        err_C_b <= commanded_C[2*WIDTH-1:WIDTH] - actual_C[2*WIDTH-1:WIDTH];
                        err_D_a <= commanded_D[WIDTH-1:0] - actual_D[WIDTH-1:0];
                        err_D_b <= commanded_D[2*WIDTH-1:WIDTH] - actual_D[2*WIDTH-1:WIDTH];
                        state <= S_QUADRANCE;
                    end
                end

                S_QUADRANCE: begin
                    // Quadrance per component: Q_c = a² − 3b²
                    // Sum all 4 components, take absolute value
                    wire signed [63:0] qA = err_A_a*err_A_a - 3*err_A_b*err_A_b;
                    wire signed [63:0] qB = err_B_a*err_B_a - 3*err_B_b*err_B_b;
                    wire signed [63:0] qC = err_C_a*err_C_a - 3*err_C_b*err_C_b;
                    wire signed [63:0] qD = err_D_a*err_D_a - 3*err_D_b*err_D_b;
                    wire signed [63:0] q_sum = qA + qB + qC + qD;

                    // Hash: abs(q_sum) >> Q_BITS → RPLU address
                    rplu_addr <= (q_sum[63] ? -q_sum : q_sum) >> Q_BITS;
                    error_quadrance <= q_sum[31:0];
                    state <= S_CORRECT;
                end

                S_CORRECT: begin
                    // Apply correction: corrected = commanded + RPLU_value
                    // Only A and B components corrected (simplified)
                    corrected_A <= {commanded_A[63:2*WIDTH],
                                    commanded_A[2*WIDTH-1:WIDTH] + corr_A_b,
                                    commanded_A[WIDTH-1:0] + corr_A_a};
                    corrected_B <= {commanded_B[63:2*WIDTH],
                                    commanded_B[2*WIDTH-1:WIDTH] + corr_B_b,
                                    commanded_B[WIDTH-1:0] + corr_B_a};
                    corrected_C <= commanded_C;
                    corrected_D <= commanded_D;
                    correct_done <= 1;
                    state <= S_IDLE;
                end

                default: state <= S_IDLE;
            endcase
        end
    end

endmodule
