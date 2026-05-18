// spu_rotor_vault.v (v2.0 - Pell Octave Sovereign Storage)
// Stores the 8-entry Pell fundamental orbit as a boot-hydratable ROM, with
// per-axis step (int3) and octave (int8) registers.
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
    input  wire        init_we,   // 1 = hydrate an orbit entry from flash
    input  wire [2:0]  init_step, // Pell fundamental step 0-7
    input  wire [31:0] init_rotor,// {P[15:0], Q[15:0]} raw integer mantissa
    output reg  [31:0] rotor_out, // {P[15:0], Q[15:0]} fundamental mantissa
    output reg  [7:0]  octave_out,// absolute octave (0 = first 8 steps)
    output reg  [2:0]  step_out   // current step within octave (0-7)
);

    // ── Pell fundamental orbit ROM (steps 0-7) ───────────────────────────
    // orbit[i] = r^i = (P, Q) where P²-3Q²=1, packed {P[15:0], Q[15:0]}
    reg [31:0] orbit0;
    reg [31:0] orbit1;
    reg [31:0] orbit2;
    reg [31:0] orbit3;
    reg [31:0] orbit4;
    reg [31:0] orbit5;
    reg [31:0] orbit6;
    reg [31:0] orbit7;

    initial begin
        orbit0 = 32'h00010000; // r^0 = (1,    0   )  Q=1-0=1  ✓
        orbit1 = 32'h00020001; // r^1 = (2,    1   )  Q=4-3=1  ✓
        orbit2 = 32'h00070004; // r^2 = (7,    4   )  Q=49-48=1 ✓
        orbit3 = 32'h001A000F; // r^3 = (26,   15  )  Q=676-675=1 ✓
        orbit4 = 32'h00610038; // r^4 = (97,   56  )  Q=9409-9408=1 ✓
        orbit5 = 32'h016A00D1; // r^5 = (362,  209 )  Q=131044-131043=1 ✓
        orbit6 = 32'h0547030C; // r^6 = (1351, 780 )  Q=1825201-1825200=1 ✓
        orbit7 = 32'h13B20B5F; // r^7 = (5042, 2911)  Q=25421764-25421763=1 ✓
        // r^8 = (18817,10864) — overflows int16 → octave increments, step resets to 0
    end

    // ── Per-axis step and octave registers (13 axes) ─────────────────────
    reg [2:0] axis_step0;
    reg [2:0] axis_step1;
    reg [2:0] axis_step2;
    reg [2:0] axis_step3;
    reg [2:0] axis_step4;
    reg [2:0] axis_step5;
    reg [2:0] axis_step6;
    reg [2:0] axis_step7;
    reg [2:0] axis_step8;
    reg [2:0] axis_step9;
    reg [2:0] axis_step10;
    reg [2:0] axis_step11;
    reg [2:0] axis_step12;

    reg [7:0] axis_octave0;
    reg [7:0] axis_octave1;
    reg [7:0] axis_octave2;
    reg [7:0] axis_octave3;
    reg [7:0] axis_octave4;
    reg [7:0] axis_octave5;
    reg [7:0] axis_octave6;
    reg [7:0] axis_octave7;
    reg [7:0] axis_octave8;
    reg [7:0] axis_octave9;
    reg [7:0] axis_octave10;
    reg [7:0] axis_octave11;
    reg [7:0] axis_octave12;

    function [31:0] orbit_at;
        input [2:0] step;
        begin
            case (step)
                3'd0: orbit_at = orbit0;
                3'd1: orbit_at = orbit1;
                3'd2: orbit_at = orbit2;
                3'd3: orbit_at = orbit3;
                3'd4: orbit_at = orbit4;
                3'd5: orbit_at = orbit5;
                3'd6: orbit_at = orbit6;
                3'd7: orbit_at = orbit7;
                default: orbit_at = orbit0;
            endcase
        end
    endfunction

    function [2:0] axis_step_at;
        input [3:0] axis;
        begin
            case (axis)
                4'd0: axis_step_at = axis_step0;
                4'd1: axis_step_at = axis_step1;
                4'd2: axis_step_at = axis_step2;
                4'd3: axis_step_at = axis_step3;
                4'd4: axis_step_at = axis_step4;
                4'd5: axis_step_at = axis_step5;
                4'd6: axis_step_at = axis_step6;
                4'd7: axis_step_at = axis_step7;
                4'd8: axis_step_at = axis_step8;
                4'd9: axis_step_at = axis_step9;
                4'd10: axis_step_at = axis_step10;
                4'd11: axis_step_at = axis_step11;
                4'd12: axis_step_at = axis_step12;
                default: axis_step_at = 3'd0;
            endcase
        end
    endfunction

    function [7:0] axis_octave_at;
        input [3:0] axis;
        begin
            case (axis)
                4'd0: axis_octave_at = axis_octave0;
                4'd1: axis_octave_at = axis_octave1;
                4'd2: axis_octave_at = axis_octave2;
                4'd3: axis_octave_at = axis_octave3;
                4'd4: axis_octave_at = axis_octave4;
                4'd5: axis_octave_at = axis_octave5;
                4'd6: axis_octave_at = axis_octave6;
                4'd7: axis_octave_at = axis_octave7;
                4'd8: axis_octave_at = axis_octave8;
                4'd9: axis_octave_at = axis_octave9;
                4'd10: axis_octave_at = axis_octave10;
                4'd11: axis_octave_at = axis_octave11;
                4'd12: axis_octave_at = axis_octave12;
                default: axis_octave_at = 8'd0;
            endcase
        end
    endfunction

    reg [2:0] selected_step;
    reg [7:0] selected_octave;
    reg [2:0] next_step;
    reg [7:0] next_octave;

    always @(posedge clk) begin
        if (reset) begin
            axis_step0 <= 3'd0;
            axis_step1 <= 3'd0;
            axis_step2 <= 3'd0;
            axis_step3 <= 3'd0;
            axis_step4 <= 3'd0;
            axis_step5 <= 3'd0;
            axis_step6 <= 3'd0;
            axis_step7 <= 3'd0;
            axis_step8 <= 3'd0;
            axis_step9 <= 3'd0;
            axis_step10 <= 3'd0;
            axis_step11 <= 3'd0;
            axis_step12 <= 3'd0;

            axis_octave0 <= 8'd0;
            axis_octave1 <= 8'd0;
            axis_octave2 <= 8'd0;
            axis_octave3 <= 8'd0;
            axis_octave4 <= 8'd0;
            axis_octave5 <= 8'd0;
            axis_octave6 <= 8'd0;
            axis_octave7 <= 8'd0;
            axis_octave8 <= 8'd0;
            axis_octave9 <= 8'd0;
            axis_octave10 <= 8'd0;
            axis_octave11 <= 8'd0;
            axis_octave12 <= 8'd0;

            rotor_out  <= orbit_at(3'd0);
            octave_out <= 8'd0;
            step_out   <= 3'd0;
        end else begin
            selected_step = axis_step_at(axis_id);
            selected_octave = axis_octave_at(axis_id);
            next_step = selected_step;
            next_octave = selected_octave;

            if (rot_en && (axis_id <= 4'd12)) begin
                if (selected_step == 3'd7) begin
                    next_step = 3'd0;
                    next_octave = selected_octave + 8'd1;
                end else begin
                    next_step = selected_step + 3'd1;
                end
            end

            if (init_we) begin
                case (init_step)
                    3'd0: orbit0 <= init_rotor;
                    3'd1: orbit1 <= init_rotor;
                    3'd2: orbit2 <= init_rotor;
                    3'd3: orbit3 <= init_rotor;
                    3'd4: orbit4 <= init_rotor;
                    3'd5: orbit5 <= init_rotor;
                    3'd6: orbit6 <= init_rotor;
                    3'd7: orbit7 <= init_rotor;
                    default: ;
                endcase
            end
            if (rot_en && (axis_id <= 4'd12)) begin
                // Increment step; carry into octave when step wraps 7→0
                case (axis_id)
                    4'd0: begin axis_step0 <= next_step; axis_octave0 <= next_octave; end
                    4'd1: begin axis_step1 <= next_step; axis_octave1 <= next_octave; end
                    4'd2: begin axis_step2 <= next_step; axis_octave2 <= next_octave; end
                    4'd3: begin axis_step3 <= next_step; axis_octave3 <= next_octave; end
                    4'd4: begin axis_step4 <= next_step; axis_octave4 <= next_octave; end
                    4'd5: begin axis_step5 <= next_step; axis_octave5 <= next_octave; end
                    4'd6: begin axis_step6 <= next_step; axis_octave6 <= next_octave; end
                    4'd7: begin axis_step7 <= next_step; axis_octave7 <= next_octave; end
                    4'd8: begin axis_step8 <= next_step; axis_octave8 <= next_octave; end
                    4'd9: begin axis_step9 <= next_step; axis_octave9 <= next_octave; end
                    4'd10: begin axis_step10 <= next_step; axis_octave10 <= next_octave; end
                    4'd11: begin axis_step11 <= next_step; axis_octave11 <= next_octave; end
                    4'd12: begin axis_step12 <= next_step; axis_octave12 <= next_octave; end
                    default: ;
                endcase
                end
            // Read registered output (1-cycle latency from rot_en)
            rotor_out  <= orbit_at(next_step);
            octave_out <= next_octave;
            step_out   <= next_step;
        end
    end

endmodule
