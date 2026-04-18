// spu_artery_tx.v (v1.1 - Whisper Link Streamer)
// Objective: Parallel-to-Serial Manifold "Exhalation" for RP2040 telemetry.
// Standard: Fibonacci-Gated Transmission (Pulse 21 Trigger).
// Manifold: 13 Axes x 64-bit = 104 bytes.

module spu_artery_tx (
    input  wire         clk,          // System Clock
    input  wire         phi_21,       // Commit Pulse (Fibonacci Sync)
    input  wire [3:0]   axis_ptr,     // Current TDM Axis (0-12)
    input  wire [63:0]  axis_data,    // Current 8-byte Axis Chord
    output reg          tx_out,       // Serial Link to RP2040
    output reg          tx_active     // High during 104-byte frame transfer
);

    reg [5:0]  bit_cnt;   // Counts 0-63 bits per axis
    reg [63:0] shift_reg;
    reg [3:0]  axis_count;
    
    // Trigger transmission at the end of the 13th axis commit
    wire start_frame;
    assign start_frame = (axis_ptr == 4'd12 && phi_21);

    always @(posedge clk) begin
        if (start_frame) begin
            shift_reg  <= axis_data;
            bit_cnt    <= 6'd0;
            axis_count <= 4'd0;
            tx_active  <= 1'b1;
            tx_out     <= axis_data[63];
        end else if (tx_active) begin
            // Shift out bit-by-bit at system clock speed
            if (bit_cnt == 6'd63) begin
                if (axis_count == 4'd12) begin
                    tx_active <= 1'b0;
                    tx_out    <= 1'b0;
                end else begin
                    // This implementation expects the manifold_reg to be stable
                    // or for this module to have its own 832-bit buffer.
                    // For simplicity, we assume the caller provides the next axis_data.
                    // In a more robust version, we'd latch the full 832 bits.
                    axis_count <= axis_count + 4'd1;
                    bit_cnt    <= 6'd0;
                    // Note: This requires the parent to update axis_data as we shift.
                    // We'll adjust the top-level to handle this.
                end
            end else begin
                bit_cnt <= bit_cnt + 6'd1;
                tx_out  <= shift_reg[62];
                shift_reg <= {shift_reg[62:0], 1'b0};
            end
        end else begin
            tx_out <= 1'b0;
        end
    end
endmodule
