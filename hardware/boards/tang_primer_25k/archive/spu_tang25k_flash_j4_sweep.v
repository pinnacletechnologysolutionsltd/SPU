module spu_tang25k_flash_j4_sweep(
    input  wire       sys_clk,
    output wire [2:0] led,
    output wire       uart_tx,
    output wire       uart_tx_telemetry,
    inout  wire [3:0] j4
);
    reg [25:0] counter = 0;
    always @(posedge sys_clk) counter <= counter + 1'b1;

    assign led[0] = counter[24];
    assign led[1] = counter[23];
    assign led[2] = counter[22];

    localparam PH_SPI_INIT = 2'd0;
    localparam PH_SPI_RUN  = 2'd1;
    localparam PH_UART_RUN = 2'd2;
    localparam PH_NEXT     = 2'd3;

    localparam SPI_IDLE   = 3'd0;
    localparam SPI_CMD    = 3'd1;
    localparam SPI_READ   = 3'd2;
    localparam SPI_FINISH = 3'd3;

    reg [1:0] phase = PH_SPI_INIT;
    reg [4:0] mapping_idx = 0;

    reg [2:0] spi_state = SPI_IDLE;
    reg [5:0] spi_clk_div = 0;
    reg       sck_en = 0;
    reg [4:0] spi_bit_cnt = 0;
    reg [7:0] spi_cmd = 8'h9F;
    reg [23:0] spi_shift_in = 24'h000000;
    reg [23:0] jedec_id = 24'hFFFFFF;
    reg       spi_done = 0;
    reg       flash_cs_reg = 1'b1;
    reg       flash_mosi_reg = 1'b0;

    reg [1:0] cs_idx;
    reg [1:0] sck_idx;
    reg [1:0] mosi_idx;
    reg [1:0] miso_idx;

    reg [3:0] j4_out;
    reg [3:0] j4_oe;
    wire [3:0] j4_in = j4;
    wire       flash_sck_wire = sck_en ? spi_clk_div[5] : 1'b0;
    wire       flash_miso_wire = j4_in[miso_idx];

    genvar i;
    generate
        for (i = 0; i < 4; i = i + 1) begin : gen_j4_buf
            assign j4[i] = j4_oe[i] ? j4_out[i] : 1'bz;
        end
    endgenerate

    always @(*) begin
        case (mapping_idx)
            5'd0:  begin cs_idx = 2'd0; sck_idx = 2'd1; mosi_idx = 2'd2; miso_idx = 2'd3; end
            5'd1:  begin cs_idx = 2'd0; sck_idx = 2'd1; mosi_idx = 2'd3; miso_idx = 2'd2; end
            5'd2:  begin cs_idx = 2'd0; sck_idx = 2'd2; mosi_idx = 2'd1; miso_idx = 2'd3; end
            5'd3:  begin cs_idx = 2'd0; sck_idx = 2'd2; mosi_idx = 2'd3; miso_idx = 2'd1; end
            5'd4:  begin cs_idx = 2'd0; sck_idx = 2'd3; mosi_idx = 2'd1; miso_idx = 2'd2; end
            5'd5:  begin cs_idx = 2'd0; sck_idx = 2'd3; mosi_idx = 2'd2; miso_idx = 2'd1; end
            5'd6:  begin cs_idx = 2'd1; sck_idx = 2'd0; mosi_idx = 2'd2; miso_idx = 2'd3; end
            5'd7:  begin cs_idx = 2'd1; sck_idx = 2'd0; mosi_idx = 2'd3; miso_idx = 2'd2; end
            5'd8:  begin cs_idx = 2'd1; sck_idx = 2'd2; mosi_idx = 2'd0; miso_idx = 2'd3; end
            5'd9:  begin cs_idx = 2'd1; sck_idx = 2'd2; mosi_idx = 2'd3; miso_idx = 2'd0; end
            5'd10: begin cs_idx = 2'd1; sck_idx = 2'd3; mosi_idx = 2'd0; miso_idx = 2'd2; end
            5'd11: begin cs_idx = 2'd1; sck_idx = 2'd3; mosi_idx = 2'd2; miso_idx = 2'd0; end
            5'd12: begin cs_idx = 2'd2; sck_idx = 2'd0; mosi_idx = 2'd1; miso_idx = 2'd3; end
            5'd13: begin cs_idx = 2'd2; sck_idx = 2'd0; mosi_idx = 2'd3; miso_idx = 2'd1; end
            5'd14: begin cs_idx = 2'd2; sck_idx = 2'd1; mosi_idx = 2'd0; miso_idx = 2'd3; end
            5'd15: begin cs_idx = 2'd2; sck_idx = 2'd1; mosi_idx = 2'd3; miso_idx = 2'd0; end
            5'd16: begin cs_idx = 2'd2; sck_idx = 2'd3; mosi_idx = 2'd0; miso_idx = 2'd1; end
            5'd17: begin cs_idx = 2'd2; sck_idx = 2'd3; mosi_idx = 2'd1; miso_idx = 2'd0; end
            5'd18: begin cs_idx = 2'd3; sck_idx = 2'd0; mosi_idx = 2'd1; miso_idx = 2'd2; end
            5'd19: begin cs_idx = 2'd3; sck_idx = 2'd0; mosi_idx = 2'd2; miso_idx = 2'd1; end
            5'd20: begin cs_idx = 2'd3; sck_idx = 2'd1; mosi_idx = 2'd0; miso_idx = 2'd2; end
            5'd21: begin cs_idx = 2'd3; sck_idx = 2'd1; mosi_idx = 2'd2; miso_idx = 2'd0; end
            5'd22: begin cs_idx = 2'd3; sck_idx = 2'd2; mosi_idx = 2'd0; miso_idx = 2'd1; end
            default: begin cs_idx = 2'd3; sck_idx = 2'd2; mosi_idx = 2'd1; miso_idx = 2'd0; end
        endcase
    end

    always @(*) begin
        j4_out = 4'b0000;
        j4_oe  = 4'b0000;
        j4_oe[cs_idx]   = 1'b1;
        j4_oe[sck_idx]  = 1'b1;
        j4_oe[mosi_idx] = 1'b1;
        j4_out[cs_idx]   = flash_cs_reg;
        j4_out[sck_idx]  = flash_sck_wire;
        j4_out[mosi_idx] = flash_mosi_reg;
    end

    wire sck_rise = (spi_clk_div == 6'd31);
    wire sck_fall = (spi_clk_div == 6'd63);

    parameter CLK_FREQ = 50000000;
    parameter BAUD_RATE = 115200;
    parameter CLKS_PER_BIT = CLK_FREQ / BAUD_RATE;

    reg [8:0] tx_data = 0;
    reg [3:0] tx_bit_cnt = 0;
    reg [15:0] tx_clk_cnt = 0;
    reg tx_busy = 0;
    reg tx_out = 1;
    reg [3:0] char_idx = 0;
    reg last_char = 0;

    assign uart_tx = tx_out;
    assign uart_tx_telemetry = tx_out;

    function [7:0] to_hex;
        input [3:0] val;
        begin
            to_hex = (val < 10) ? (8'h30 + val) : (8'h41 + val - 10);
        end
    endfunction

    function [7:0] line_char;
        input [3:0] idx;
        input [4:0] map_idx;
        input [23:0] id;
        begin
            case (idx)
                4'd0: line_char = "M";
                4'd1: line_char = to_hex({3'b000, map_idx[4]});
                4'd2: line_char = to_hex(map_idx[3:0]);
                4'd3: line_char = ":";
                4'd4: line_char = to_hex(id[23:20]);
                4'd5: line_char = to_hex(id[19:16]);
                4'd6: line_char = to_hex(id[15:12]);
                4'd7: line_char = to_hex(id[11:8]);
                4'd8: line_char = to_hex(id[7:4]);
                4'd9: line_char = to_hex(id[3:0]);
                default: line_char = 8'h0A;
            endcase
        end
    endfunction

    always @(posedge sys_clk) begin
        spi_clk_div <= spi_clk_div + 1'b1;

        case (phase)
            PH_SPI_INIT: begin
                spi_state <= SPI_IDLE;
                sck_en <= 1'b0;
                spi_bit_cnt <= 5'd0;
                spi_cmd <= 8'h9F;
                spi_shift_in <= 24'h000000;
                spi_done <= 1'b0;
                flash_cs_reg <= 1'b1;
                flash_mosi_reg <= 1'b0;
                phase <= PH_SPI_RUN;
            end

            PH_SPI_RUN: begin
                if (!spi_done) begin
                    if (sck_fall) begin
                        case (spi_state)
                            SPI_IDLE: begin
                                flash_cs_reg <= 1'b0;
                                sck_en <= 1'b1;
                                spi_bit_cnt <= 5'd0;
                                flash_mosi_reg <= spi_cmd[7];
                                spi_state <= SPI_CMD;
                            end
                            SPI_CMD: begin
                                spi_cmd <= {spi_cmd[6:0], 1'b0};
                                if (spi_bit_cnt == 5'd7) begin
                                    spi_bit_cnt <= 5'd0;
                                    flash_mosi_reg <= 1'b0;
                                    spi_state <= SPI_READ;
                                end else begin
                                    spi_bit_cnt <= spi_bit_cnt + 1'b1;
                                    flash_mosi_reg <= spi_cmd[6];
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
                                flash_cs_reg <= 1'b1;
                                spi_done <= 1'b1;
                                jedec_id <= spi_shift_in;
                                char_idx <= 4'd0;
                                last_char <= 1'b0;
                                phase <= PH_UART_RUN;
                            end
                            default: spi_state <= SPI_IDLE;
                        endcase
                    end else if (sck_rise && spi_state == SPI_READ) begin
                        spi_shift_in <= {spi_shift_in[22:0], flash_miso_wire};
                    end
                end
            end

            PH_UART_RUN: begin
                if (!tx_busy) begin
                    tx_data <= {1'b1, line_char(char_idx, mapping_idx, jedec_id)};
                    tx_busy <= 1'b1;
                    tx_bit_cnt <= 4'd0;
                    tx_clk_cnt <= 16'd0;
                    tx_out <= 1'b0;
                    last_char <= (char_idx == 4'd10);
                end else begin
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
                            if (last_char)
                                phase <= PH_NEXT;
                            else
                                char_idx <= char_idx + 1'b1;
                        end
                    end
                end
            end

            PH_NEXT: begin
                if (mapping_idx == 5'd23)
                    mapping_idx <= 5'd0;
                else
                    mapping_idx <= mapping_idx + 1'b1;
                phase <= PH_SPI_INIT;
            end
        endcase
    end
endmodule
