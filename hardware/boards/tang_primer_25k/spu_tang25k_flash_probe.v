// spu_tang25k_flash_probe.v -- Minimal PMOD J4 SPI flash JEDEC probe.
// Reads command 0x9F once and prints "JEDEC: xxxxxx" on both UART pins.
module spu_tang25k_flash_probe (
    input  wire sys_clk,
    output wire uart_tx,
    output wire uart_tx_telemetry,
    output reg  flash_cs,
    output wire flash_sck,
    output reg  flash_mosi,
    input  wire flash_miso
);
    reg [25:0] counter = 26'd0;
    always @(posedge sys_clk) counter <= counter + 1'b1;

    localparam SPI_IDLE   = 3'd0;
    localparam SPI_CMD    = 3'd1;
    localparam SPI_READ   = 3'd2;
    localparam SPI_FINISH = 3'd3;

    reg [2:0]  spi_state = SPI_IDLE;
    reg [5:0]  spi_clk_div = 6'd0;
    reg        sck_en = 1'b0;
    reg [4:0]  spi_bit_cnt = 5'd0;
    reg [7:0]  spi_cmd = 8'h9F;
    reg [23:0] spi_shift_in = 24'h000000;
    reg [23:0] jedec_id = 24'hFFFFFF;
    reg        spi_done = 1'b0;

    assign flash_sck = sck_en ? spi_clk_div[5] : 1'b0;
    wire sck_rise = (spi_clk_div == 6'd31);
    wire sck_fall = (spi_clk_div == 6'd63);

    initial begin
        flash_cs = 1'b1;
        flash_mosi = 1'b0;
    end

    always @(posedge sys_clk) begin
        if (!spi_done) begin
            spi_clk_div <= spi_clk_div + 1'b1;

            if (sck_fall) begin
                case (spi_state)
                    SPI_IDLE: begin
                        flash_cs <= 1'b0;
                        sck_en <= 1'b1;
                        spi_bit_cnt <= 5'd0;
                        flash_mosi <= spi_cmd[7];
                        spi_state <= SPI_CMD;
                    end

                    SPI_CMD: begin
                        spi_cmd <= {spi_cmd[6:0], 1'b0};
                        if (spi_bit_cnt == 5'd7) begin
                            spi_bit_cnt <= 5'd0;
                            flash_mosi <= 1'b0;
                            spi_state <= SPI_READ;
                        end else begin
                            spi_bit_cnt <= spi_bit_cnt + 1'b1;
                            flash_mosi <= spi_cmd[6];
                        end
                    end

                    SPI_READ: begin
                        if (spi_bit_cnt == 5'd23) begin
                            sck_en <= 1'b0;
                            spi_state <= SPI_FINISH;
                        end else begin
                            spi_bit_cnt <= spi_bit_cnt + 1'b1;
                        end
                    end

                    SPI_FINISH: begin
                        flash_cs <= 1'b1;
                        spi_done <= 1'b1;
                        jedec_id <= spi_shift_in;
                    end

                    default: spi_state <= SPI_IDLE;
                endcase
            end else if (sck_rise && spi_state == SPI_READ) begin
                spi_shift_in <= {spi_shift_in[22:0], flash_miso};
            end
        end
    end

    localparam integer CLK_FREQ = 50000000;
    localparam integer BAUD_RATE = 115200;
    localparam integer CLKS_PER_BIT = CLK_FREQ / BAUD_RATE;

    reg [8:0]  tx_data = 9'd0;
    reg [3:0]  tx_bit_cnt = 4'd0;
    reg [15:0] tx_clk_cnt = 16'd0;
    reg        tx_busy = 1'b0;
    reg        tx_out = 1'b1;

    assign uart_tx = tx_out;
    assign uart_tx_telemetry = tx_out;

    function [7:0] to_hex;
        input [3:0] val;
        begin
            to_hex = (val < 10) ? (8'h30 + val) : (8'h41 + val - 10);
        end
    endfunction

    function [7:0] message_char;
        input [3:0] idx;
        begin
            case (idx)
                4'd0:  message_char = "J";
                4'd1:  message_char = "E";
                4'd2:  message_char = "D";
                4'd3:  message_char = "E";
                4'd4:  message_char = "C";
                4'd5:  message_char = ":";
                4'd6:  message_char = " ";
                4'd7:  message_char = to_hex(jedec_id[23:20]);
                4'd8:  message_char = to_hex(jedec_id[19:16]);
                4'd9:  message_char = to_hex(jedec_id[15:12]);
                4'd10: message_char = to_hex(jedec_id[11:8]);
                4'd11: message_char = to_hex(jedec_id[7:4]);
                4'd12: message_char = to_hex(jedec_id[3:0]);
                4'd13: message_char = 8'h0A;
                default: message_char = 8'h20;
            endcase
        end
    endfunction

    reg [3:0] msg_idx = 4'd0;
    reg [24:0] send_timer = 25'd0;

    always @(posedge sys_clk) begin
        if (!tx_busy && spi_done) begin
            send_timer <= send_timer + 1'b1;
            if (send_timer == 25'd10000000) begin
                send_timer <= 25'd0;
                tx_data <= {1'b1, message_char(msg_idx)};
                tx_busy <= 1'b1;
                tx_bit_cnt <= 4'd0;
                tx_clk_cnt <= 16'd0;
                tx_out <= 1'b0;

                if (msg_idx == 4'd13)
                    msg_idx <= 4'd0;
                else
                    msg_idx <= msg_idx + 1'b1;
            end else begin
                tx_out <= 1'b1;
            end
        end else if (tx_busy) begin
            if (tx_clk_cnt < CLKS_PER_BIT - 1) begin
                tx_clk_cnt <= tx_clk_cnt + 1'b1;
            end else begin
                tx_clk_cnt <= 16'd0;
                if (tx_bit_cnt < 4'd9) begin
                    tx_out <= tx_data[0];
                    tx_data <= {1'b1, tx_data[8:1]};
                    tx_bit_cnt <= tx_bit_cnt + 1'b1;
                end else begin
                    tx_busy <= 1'b0;
                    tx_out <= 1'b1;
                end
            end
        end
    end
endmodule
