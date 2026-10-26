// spu_whisper_v1_listener.v — Whisper v1 coherence-plane frame listener
//
// Receives 18-byte ASCII frames "W1 ii ff dd ss xx\n" over UART RX.
// Validates frame format, XOR checksum (bytes 0..14), and tracks a
// 3-consecutive-miss incoherence timeout.
//
// Per docs/WHISPER_V1_SPEC.md §4.  Never replies on the whisper plane.
module spu_whisper_v1_listener #(
    parameter CLK_HZ        = 12000000,
    parameter BAUD          = 115200,
    parameter PERIOD_CYCLES = CLK_HZ / 1   // 1 Hz default
) (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       rx,
    output wire [3:0] node_id,
    output wire [2:0] flags,
    output wire [7:0] dissonance,
    // Legacy port name: decoded `ss` application-status byte, not sequence.
    output wire [7:0] seq,
    output reg        frame_valid,
    output reg        frame_err,
    output reg        incoherent
);
    localparam FRAME_LEN      = 18;
    localparam TIMEOUT_PERIODS = 3;

    // ── UART RX ──────────────────────────────────────────────────────
    wire [7:0] rx_data;
    wire       rx_valid;
    wire       rx_frame_err;

    spu_uart_rx #(.CLK_HZ(CLK_HZ), .BAUD(BAUD)) u_uart (
        .clk(clk), .rst_n(rst_n),
        .rx(rx),
        .data(rx_data), .valid(rx_valid), .frame_err(rx_frame_err)
    );

    // ── Frame assembly (flat registers, no array) ────────────────────
    reg [4:0]  byte_cnt;
    reg        collecting;
    reg        frame_done;
    reg [7:0]  b0,  b1,  b2,  b3,  b4,  b5,  b6,  b7,  b8;
    reg [7:0]  b9,  b10, b11, b12, b13, b14, b15, b16, b17;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            byte_cnt   <= 5'd0;
            collecting <= 1'b0;
            frame_done <= 1'b0;
        end else begin
            frame_done <= 1'b0;
            if (rx_frame_err && collecting) begin
                byte_cnt   <= 5'd0;
                collecting <= 1'b0;
            end else if (rx_valid) begin
                if (!collecting) begin
                    if (rx_data == 8'h57) begin
                        b0         <= rx_data;
                        byte_cnt   <= 5'd1;
                        collecting <= 1'b1;
                    end
                end else begin
                    case (byte_cnt)
                        5'd1:  b1  <= rx_data;
                        5'd2:  b2  <= rx_data;
                        5'd3:  b3  <= rx_data;
                        5'd4:  b4  <= rx_data;
                        5'd5:  b5  <= rx_data;
                        5'd6:  b6  <= rx_data;
                        5'd7:  b7  <= rx_data;
                        5'd8:  b8  <= rx_data;
                        5'd9:  b9  <= rx_data;
                        5'd10: b10 <= rx_data;
                        5'd11: b11 <= rx_data;
                        5'd12: b12 <= rx_data;
                        5'd13: b13 <= rx_data;
                        5'd14: b14 <= rx_data;
                        5'd15: b15 <= rx_data;
                        5'd16: b16 <= rx_data;
                        5'd17: b17 <= rx_data;
                    endcase
                    if (byte_cnt == FRAME_LEN - 1) begin
                        byte_cnt   <= 5'd0;
                        collecting <= 1'b0;
                        frame_done <= 1'b1;
                    end else begin
                        byte_cnt <= byte_cnt + 5'd1;
                    end
                end
            end
        end
    end

    // ── hex char → nibble ────────────────────────────────────────────
    function [3:0] hex_to_nibble;
        input [7:0] ch;
        begin
            if (ch >= 8'h30 && ch <= 8'h39)
                hex_to_nibble = ch[3:0];
            else if (ch >= 8'h41 && ch <= 8'h46)
                hex_to_nibble = ch[3:0] + 4'd9;
            else if (ch >= 8'h61 && ch <= 8'h66)
                hex_to_nibble = ch[3:0] + 4'd9;
            else
                hex_to_nibble = 4'd0;
        end
    endfunction

    // ── Frame validation ─────────────────────────────────────────────
    wire format_ok = (b0  == 8'h57)
                  && (b1  == 8'h31)
                  && (b2  == 8'h20)
                  && (b5  == 8'h20)
                  && (b8  == 8'h20)
                  && (b11 == 8'h20)
                  && (b14 == 8'h20)
                  && (b17 == 8'h0A);

    wire [7:0] checksum_computed = b0 ^ b1 ^ b2 ^ b3 ^ b4 ^ b5
                                 ^ b6 ^ b7 ^ b8 ^ b9 ^ b10 ^ b11
                                 ^ b12 ^ b13 ^ b14;

    wire [7:0] checksum_received;
    assign checksum_received[7:4] = hex_to_nibble(b15);
    assign checksum_received[3:0] = hex_to_nibble(b16);

    wire xor_ok = (checksum_computed == checksum_received);
    wire frame_ok = format_ok && xor_ok;

    // ── Decode fields ────────────────────────────────────────────────
    wire [3:0] node_hi = hex_to_nibble(b3);
    wire [3:0] node_lo = hex_to_nibble(b4);
    assign node_id = {node_hi, node_lo};

    wire [3:0] f_hi = hex_to_nibble(b6);   // {3'b0, relayed}
    wire [3:0] f_lo = hex_to_nibble(b7);   // {henosis, snap_locked, 2'b00}
    wire [7:0] flags_byte = {f_hi, f_lo};  // {3'b0, relayed, henosis, snap_locked, 2'b00}
    assign flags = flags_byte[2:0];  // {relayed, henosis, snap_locked}

    wire [3:0] dd_hi = hex_to_nibble(b9);
    wire [3:0] dd_lo = hex_to_nibble(b10);
    assign dissonance = {dd_hi, dd_lo};

    wire [3:0] ss_hi = hex_to_nibble(b12);
    wire [3:0] ss_lo = hex_to_nibble(b13);
    assign seq = {ss_hi, ss_lo};

    // ── Valid / error pulses ─────────────────────────────────────────
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            frame_valid <= 1'b0;
            frame_err   <= 1'b0;
        end else begin
            frame_valid <= 1'b0;
            frame_err   <= 1'b0;
            if (frame_done) begin
                if (frame_ok)
                    frame_valid <= 1'b1;
                else
                    frame_err <= 1'b1;
                if (frame_ok)
                    frame_valid <= 1'b1;
                else
                    frame_err <= 1'b1;
            end
        end
    end

    // ── 3-miss incoherence timeout ───────────────────────────────────
    reg [31:0] timeout_cnt;
    reg [1:0]  miss_cnt;
    reg        last_tick;

    wire period_tick = (timeout_cnt == PERIOD_CYCLES - 1);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            timeout_cnt <= 32'd0;
            miss_cnt    <= 2'd0;
            incoherent  <= 1'b0;
            last_tick   <= 1'b0;
        end else begin
            if (timeout_cnt == PERIOD_CYCLES - 1)
                timeout_cnt <= 32'd0;
            else
                timeout_cnt <= timeout_cnt + 32'd1;

            last_tick <= period_tick;

            if (frame_valid) begin
                miss_cnt   <= 2'd0;
                incoherent <= 1'b0;
            end else if (period_tick && !last_tick) begin
                if (miss_cnt < TIMEOUT_PERIODS)
                    miss_cnt <= miss_cnt + 2'd1;
                if (miss_cnt >= (TIMEOUT_PERIODS - 1))
                    incoherent <= 1'b1;
            end
        end
    end

endmodule
