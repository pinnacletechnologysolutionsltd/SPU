// spu_spi_cfg.v — Minimal SPI for SOM sidecar (write + readback)
//
// SPI Mode 0, MSB-first.
// Write: cmd(0xA5) + hdr(8) + data(8) + crc(1) = 18 bytes. Pulses wr_en on CS rise.
// Read:  CS low, shift out result[3:0] on MISO (4 SCK cycles), remainder driven 0.
//   result = {bmu_done, bmu_busy, bmu_label[1:0]}

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
    input  wire [3:0]  result
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
    reg [63:0] hdr, dat;
    reg        got_cmd;
    reg [3:0] result_s;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wr_en <= 1'b0;
            spi_miso <= 1'b0;
            bit_cnt <= 0; byte_cnt <= 0;
            hdr <= 64'd0; dat <= 64'd0;
            got_cmd <= 1'b0;
            sel <= 3'd0; addr <= 10'd0; data <= 64'd0;
            result_s <= 4'd0;
        end else begin
            wr_en <= 1'b0;

            if (cs_fall) begin
                bit_cnt <= 0; byte_cnt <= 0;
                hdr <= 64'd0; dat <= 64'd0;
                got_cmd <= 1'b0;
                result_s <= result;
            end else if (cs_rise) begin
                if (byte_cnt >= 17 && got_cmd) begin
                    sel <= hdr[50:48];
                    addr <= hdr[43:34];
                    data <= dat;
                    wr_en <= 1'b1;
                end
            end else if (sck_rise) begin
                if (byte_cnt == 0) begin
                    // Receiving command byte — shift into hdr[63:56]
                    hdr[63] <= spi_mosi;
                    hdr[62:56] <= hdr[63:57];
                    bit_cnt <= bit_cnt + 1;
                    if (bit_cnt == 7) begin
                        // Check if it's 0xA5 (write) or 0x01 (read)
                        // hdr[63:56] now holds the full command byte
                        if (hdr[63:56] == 8'hA5) begin
                            got_cmd <= 1'b1;
                            byte_cnt <= 1;
                            bit_cnt <= 0;
                        end else begin
                            // Read command: shift out result[3:0]
                            // Send result MSB first, then zeros
                            spi_miso <= result_s[3];
                            result_s <= {result_s[2:0], 1'b0};
                            bit_cnt <= 0;
                            byte_cnt <= 1; // stay in "read mode" for 4 bits
                        end
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
                end else begin
                    // Read mode: continue shifting out result (already set)
                    spi_miso <= result_s[3];
                    result_s <= {result_s[2:0], 1'b0};
                end
            end
        end
    end

endmodule
