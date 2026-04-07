// HAL_HDMI_TMDS.v — TMDS encoder for one DVI/HDMI channel
// Implements DVI 1.0 TMDS encoding: transition minimisation + DC balance.
// Data region: encodes 8-bit pixel data → 10-bit DC-balanced symbol.
// Control region: outputs fixed TMDS control words.
// No floating point. Pure registered pipeline.
// CC0 1.0 Universal.

module HAL_HDMI_TMDS (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  data,
    input  wire [1:0]  ctrl,
    input  wire        active,
    output reg  [9:0]  tmds_out
);

    // Count ones in 8-bit data
    wire [3:0] n1d = data[0]+data[1]+data[2]+data[3]+
                     data[4]+data[5]+data[6]+data[7];

    // Phase 1: build q_m via XOR (q_m[8]=1) or XNOR (q_m[8]=0)
    wire xnor_mode = (n1d > 4'd4) || (n1d == 4'd4 && !data[0]);

    wire [7:0] qm;
    assign qm[0] = data[0];
    assign qm[1] = xnor_mode ? ~(qm[0] ^ data[1]) : (qm[0] ^ data[1]);
    assign qm[2] = xnor_mode ? ~(qm[1] ^ data[2]) : (qm[1] ^ data[2]);
    assign qm[3] = xnor_mode ? ~(qm[2] ^ data[3]) : (qm[2] ^ data[3]);
    assign qm[4] = xnor_mode ? ~(qm[3] ^ data[4]) : (qm[3] ^ data[4]);
    assign qm[5] = xnor_mode ? ~(qm[4] ^ data[5]) : (qm[4] ^ data[5]);
    assign qm[6] = xnor_mode ? ~(qm[5] ^ data[6]) : (qm[5] ^ data[6]);
    assign qm[7] = xnor_mode ? ~(qm[6] ^ data[7]) : (qm[6] ^ data[7]);

    wire [8:0] q_m = {~xnor_mode, qm}; // q_m[8]=1 → XOR mode

    // Count ones and zeros in q_m[7:0]
    wire [3:0] n1q = qm[0]+qm[1]+qm[2]+qm[3]+qm[4]+qm[5]+qm[6]+qm[7];
    wire [3:0] n0q = 4'd8 - n1q;

    // Running DC balance accumulator (signed 5-bit)
    reg signed [4:0] cnt;

    wire equal     = (n1q == n0q);
    wire cnt_zero  = (cnt == 5'sd0);
    wire cnt_pos   = !cnt[4] && !cnt_zero;
    wire cnt_neg   = cnt[4];
    wire n1_gt_n0  = (n1q > n0q);

    // DC balance deltas
    wire signed [4:0] d_pos = $signed({1'b0, n1q}) - $signed({1'b0, n0q}); // N1-N0
    wire signed [4:0] d_neg = $signed({1'b0, n0q}) - $signed({1'b0, n1q}); // N0-N1

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cnt      <= 5'sd0;
            tmds_out <= 10'd0;
        end else if (!active) begin
            // Control period — fixed TMDS guard band / control words
            cnt <= 5'sd0;
            case (ctrl)
                2'b00: tmds_out <= 10'b1101010100;
                2'b01: tmds_out <= 10'b0010101011;
                2'b10: tmds_out <= 10'b0101010100;
                2'b11: tmds_out <= 10'b1010101011;
            endcase
        end else if (cnt_zero || equal) begin
            // No DC bias yet: choose inversion based on q_m[8]
            if (!q_m[8]) begin
                tmds_out <= {1'b1, q_m[8], ~q_m[7:0]};
                cnt      <= cnt + d_neg;
            end else begin
                tmds_out <= {1'b0, q_m[8], q_m[7:0]};
                cnt      <= cnt + d_pos;
            end
        end else if ((cnt_pos && n1_gt_n0) || (cnt_neg && !n1_gt_n0 && !equal)) begin
            // Invert to reduce bias
            tmds_out <= {1'b1, q_m[8], ~q_m[7:0]};
            cnt      <= cnt + (q_m[8] ? 5'sd2 : 5'sd0) + d_neg;
        end else begin
            // No inversion needed
            tmds_out <= {1'b0, q_m[8], q_m[7:0]};
            cnt      <= cnt - (q_m[8] ? 5'sd0 : 5'sd2) + d_pos;
        end
    end

endmodule
