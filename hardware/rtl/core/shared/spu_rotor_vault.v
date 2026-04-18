// spu_rotor_vault.v (v2.0 - Pell Octave Sovereign Storage)
// Stores the 8-entry Pell fundamental orbit as a ROM, with per-axis
// step (int3) and octave (int8) registers.
//
// Pell orbit in Q(√3): r^n where r=(2+√3).  Fundamental domain: steps 0-7.
// Representation:  orbit[step] = {P[15:0], Q[15:0]}  (raw integers, not scaled)
// Norm invariant:  P²−3Q²=1 for every step.  Max value: (5042,2911) at step 7.
//
// ROT operation:
//   step[axis]    = (step[axis] + 1) % 8
//   octave[axis] += carry from step wrap
//   rotor_out     = orbit[new step]          (16-bit P, 16-bit Q)
//   octave_out    = octave[axis]             (absolute octave count)
//
// READ operation (rot_en=0): synchronous read of current state for axis.
//
// The actual rotation r^(8k+s) has:
//   stored (P,Q) = orbit[s]   — always fits int16
//   scale        = OCTAVE^k   — tracked as octave integer, never computed
//
// This is the hardware implementation of knowledge/PELL_OCTAVE.md.

module spu_rotor_vault (
    input  wire        clk,
    input  wire        reset,
    input  wire [3:0]  axis_id,   // which of the 13 axes (0-12)
    input  wire        rot_en,    // 1 = apply one ROT step to axis_id
    output reg  [31:0] rotor_out, // {P[15:0], Q[15:0]} fundamental mantissa
    output reg  [7:0]  octave_out,// absolute octave (0 = first 8 steps)
    output reg  [2:0]  step_out   // current step within octave (0-7)
);

    // ── Pell fundamental orbit ROM (steps 0-7) ───────────────────────────
    // orbit[i] = r^i = (P, Q) where P²-3Q²=1, packed {P[15:0], Q[15:0]}
    reg [31:0] orbit [0:7];
    initial begin
        orbit[0] = 32'h00010000; // r^0 = (1,    0   )  Q=1-0=1  ✓
        orbit[1] = 32'h00020001; // r^1 = (2,    1   )  Q=4-3=1  ✓
        orbit[2] = 32'h00070004; // r^2 = (7,    4   )  Q=49-48=1 ✓
        orbit[3] = 32'h001A000F; // r^3 = (26,   15  )  Q=676-675=1 ✓
        orbit[4] = 32'h00610038; // r^4 = (97,   56  )  Q=9409-9408=1 ✓
        orbit[5] = 32'h016A00D1; // r^5 = (362,  209 )  Q=131044-131043=1 ✓
        orbit[6] = 32'h0547030C; // r^6 = (1351, 780 )  Q=1825201-1825200=1 ✓
        orbit[7] = 32'h13B20B5F; // r^7 = (5042, 2911)  Q=25421764-25421763=1 ✓
        // r^8 = (18817,10864) — overflows int16 → octave increments, step resets to 0
    end

    // ── Per-axis step and octave registers (13 axes) ─────────────────────
    reg [2:0] axis_step   [0:12]; // step within octave, 0-7
    reg [7:0] axis_octave [0:12]; // octave count (signed, range ±127)

    integer i;
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            for (i = 0; i < 13; i = i + 1) begin
                axis_step[i]   <= 3'd0;
                axis_octave[i] <= 8'd0;
            end
            rotor_out  <= orbit[0];
            octave_out <= 8'd0;
            step_out   <= 3'd0;
        end else begin
            if (rot_en && (axis_id <= 4'd12)) begin
                // Increment step; carry into octave when step wraps 7→0
                if (axis_step[axis_id] == 3'd7) begin
                    axis_step[axis_id]   <= 3'd0;
                    axis_octave[axis_id] <= axis_octave[axis_id] + 8'd1;
                end else begin
                    axis_step[axis_id] <= axis_step[axis_id] + 3'd1;
                end
            end
            // Read registered output (1-cycle latency from rot_en)
            rotor_out  <= orbit[rot_en ? (axis_step[axis_id] == 3'd7 ? 3'd0
                                         : axis_step[axis_id] + 3'd1)
                                       : axis_step[axis_id]];
            octave_out <= rot_en ? (axis_step[axis_id] == 3'd7
                                    ? axis_octave[axis_id] + 8'd1
                                    : axis_octave[axis_id])
                                 : axis_octave[axis_id];
            step_out   <= rot_en ? (axis_step[axis_id] == 3'd7 ? 3'd0
                                    : axis_step[axis_id] + 3'd1)
                                 : axis_step[axis_id];
        end
    end

endmodule

