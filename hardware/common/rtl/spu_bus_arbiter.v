// SPU-13 Whisper Bus Arbiter v2.0 — Fibonacci Round-Robin
// CC0 1.0 Universal.
//
// Manages contention between up to NUM_NODES SPU-4 Sentinel nodes
// communicating with the SPU-13 Governor.
//
// Arbitration policy:
//   Rotating priority (round-robin starting from priority_ptr).
//   On each grant the pointer advances to (winner+1) % NUM_NODES, so
//   every node gets a fair turn regardless of arrival order.
//
//   The background pointer also advances one step each Phi-21 cycle
//   (21 idle clocks) to stay phase-aligned with the Sierpinski clock —
//   the "Fibonacci" in "Fibonacci round-robin."
//
//   Manifold Strike pre-emption: an external `strike_req[NUM_NODES-1:0]`
//   signal bypasses the round-robin and grants the lowest-indexed striker
//   immediately.  Strike has one-cycle latency; normal requests see at most
//   NUM_NODES cycles of latency.
//
// Ports match v1.0 plus `strike_req`.

`timescale 1ns/1ps

module spu_bus_arbiter #(
    parameter NUM_NODES   = 8,
    parameter PHI_ADVANCE = 21   // advance ptr after this many idle cycles
) (
    input  wire                    clk,
    input  wire                    rst_n,

    // Normal request lines from each SPU-4 node
    input  wire [NUM_NODES-1:0]    req_lines,

    // Manifold Strike lines — immediate pre-emption, bypasses round-robin
    input  wire [NUM_NODES-1:0]    strike_req,

    // Grant lines to each SPU-4 node (1-cycle pulse)
    output reg  [NUM_NODES-1:0]    grant_lines,

    // Governor interface
    output reg                     governor_busy,
    output reg  [2:0]              active_node_id
);

    localparam [2:0] NODE_MASK = NUM_NODES[2:0] - 3'd1;  // mod mask (NUM_NODES must be power of 2)

    reg [2:0]  priority_ptr;     // rotating base for round-robin scan
    reg [4:0]  idle_ctr;         // counts idle cycles for Phi-advance

    // ── Combinatorial rotating priority scan ────────────────────────────
    integer j;
    reg [NUM_NODES-1:0] rotated;
    reg [2:0] rr_winner;
    reg       rr_valid;

    always @(*) begin
        rr_valid  = 1'b0;
        rr_winner = 3'd0;
        for (j = 0; j < NUM_NODES; j = j + 1) begin
            rotated[j] = req_lines[(priority_ptr + j[2:0]) & NODE_MASK];
        end
        for (j = NUM_NODES-1; j >= 0; j = j - 1) begin
            if (rotated[j]) begin
                rr_winner = j[2:0];
                rr_valid  = 1'b1;
            end
        end
    end

    wire [2:0] rr_id = (priority_ptr + rr_winner) & NODE_MASK;

    // ── Strike pre-emption ───────────────────────────────────────────────
    reg [2:0] strike_winner;
    reg       strike_valid;
    always @(*) begin
        strike_valid  = 1'b0;
        strike_winner = 3'd0;
        for (j = NUM_NODES-1; j >= 0; j = j - 1) begin
            if (strike_req[j]) begin
                strike_winner = j[2:0];
                strike_valid  = 1'b1;
            end
        end
    end

    // ── Registered output ────────────────────────────────────────────────
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            grant_lines    <= {NUM_NODES{1'b0}};
            governor_busy  <= 1'b0;
            active_node_id <= 3'd0;
            priority_ptr   <= 3'd0;
            idle_ctr       <= 5'd0;
        end else begin
            grant_lines   <= {NUM_NODES{1'b0}};
            governor_busy <= 1'b0;

            if (strike_valid) begin
                grant_lines[strike_winner]  <= 1'b1;
                governor_busy              <= 1'b1;
                active_node_id             <= strike_winner;
                idle_ctr <= 5'd0;

            end else if (rr_valid) begin
                grant_lines[rr_id] <= 1'b1;
                governor_busy      <= 1'b1;
                active_node_id     <= rr_id;
                priority_ptr       <= (rr_id + 3'd1) & NODE_MASK;
                idle_ctr           <= 5'd0;

            end else begin
                if (idle_ctr == PHI_ADVANCE[4:0] - 5'd1) begin
                    priority_ptr <= (priority_ptr + 3'd1) & NODE_MASK;
                    idle_ctr     <= 5'd0;
                end else begin
                    idle_ctr <= idle_ctr + 5'd1;
                end
            end
        end
    end

endmodule
