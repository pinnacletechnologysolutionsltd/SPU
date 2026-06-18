module spu_tang25k_flash_probe(
    input  wire sys_clk,
    output wire [2:0] led,
    output wire uart_tx,
    output wire uart_tx_telemetry,
    output reg  flash_cs,
    output wire flash_sck,
    output reg  flash_mosi,
    input  wire flash_miso
);
    reg [25:0] counter = 0;
    always @(posedge sys_clk) counter <= counter + 1'b1;

    assign led[0] = counter[24];
    assign led[1] = counter[23];
    assign led[2] = counter[22];

    localparam SPI_IDLE   = 3'd0;
    localparam SPI_CMD    = 3'd1;
    localparam SPI_READ   = 3'd2;
    localparam SPI_FINISH = 3'd3;

    reg [2:0]  spi_state = SPI_IDLE;
    reg [5:0]  spi_clk_div = 0;
    reg        sck_en = 0;
    reg [4:0]  spi_bit_cnt = 0;
    reg [7:0]  spi_cmd = 8'h9F;
    reg [23:0] spi_shift_in = 24'h000000;
    reg [23:0] jedec_id = 24'hFFFFFF;
    reg        spi_done = 0;

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

    parameter CLK_FREQ = 50000000;
    parameter BAUD_RATE = 115200;
    parameter CLKS_PER_BIT = CLK_FREQ / BAUD_RATE;

    reg [8:0] tx_data = 0;
    reg [3:0] tx_bit_cnt = 0;
    reg [15:0] tx_clk_cnt = 0;
    reg tx_busy = 0;
    reg tx_out = 1;

    assign uart_tx = tx_out;
    assign uart_tx_telemetry = tx_out;

    function [7:0] to_hex;
        input [3:0] val;
        begin
            to_hex = (val < 10) ? (8'h30 + val) : (8'h41 + val - 10);
        end
    endfunction

    reg [7:0] message [0:13];
    reg [3:0] msg_idx = 0;
    reg [24:0] send_timer = 0;

    always @(posedge sys_clk) begin
        message[0] = "J";
        message[1] = "E";
        message[2] = "D";
        message[3] = "E";
        message[4] = "C";
        message[5] = ":";
        message[6] = " ";
        message[7] = to_hex(jedec_id[23:20]);
        message[8] = to_hex(jedec_id[19:16]);
        message[9] = to_hex(jedec_id[15:12]);
        message[10] = to_hex(jedec_id[11:8]);
        message[11] = to_hex(jedec_id[7:4]);
        message[12] = to_hex(jedec_id[3:0]);
        message[13] = 8'h0A;

        if (!tx_busy && spi_done) begin
            send_timer <= send_timer + 1'b1;
            if (send_timer == 25'd10000000) begin
                send_timer <= 0;
                tx_data <= {1'b1, message[msg_idx]};
                tx_busy <= 1'b1;
                tx_bit_cnt <= 0;
                tx_clk_cnt <= 0;
                tx_out <= 1'b0;

                if (msg_idx == 4'd13)
                    msg_idx <= 0;
                else
                    msg_idx <= msg_idx + 1'b1;
            end else begin
                tx_out <= 1'b1;
            end
        end else if (tx_busy) begin
            if (tx_clk_cnt < CLKS_PER_BIT - 1) begin
                tx_clk_cnt <= tx_clk_cnt + 1'b1;
            end else begin
                tx_clk_cnt <= 0;
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
