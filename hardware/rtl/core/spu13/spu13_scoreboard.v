// SPU-13 Scoreboarded Pipeline Controller (v2.1 Sovereign)
// Objective: Track register readiness to enable out-of-order execution stall logic.
// Logic: 26-bit scoreboard (one bit per manifold register)

module spu13_scoreboard (
    input  wire        clk,
    input  wire        reset,
    
    // Dispatch Interface
    input  wire [7:0]  r1_idx,
    input  wire [7:0]  r2_idx,
    input  wire        inst_valid,
    
    // Pipeline Feedback
    input  wire        writeback_valid,
    input  wire [7:0]  writeback_reg,
    
    output wire        stall_core
);

    // Scoreboard with latency tracking
    reg [25:0] scoreboard;
    reg [25:0] pending_writeback [2:0]; // 3-cycle latency shift register

    integer i;
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            scoreboard <= 26'b0;
            for(i=0; i<3; i=i+1) pending_writeback[i] <= 26'b0;
        end else begin
            // 1. Mark registers busy
            if (inst_valid) scoreboard[r1_idx] <= 1'b1;
            
            // 2. Shift pipeline latency and resolve writebacks
            pending_writeback[0] <= (inst_valid) ? (1 << r1_idx) : 26'b0;
            pending_writeback[1] <= pending_writeback[0];
            pending_writeback[2] <= pending_writeback[1];
            
            if (pending_writeback[2] != 0) begin
                scoreboard <= scoreboard & ~pending_writeback[2];
            end
        end
    end

    assign stall_core = (inst_valid) && (scoreboard[r1_idx] || scoreboard[r2_idx]);

endmodule
