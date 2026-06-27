// spu_spi_slave.v (v1.0)
// SPU Sovereign SPI Protocol v1.0 — FPGA-side slave receiver.
//
// Answers RP2350 master polls at up to 2 MHz, SPI Mode 0 (CPOL=0, CPHA=0).
//
// Commands:
//   CMD 0xA0 → 32-byte manifold burst:
//              4 axes × 8 bytes = [{P_hi,P_lo,0,0,Q_hi,Q_lo,0,0},...]
//              P,Q = signed int16, Q12 big-endian. Latched at CS assertion.
//   CMD 0xAC → 4-byte status:
//              [laminar_hi, laminar_lo, flags, rplu_mode]
//              flags bit0 = satellite_snaps[0] (snap_lock)
//              flags bit1 = is_janus_point
//   CMD 0xAD → 9-byte scale table and overflow flags.
//   CMD 0xAE → read last QR commit: [valid, lane, A/B/C/D big-endian].
//   CMD 0xAF → read sticky HEX result: [valid, q_hi, q_lo, r_hi, r_lo].
//   CMD 0xB0 → 64-byte Sentinel telemetry burst.
//   CMD 0xB1 → write one 64-bit SPU instruction/chord, big-endian.
//   CMD 0xA5 → write two 64-bit RPLU config chords: HEADER, DATA.
//
// Manifold layout (manifold_state[831:0], 26 × 32-bit RationalSurd):
//   Axis N: manifold_state[32*N+31:32*N+16] = P (rational)
//           manifold_state[32*N+15:32*N]    = Q (surd)

