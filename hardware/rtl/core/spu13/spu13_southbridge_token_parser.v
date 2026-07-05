// spu13_southbridge_token_parser.v -- CRC-gated 0xA5 config token parser.
//
// Packet shape:
//   byte 0      token 0xA5
//   byte 1      target/address byte
//   bytes 2..9  64-bit payload, big-endian
//   byte 10     CRC-8 over bytes 0..9
//
// This helper is intentionally narrow. The live SPI slave performs its own
// full HEADER/DATA decode; this parser is a small reusable safety primitive.

module spu13_southbridge_token_parser (
    input           sys_clk,
    input           rst_n,
    input           fifo_valid,
    input  [7:0]    fifo_data_out,
    input  [3:0]    byte_counter,
    input  [7:0]    calculated_crc,

    output reg      config_reg_write,
    output reg      error_flag_out
);

    localparam [1:0] ST_IDLE   = 2'd0;
    localparam [1:0] ST_DATA   = 2'd1;
    localparam [1:0] ST_VERIFY = 2'd2;

    reg [1:0]  state;
    reg [7:0]  timeout_cnt;
    reg [87:0] shift_reg;

    always @(posedge sys_clk or negedge rst_n) begin
        if (!rst_n) begin
            state            <= ST_IDLE;
            timeout_cnt      <= 8'd0;
            shift_reg        <= 88'd0;
            config_reg_write <= 1'b0;
            error_flag_out   <= 1'b0;
        end else begin
            config_reg_write <= 1'b0;
            error_flag_out   <= 1'b0;

            case (state)
                ST_IDLE: begin
                    timeout_cnt <= 8'd0;
                    if (fifo_valid && fifo_data_out == 8'hA5) begin
                        shift_reg <= {8'hA5, 80'd0};
                        state     <= ST_DATA;
                    end
                end

                ST_DATA: begin
                    if (fifo_valid) begin
                        timeout_cnt <= 8'd0;
                        if (byte_counter < 4'd10) begin
                            shift_reg[79 - byte_counter*8 -: 8] <= fifo_data_out;
                            if (byte_counter == 4'd9)
                                state <= ST_VERIFY;
                        end else begin
                            error_flag_out <= 1'b1;
                            state <= ST_IDLE;
                        end
                    end else if (timeout_cnt >= 8'd16) begin
                        state <= ST_IDLE;
                    end else begin
                        timeout_cnt <= timeout_cnt + 8'd1;
                    end
                end

                ST_VERIFY: begin
                    if (calculated_crc == shift_reg[7:0])
                        config_reg_write <= 1'b1;
                    else
                        error_flag_out <= 1'b1;
                    state <= ST_IDLE;
                end

                default: state <= ST_IDLE;
            endcase
        end
    end

endmodule
