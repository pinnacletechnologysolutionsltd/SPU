`timescale 1ns / 1ps

// uart_debug_tx.v — small debug UART transmitter (sends boot head words on trigger)
// - Operates in the fast clock domain (clk_fast).
// - On rising trigger, emits: '>' + 6 hex chars of word0 + ' ' + 6 hex chars of word1 + LF

module uart_debug_tx #(
    parameter BAUD_DIV = 26 // nominal divider for clk_fast -> ~921k at 24MHz (tune if clk differs)
)(
    input  wire        clk,
    input  wire        rst_n,
    input  wire        trigger,     // rising-edge triggers a frame
    input  wire [23:0] word0,
    input  wire [23:0] word1,
    output reg         uart_tx
);

// simple nibble -> ASCII hex helper
function [7:0] nib2asc;
    input [3:0] n;
    begin
        case (n)
            4'h0: nib2asc = "0";
            4'h1: nib2asc = "1";
            4'h2: nib2asc = "2";
            4'h3: nib2asc = "3";
            4'h4: nib2asc = "4";
            4'h5: nib2asc = "5";
            4'h6: nib2asc = "6";
            4'h7: nib2asc = "7";
            4'h8: nib2asc = "8";
            4'h9: nib2asc = "9";
            4'ha: nib2asc = "A";
            4'hb: nib2asc = "B";
            4'hc: nib2asc = "C";
            4'hd: nib2asc = "D";
            4'he: nib2asc = "E";
            4'hf: nib2asc = "F";
        endcase
    end
endfunction

// TX buffer (small, static)
reg [7:0] tx_buf [0:31];
reg [5:0] tx_len;
reg [5:0] tx_pos;
reg       sending;

// shift register for serial bits (start,8 data,stop) LSB-first
reg [9:0] shift_reg;
reg [3:0] bits_rem;

// Baud counter
reg [31:0] baud_cnt;
wire baud_tick;
assign baud_tick = (baud_cnt == (BAUD_DIV-1));

// trigger edge detect
reg trigger_r;

integer i;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        uart_tx <= 1'b1;
        baud_cnt <= 0;
        sending <= 1'b0;
        tx_len <= 0;
        tx_pos <= 0;
        shift_reg <= 10'h3FF;
        bits_rem <= 0;
        trigger_r <= 1'b0;
        for (i = 0; i < 32; i = i + 1) tx_buf[i] <= 8'h00;
    end else begin
        // update baud counter
        if (baud_tick) baud_cnt <= 0; else baud_cnt <= baud_cnt + 1;

        trigger_r <= trigger;

        // start frame on rising edge of trigger and if idle
        if (!sending && trigger && !trigger_r) begin
            // build frame: '>' + WORD0(6 hex) + ' ' + WORD1(6 hex) + '\n'
            tx_buf[0] <= 8'h3E; // '>'
            // word0: 24 bits -> 6 nibbles
            tx_buf[1] <= nib2asc(word0[23:20]);
            tx_buf[2] <= nib2asc(word0[19:16]);
            tx_buf[3] <= nib2asc(word0[15:12]);
            tx_buf[4] <= nib2asc(word0[11:8]);
            tx_buf[5] <= nib2asc(word0[7:4]);
            tx_buf[6] <= nib2asc(word0[3:0]);
            tx_buf[7] <= 8'h20; // space
            tx_buf[8] <= nib2asc(word1[23:20]);
            tx_buf[9] <= nib2asc(word1[19:16]);
            tx_buf[10] <= nib2asc(word1[15:12]);
            tx_buf[11] <= nib2asc(word1[11:8]);
            tx_buf[12] <= nib2asc(word1[7:4]);
            tx_buf[13] <= nib2asc(word1[3:0]);
            tx_buf[14] <= 8'h0A; // LF
            tx_len <= 15;
            tx_pos <= 0;
            sending <= 1'b1;
            // ensure next phase starts clean
            bits_rem <= 0;
        end

        // UART transmit engine: on baud_tick shift bits
        if (sending && baud_tick) begin
            if (bits_rem == 0) begin
                if (tx_pos < tx_len) begin
                    // load next byte into shift register: {stop, data[7:0], start}
                    shift_reg <= {1'b1, tx_buf[tx_pos], 1'b0};
                    bits_rem <= 10;
                    tx_pos <= tx_pos; // keep pos until byte done
                end else begin
                    // finished sending
                    sending <= 1'b0;
                    uart_tx <= 1'b1;
                end
            end else begin
                // output LSB
                uart_tx <= shift_reg[0];
                shift_reg <= shift_reg >> 1;
                bits_rem <= bits_rem - 1;
                if (bits_rem == 1) begin
                    // this was last bit of this byte — advance position next tick
                    tx_pos <= tx_pos + 1;
                end
            end
        end
    end
end

endmodule
