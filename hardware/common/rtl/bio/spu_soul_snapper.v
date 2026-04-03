// SPU-13 Soul Snapper (v1.0)
// Target: Unified SPU-13 Fleet
// Objective: Perform LHS Handshake and Snap internal logic to Soul Class.
// Feature: Auto-detects Seed, Aura, or Manifold capacity.

`include "soul_map.vh"

module spu_soul_snapper (
    input  wire         clk,
    input  wire         reset,
    
    // SPI Flash Interface
    output reg          spi_cs_n,
    output reg          spi_sck,
    input  wire         spi_miso,
    
    // Snap Status
    output reg  [1:0]   soul_class, // 1:Seed, 2:Aura, 3:Manifold
    output reg  [7:0]   resolution,
    output reg          snap_ready
);

    // LHS v1.0 Signature
    localparam SIG_LHS = 32'h53515213; // "SQR13"

    reg [3:0] state;
    localparam IDLE=0, READ_HDR=1, ANALYZE=2, DONE=3;
    
    reg [255:0] hdr_buf;
    reg [8:0]   bit_cnt;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            state <= READ_HDR;
            soul_class <= 0;
            resolution <= 0;
            snap_ready <= 0;
            spi_cs_n <= 1; spi_sck <= 0;
            bit_cnt <= 0; hdr_buf <= 0;
        end else begin
            case (state)
                READ_HDR: begin
                    spi_cs_n <= 0;
                    if (bit_cnt < 256) begin
                        spi_sck <= ~spi_sck;
                        if (spi_sck) begin // Falling edge: sample
                            hdr_buf <= {hdr_buf[254:0], spi_miso};
                            bit_cnt <= bit_cnt + 1;
                        end
                    end else begin
                        spi_cs_n <= 1;
                        state <= ANALYZE;
                    end
                end

                ANALYZE: begin
                    if (hdr_buf[255:224] == SIG_LHS) begin
                        soul_class <= hdr_buf[223:216];
                        resolution <= hdr_buf[215:208];
                    end else begin
                        soul_class <= 2'b01; // Default to Seed (Class I)
                        resolution <= 8'd16; // Default 16-bit
                    end
                    state <= DONE;
                end

                DONE: begin
                    snap_ready <= 1;
                end
            endcase
        end
    end

endmodule
