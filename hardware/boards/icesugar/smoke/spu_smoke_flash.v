// spu_smoke_flash.v — SPU-13 iCEsugar Level 2 Smoke Test
// Target : iCEsugar v1.5 (iCE40UP5K-SG48)
// Purpose: Read JEDEC ID from W25Q128JVSQ via SPI, print over UART.
//
// Expected JEDEC response: EF 40 18
//   EF = Winbond manufacturer ID
//   40 = SPI NOR flash family
//   18 = 128 Mbit density (2^24 bytes)
//
// If UART shows "JEDEC: EF 40 18" the new flash chip is correctly soldered.
// If it shows "JEDEC: FF FF FF" the chip is not responding (cold solder / orientation).
//
// SPI uses bit-bang on the config flash pins (post-configuration access).
// Flash must NOT be in config-only mode — check iCEsugar jumper J5 is removed
// or set to "user SPI" mode.
//
// ⚠ Do NOT program this test until soldering is complete and visually inspected.

`default_nettype none

module spu_smoke_flash (
    input  wire clk,       // 12 MHz
    output wire uart_tx,
    output wire LED_R,
    output wire LED_G,
    output wire LED_B,
    // SPI flash pins (post-config access)
    output wire flash_cs_n,
    output wire flash_sck,
    output wire flash_io0,   // MOSI
    input  wire flash_io1    // MISO
);

    // -------------------------------------------------------------------
    // Parameters
    // -------------------------------------------------------------------
    localparam BAUD_DIV  = 104;  // 12MHz / 115200
    localparam SPI_DIV   = 6;    // 12MHz / 12 = 1 MHz SPI clock

    // JEDEC Read ID command: 0x9F
    localparam CMD_JEDEC = 8'h9F;

    // -------------------------------------------------------------------
    // State machine
    // -------------------------------------------------------------------
    localparam S_INIT      = 3'd0;  // wait 1ms for flash power-up
    localparam S_CS_LOW    = 3'd1;  // assert CS
    localparam S_SEND_CMD  = 3'd2;  // send 0x9F (8 bits)
    localparam S_RECV_BYTE = 3'd3;  // receive 3 bytes
    localparam S_CS_HIGH   = 3'd4;  // deassert CS
    localparam S_UART      = 3'd5;  // transmit result over UART
    localparam S_DONE      = 3'd6;  // loop idle

    reg [2:0]  state     = S_INIT;
    reg [13:0] init_cnt  = 0;       // 12000 cycles ≈ 1 ms
    reg [2:0]  spi_cnt   = 0;       // SPI clock divider
    reg [3:0]  bit_cnt   = 0;       // bits sent/received
    reg [1:0]  byte_cnt  = 0;       // bytes received (0..2)
    reg [7:0]  shift_out = 0;
    reg [7:0]  shift_in  = 0;
    reg [23:0] jedec_id  = 0;       // 3-byte result

    reg        sck_reg   = 1'b0;
    reg        cs_n_reg  = 1'b1;
    reg        mosi_reg  = 1'b1;

    always @(posedge clk) begin
        case (state)

            S_INIT: begin
                cs_n_reg <= 1'b1;
                if (init_cnt == 14'd12000) begin
                    state     <= S_CS_LOW;
                    init_cnt  <= 0;
                end else
                    init_cnt <= init_cnt + 1;
            end

            S_CS_LOW: begin
                cs_n_reg  <= 1'b0;
                shift_out <= CMD_JEDEC;
                bit_cnt   <= 0;
                spi_cnt   <= 0;
                state     <= S_SEND_CMD;
            end

            S_SEND_CMD: begin
                if (spi_cnt == SPI_DIV - 1) begin
                    spi_cnt  <= 0;
                    sck_reg  <= ~sck_reg;
                    if (!sck_reg) begin
                        // Rising edge: shift out MSB
                        mosi_reg  <= shift_out[7];
                        shift_out <= {shift_out[6:0], 1'b0};
                    end else begin
                        // Falling edge: count bit
                        if (bit_cnt == 7) begin
                            bit_cnt  <= 0;
                            byte_cnt <= 0;
                            state    <= S_RECV_BYTE;
                        end else
                            bit_cnt <= bit_cnt + 1;
                    end
                end else
                    spi_cnt <= spi_cnt + 1;
            end

            S_RECV_BYTE: begin
                if (spi_cnt == SPI_DIV - 1) begin
                    spi_cnt <= 0;
                    sck_reg <= ~sck_reg;
                    if (!sck_reg) begin
                        // Rising edge: sample MISO
                        shift_in <= {shift_in[6:0], flash_io1};
                    end else begin
                        // Falling edge: count bit
                        if (bit_cnt == 7) begin
                            bit_cnt <= 0;
                            jedec_id <= {jedec_id[15:0], shift_in};
                            if (byte_cnt == 2)
                                state <= S_CS_HIGH;
                            else
                                byte_cnt <= byte_cnt + 1;
                        end else
                            bit_cnt <= bit_cnt + 1;
                    end
                end else
                    spi_cnt <= spi_cnt + 1;
            end

            S_CS_HIGH: begin
                cs_n_reg <= 1'b1;
                sck_reg  <= 1'b0;
                state    <= S_UART;
            end

            S_UART: begin
                // Hand off to UART TX FSM (see below)
                // Returns to S_DONE when complete
            end

            S_DONE: begin
                // Idle — LED shows result
            end

        endcase
    end

    assign flash_cs_n = cs_n_reg;
    assign flash_sck  = sck_reg;
    assign flash_io0  = mosi_reg;

    // -------------------------------------------------------------------
    // UART TX: "JEDEC: XX XX XX\r\n" (18 bytes)
    // Triggered when state == S_UART
    // -------------------------------------------------------------------
    function [7:0] nibble_to_hex;
        input [3:0] n;
        begin
            if (n < 10) nibble_to_hex = 8'h30 + {4'h0, n};
            else        nibble_to_hex = 8'h41 + {4'h0, n - 4'd10};
        end
    endfunction

    // Build message bytes
    wire [7:0] uart_bytes [0:17];
    assign uart_bytes[0]  = 8'h4A; // J
    assign uart_bytes[1]  = 8'h45; // E
    assign uart_bytes[2]  = 8'h44; // D
    assign uart_bytes[3]  = 8'h45; // E
    assign uart_bytes[4]  = 8'h43; // C
    assign uart_bytes[5]  = 8'h3A; // :
    assign uart_bytes[6]  = 8'h20; // space
    assign uart_bytes[7]  = nibble_to_hex(jedec_id[23:20]);
    assign uart_bytes[8]  = nibble_to_hex(jedec_id[19:16]);
    assign uart_bytes[9]  = 8'h20; // space
    assign uart_bytes[10] = nibble_to_hex(jedec_id[15:12]);
    assign uart_bytes[11] = nibble_to_hex(jedec_id[11:8]);
    assign uart_bytes[12] = 8'h20; // space
    assign uart_bytes[13] = nibble_to_hex(jedec_id[7:4]);
    assign uart_bytes[14] = nibble_to_hex(jedec_id[3:0]);
    assign uart_bytes[15] = 8'h0D; // CR
    assign uart_bytes[16] = 8'h0A; // LF
    assign uart_bytes[17] = 8'h00; // sentinel

    reg [4:0] uart_idx   = 0;
    reg [3:0] uart_bit   = 0;
    reg [6:0] uart_baud  = 0;
    reg [9:0] uart_shift = 10'h3FF;
    reg       uart_busy  = 1'b0;
    reg       uart_done  = 1'b0;

    always @(posedge clk) begin
        if (state == S_UART && !uart_busy && !uart_done) begin
            uart_busy  <= 1'b1;
            uart_idx   <= 0;
            uart_shift <= {1'b1, uart_bytes[0], 1'b0};
            uart_bit   <= 0;
            uart_baud  <= 0;
        end else if (uart_busy) begin
            if (uart_baud == BAUD_DIV - 1) begin
                uart_baud <= 0;
                uart_shift <= {1'b1, uart_shift[9:1]};
                if (uart_bit == 9) begin
                    uart_bit <= 0;
                    if (uart_idx == 16) begin
                        uart_busy <= 1'b0;
                        uart_done <= 1'b1;
                    end else begin
                        uart_idx  <= uart_idx + 1;
                        uart_shift <= {1'b1, uart_bytes[uart_idx+1], 1'b0};
                    end
                end else
                    uart_bit <= uart_bit + 1;
            end else
                uart_baud <= uart_baud + 1;
        end

        if (uart_done)
            state <= S_DONE;  // only safe to write from single always block
    end

    assign uart_tx = uart_busy ? uart_shift[0] : 1'b1;

    // -------------------------------------------------------------------
    // RGB status
    //   Blue  = initialising
    //   Green = JEDEC read OK (EF 40 18)
    //   Red   = JEDEC mismatch (all FF or wrong ID)
    // -------------------------------------------------------------------
    wire jedec_ok = (jedec_id == 24'hEF4018);

    SB_RGBA_DRV #(
        .CURRENT_MODE ("0b0"),
        .RGB0_CURRENT ("0b000001"),
        .RGB1_CURRENT ("0b000001"),
        .RGB2_CURRENT ("0b000001")
    ) u_rgb (
        .CURREN   (1'b1),
        .RGBLEDEN (1'b1),
        .RGB0PWM  (state == S_DONE && !jedec_ok),  // Red: bad ID
        .RGB1PWM  (state == S_DONE &&  jedec_ok),  // Green: good
        .RGB2PWM  (state != S_DONE),               // Blue: working
        .RGB0     (LED_R),
        .RGB1     (LED_G),
        .RGB2     (LED_B)
    );

endmodule
