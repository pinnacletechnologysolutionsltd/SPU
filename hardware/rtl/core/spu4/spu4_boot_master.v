// spu4_boot_master.v (v1.0 - Sentinel Sovereignty)
// Objective: Autonomous SPI Flash Inhale for SPU-4 Sentinel nodes.
// Standard: Bit-banged SPI Master for iCE40 LP1K.

module spu4_boot_master (
    input  wire        clk,
    input  wire        reset,
    
    // SPI Physical Pins
    output reg         spi_cs_n,
    output reg         spi_sck,
    output reg         spi_mosi,
    input  wire        spi_miso,
    
    // Inhale Interface (to Dream Sequencer)
    output reg         inhale_en,
    output reg  [3:0]  inhale_addr,
    output reg  [15:0] inhale_data,
    output reg         inhale_done
);

    // SPI States: 0:IDLE, 1:CMD_8, 2:ADDR_24, 3:DATA_INHALE, 4:DONE
    reg [2:0]  state;
    reg [9:0]  bit_cnt;
    reg [23:0] boot_addr = 24'h00F000; // 60KB offset for SPU-4 Dream
    reg [7:0]  read_cmd = 8'h03;
    reg [15:0] shift_reg;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            state <= 0;
            bit_cnt <= 0;
            spi_cs_n <= 1;
            spi_sck <= 0;
            spi_mosi <= 0;
            inhale_en <= 0;
            inhale_done <= 0;
            inhale_addr <= 0;
        end else begin
            case (state)
                3'd0: begin // IDLE: Wait for release of reset
                    state <= 3'd1;
                    spi_cs_n <= 0;
                    bit_cnt <= 0;
                end
                
                3'd1: begin // CMD_8 (0x03)
                    spi_sck <= ~spi_sck;
                    if (spi_sck) begin // Falling edge of SCK (pre-increment bit_cnt)
                        spi_mosi <= read_cmd[7 - bit_cnt[2:0]];
                        if (bit_cnt == 15) begin // 8 bits * 2 cycles each
                            state <= 3'd2;
                            bit_cnt <= 0;
                        end else bit_cnt <= bit_cnt + 1;
                    end
                end
                
                3'd2: begin // ADDR_24
                    spi_sck <= ~spi_sck;
                    if (spi_sck) begin
                        spi_mosi <= boot_addr[23 - bit_cnt[4:0]];
                        if (bit_cnt == 47) begin // 24 bits * 2 cycles
                            state <= 3'd3;
                            bit_cnt <= 0;
                            inhale_en <= 1;
                        end else bit_cnt <= bit_cnt + 1;
                    end
                end
                
                3'd3: begin // DATA_INHALE (16 instructions x 16 bits = 256 bits)
                    spi_sck <= ~spi_sck;
                    if (!spi_sck) begin // Rising edge of SCK: Capture MISO
                        shift_reg <= {shift_reg[14:0], spi_miso};
                    end else begin // Falling edge: Check word boundary
                        if (bit_cnt[4:0] == 31) begin // 16 bits captured
                            inhale_data <= shift_reg;
                            inhale_addr <= bit_cnt[8:5];
                            if (bit_cnt == 511) begin // 256 bits * 2 cycles
                                state <= 3'd4;
                                inhale_en <= 0;
                            end
                        end
                        bit_cnt <= bit_cnt + 1;
                    end
                end
                
                3'd4: begin // DONE
                    spi_cs_n <= 1;
                    inhale_done <= 1;
                    inhale_en <= 0;
                end
            endcase
        end
    end

endmodule
