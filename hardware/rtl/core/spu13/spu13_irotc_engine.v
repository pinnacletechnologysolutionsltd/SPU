// spu13_irotc_engine.v — Icosahedral A5 rotation engine (IROTC opcode)
//
// Copyright 2026 John Curley
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//
// Term-serial coefficient-select datapath (docs/IROTC_SPEC.md §6, design
// decision 2026-07-10): the doubled numerator alphabet is only
// {0, ±1, ±2, ±phi, ±phi^-1, ±sqrt5}, each a single-cycle signed map on a
// Z[phi] pair, so one shared term unit + 9 accumulate cycles executes any
// of the 60 rotations — either catalog — in a FIXED 13-cycle slot:
//
//   cycle  0    : start accepted, guards, operand/index latch
//   cycles 1-9  : acc[row] += code(idx,row,col) * w[col]   (x0 burns the
//                 cycle — latency is uniform across all indices)
//   cycle 10    : acc >>>= 1 (unguarded — licensed by the DOUBLED
//                 typestate at dispatch; doubling theorem)
//   cycle 11    : A = -(B+C+D) zero-sum recompute
//   cycle 12    : done pulse, outputs + out_tag valid
//
// This is signed exact Z[phi] integer arithmetic — NOT the mod-L_p plane
// of spu13_lucas_mac.v. No multipliers, no DSPs: adders and muxes only.
//
// The conjugate catalog (sel[6], Galois phi -> 1-phi) is the code remap
// 5<->8, 6<->7, 9<->10 — no second ROM. Code ROM is GENERATED:
//   python3 software/tests/test_icosahedral_catalog.py --emit-rtl
// (catalog sha aabef37c9c8b0317; never hand-edit the .mem).
//
// Dispatch faults (all leave outputs bit-identically untouched):
//   FAULT_BADIDX   sel[5:0] > 59
//   FAULT_UNTAGGED src_tag == TAG_UNTAGGED
//   FAULT_CATMIX   src_tag locked to the other catalog (typestate v0.2)
module spu13_irotc_engine #(
    parameter W = 32,
    parameter CODES_PATH = "hardware/rtl/core/spu13/spu13_irotc_codes.mem"
) (
    input  wire                 clk,
    input  wire                 rst_n,
    input  wire                 start,
    input  wire [6:0]           sel,        // [5:0] index, [6] conjugate
    input  wire [1:0]           src_tag,    // source register typestate
    input  wire signed [W-1:0]  in_b_a, in_b_b,
    input  wire signed [W-1:0]  in_c_a, in_c_b,
    input  wire signed [W-1:0]  in_d_a, in_d_b,
    output reg                  busy,
    output reg                  done,
    output reg                  fault,
    output reg  [1:0]           fault_code,
    output reg  [1:0]           out_tag,    // TAG_MAIN or TAG_CONJ on done
    output reg  signed [W-1:0]  out_a_a, out_a_b,
    output reg  signed [W-1:0]  out_b_a, out_b_b,
    output reg  signed [W-1:0]  out_c_a, out_c_b,
    output reg  signed [W-1:0]  out_d_a, out_d_b
);
    // φ-plane typestate encodings (IROTC_SPEC.md §3)
    localparam [1:0] TAG_UNTAGGED = 2'd0;
    localparam [1:0] TAG_FRESH    = 2'd1;
    localparam [1:0] TAG_MAIN     = 2'd2;
    localparam [1:0] TAG_CONJ     = 2'd3;

    localparam [1:0] FAULT_BADIDX   = 2'd1;
    localparam [1:0] FAULT_UNTAGGED = 2'd2;
    localparam [1:0] FAULT_CATMIX   = 2'd3;

    localparam [1:0] S_IDLE = 2'd0, S_ACC = 2'd1, S_SHIFT = 2'd2,
                     S_ZSUM = 2'd3;

    reg [3:0] code_rom [0:539];             // 60 x 9 alphabet codes
    initial $readmemh(CODES_PATH, code_rom);

    reg                 conj_r;
    reg [9:0]           addr;               // idx*9 + term counter
    reg [3:0]           term;               // 0..8 = row*3 + col
    reg signed [W-1:0]  w_a [0:2];          // latched source (B,C,D) pairs
    reg signed [W-1:0]  w_b [0:2];
    reg signed [W-1:0]  acc_a [0:2];        // output accumulators
    reg signed [W-1:0]  acc_b [0:2];
    reg [1:0]           state;

    // ── term unit ──────────────────────────────────────────────────
    // Conjugate remap first (Galois phi -> 1-phi on the coefficient):
    //   +phi <-> -phi^-1, -phi <-> +phi^-1, +sqrt5 <-> -sqrt5
    wire [3:0] code_raw = code_rom[addr];
    wire [3:0] code = !conj_r        ? code_raw :
                      (code_raw == 4'd5)  ? 4'd8 :
                      (code_raw == 4'd8)  ? 4'd5 :
                      (code_raw == 4'd6)  ? 4'd7 :
                      (code_raw == 4'd7)  ? 4'd6 :
                      (code_raw == 4'd9)  ? 4'd10 :
                      (code_raw == 4'd10) ? 4'd9 : code_raw;

    wire [1:0] col = (term == 4'd0 || term == 4'd3 || term == 4'd6) ? 2'd0 :
                     (term == 4'd1 || term == 4'd4 || term == 4'd7) ? 2'd1 :
                                                                      2'd2;
    wire [1:0] row = (term < 4'd3) ? 2'd0 : (term < 4'd6) ? 2'd1 : 2'd2;

    wire signed [W-1:0] wa = w_a[col];
    wire signed [W-1:0] wb = w_b[col];

    // code * (wa + wb*phi) in Z[phi] — adders and negates only
    reg signed [W-1:0] term_a, term_b;
    always @* begin
        case (code)
            4'd1:    begin term_a =  wa;           term_b =  wb;           end
            4'd2:    begin term_a = -wa;           term_b = -wb;           end
            4'd3:    begin term_a =  wa + wa;      term_b =  wb + wb;      end
            4'd4:    begin term_a = -(wa + wa);    term_b = -(wb + wb);    end
            4'd5:    begin term_a =  wb;           term_b =  wa + wb;      end
            4'd6:    begin term_a = -wb;           term_b = -(wa + wb);    end
            4'd7:    begin term_a =  wb - wa;      term_b =  wa;           end
            4'd8:    begin term_a =  wa - wb;      term_b = -wa;           end
            4'd9:    begin term_a =  wb + wb - wa; term_b =  wa + wa + wb; end
            4'd10:   begin term_a =  wa - wb - wb; term_b = -(wa + wa + wb); end
            default: begin term_a = {W{1'b0}};     term_b = {W{1'b0}};     end
        endcase
    end

    // ── dispatch guards (decode order: BADIDX, UNTAGGED, CATMIX) ───
    wire       bad_idx  = (sel[5:0] > 6'd59);
    wire       untagged = (src_tag == TAG_UNTAGGED);
    wire       catmix   = (src_tag == TAG_MAIN &&  sel[6]) ||
                          (src_tag == TAG_CONJ && !sel[6]);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= S_IDLE; busy <= 0; done <= 0;
            fault <= 0; fault_code <= 0; out_tag <= TAG_UNTAGGED;
            conj_r <= 0; addr <= 0; term <= 0;
            w_a[0] <= 0; w_a[1] <= 0; w_a[2] <= 0;
            w_b[0] <= 0; w_b[1] <= 0; w_b[2] <= 0;
            acc_a[0] <= 0; acc_a[1] <= 0; acc_a[2] <= 0;
            acc_b[0] <= 0; acc_b[1] <= 0; acc_b[2] <= 0;
            out_a_a <= 0; out_a_b <= 0; out_b_a <= 0; out_b_b <= 0;
            out_c_a <= 0; out_c_b <= 0; out_d_a <= 0; out_d_b <= 0;
        end else begin
            done <= 0; fault <= 0;
            case (state)
                S_IDLE: if (start) begin
                    if (bad_idx) begin
                        fault <= 1; fault_code <= FAULT_BADIDX;
                    end else if (untagged) begin
                        fault <= 1; fault_code <= FAULT_UNTAGGED;
                    end else if (catmix) begin
                        fault <= 1; fault_code <= FAULT_CATMIX;
                    end else begin
                        conj_r <= sel[6];
                        // idx*9 = idx*8 + idx
                        addr   <= {1'b0, sel[5:0], 3'b000} + {4'b0, sel[5:0]};
                        term   <= 0;
                        w_a[0] <= in_b_a; w_b[0] <= in_b_b;
                        w_a[1] <= in_c_a; w_b[1] <= in_c_b;
                        w_a[2] <= in_d_a; w_b[2] <= in_d_b;
                        acc_a[0] <= 0; acc_a[1] <= 0; acc_a[2] <= 0;
                        acc_b[0] <= 0; acc_b[1] <= 0; acc_b[2] <= 0;
                        busy <= 1; state <= S_ACC;
                    end
                end

                S_ACC: begin
                    acc_a[row] <= acc_a[row] + term_a;
                    acc_b[row] <= acc_b[row] + term_b;
                    if (term == 4'd8) state <= S_SHIFT;
                    else begin term <= term + 4'd1; addr <= addr + 10'd1; end
                end

                S_SHIFT: begin
                    // Unguarded >>>1: licensed by the typestate at dispatch
                    // (doubling theorem — pre-shift sums are even for every
                    // legally tagged input; no divisibility check here).
                    acc_a[0] <= acc_a[0] >>> 1; acc_b[0] <= acc_b[0] >>> 1;
                    acc_a[1] <= acc_a[1] >>> 1; acc_b[1] <= acc_b[1] >>> 1;
                    acc_a[2] <= acc_a[2] >>> 1; acc_b[2] <= acc_b[2] >>> 1;
                    state <= S_ZSUM;
                end

                S_ZSUM: begin
                    out_b_a <= acc_a[0]; out_b_b <= acc_b[0];
                    out_c_a <= acc_a[1]; out_c_b <= acc_b[1];
                    out_d_a <= acc_a[2]; out_d_b <= acc_b[2];
                    out_a_a <= -(acc_a[0] + acc_a[1] + acc_a[2]);
                    out_a_b <= -(acc_b[0] + acc_b[1] + acc_b[2]);
                    out_tag <= conj_r ? TAG_CONJ : TAG_MAIN;
                    done <= 1; busy <= 0; state <= S_IDLE;
                end
            endcase
        end
    end
endmodule
