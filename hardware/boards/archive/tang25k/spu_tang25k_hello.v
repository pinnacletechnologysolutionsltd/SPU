`timescale 1ns / 1ps

module spu_tang25k_hello #(
    parameter CLK_FREQ = 50000000,
    parameter BAUD_RATE = 921600
)(
    input  wire        clk,
    output reg         uart_tx
);

    localparam BAUD_DIV = CLK_FREQ / BAUD_RATE;
    localparam MSG_LEN = 16;
    
    function [7:0] get_char(input [3:0] pos);
        case (pos)
            4'h0: get_char = "S";
            4'h1: get_char = "P";
            4'h2: get_char = "U";
            4'h3: get_char = "-";
            4'h4: get_char = "1";
            4'h5: get_char = "3";
            4'h6: get_char = " ";
            4'h7: get_char = "O";
            4'h8: get_char = "N";
            4'h9: get_char = "L";
            4'hA: get_char = "I";
            4'hB: get_char = "N";
            4'hC: get_char = "E";
            4'hD: get_char = " ";
            4'hE: get_char = "!";
            4'hF: get_char = " ";
            default: get_char = " ";
        endcase
    endfunction

    reg [31:0] baud_cnt = 0; // Initialize for no explicit reset
    reg [3:0]  bit_cnt = 0;  // Initialize for no explicit reset
    reg [3:0]  char_pos = 0; // Initialize for no explicit reset
    reg [9:0]  shift_reg = 10'h3FF; // Initialize for no explicit reset
    reg [1:0]  state = IDLE; // Initialize for no explicit reset

    always @(posedge clk) begin
        case (state)
                IDLE: begin
                    uart_tx <= 1'b1;
                    char_pos <= 0;
                    state <= LOAD;
                end
                
                LOAD: begin
                    shift_reg <= {1'b1, get_char(char_pos), 1'b0};
                    bit_cnt <= 0;
                    baud_cnt <= 0;
                    state <= SHIFT;
                end
                
                SHIFT: begin
                    if (baud_cnt < BAUD_DIV - 1) begin
                        baud_cnt <= baud_cnt + 1;
                    end else begin
                        baud_cnt <= 0;
                        uart_tx <= shift_reg[0];
                        shift_reg <= {1'b1, shift_reg[9:1]};
                        if (bit_cnt < 9) begin
                            bit_cnt <= bit_cnt + 1;
                        end else begin
                            if (char_pos < MSG_LEN - 1) begin
                                char_pos <= char_pos + 1;
                                state <= LOAD;
                            end else begin
                                state <= WAIT;
                                baud_cnt <= 0;
                            end
                        end
                    end
                end
                
                WAIT: begin
                    if (baud_cnt < CLK_FREQ) begin
                        baud_cnt <= baud_cnt + 1;
                    end else begin
                        state <= IDLE;
                    end
                end
            endcase
        end
    end

endmodule
