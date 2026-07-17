// spu_spi_cfg.v — Minimal SPI for SOM sidecar (write + readback)
//
// SPI Mode 0, MSB-first.
// Write: cmd(0xA5) + hdr(8) + data(8) + crc(1) = 18 bytes. Pulses wr_en on CS rise.
// Legacy read 0x01: result[3:0] in the high nibble of the following byte.
// SOM1 read   0x02: fixed 52-byte result_frame, MSB/byte 0 first.

module spu_spi_cfg (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        spi_cs_n,
    input  wire        spi_sck,
    input  wire        spi_mosi,
    output reg         spi_miso,
    output reg         wr_en,
    output reg  [2:0]  sel,
    output reg  [9:0]  addr,
    output reg  [63:0] data,
    input  wire [3:0]  result,
    input  wire [415:0] result_frame
);

    reg [2:0] sck_sync, cs_sync;
    wire sck_rise = (sck_sync[1:0] == 2'b01);
    wire cs_fall  = (cs_sync[1:0] == 2'b10);
    wire cs_rise  = (cs_sync[1:0] == 2'b01);

    always @(posedge clk) begin
        sck_sync <= {sck_sync[1:0], spi_sck};
        cs_sync  <= {cs_sync[1:0],  spi_cs_n};
    end

    reg [3:0] bit_cnt;
    reg [4:0] byte_cnt;
    reg [7:0] cmd_shift;
    reg [63:0] hdr, dat;
    reg        got_cmd;
    reg [1:0]  read_mode;
    reg [3:0] result_s;
    reg [415:0] frame_s;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wr_en <= 1'b0;
            spi_miso <= 1'b0;
            bit_cnt <= 0; byte_cnt <= 0;
            cmd_shift <= 8'd0;
            hdr <= 64'd0; dat <= 64'd0;
            got_cmd <= 1'b0;
            read_mode <= 2'd0;
            sel <= 3'd0; addr <= 10'd0; data <= 64'd0;
            result_s <= 4'd0;
            frame_s <= 416'd0;
        end else begin
            wr_en <= 1'b0;

            if (cs_fall) begin
                bit_cnt <= 0; byte_cnt <= 0;
                cmd_shift <= 8'd0;
                hdr <= 64'd0; dat <= 64'd0;
                got_cmd <= 1'b0;
                read_mode <= 2'd0;
                result_s <= result;
                frame_s <= result_frame;
                spi_miso <= 1'b0;
            end else if (cs_rise) begin
                if (byte_cnt >= 17 && got_cmd) begin
                    sel <= hdr[50:48];
                    addr <= hdr[43:34];
                    data <= dat;
                    wr_en <= 1'b1;
                end
            end else if (sck_rise) begin
                if (byte_cnt == 0) begin
                    // Receive the command MSB-first.  Do not reuse hdr as a
                    // reverse-direction scratch register: 0xA5 happens to be
                    // bit-palindromic and used to hide that bug, while 0x01
                    // and 0x02 were decoded as 0x80 and 0x40.
                    cmd_shift <= {cmd_shift[6:0], spi_mosi};
                    bit_cnt <= bit_cnt + 1;
                    if (bit_cnt == 7) begin
                        case ({cmd_shift[6:0], spi_mosi})
                            8'hA5: begin
                                got_cmd <= 1'b1;
                                read_mode <= 2'd0;
                                byte_cnt <= 1;
                                bit_cnt <= 0;
                            end
                            8'h01: begin
                                read_mode <= 2'd1;
                                spi_miso <= result_s[3];
                                result_s <= {result_s[2:0], 1'b0};
                                bit_cnt <= 0;
                                byte_cnt <= 1;
                            end
                            8'h02: begin
                                read_mode <= 2'd2;
                                spi_miso <= frame_s[415];
                                frame_s <= {frame_s[414:0], 1'b0};
                                bit_cnt <= 0;
                                byte_cnt <= 1;
                            end
                            default: begin
                                read_mode <= 2'd0;
                                spi_miso <= 1'b0;
                                bit_cnt <= 0;
                                byte_cnt <= 1;
                            end
                        endcase
                    end
                end else if (got_cmd) begin
                    // Writing: receive header + data + crc
                    if (byte_cnt <= 8) begin
                        hdr <= {hdr[62:0], spi_mosi};
                    end else if (byte_cnt <= 16) begin
                        dat <= {dat[62:0], spi_mosi};
                    end
                    // else crc byte — ignore
                    bit_cnt <= bit_cnt + 1;
                    if (bit_cnt == 7) begin
                        byte_cnt <= byte_cnt + 1;
                        bit_cnt <= 0;
                    end
                end else if (read_mode == 2'd1) begin
                    // Legacy read: continue result nibble, then zeros.
                    spi_miso <= result_s[3];
                    result_s <= {result_s[2:0], 1'b0};
                end else if (read_mode == 2'd2) begin
                    spi_miso <= frame_s[415];
                    frame_s <= {frame_s[414:0], 1'b0};
                end else begin
                    spi_miso <= 1'b0;
                end
            end
        end
    end

endmodule
