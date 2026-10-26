// spu_tang25k_flash_rplu2_read_probe.v -- PMOD J4 flash content probe.
// Uses the J4 sweep-proven M00 mapping:
//   j4[0]=CS#(G10), j4[1]=SCK(D10), j4[2]=MOSI(B10), j4[3]=MISO(C10).
// Prints JEDEC plus the first RPLU2 config record at flash offset 0x110000.
module spu_tang25k_flash_rplu2_read_probe (
    input  wire       sys_clk,
    output wire [2:0] led,
    output wire       uart_tx,
    output wire       uart_tx_telemetry,
    output wire       flash_cs,
    output wire       flash_sck,
    output wire       flash_mosi,
    input  wire       flash_miso
);
    localparam [23:0] RPLU_CFG_BASE = 24'h110000;

    reg [25:0] counter = 26'd0;
    always @(posedge sys_clk) counter <= counter + 1'b1;

    assign led[0] = counter[24];
    assign led[1] = counter[23];
    assign led[2] = counter[22];

    localparam PH_JEDEC_INIT = 3'd0;
    localparam PH_JEDEC_RUN  = 3'd1;
    localparam PH_READ_INIT  = 3'd2;
    localparam PH_READ_RUN   = 3'd3;
    localparam PH_UART_RUN   = 3'd4;

    localparam SPI_IDLE   = 3'd0;
    localparam SPI_TX     = 3'd1;
    localparam SPI_RX     = 3'd2;
    localparam SPI_FINISH = 3'd3;

    reg [2:0] phase = PH_JEDEC_INIT;
    reg [2:0] spi_state = SPI_IDLE;
    reg [5:0] spi_clk_div = 6'd0;
    reg       sck_en = 1'b0;
    reg [5:0] tx_bit_cnt = 6'd0;
    reg [7:0] rx_bit_cnt = 8'd0;
    reg [31:0] spi_tx_shift = 32'd0;
    reg [7:0] tx_bits = 8'd0;
    reg [7:0] rx_bits = 8'd0;
    reg [127:0] spi_rx_shift = 128'd0;
    reg       spi_done = 1'b0;

    reg [23:0] jedec_id = 24'hFFFFFF;
    reg [63:0] first_header = 64'hFFFFFFFFFFFFFFFF;
    reg [63:0] first_data = 64'hFFFFFFFFFFFFFFFF;

    reg flash_cs_reg = 1'b1;
    reg flash_mosi_reg = 1'b0;
    wire flash_sck_wire = sck_en ? spi_clk_div[5] : 1'b0;
    wire flash_miso_wire = flash_miso;

    assign flash_cs = flash_cs_reg;
    assign flash_sck = flash_sck_wire;
    assign flash_mosi = flash_mosi_reg;

    wire sck_rise = (spi_clk_div == 6'd31);
    wire sck_fall = (spi_clk_div == 6'd63);

    always @(posedge sys_clk) begin
        spi_clk_div <= spi_clk_div + 1'b1;

        case (phase)
            PH_JEDEC_INIT: begin
                spi_state <= SPI_IDLE;
                spi_clk_div <= 6'd0;
                sck_en <= 1'b0;
                tx_bit_cnt <= 6'd0;
                rx_bit_cnt <= 8'd0;
                spi_tx_shift <= {8'h9F, 24'd0};
                tx_bits <= 8'd8;
                rx_bits <= 8'd24;
                spi_rx_shift <= 128'd0;
                spi_done <= 1'b0;
                flash_cs_reg <= 1'b1;
                flash_mosi_reg <= 1'b0;
                phase <= PH_JEDEC_RUN;
            end

            PH_JEDEC_RUN: begin
                if (spi_done) begin
                    jedec_id <= spi_rx_shift[23:0];
                    phase <= PH_READ_INIT;
                end else if (sck_rise && spi_state == SPI_RX) begin
                    spi_rx_shift <= {spi_rx_shift[126:0], flash_miso_wire};
                end else if (sck_fall) begin
                    case (spi_state)
                        SPI_IDLE: begin
                            flash_cs_reg <= 1'b0;
                            sck_en <= 1'b1;
                            tx_bit_cnt <= 6'd0;
                            rx_bit_cnt <= 8'd0;
                            flash_mosi_reg <= spi_tx_shift[31];
                            spi_state <= SPI_TX;
                        end

                        SPI_TX: begin
                            spi_tx_shift <= {spi_tx_shift[30:0], 1'b0};
                            if (tx_bit_cnt == tx_bits[5:0] - 6'd1) begin
                                tx_bit_cnt <= 6'd0;
                                flash_mosi_reg <= 1'b0;
                                spi_state <= SPI_RX;
                            end else begin
                                tx_bit_cnt <= tx_bit_cnt + 1'b1;
                                flash_mosi_reg <= spi_tx_shift[30];
                            end
                        end

                        SPI_RX: begin
                            if (rx_bit_cnt == rx_bits - 8'd1) begin
                                sck_en <= 1'b0;
                                spi_state <= SPI_FINISH;
                            end else begin
                                rx_bit_cnt <= rx_bit_cnt + 1'b1;
                            end
                        end

                        SPI_FINISH: begin
                            flash_cs_reg <= 1'b1;
                            spi_done <= 1'b1;
                        end

                        default: spi_state <= SPI_IDLE;
                    endcase
                end
            end

            PH_READ_INIT: begin
                spi_state <= SPI_IDLE;
                spi_clk_div <= 6'd0;
                sck_en <= 1'b0;
                tx_bit_cnt <= 6'd0;
                rx_bit_cnt <= 8'd0;
                spi_tx_shift <= {8'h03, RPLU_CFG_BASE};
                tx_bits <= 8'd32;
                rx_bits <= 8'd128;
                spi_rx_shift <= 128'd0;
                spi_done <= 1'b0;
                flash_cs_reg <= 1'b1;
                flash_mosi_reg <= 1'b0;
                phase <= PH_READ_RUN;
            end

            PH_READ_RUN: begin
                if (spi_done) begin
                    first_header <= spi_rx_shift[127:64];
                    first_data <= spi_rx_shift[63:0];
                    phase <= PH_UART_RUN;
                end else if (sck_rise && spi_state == SPI_RX) begin
                    spi_rx_shift <= {spi_rx_shift[126:0], flash_miso_wire};
                end else if (sck_fall) begin
                    case (spi_state)
                        SPI_IDLE: begin
                            flash_cs_reg <= 1'b0;
                            sck_en <= 1'b1;
                            tx_bit_cnt <= 6'd0;
                            rx_bit_cnt <= 8'd0;
                            flash_mosi_reg <= spi_tx_shift[31];
                            spi_state <= SPI_TX;
                        end

                        SPI_TX: begin
                            spi_tx_shift <= {spi_tx_shift[30:0], 1'b0};
                            if (tx_bit_cnt == tx_bits[5:0] - 6'd1) begin
                                tx_bit_cnt <= 6'd0;
                                flash_mosi_reg <= 1'b0;
                                spi_state <= SPI_RX;
                            end else begin
                                tx_bit_cnt <= tx_bit_cnt + 1'b1;
                                flash_mosi_reg <= spi_tx_shift[30];
                            end
                        end

                        SPI_RX: begin
                            if (rx_bit_cnt == rx_bits - 8'd1) begin
                                sck_en <= 1'b0;
                                spi_state <= SPI_FINISH;
                            end else begin
                                rx_bit_cnt <= rx_bit_cnt + 1'b1;
                            end
                        end

                        SPI_FINISH: begin
                            flash_cs_reg <= 1'b1;
                            spi_done <= 1'b1;
                        end

                        default: spi_state <= SPI_IDLE;
                    endcase
                end
            end

            PH_UART_RUN: begin
                flash_cs_reg <= 1'b1;
                sck_en <= 1'b0;
                flash_mosi_reg <= 1'b0;
            end

            default: begin
                phase <= PH_UART_RUN;
            end
        endcase
    end

    localparam integer CLK_FREQ = 50000000;
    localparam integer CLKS_PER_BIT = 434;
    localparam integer START_DELAY = CLK_FREQ / 2;
    localparam integer LINE_PERIOD = CLK_FREQ / 2;
    localparam integer LINE_LAST = 46;

    reg [9:0]  tx_shift = 10'h3FF;
    reg [3:0]  tx_bits_remaining = 4'd0;
    reg [15:0] baud_cnt = 16'd0;
    reg        tx_busy = 1'b0;
    reg [25:0] start_cnt = 26'd0;
    reg        start_ready = 1'b0;
    reg [25:0] line_timer = 26'd0;
    reg        line_active = 1'b0;
    reg [5:0]  msg_idx = 6'd0;

    assign uart_tx = tx_shift[0];
    assign uart_tx_telemetry = tx_shift[0];

    function [7:0] to_hex;
        input [3:0] val;
        begin
            to_hex = (val < 10) ? (8'h30 + val) : (8'h41 + val - 10);
        end
    endfunction

    function [3:0] nibble64;
        input [63:0] value;
        input [3:0] idx;
        begin
            nibble64 = value[(15 - idx) * 4 +: 4];
        end
    endfunction

    function [7:0] msg_byte;
        input [5:0] idx;
        begin
            case (idx)
                6'd0:  msg_byte = "J";
                6'd1:  msg_byte = ":";
                6'd2:  msg_byte = to_hex(jedec_id[23:20]);
                6'd3:  msg_byte = to_hex(jedec_id[19:16]);
                6'd4:  msg_byte = to_hex(jedec_id[15:12]);
                6'd5:  msg_byte = to_hex(jedec_id[11:8]);
                6'd6:  msg_byte = to_hex(jedec_id[7:4]);
                6'd7:  msg_byte = to_hex(jedec_id[3:0]);
                6'd8:  msg_byte = " ";
                6'd9:  msg_byte = "H";
                6'd10: msg_byte = ":";
                6'd11: msg_byte = to_hex(nibble64(first_header, 4'd0));
                6'd12: msg_byte = to_hex(nibble64(first_header, 4'd1));
                6'd13: msg_byte = to_hex(nibble64(first_header, 4'd2));
                6'd14: msg_byte = to_hex(nibble64(first_header, 4'd3));
                6'd15: msg_byte = to_hex(nibble64(first_header, 4'd4));
                6'd16: msg_byte = to_hex(nibble64(first_header, 4'd5));
                6'd17: msg_byte = to_hex(nibble64(first_header, 4'd6));
                6'd18: msg_byte = to_hex(nibble64(first_header, 4'd7));
                6'd19: msg_byte = to_hex(nibble64(first_header, 4'd8));
                6'd20: msg_byte = to_hex(nibble64(first_header, 4'd9));
                6'd21: msg_byte = to_hex(nibble64(first_header, 4'd10));
                6'd22: msg_byte = to_hex(nibble64(first_header, 4'd11));
                6'd23: msg_byte = to_hex(nibble64(first_header, 4'd12));
                6'd24: msg_byte = to_hex(nibble64(first_header, 4'd13));
                6'd25: msg_byte = to_hex(nibble64(first_header, 4'd14));
                6'd26: msg_byte = to_hex(nibble64(first_header, 4'd15));
                6'd27: msg_byte = " ";
                6'd28: msg_byte = "D";
                6'd29: msg_byte = ":";
                6'd30: msg_byte = to_hex(nibble64(first_data, 4'd0));
                6'd31: msg_byte = to_hex(nibble64(first_data, 4'd1));
                6'd32: msg_byte = to_hex(nibble64(first_data, 4'd2));
                6'd33: msg_byte = to_hex(nibble64(first_data, 4'd3));
                6'd34: msg_byte = to_hex(nibble64(first_data, 4'd4));
                6'd35: msg_byte = to_hex(nibble64(first_data, 4'd5));
                6'd36: msg_byte = to_hex(nibble64(first_data, 4'd6));
                6'd37: msg_byte = to_hex(nibble64(first_data, 4'd7));
                6'd38: msg_byte = to_hex(nibble64(first_data, 4'd8));
                6'd39: msg_byte = to_hex(nibble64(first_data, 4'd9));
                6'd40: msg_byte = to_hex(nibble64(first_data, 4'd10));
                6'd41: msg_byte = to_hex(nibble64(first_data, 4'd11));
                6'd42: msg_byte = to_hex(nibble64(first_data, 4'd12));
                6'd43: msg_byte = to_hex(nibble64(first_data, 4'd13));
                6'd44: msg_byte = to_hex(nibble64(first_data, 4'd14));
                6'd45: msg_byte = to_hex(nibble64(first_data, 4'd15));
                default: msg_byte = 8'h0A;
            endcase
        end
    endfunction

    always @(posedge sys_clk) begin
        if (tx_busy) begin
            if (baud_cnt < CLKS_PER_BIT - 1) begin
                baud_cnt <= baud_cnt + 1'b1;
            end else begin
                baud_cnt <= 16'd0;
                tx_shift <= {1'b1, tx_shift[9:1]};
                if (tx_bits_remaining == 4'd1) begin
                    tx_busy <= 1'b0;
                    tx_bits_remaining <= 4'd0;
                    if (msg_idx == LINE_LAST[5:0]) begin
                        msg_idx <= 6'd0;
                        line_active <= 1'b0;
                    end else begin
                        msg_idx <= msg_idx + 1'b1;
                    end
                end else begin
                    tx_bits_remaining <= tx_bits_remaining - 1'b1;
                end
            end
        end else if (line_active) begin
            tx_shift <= {1'b1, msg_byte(msg_idx), 1'b0};
            tx_bits_remaining <= 4'd10;
            baud_cnt <= 16'd0;
            tx_busy <= 1'b1;
        end else if (!start_ready) begin
            tx_shift <= 10'h3FF;
            if (start_cnt < START_DELAY - 1) begin
                start_cnt <= start_cnt + 1'b1;
            end else begin
                start_ready <= 1'b1;
            end
        end else if (line_timer < LINE_PERIOD - 1) begin
            line_timer <= line_timer + 1'b1;
        end else begin
            line_timer <= 26'd0;
            line_active <= 1'b1;
            msg_idx <= 6'd0;
        end
    end
endmodule
