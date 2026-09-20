// spu_t1d_diag_record.v -- retained T1d repeatability diagnostic records.
//
// The record producer observes the existing loader events but does not alter
// the receive, loader, commit, or renderer paths. It emits the fixed 16-byte
// record specified by GPU-T1D-REPEATABILITY-DIAGNOSTIC-2026-09-20.
// CC0 1.0 Universal.

module spu_t1d_diag_record (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         ready_state,
    input  wire         start_accepted,
    input  wire         payload_accepted,
    input  wire [7:0]   payload_byte,
    input  wire         frame_start,
    input  wire         frame_error,
    input  wire         loader_commit_pending,
    input  wire         scene_activate,
    input  wire         active_bank,
    input  wire         record_ready,
    output reg          record_valid,
    output reg  [127:0] record_data
);

    localparam integer RX_IDLE_LIMIT = 32 * 217;

    reg         ready_emitted;
    reg         txn_active;
    reg         payload_complete;
    reg [7:0]   txn_sequence;
    reg [7:0]   accepted_count;
    reg [15:0]  payload_crc;
    reg [15:0]  completed_crc;
    reg [15:0]  frame_wait;
    reg [15:0]  idle_count;
    reg         commit_seen;

    wire record_slot_free = !record_valid || record_ready;

    function [15:0] crc16_byte;
        input [15:0] crc_in;
        input [7:0]  data_byte;
        integer bit_index;
        reg [15:0] c;
        begin
            c = crc_in ^ {data_byte, 8'd0};
            for (bit_index = 0; bit_index < 8; bit_index = bit_index + 1) begin
                if (c[15])
                    c = {c[14:0], 1'b0} ^ 16'h1021;
                else
                    c = {c[14:0], 1'b0};
            end
            crc16_byte = c;
        end
    endfunction

    function [7:0] crc8_record;
        input [111:0] record_prefix;
        integer byte_index;
        integer bit_index;
        reg [7:0] c;
        begin
            c = 8'h00;
            for (byte_index = 0; byte_index < 14; byte_index = byte_index + 1) begin
                c = c ^ record_prefix[(byte_index * 8) +: 8];
                for (bit_index = 0; bit_index < 8; bit_index = bit_index + 1) begin
                    if (c[7])
                        c = {c[6:0], 1'b0} ^ 8'h07;
                    else
                        c = {c[6:0], 1'b0};
                end
            end
            crc8_record = c;
        end
    endfunction

    function [127:0] make_record;
        input [7:0]  kind;
        input [7:0]  seq_value;
        input [7:0]  flags;
        input [7:0]  count;
        input [15:0] crc;
        input        bank;
        input [7:0]  reason;
        input [15:0] wait_count;
        input        ready_byte;
        reg [127:0] r;
        begin
            r = 128'd0;
            r[7:0]    = 8'hD7;
            r[15:8]   = 8'h01;
            r[23:16]  = kind;
            r[31:24]  = seq_value;
            r[39:32]  = flags;
            r[47:40]  = count;
            r[55:48]  = crc[7:0];
            r[63:56]  = crc[15:8];
            r[71:64]  = {7'd0, bank};
            r[79:72]  = reason;
            r[87:80]  = wait_count[7:0];
            r[95:88]  = wait_count[15:8];
            r[103:96] = {7'd0, ready_byte};
            r[111:104] = 8'h00;
            r[119:112] = crc8_record(r[111:0]);
            r[127:120] = 8'h7E;
            make_record = r;
        end
    endfunction

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            ready_emitted    <= 1'b0;
            txn_active       <= 1'b0;
            payload_complete <= 1'b0;
            txn_sequence     <= 8'd0;
            accepted_count   <= 8'd0;
            payload_crc      <= 16'hFFFF;
            completed_crc    <= 16'h0000;
            frame_wait       <= 16'd0;
            idle_count       <= 16'd0;
            commit_seen      <= 1'b0;
            record_valid     <= 1'b0;
            record_data      <= 128'd0;
        end else begin
            if (record_valid && record_ready)
                record_valid <= 1'b0;

            if (start_accepted && !txn_active && !payload_complete) begin
                txn_sequence   <= txn_sequence + 8'd1;
                txn_active     <= 1'b1;
                accepted_count <= 8'd0;
                payload_crc    <= 16'hFFFF;
                completed_crc  <= 16'h0000;
                frame_wait     <= 16'd0;
                idle_count     <= 16'd0;
                commit_seen    <= 1'b0;
            end else if (payload_accepted && txn_active) begin
                payload_crc  <= crc16_byte(payload_crc, payload_byte);
                accepted_count <= accepted_count + 8'd1;
                idle_count   <= 16'd0;
                if (accepted_count == 8'd62) begin
                    completed_crc    <= crc16_byte(payload_crc, payload_byte);
                    payload_complete <= 1'b1;
                    txn_active       <= 1'b0;
                    frame_wait       <= 16'd0;
                end
            end else if (txn_active) begin
                if (idle_count == RX_IDLE_LIMIT - 1) begin
                    txn_active <= 1'b0;
                    idle_count <= 16'd0;
                    if (record_slot_free) begin
                        record_data  <= make_record(8'h02, txn_sequence,
                                                     8'h03, accepted_count,
                                                     payload_crc, active_bank,
                                                     8'h03, 16'd0, ready_state);
                        record_valid <= 1'b1;
                    end
                end else begin
                    idle_count <= idle_count + 16'd1;
                end
            end

            if (loader_commit_pending)
                commit_seen <= 1'b1;

            if (record_slot_free) begin
                if (!ready_emitted && ready_state) begin
                    record_data   <= make_record(8'h01, 8'h00, 8'h01, 8'h00,
                                                  16'h0000, 1'b0, 8'h01,
                                                  16'h0000, 1'b1);
                    record_valid  <= 1'b1;
                    ready_emitted <= 1'b1;
                end else if (frame_error && txn_active) begin
                    record_data  <= make_record(8'h02, txn_sequence,
                                                 8'h07, accepted_count,
                                                 payload_crc, active_bank,
                                                 8'h04, 16'd0, ready_state);
                    record_valid <= 1'b1;
                    txn_active   <= 1'b0;
                end else if (payload_complete && scene_activate) begin
                    record_data  <= make_record(8'h02, txn_sequence,
                                                 8'h7B, 8'd63, completed_crc,
                                                 ~active_bank, 8'h02,
                                                 frame_wait, ready_state);
                    record_valid      <= 1'b1;
                    payload_complete  <= 1'b0;
                    commit_seen       <= 1'b0;
                end else if (payload_complete && frame_start &&
                             (frame_wait >= 16'd1)) begin
                    record_data  <= make_record(8'h02, txn_sequence,
                                                 8'h5B, 8'd63, completed_crc,
                                                 active_bank, 8'h05,
                                                 frame_wait + 16'd1, ready_state);
                    record_valid     <= 1'b1;
                    payload_complete <= 1'b0;
                    commit_seen      <= 1'b0;
                end
            end

            if (payload_complete && frame_start && !scene_activate &&
                (frame_wait < 16'd1))
                frame_wait <= frame_wait + 16'd1;
        end
    end

endmodule
