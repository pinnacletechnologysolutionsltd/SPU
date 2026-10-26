// SPU-13 Scoreboard v2 — done-coupled busy-bit hazard tracking
//
// Replaces the timer-based prototype (spu13_scoreboard.v, unverified).
// One busy bit per architectural register, set when a multi-cycle tower
// operation is accepted, cleared by the tower's actual completion pulse —
// never by a latency assumption. This stays correct when the tower exits
// early on a zero-norm operand (FLAGS.V singular-absorber path) and under
// any future variable-latency unit.
//
// Single-cycle ops are not tracked: the 4R2W register file's combinational
// write-forwarding bypass already covers their read-after-write window.
//
// Structural hazard: there is one tower, so a second tower op stalls while
// tower_busy is high regardless of its registers. Because tower_busy clears
// on the same edge the done pulse is observed, a same-cycle done + reissue
// collision is structurally impossible: the reissue stalls that cycle and
// is accepted the next.

module spu13_scoreboard_v2 #(
    parameter REG_COUNT = 32,           // 32 for SPU-13, 8 for SPU-4
    parameter REG_BITS  = 5
)(
    input  wire                clk,
    input  wire                rst,

    // Issue interface
    input  wire                issue_valid,
    input  wire [REG_BITS-1:0] issue_rs1,
    input  wire [REG_BITS-1:0] issue_rs2,
    input  wire [REG_BITS-1:0] issue_rd,
    input  wire                issue_uses_rs1,
    input  wire                issue_uses_rs2,
    input  wire                issue_is_tower,  // multi-cycle tower op (INVJ, Pade, PHSLK)

    // Tower writeback snoop
    input  wire                tower_done,      // pulses with tower writeback
    input  wire                tower_abort,     // zero-norm early exit: no writeback, FLAGS.V

    output wire                hazard_stall,    // stall issue stage this cycle
    output wire                tower_busy
);

    reg [REG_COUNT-1:0] busy;
    reg                 tower_busy_r;
    reg [REG_BITS-1:0]  tower_rd;

    assign tower_busy = tower_busy_r;

    wire rs1_hazard = issue_uses_rs1 && busy[issue_rs1];
    wire rs2_hazard = issue_uses_rs2 && busy[issue_rs2];
    wire rd_hazard  = busy[issue_rd];                       // WAW / WAR on pending tower dest
    wire structural = issue_is_tower && tower_busy_r;       // one tower only

    assign hazard_stall = issue_valid &&
                          (rs1_hazard || rs2_hazard || rd_hazard || structural);

    wire accept_tower = issue_valid && issue_is_tower && !hazard_stall;
    wire tower_release = tower_busy_r && (tower_done || tower_abort);

    always @(posedge clk) begin
        if (rst) begin
            busy         <= {REG_COUNT{1'b0}};
            tower_busy_r <= 1'b0;
            tower_rd     <= {REG_BITS{1'b0}};
        end else begin
            // Release first, then accept: an accept can never target the
            // releasing register in the same cycle (structural stall above),
            // so the ordering is safe by construction.
            if (tower_release) begin
                busy[tower_rd] <= 1'b0;
                tower_busy_r   <= 1'b0;
            end
            if (accept_tower) begin
                busy[issue_rd] <= 1'b1;
                tower_busy_r   <= 1'b1;
                tower_rd       <= issue_rd;
            end
        end
    end

endmodule
