// Simple LAU: minimal sound engine using precomputed vnorm lookup
// No per-material properties; maps 16-bit PCM -> 10-bit index -> vnorm ROM (Q16.16)
module simple_lau(
    input  wire         clk,
    input  wire         rst_n,
    input  wire         start,
    input  wire signed [15:0] pcm_in,
    output reg  signed [31:0] vout_q16,
    output reg          valid_out
);

    // 1024-entry normalized V ROM (use carbon file as default)
    reg signed [31:0] vnorm [0:1023];
    initial begin
        // best-effort read; if missing, values are zero
        $readmemh("hardware/common/rtl/gpu/vnorm_carbon.mem", vnorm);
    end

    reg [1:0] state;
    reg signed [9:0] pcm_top_s;
    reg [9:0] idx;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            vout_q16 <= 32'sd0;
            valid_out <= 1'b0;
            state <= 2'b00;
            pcm_top_s <= 0;
            idx <= 0;
        end else begin
            valid_out <= 1'b0;
            case (state)
                2'b00: begin
                    if (start) begin
                        // coarse mapping: take top 10 bits of PCM (signed arithmetic shift)
                        pcm_top_s <= pcm_in >>> 6; // signed divide by 64 -> -512..+511
                        idx <= (pcm_in >>> 6) + 10'd512; // map to 0..1023
                        state <= 2'b01;
                    end
                end
                2'b01: begin
                    // one-cycle ROM read (synth-friendly)
                    vout_q16 <= vnorm[idx];
                    valid_out <= 1'b1;
                    state <= 2'b00;
                end
            endcase
        end
    end

endmodule
