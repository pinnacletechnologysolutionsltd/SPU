// spu_ve_qr_init.v — Vector Equilibrium QR Register File Loader (v1.0)
// CC0 1.0 Universal.
//
// On boot_done, hydrates the 12 QR registers (QR1–QR12) with the
// zero-sum VE (cuboctahedron) vertex set. QR0 is set to identity.
//
// Vertices are the 12 permutations of (-1,0,0,1) — integer Quadray,
// sum=0, Davis-laminar. Computed from Cartesian (±1,±1,0) via the
// Tom Ace basis transform.
//
// Each component is a 64-bit surd: {P[31:0], Q[31:0]}.
// Integer values are stored as P=value (Q12 scaled for consistency
// with the rest of the arithmetic pipeline: 1 → 0x00001000).
// Q=0 always (no √3 component in these pure-rational seed vectors).
//
// Latency: 0 (combinational output). Registered at the QR regfile.
// Depends on: nothing.
//
// Integration: wire ve_valid → init_en on spu_quadray_regfile,
//   and sequence ve_state through 13 init cycles (one per lane).

`timescale 1ns/1ps

module spu_ve_qr_init (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         boot_done,

    // QR regfile hydration interface
    output reg          init_en,
    output reg  [3:0]   init_lane,
    output reg  [63:0]  init_A, init_B, init_C, init_D,
    output wire         init_done
);

    // Q12 integer values: 1 = 0x00001000, -1 = 0xFFFF_F000, 0 = 0
    localparam [31:0] P1  = 32'h0000_1000;
    localparam [31:0] N1  = 32'hFFFF_F000;
    localparam [31:0] Z   = 32'h0000_0000;
    localparam [63:0] POS = {Z, P1};  // +1: Q=0, P=+1 (Q12)
    localparam [63:0] NEG = {Z, N1};  // -1: Q=0, P=-1 (Q12)
    localparam [63:0] Z64 = 64'h0;

    // 12 VE vertices: permutations of (-1,0,0,1), zero-sum
    // Stored as {A, B, C, D} each 64-bit surd
    reg [255:0] ve_vertices [0:11];
    integer i;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 12; i = i + 1)
                ve_vertices[i] <= 256'b0;
        end else if (boot_done) begin
            // Vertex 0:  (-1,  0,  0,  1)
            ve_vertices[0]  <= {NEG, Z64, Z64, POS};
            // Vertex 1:  (-1,  0,  1,  0)
            ve_vertices[1]  <= {NEG, Z64, POS, Z64};
            // Vertex 2:  (-1,  1,  0,  0)
            ve_vertices[2]  <= {NEG, POS, Z64, Z64};
            // Vertex 3:  ( 0, -1,  0,  1)
            ve_vertices[3]  <= {Z64, NEG, Z64, POS};
            // Vertex 4:  ( 0, -1,  1,  0)
            ve_vertices[4]  <= {Z64, NEG, POS, Z64};
            // Vertex 5:  ( 0,  0, -1,  1)
            ve_vertices[5]  <= {Z64, Z64, NEG, POS};
            // Vertex 6:  ( 0,  0,  1, -1)
            ve_vertices[6]  <= {Z64, Z64, POS, NEG};
            // Vertex 7:  ( 0,  1, -1,  0)
            ve_vertices[7]  <= {Z64, POS, NEG, Z64};
            // Vertex 8:  ( 0,  1,  0, -1)
            ve_vertices[8]  <= {Z64, POS, Z64, NEG};
            // Vertex 9:  ( 1, -1,  0,  0)
            ve_vertices[9]  <= {POS, NEG, Z64, Z64};
            // Vertex 10: ( 1,  0, -1,  0)
            ve_vertices[10] <= {POS, Z64, NEG, Z64};
            // Vertex 11: ( 1,  0,  0, -1)
            ve_vertices[11] <= {POS, Z64, Z64, NEG};
        end
    end

    // ── Hydration sequencer ───────────────────────────────────────────
    // Walks through lanes 1–12 on successive cycles after boot_done,
    // emitting one init_en pulse per lane.
    reg [3:0] seq_lane;
    reg       active;
    reg       done_flag;

    assign init_done = done_flag;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            seq_lane  <= 0;
            active    <= 0;
            done_flag <= 0;
            init_en   <= 0;
        end else begin
            init_en <= 0;  // default: no pulse

            if (boot_done && !active && !done_flag) begin
                active   <= 1;
                seq_lane <= 0;
            end else if (active) begin
                // Emit one init pulse per cycle
                init_en   <= 1;
                init_lane <= seq_lane + 1;  // QR1–QR12
                // Unpack vertex from ve_vertices[seq_lane]
                init_A <= ve_vertices[seq_lane][255:192];
                init_B <= ve_vertices[seq_lane][191:128];
                init_C <= ve_vertices[seq_lane][127:64];
                init_D <= ve_vertices[seq_lane][63:0];

                if (seq_lane == 11) begin
                    active    <= 0;
                    done_flag <= 1;
                end else begin
                    seq_lane <= seq_lane + 1;
                end
            end
        end
    end

endmodule