module spu_spi_slave (
    input  wire        clk,            // System clock (24 MHz)
    input  wire        rst_n,

    // SPI bus (from RP2350 master)
    input  wire        spi_cs_n,       // Chip select, active low
    input  wire        spi_sck,        // SPI clock
    input  wire        spi_mosi,       // MOSI
    output reg         spi_miso,       // MISO

    // Manifold snapshot inputs (from spu_system)
    input  wire [831:0] manifold_state,
    input  wire [3:0]   satellite_snaps,
    input  wire         is_janus_point,
    input  wire [15:0]  dissonance,     // manifold tension metric

    // Scale snapshot inputs (from spu13_core)
    input  wire [51:0]  scale_table,
    input  wire [12:0]  scale_overflow,

    // QR/HEX telemetry from spu13_core.
    input  wire         qr_commit_valid,
    input  wire [3:0]   qr_commit_lane,
    input  wire [63:0]  qr_commit_A,
    input  wire [63:0]  qr_commit_B,
    input  wire [63:0]  qr_commit_C,
    input  wire [63:0]  qr_commit_D,
    input  wire         hex_valid,
    input  wire [15:0]  hex_q,
    input  wire [15:0]  hex_r,

    // RPLU runtime comparator inputs (fast domain)
    input  wire signed [2:0] rplu_ratio_res,
    input  wire             rplu_ratio_valid,

    // RPLU runtime config outputs (pulsed on DATA chord)
    // HEADER layout: [63:56]=0xA5, [55:48]=sel, [47:44]=material, [43:34]=addr.
    output reg         rplu_cfg_wr_en,
    output reg  [2:0]  rplu_cfg_sel,
    output reg  [7:0]  rplu_cfg_material,
    output reg  [9:0]  rplu_cfg_addr,
    output reg [63:0]  rplu_cfg_data,

    // Optional instruction ingress (CMD 0xB1). Unconnected users keep the
    // telemetry/RPLU behavior unchanged.
    output reg         inst_valid,
    output reg [63:0]  inst_word,

    // Flow control & Status
    input  wire        fifo_full,
    input  wire [15:0] laminar_index,
    input  wire        turbulence,
    input  wire        rplu_mode,   // Current RPLU bank: 0=Smooth 1=Turbulent

    // Sentinel Telemetry (piranha domain snapshot)
    input  wire [511:0] sentinel_telemetry
);

    // --- 2-stage synchronisers for async SPI signals ---
    reg [2:0] sck_r, cs_r;
    reg [1:0] mosi_r;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sck_r  <= 3'b0;
            cs_r   <= 3'b111;
            mosi_r <= 2'b0;
        end else begin
            sck_r  <= {sck_r[1:0],  spi_sck};
            cs_r   <= {cs_r[1:0],   spi_cs_n};
            mosi_r <= {mosi_r[0],   spi_mosi};
        end
    end

    wire sck_rise;
    assign sck_rise = (sck_r[2:1] == 2'b01);
    wire sck_fall;
    assign sck_fall = (sck_r[2:1] == 2'b10);
    wire cs_active;
    assign cs_active = !cs_r[1];
    wire cs_fall   = (cs_r[2:1] == 2'b10);  // CS asserted (falling edge)
    wire mosi_d;
    assign mosi_d = mosi_r[1];

    // --- Manifold snapshot (latched at CS assertion) ---
    reg [15:0] p_axis [0:3];
    reg [15:0] q_axis [0:3];
    reg [15:0] dissonance_lat;
    reg [3:0]  snaps_lat;
    reg        janus_lat;
    reg [51:0] scale_tab_lat;
    reg [12:0] scale_overflow_lat;
    // Latched RPLU comparator results (sticky until reported)
    reg signed [2:0] ratio_lat;
    reg              ratio_valid_lat;
    reg [511:0]      sentinel_lat;

    integer ax;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            dissonance_lat <= 16'h0;
            snaps_lat      <= 4'h0;
            janus_lat      <= 1'b0;
            scale_tab_lat  <= 52'h0;
            scale_overflow_lat <= 13'h0;
            sentinel_lat   <= 512'h0;
            for (ax = 0; ax < 4; ax = ax + 1) begin
                p_axis[ax] <= 16'h0;
                q_axis[ax] <= 16'h0;
            end
        end else if (cs_fall) begin
            // Latch entire snapshot at the moment RP2350 asserts CS
            p_axis[0] <= manifold_state[31:16];
            q_axis[0] <= manifold_state[15:0];
            p_axis[1] <= manifold_state[63:48];
            q_axis[1] <= manifold_state[47:32];
            p_axis[2] <= manifold_state[95:80];
            q_axis[2] <= manifold_state[79:64];
            p_axis[3] <= manifold_state[127:112];
            q_axis[3] <= manifold_state[111:96];
            dissonance_lat <= dissonance;
            snaps_lat      <= satellite_snaps;
            janus_lat      <= is_janus_point;
            scale_tab_lat  <= scale_table;
            scale_overflow_lat <= scale_overflow;
            sentinel_lat   <= sentinel_telemetry;
        end
    end

    // --- Response buffer (64 bytes max for Sentinel Burst) ---
    // Filled after command byte is received.
    reg [7:0] resp_buf [0:63];
    reg [6:0] resp_len;   // 0–64; must be 7-bit so 64 doesn't truncate
 
    // --- State machine ---
    localparam S_IDLE      = 3'd0;  // waiting for CS
    localparam S_CMD       = 3'd1;  // receiving 8-bit command
    localparam S_FILL      = 3'd2;  // one cycle to load resp_buf
    localparam S_RESP      = 3'd3;  // clocking out response
    localparam S_RECV_HDR  = 3'd4;  // receive 64-bit HEADER
    localparam S_RECV_DATA = 3'd5;  // receive 64-bit DATA
    localparam S_RECV_INST = 3'd6;  // receive 64-bit instruction chord
 
    reg [2:0]  state;
    reg [2:0]  bit_cnt;    // bits received in CMD phase
    reg [7:0]  cmd_byte;
    reg [6:0]  byte_idx;   // current response byte index (0–63)
    reg [2:0]  resp_bit;   // bit within current response byte
    reg [7:0]  shift_out;  // byte being clocked out

    // For multi-byte receive (HEADER/DATA)
    reg [5:0]  recv_bits;  // 0..63
    reg [63:0] hdr_shift;
    reg [63:0] data_shift;
    reg        qr_valid_lat;
    reg [3:0]  qr_lane_lat;
    reg [63:0] qr_A_lat, qr_B_lat, qr_C_lat, qr_D_lat;
    reg        hex_valid_lat;
    reg [15:0] hex_q_lat;
    reg [15:0] hex_r_lat;

    integer b, k;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state     <= S_IDLE;
            bit_cnt   <= 3'd0;
            cmd_byte  <= 8'h0;
            byte_idx  <= 6'd0;
            resp_bit  <= 3'd7;
            shift_out <= 8'h0;
            resp_len  <= 6'd0;
            spi_miso  <= 1'b0;

            rplu_cfg_wr_en   <= 1'b0;
            rplu_cfg_sel     <= 3'd0;
            rplu_cfg_material<= 8'd0;
            rplu_cfg_addr    <= 10'd0;
            rplu_cfg_data    <= 64'd0;
            inst_valid       <= 1'b0;
            inst_word        <= 64'd0;

            hdr_shift <= 64'd0;
            data_shift<= 64'd0;
            recv_bits <= 6'd0;
            ratio_lat <= 3'sd0;
            ratio_valid_lat <= 1'b0;
            hex_valid_lat <= 1'b0;
            hex_q_lat <= 16'd0;
            hex_r_lat <= 16'd0;
            qr_valid_lat <= 1'b0;
            qr_lane_lat <= 4'd0;
            qr_A_lat <= 64'd0;
            qr_B_lat <= 64'd0;
            qr_C_lat <= 64'd0;
            qr_D_lat <= 64'd0;

            for (b = 0; b < 64; b = b + 1) resp_buf[b] <= 8'h0;
        end else begin
            // default: clear the one-cycle strobe
            rplu_cfg_wr_en <= 1'b0;
            inst_valid <= 1'b0;

            // Sample incoming RPLU comparator pulses (sticky latch)
            if (rplu_ratio_valid) begin
                ratio_lat <= rplu_ratio_res;
                ratio_valid_lat <= 1'b1;
            end
            if (hex_valid) begin
                hex_valid_lat <= 1'b1;
                hex_q_lat <= hex_q;
                hex_r_lat <= hex_r;
            end
            if (qr_commit_valid) begin
                qr_valid_lat <= 1'b1;
                qr_lane_lat <= qr_commit_lane;
                qr_A_lat <= qr_commit_A;
                qr_B_lat <= qr_commit_B;
                qr_C_lat <= qr_commit_C;
                qr_D_lat <= qr_commit_D;
            end

            case (state)

                S_IDLE: begin
                    spi_miso <= 1'b0;
                    if (cs_active) begin
                        bit_cnt  <= 3'd0;
                        cmd_byte <= 8'h0;
                        state    <= S_CMD;
                    end
                end

                S_CMD: begin
                    if (!cs_active) begin
                        state <= S_IDLE;  // CS deasserted early
                    end else if (sck_rise) begin
                        cmd_byte <= {cmd_byte[6:0], mosi_d};
                        if (bit_cnt == 3'd7) begin
                            state   <= S_FILL;
                            bit_cnt <= 3'd0;
                        end else begin
                            bit_cnt <= bit_cnt + 3'd1;
                        end
                    end
                end

                S_FILL: begin
                    // Wait for the trailing CMD SCK fall before loading resp_buf.
                    // The last CMD clock's fall must be consumed here so S_RESP
                    // never sees it as a response clock edge.
                    if (sck_fall) begin
                        // Build response buffer based on latched cmd_byte
                        if (cmd_byte == 8'hA0) begin
                            // 4 axes × 8 bytes = 32 bytes
                            resp_buf[0]  <= p_axis[0][15:8];
                            resp_buf[1]  <= p_axis[0][7:0];
                            resp_buf[2]  <= 8'h00;
                            resp_buf[3]  <= 8'h00;
                            resp_buf[4]  <= q_axis[0][15:8];
                            resp_buf[5]  <= q_axis[0][7:0];
                            resp_buf[6]  <= 8'h00;
                            resp_buf[7]  <= 8'h00;
                            resp_buf[8]  <= p_axis[1][15:8];
                            resp_buf[9]  <= p_axis[1][7:0];
                            resp_buf[10] <= 8'h00;
                            resp_buf[11] <= 8'h00;
                            resp_buf[12] <= q_axis[1][15:8];
                            resp_buf[13] <= q_axis[1][7:0];
                            resp_buf[14] <= 8'h00;
                            resp_buf[15] <= 8'h00;
                            resp_buf[16] <= p_axis[2][15:8];
                            resp_buf[17] <= p_axis[2][7:0];
                            resp_buf[18] <= 8'h00;
                            resp_buf[19] <= 8'h00;
                            resp_buf[20] <= q_axis[2][15:8];
                            resp_buf[21] <= q_axis[2][7:0];
                            resp_buf[22] <= 8'h00;
                            resp_buf[23] <= 8'h00;
                            resp_buf[24] <= p_axis[3][15:8];
                            resp_buf[25] <= p_axis[3][7:0];
                            resp_buf[26] <= 8'h00;
                            resp_buf[27] <= 8'h00;
                            resp_buf[28] <= q_axis[3][15:8];
                            resp_buf[29] <= q_axis[3][7:0];
                            resp_buf[30] <= 8'h00;
                            resp_buf[31] <= 8'h00;
                            resp_len     <= 6'd32;
                            // Pre-load first byte MSB onto MISO before first SCK fall
                            shift_out <= p_axis[0][15:8];
                            byte_idx  <= 6'd0;
                            resp_bit  <= 3'd7;
                            spi_miso  <= p_axis[0][15];
                            state     <= S_RESP;

                        end else if (cmd_byte == 8'hAC) begin
                            // 4-byte status:
                            //   [0..1] laminar_index (big-endian)
                            //   [2]    flags: {ratio_lat[2:0], ratio_valid, fifo_full, turbulence, janus, snap}
                            //   [3]    rplu_mode[0] — current RPLU bank (0=Smooth, 1=Turbulent)
                            resp_buf[0] <= laminar_index[15:8];
                            resp_buf[1] <= laminar_index[7:0];
                            resp_buf[2] <= {ratio_lat[2:0], ratio_valid_lat, fifo_full, turbulence, janus_lat, snaps_lat[0]};
                            resp_buf[3] <= {7'h0, rplu_mode};
                            resp_len    <= 6'd4;
                            shift_out <= laminar_index[15:8];
                            byte_idx  <= 6'd0;
                            resp_bit  <= 3'd7;
                            spi_miso  <= laminar_index[15];
                            ratio_valid_lat <= 1'b0;
                            state     <= S_RESP;

                        end else if (cmd_byte == 8'hAD) begin
                            // 9-byte scale table: 7 bytes scale_table + 2 bytes overflow
                            resp_buf[0] <= scale_tab_lat[51:44];
                            resp_buf[1] <= scale_tab_lat[43:36];
                            resp_buf[2] <= scale_tab_lat[35:28];
                            resp_buf[3] <= scale_tab_lat[27:20];
                            resp_buf[4] <= scale_tab_lat[19:12];
                            resp_buf[5] <= scale_tab_lat[11:4];
                            resp_buf[6] <= {4'b0, scale_tab_lat[3:0]};
                            resp_buf[7] <= scale_overflow_lat[12:5];
                            resp_buf[8] <= {3'b0, scale_overflow_lat[4:0]};
                            resp_len     <= 6'd9;
                            // Pre-load first byte MSB onto MISO before first SCK fall
                            shift_out <= scale_tab_lat[51:44];
                            byte_idx  <= 6'd0;
                            resp_bit  <= 3'd7;
                            spi_miso  <= scale_tab_lat[51];
                            state     <= S_RESP;

                        end else if (cmd_byte == 8'hAE) begin
                            // Last committed QR lane and its four components.
                            resp_buf[0] <= {7'd0, qr_valid_lat};
                            resp_buf[1] <= {4'd0, qr_lane_lat};
                            for (k = 0; k < 8; k = k + 1) begin
                                resp_buf[2+k]  <= qr_A_lat[63 - k*8 -: 8];
                                resp_buf[10+k] <= qr_B_lat[63 - k*8 -: 8];
                                resp_buf[18+k] <= qr_C_lat[63 - k*8 -: 8];
                                resp_buf[26+k] <= qr_D_lat[63 - k*8 -: 8];
                            end
                            resp_len  <= 7'd34;
                            shift_out <= {7'd0, qr_valid_lat};
                            byte_idx  <= 7'd0;
                            resp_bit  <= 3'd7;
                            spi_miso  <= 1'b0;
                            state     <= S_RESP;

                        end else if (cmd_byte == 8'hAF) begin
                            // Sticky HEX projection result.
                            resp_buf[0] <= {7'd0, hex_valid_lat};
                            resp_buf[1] <= hex_q_lat[15:8];
                            resp_buf[2] <= hex_q_lat[7:0];
                            resp_buf[3] <= hex_r_lat[15:8];
                            resp_buf[4] <= hex_r_lat[7:0];
                            resp_len    <= 7'd5;
                            shift_out <= {7'd0, hex_valid_lat};
                            byte_idx  <= 7'd0;
                            resp_bit  <= 3'd7;
                            spi_miso  <= 1'b0;
                            hex_valid_lat <= 1'b0;
                            state     <= S_RESP;

                        end else if (cmd_byte == 8'hB0) begin
                            // 64-byte Sentinel Telemetry Burst (8 nodes * 8 bytes)
                            for (k = 0; k < 64; k = k + 1) begin
                                // Big-endian byte streaming. node 0 (bits 511:448) is bytes 0-7.
                                resp_buf[k] <= sentinel_lat[511 - k*8 -: 8];
                            end
                            resp_len  <= 7'd64;
                            shift_out <= sentinel_lat[511 : 504];
                            byte_idx  <= 7'd0;
                            resp_bit  <= 3'd7;
                            spi_miso  <= sentinel_lat[511];
                            state     <= S_RESP;

                        end else if (cmd_byte == 8'hB1) begin
                            // CMD B1: receive one 64-bit SPU instruction/chord
                            recv_bits <= 6'd0;
                            data_shift <= 64'd0;
                            spi_miso <= 1'b0;
                            state <= S_RECV_INST;

                        end else if (cmd_byte == 8'hA5) begin
                            // CMD A5: receive two 64-bit chords (HEADER then DATA)
                            recv_bits <= 6'd0;
                            hdr_shift <= 64'd0;
                            data_shift<= 64'd0;
                            // Keep MISO low while receiving payload
                            spi_miso <= 1'b0;
                            state <= S_RECV_HDR;

                        end else begin
                            // Unknown command — respond with one 0x00
                            resp_buf[0] <= 8'h00;
                            resp_len    <= 6'd1;
                            // Pre-load first byte MSB onto MISO before first SCK fall
                            shift_out <= 8'h00;
                            byte_idx  <= 6'd0;
                            resp_bit  <= 3'd7;
                            spi_miso  <= 1'b0;
                            state     <= S_RESP;
                        end
                    end
                end

                S_RECV_HDR: begin
                    if (!cs_active) begin
                        state <= S_IDLE; // CS dropped unexpectedly
                    end else if (sck_rise) begin
                        hdr_shift <= {hdr_shift[62:0], mosi_d};
                        if (recv_bits == 6'd63) begin
                            recv_bits <= 6'd0;
                            state <= S_RECV_DATA;
                        end else begin
                            recv_bits <= recv_bits + 6'd1;
                        end
                    end
                end

                S_RECV_DATA: begin
                    if (!cs_active) begin
                        state <= S_IDLE; // CS dropped unexpectedly
                    end else if (sck_rise) begin
                        data_shift <= {data_shift[62:0], mosi_d};
                        if (recv_bits == 6'd63) begin
                            recv_bits <= 6'd0;
                            // Decode HEADER and emit single-cycle cfg pulse
                            if (hdr_shift[63:56] == 8'hA5) begin
                                rplu_cfg_sel      <= hdr_shift[50:48];
                                rplu_cfg_material <= {4'd0, hdr_shift[47:44]};
                                rplu_cfg_addr     <= hdr_shift[43:34];
                                rplu_cfg_data     <= {data_shift[62:0], mosi_d};
                                rplu_cfg_wr_en    <= 1'b1; // single-cycle pulse (cleared by default at next tick)
                            end
                            // Return to idle and wait for CS to be deasserted
                            state <= S_IDLE;
                        end else begin
                            recv_bits <= recv_bits + 6'd1;
                        end
                    end
                end

                S_RECV_INST: begin
                    if (!cs_active) begin
                        state <= S_IDLE; // CS dropped unexpectedly
                    end else if (sck_rise) begin
                        data_shift <= {data_shift[62:0], mosi_d};
                        if (recv_bits == 6'd63) begin
                            recv_bits <= 6'd0;
                            inst_word <= {data_shift[62:0], mosi_d};
                            inst_valid <= 1'b1;
                            state <= S_IDLE;
                        end else begin
                            recv_bits <= recv_bits + 6'd1;
                        end
                    end
                end

                S_RESP: begin
                    if (!cs_active) begin
                        state    <= S_IDLE;
                        spi_miso <= 1'b0;
                    end else if (sck_fall) begin
                        if (resp_bit == 3'd0) begin
                            // Last bit of this byte — advance to next
                            resp_bit <= 3'd7;
                            if (byte_idx + 6'd1 < resp_len) begin
                                byte_idx  <= byte_idx + 6'd1;
                                shift_out <= resp_buf[byte_idx + 6'd1];
                                spi_miso  <= resp_buf[byte_idx + 6'd1][7];
                            end else begin
                                spi_miso <= 1'b0;  // all bytes sent
                            end
                        end else begin
                            resp_bit <= resp_bit - 3'd1;
                            spi_miso <= shift_out[resp_bit - 3'd1];
                        end
                    end
                end

                default: state <= S_IDLE;
            endcase
        end
    end

endmodule
