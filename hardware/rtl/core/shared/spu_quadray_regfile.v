// spu_quadray_regfile.v — Quadray Register File (v1.0)
//
// 13 registers, each holding a full 4-component Quadray vector.
// Encoding per component: [63:32] = Q (coefficient of √3, signed int32)
//                         [31:0]  = P (rational part, signed int32)
//
// Total: 13 × 4 × 64 = 3328 bits ≈ 104 LUTs as distributed RAM.
//
// Two read ports and one write port:
//   Read:  source lane → A,B,C,D components (4×64-bit)
//   Write: A,B,C,D components → destination lane
//
// Designed to interface directly with spu13_rotor_core.v (F,G,H circulant).

module spu_quadray_regfile #(
    parameter AXES = 13,
    parameter LANE_BITS = 64,    // bits per surd component
    parameter LANE_AW = 4        // address width (0-12)
) (
    input  wire        clk,
    input  wire        rst_n,

    // ── Read port (combinational) ──────────────────────────────────────
    input  wire [LANE_AW-1:0]  rd_lane,
    output wire [LANE_BITS-1:0] rd_A, rd_B, rd_C, rd_D,

    // ── Write port (registered) ────────────────────────────────────────
    input  wire                 wr_en,
    input  wire [LANE_AW-1:0]   wr_lane,
    input  wire [LANE_BITS-1:0] wr_A, wr_B, wr_C, wr_D,

    // ── Initialization (hydration from bootloader) ─────────────────────
    input  wire                 init_en,
    input  wire [LANE_AW-1:0]   init_lane,
    input  wire [LANE_BITS-1:0] init_A, init_B, init_C, init_D,

    // ── Debug / telemetry ──────────────────────────────────────────────
    output wire [LANE_BITS-1:0] dbg_A, dbg_B, dbg_C, dbg_D
);

    // ── Register storage ───────────────────────────────────────────────
    // 13 lanes × 4 components × 64 bits each
    reg [LANE_BITS-1:0] reg_A [0:AXES-1];
    reg [LANE_BITS-1:0] reg_B [0:AXES-1];
    reg [LANE_BITS-1:0] reg_C [0:AXES-1];
    reg [LANE_BITS-1:0] reg_D [0:AXES-1];

    integer i;

    // ── Write logic ────────────────────────────────────────────────────
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < AXES; i = i + 1) begin
                reg_A[i] <= 64'h0000_0001_0000_0000;  // QR identity: A=1, others 0
                reg_B[i] <= 64'h0000_0000_0000_0000;
                reg_C[i] <= 64'h0000_0000_0000_0000;
                reg_D[i] <= 64'h0000_0000_0000_0000;
            end
        end else begin
            if (init_en) begin
                reg_A[init_lane] <= init_A;
                reg_B[init_lane] <= init_B;
                reg_C[init_lane] <= init_C;
                reg_D[init_lane] <= init_D;
            end else if (wr_en) begin
                reg_A[wr_lane] <= wr_A;
                reg_B[wr_lane] <= wr_B;
                reg_C[wr_lane] <= wr_C;
                reg_D[wr_lane] <= wr_D;
            end
        end
    end

    // ── Read logic (combinational) ─────────────────────────────────────
    assign rd_A = reg_A[rd_lane];
    assign rd_B = reg_B[rd_lane];
    assign rd_C = reg_C[rd_lane];
    assign rd_D = reg_D[rd_lane];

    // ── Debug output (lane 0) ──────────────────────────────────────────
    assign dbg_A = reg_A[0];
    assign dbg_B = reg_B[0];
    assign dbg_C = reg_C[0];
    assign dbg_D = reg_D[0];

endmodule
