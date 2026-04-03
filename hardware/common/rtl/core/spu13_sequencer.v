// spu13_sequencer.v
// Pipelined TDM controller for 13-axis Sovereign Core
// Objective: Orchestrate the 3-stage "Inhale" (Fetch -> Compute -> Commit)

module spu13_sequencer (
    input  wire        clk,            // 24MHz Fast Clock
    input  wire        pulse_61k,      // Heartbeat 61.44kHz
    output reg [3:0]   fetch_ptr,
    output reg [3:0]   commit_ptr,
    output reg         write_en,
    output reg         processing
);

    reg [3:0] delay_cnt;

    initial begin
        fetch_ptr  = 0;
        commit_ptr = 4'hF;
        processing = 0;
        delay_cnt  = 0;
        write_en   = 0;
    end

    always @(posedge clk) begin
        if (pulse_61k) begin
            fetch_ptr  <= 4'h0;
            commit_ptr <= 4'hF; // Offset for 2-cycle compute delay
            processing <= 1'b1;
            delay_cnt  <= 4'h0;
            write_en   <= 1'b0;
        end else if (processing) begin
            // 1. Fetch Stage: Move as long as we haven't reached the 13th axis
            if (fetch_ptr < 4'd12) begin
                fetch_ptr <= fetch_ptr + 4'd1;
            end

            // 2. Compute/Commit Latency: The Commit Pointer follows 2 cycles behind
            if (delay_cnt < 4'd2) begin
                delay_cnt <= delay_cnt + 4'd1;
                write_en  <= 1'b0;
            end else begin
                // Commit Stage: Start committing after the 2-cycle compute window
                if (commit_ptr == 4'hF) begin
                    commit_ptr <= 4'h0;
                    write_en   <= 1'b1;
                end else if (commit_ptr < 4'd12) begin
                    commit_ptr <= commit_ptr + 4'd1;
                    write_en   <= 1'b1;
                end else begin
                    // Bloom Complete: All 13 axes committed
                    processing <= 1'b0;
                    write_en   <= 1'b0;
                end
            end
        end else begin
            write_en   <= 1'b0;
        end
    end

endmodule
