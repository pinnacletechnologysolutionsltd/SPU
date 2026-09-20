// spu_scene_loader.v -- fixed two-bank, 504-bit scene loader.
// Byte i maps to scene[8*i +: 8]. A complete inactive scene becomes visible
// only on a later qualified activation while commit_pending is asserted.
// CC0 1.0 Universal.

module spu_scene_loader (
    input  wire         clk,
    input  wire         rst_n,
    input  wire [7:0]   rx_byte,
    input  wire         rx_valid,
    input  wire         activate_raw_bank,
    output wire [503:0] active_scene,
    output wire [503:0] candidate_scene,
    output reg          commit_pending
`ifdef GPU_T1D_DIAG
    , output wire       diag_start_accepted,
    output wire         diag_payload_accepted,
    output wire [5:0]   diag_payload_count,
    output wire         diag_receiving,
    output wire         diag_active_bank
`endif
);

    localparam [7:0] START_BYTE = 8'hA5;

    reg [503:0] scene_bank0;
    reg [503:0] scene_bank1;
    reg         active_bank;
    reg         receiving;
    reg [5:0]   payload_count;

    assign active_scene = active_bank ? scene_bank1 : scene_bank0;
    assign candidate_scene = active_bank ? scene_bank0 : scene_bank1;

`ifdef GPU_T1D_DIAG
    assign diag_start_accepted = rx_valid && !receiving && !commit_pending &&
        (rx_byte == START_BYTE);
    assign diag_payload_accepted = rx_valid && receiving && !commit_pending;
    assign diag_payload_count = payload_count;
    assign diag_receiving = receiving;
    assign diag_active_bank = active_bank;
`endif

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            scene_bank0    <= 504'b0;
            scene_bank1    <= 504'b0;
            active_bank    <= 1'b0;
            receiving      <= 1'b0;
            payload_count  <= 6'd0;
            commit_pending <= 1'b0;
        end else if (commit_pending) begin
            // All bytes are ignored while the completed inactive bank waits.
            if (activate_raw_bank) begin
                active_bank    <= ~active_bank;
                commit_pending <= 1'b0;
            end
        end else if (receiving) begin
            if (rx_valid) begin
                if (active_bank)
                    scene_bank0[payload_count * 8 +: 8] <= rx_byte;
                else
                    scene_bank1[payload_count * 8 +: 8] <= rx_byte;

                if (payload_count == 6'd62) begin
                    payload_count  <= 6'd0;
                    receiving      <= 1'b0;
                    commit_pending <= 1'b1;
                end else begin
                    payload_count <= payload_count + 6'd1;
                end
            end
        end else if (rx_valid && rx_byte == START_BYTE) begin
            receiving     <= 1'b1;
            payload_count <= 6'd0;
        end
    end

endmodule
