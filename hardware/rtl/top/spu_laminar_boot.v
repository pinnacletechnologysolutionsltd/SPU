// spu_laminar_boot.v
// First-stage bootloader: read JEDEC ID from SPI flash, then hydrate the core
// with the Pell rotor and golden-prime seed tables stored in the PMOD flash image.
`ifndef FLASH_PELL_BASE
`include "hardware/rtl/arch/spu_flash_map.vh"
`endif

module spu_laminar_boot #(
    parameter ENABLE_RPLU_BOOT = 1,
    parameter [15:0] RPLU_CFG_RECORDS = 16'd2051,
    parameter integer SPI_SCK_HALF_CYCLES = 32
) (
    input  clk,       // Expected 12MHz domain
    input  rst_n,
    // SPI Physical Interface
    output reg flash_cs,
    output wire flash_sck,
    input  flash_miso,
    output reg flash_mosi,
    output reg [23:0] jedec_id,
    // Internal BRAM Interface
    output reg [23:0] bram_data,
    output reg [3:0]  bram_addr,
    output reg        bram_we,
    // Pell Rotor Vault Interface
    output reg [31:0] pell_data,
    output reg [2:0]  pell_addr,
    output reg        pell_we,
    // SDRAM Inhaler Interface
    output reg        mem_burst_wr,
    output reg [24:0] mem_addr,
    output reg [831:0] mem_wr_manifold,
    input  wire       mem_burst_done,
    // RPLU runtime config stream from SPI flash chord records.
    output reg        rplu_cfg_wr_en,
    output reg [2:0]  rplu_cfg_sel,
    output reg [7:0]  rplu_cfg_material,
    output reg [9:0]  rplu_cfg_addr,
    output reg [63:0] rplu_cfg_data,
    output reg [15:0] rplu_cfg_loaded,
    output reg [31:0] rplu_cfg_checksum,
    output reg        boot_done,
    output wire [5:0]  boot_state
);

    // Flash Addresses
    localparam [7:0]  JEDEC_CMD           = 8'h9F;
    localparam [7:0]  READ_CMD            = 8'h03;
    localparam [23:0] FLASH_PELL_BOOT_BASE     = `FLASH_PELL_BASE;
    localparam [23:0] FLASH_PRIME_BOOT_BASE    = `FLASH_GOLDEN_BASE;
    localparam [23:0] FLASH_RPLU_CFG_BOOT_BASE = `FLASH_RPLU_CFG_BASE;
    localparam [7:0]  RPLU_CFG_OPCODE     = 8'hA5;

    reg [5:0] state;
    reg [7:0] bit_cnt;
    reg [31:0] shift_reg;
    reg [31:0] read_word;
    reg [31:0] pell_p_word;
    reg [31:0] pell_q_word;
    reg [63:0] rplu_header_word;
    reg [63:0] rplu_data_word;
    reg [3:0]  prime_cnt;
    reg [2:0]  pell_cnt;
    reg [15:0] rplu_record_cnt;
    reg [7:0]  sck_div;
    reg        sck_en;

    assign boot_state = state;

    // SDRAM Inhaler Regs
    reg [6:0]  element_cnt;     // 0-117
    reg [7:0]  burst_cnt;       // Bursts per element
    reg [5:0]  word_in_burst;   // 0-51 (52 words = 832 bits)

    localparam integer SPI_SCK_HALF_SAFE = (SPI_SCK_HALF_CYCLES < 1) ? 1 : SPI_SCK_HALF_CYCLES;
    localparam integer SPI_SCK_PERIOD_SAFE = SPI_SCK_HALF_SAFE * 2;

    assign flash_sck = sck_en ? (sck_div >= SPI_SCK_HALF_SAFE[7:0]) : 1'b0;
    wire sck_rise = sck_en && (sck_div == SPI_SCK_HALF_SAFE[7:0] - 8'd1);
    wire sck_fall = sck_en && (sck_div == SPI_SCK_PERIOD_SAFE[7:0] - 8'd1);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= 0;
            flash_cs <= 1;
            flash_mosi <= 0;
            jedec_id <= 0;
            boot_done <= 0;
            bram_we <= 0;
            bram_addr <= 0;
            pell_we <= 0;
            pell_addr <= 0;
            pell_data <= 0;
            sck_div <= 0;
            sck_en <= 0;
            prime_cnt <= 0;
            pell_cnt <= 0;
            bit_cnt <= 0;
            bram_data <= 0;
            mem_burst_wr <= 0;
            mem_addr <= 0;
            mem_wr_manifold <= 0;
            rplu_cfg_wr_en <= 1'b0;
            rplu_cfg_sel <= 3'd0;
            rplu_cfg_material <= 8'd0;
            rplu_cfg_addr <= 10'd0;
            rplu_cfg_data <= 64'd0;
            rplu_cfg_loaded <= 16'd0;
            rplu_cfg_checksum <= 32'd0;
            element_cnt <= 0;
            burst_cnt <= 0;
            word_in_burst <= 0;
            shift_reg <= 0;
            read_word <= 0;
            pell_p_word <= 0;
            pell_q_word <= 0;
            rplu_header_word <= 64'd0;
            rplu_data_word <= 64'd0;
            rplu_record_cnt <= 16'd0;
        end else if (!boot_done) begin
            if (sck_en) begin
                sck_div <= sck_fall ? 8'd0 : (sck_div + 1'b1);
            end else begin
                sck_div <= 8'd0;
            end
            bram_we <= 1'b0;
            pell_we <= 1'b0;
            mem_burst_wr <= 1'b0;
            rplu_cfg_wr_en <= 1'b0;

            case (state)
                0: begin // Initial Idle -> Read JEDEC ID
                    flash_cs <= 0;
                    sck_en <= 1'b1;
                    shift_reg <= {JEDEC_CMD, 24'h0};
                    flash_mosi <= JEDEC_CMD[7];
                    bit_cnt <= 0;
                    state <= 1;
                    sck_div <= 8'd0;
                end

                1: begin // Send JEDEC command (8 bits)
                    if (sck_fall) begin
                        shift_reg <= {shift_reg[30:0], 1'b0};
                        if (bit_cnt == 7) begin
                            state <= 2;
                            bit_cnt <= 0;
                            flash_mosi <= 1'b0;
                        end else begin
                            bit_cnt <= bit_cnt + 1;
                            flash_mosi <= shift_reg[30];
                        end
                    end
                end

                2: begin // Read JEDEC ID (24 bits)
                    if (sck_fall) begin
                        if (bit_cnt == 23) begin
                            sck_en <= 1'b0;
                            bit_cnt <= 8'd0;
                            state <= 3;
                        end else begin
                            bit_cnt <= bit_cnt + 1;
                        end
                    end else if (sck_rise) begin
                        shift_reg <= {shift_reg[30:0], flash_miso};
                        if (bit_cnt == 23) begin
                            jedec_id <= {shift_reg[22:0], flash_miso};
                        end
                    end
                end

                3: begin // CS high gap between JEDEC and normal read command
                    flash_cs <= 1'b1;
                    sck_en <= 1'b0;
                    flash_mosi <= 1'b0;
                    if (bit_cnt == 8'd15) begin
                        bit_cnt <= 8'd0;
                        state <= 4;
                    end else begin
                        bit_cnt <= bit_cnt + 1'b1;
                    end
                end

                4: begin // Start READ 0x03 at the Pell table base
                    flash_cs <= 1'b0;
                    sck_en <= 1'b1;
                    shift_reg <= {READ_CMD, FLASH_PELL_BOOT_BASE};
                    flash_mosi <= READ_CMD[7];
                    bit_cnt <= 8'd0;
                    pell_cnt <= 3'd0;
                    read_word <= 32'd0;
                    pell_p_word <= 32'd0;
                    pell_q_word <= 32'd0;
                    sck_div <= 8'd0;
                    state <= 5;
                end

                5: begin // Send Pell READ command and 24-bit address
                    if (sck_fall) begin
                        shift_reg <= {shift_reg[30:0], 1'b0};
                        if (bit_cnt == 8'd31) begin
                            bit_cnt <= 8'd0;
                            flash_mosi <= 1'b0;
                            pell_p_word <= 32'd0;
                            state <= 6;
                        end else begin
                            bit_cnt <= bit_cnt + 1'b1;
                            flash_mosi <= shift_reg[30];
                        end
                    end
                end

                6: begin // Read one big-endian 32-bit Pell P word
                    if (sck_fall) begin
                        if (bit_cnt == 8'd31) begin
                            bit_cnt <= 8'd0;
                            pell_q_word <= 32'd0;
                            state <= 7;
                        end else begin
                            bit_cnt <= bit_cnt + 1'b1;
                        end
                    end else if (sck_rise) begin
                        pell_p_word <= {pell_p_word[30:0], flash_miso};
                    end
                end

                7: begin // Read one big-endian 32-bit Pell Q word
                    if (sck_fall) begin
                        if (bit_cnt == 8'd31) begin
                            bit_cnt <= 8'd0;
                            sck_en <= 1'b0;
                            state <= 8;
                        end else begin
                            bit_cnt <= bit_cnt + 1'b1;
                        end
                    end else if (sck_rise) begin
                        pell_q_word <= {pell_q_word[30:0], flash_miso};
                    end
                end

                8: begin // Hydrate one Pell vault entry
                    pell_addr <= pell_cnt;
                    pell_data <= {pell_p_word[15:0], pell_q_word[15:0]};
                    pell_we <= 1'b1;
                    if (pell_cnt == 3'd7) begin
                        flash_cs <= 1'b1;
                        state <= 9;
                    end else begin
                        pell_cnt <= pell_cnt + 1'b1;
                        pell_p_word <= 32'd0;
                        pell_q_word <= 32'd0;
                        sck_en <= 1'b1;
                        sck_div <= 8'd0;
                        state <= 6;
                    end
                end

                9: begin // CS high gap between Pell and golden-prime reads
                    flash_cs <= 1'b1;
                    sck_en <= 1'b0;
                    flash_mosi <= 1'b0;
                    if (bit_cnt == 8'd15) begin
                        bit_cnt <= 8'd0;
                        state <= 10;
                    end else begin
                        bit_cnt <= bit_cnt + 1'b1;
                    end
                end

                10: begin // Start READ 0x03 at the golden-prime table base
                    flash_cs <= 1'b0;
                    sck_en <= 1'b1;
                    shift_reg <= {READ_CMD, FLASH_PRIME_BOOT_BASE};
                    flash_mosi <= READ_CMD[7];
                    bit_cnt <= 8'd0;
                    prime_cnt <= 4'd0;
                    read_word <= 32'd0;
                    sck_div <= 8'd0;
                    state <= 11;
                end

                11: begin // Send prime READ command and 24-bit address
                    if (sck_fall) begin
                        shift_reg <= {shift_reg[30:0], 1'b0};
                        if (bit_cnt == 8'd31) begin
                            bit_cnt <= 8'd0;
                            flash_mosi <= 1'b0;
                            read_word <= 32'd0;
                            state <= 12;
                        end else begin
                            bit_cnt <= bit_cnt + 1'b1;
                            flash_mosi <= shift_reg[30];
                        end
                    end
                end

                12: begin // Read one big-endian 32-bit prime word
                    if (sck_fall) begin
                        if (bit_cnt == 8'd31) begin
                            bit_cnt <= 8'd0;
                            sck_en <= 1'b0;
                            state <= 13;
                        end else begin
                            bit_cnt <= bit_cnt + 1'b1;
                        end
                    end else if (sck_rise) begin
                        read_word <= {read_word[30:0], flash_miso};
                    end
                end

                13: begin // Present a one-cycle prime write strobe to the core
                    bram_addr <= prime_cnt;
                    bram_data <= read_word[23:0];
                    bram_we <= 1'b1;
                    if (prime_cnt == 4'd12) begin
                        flash_cs <= 1'b1;
                        state <= (ENABLE_RPLU_BOOT && (RPLU_CFG_RECORDS != 16'd0)) ? 15 : 14;
                    end else begin
                        prime_cnt <= prime_cnt + 1'b1;
                        read_word <= 32'd0;
                        sck_en <= 1'b1;
                        sck_div <= 8'd0;
                        state <= 12;
                    end
                end

                14: begin // Final Cleanup
                    flash_cs <= 1'b1;
                    sck_en <= 1'b0;
                    flash_mosi <= 1'b0;
                    boot_done <= 1'b1;
                end

                15: begin // CS high gap between golden-prime reads and RPLU config stream
                    flash_cs <= 1'b1;
                    sck_en <= 1'b0;
                    flash_mosi <= 1'b0;
                    if (bit_cnt == 8'd15) begin
                        bit_cnt <= 8'd0;
                        state <= 16;
                    end else begin
                        bit_cnt <= bit_cnt + 1'b1;
                    end
                end

                16: begin // Start READ 0x03 at the RPLU chord stream base
                    flash_cs <= 1'b0;
                    sck_en <= 1'b1;
                    shift_reg <= {READ_CMD, FLASH_RPLU_CFG_BOOT_BASE};
                    flash_mosi <= READ_CMD[7];
                    bit_cnt <= 8'd0;
                    rplu_record_cnt <= 16'd0;
                    rplu_header_word <= 64'd0;
                    rplu_data_word <= 64'd0;
                    sck_div <= 8'd0;
                    state <= 17;
                end

                17: begin // Send RPLU READ command and 24-bit address
                    if (sck_fall) begin
                        shift_reg <= {shift_reg[30:0], 1'b0};
                        if (bit_cnt == 8'd31) begin
                            bit_cnt <= 8'd0;
                            flash_mosi <= 1'b0;
                            rplu_header_word <= 64'd0;
                            state <= 18;
                        end else begin
                            bit_cnt <= bit_cnt + 1'b1;
                            flash_mosi <= shift_reg[30];
                        end
                    end
                end

                18: begin // Read one big-endian 64-bit RPLU header chord
                    if (sck_fall) begin
                        if (bit_cnt == 8'd63) begin
                            bit_cnt <= 8'd0;
                            rplu_data_word <= 64'd0;
                            state <= 19;
                        end else begin
                            bit_cnt <= bit_cnt + 1'b1;
                        end
                    end else if (sck_rise) begin
                        rplu_header_word <= {rplu_header_word[62:0], flash_miso};
                    end
                end

                19: begin // Read one big-endian 64-bit RPLU data chord
                    if (sck_fall) begin
                        if (bit_cnt == 8'd63) begin
                            bit_cnt <= 8'd0;
                            sck_en <= 1'b0;
                            state <= 20;
                        end else begin
                            bit_cnt <= bit_cnt + 1'b1;
                        end
                    end else if (sck_rise) begin
                        rplu_data_word <= {rplu_data_word[62:0], flash_miso};
                    end
                end

                20: begin // Decode the chord pair into one RPLU config write
                    if (rplu_header_word[63:56] == RPLU_CFG_OPCODE) begin
                        rplu_cfg_sel <= rplu_header_word[50:48];
                        rplu_cfg_material <= {4'd0, rplu_header_word[47:44]};
                        rplu_cfg_addr <= rplu_header_word[43:34];
                        rplu_cfg_data <= rplu_data_word;
                        rplu_cfg_wr_en <= 1'b1;
                        rplu_cfg_loaded <= rplu_cfg_loaded + 1'b1;
                        rplu_cfg_checksum <= rplu_cfg_checksum
                                           + rplu_header_word[63:32]
                                           + rplu_header_word[31:0]
                                           + rplu_data_word[63:32]
                                           + rplu_data_word[31:0];
                    end

                    if (rplu_record_cnt == RPLU_CFG_RECORDS - 1'b1) begin
                        flash_cs <= 1'b1;
                        sck_en <= 1'b0;
                        flash_mosi <= 1'b0;
                        state <= 14;
                    end else begin
                        rplu_record_cnt <= rplu_record_cnt + 1'b1;
                        rplu_header_word <= 64'd0;
                        rplu_data_word <= 64'd0;
                        sck_en <= 1'b1;
                        sck_div <= 8'd0;
                        state <= 18;
                    end
                end
            endcase
        end
    end
endmodule
