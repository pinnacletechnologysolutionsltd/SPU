// hw/core/spu_whisper_sane.v - The Voice of Coherency
// Objective: Periodically send "SANE\n" via UART when the manifold is laminar.
// Result: Real-time confirmation of the 'Wolfram' observer shift.

module spu_whisper_sane #(
    parameter CLK_HZ = 12000000,
    parameter BAUD   = 115200
)(
    input  wire clk,
    input  wire rst_n,
    input  wire is_laminar,
    output reg  tx_pin
);
    localparam BIT_CYCLES = CLK_HZ / BAUD;
    
    // "SANE\n" encoded as [Start Bit][Data][Stop Bit]
    // Hex: 53 (S), 41 (A), 4E (N), 45 (E), 0A (\n)
    reg [7:0] message [0:4];
    initial begin
        message[0] = 8'h53; // S
        message[1] = 8'h41; // A
        message[2] = 8'h4E; // N
        message[3] = 8'h45; // E
        message[4] = 8'h0A; // \n
    end

    reg [23:0] interval_cnt;
    reg [2:0]  char_index;
    reg [3:0]  bit_index;
    reg [15:0] cycle_cnt;
    reg [9:0]  shift_reg;
    reg        busy;

    initial tx_pin = 1'b1;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            tx_pin <= 1'b1;
            interval_cnt <= 0;
            char_index <= 0;
            bit_index <= 0;
            cycle_cnt <= 0;
            busy <= 0;
        end else begin
            if (!busy) begin
                if (is_laminar) begin
                    if (interval_cnt == CLK_HZ) begin // Send every 1 second
                        interval_cnt <= 0;
                        char_index <= 0;
                        bit_index <= 10;
                        shift_reg <= {1'b1, message[0], 1'b0};
                        busy <= 1;
                    end else begin
                        interval_cnt <= interval_cnt + 1;
                    end
                end
            end else begin
                if (cycle_cnt < BIT_CYCLES - 1) begin
                    cycle_cnt <= cycle_cnt + 1;
                end else begin
                    cycle_cnt <= 0;
                    if (bit_index > 0) begin
                        tx_pin <= shift_reg[0];
                        shift_reg <= {1'b1, shift_reg[9:1]};
                        bit_index <= bit_index - 1;
                    end else if (char_index < 4) begin
                        char_index <= char_index + 1;
                        shift_reg <= {1'b1, message[char_index + 1], 1'b0};
                        bit_index <= 10;
                    end else begin
                        busy <= 0;
                        tx_pin <= 1'b1;
                    end
                end
            end
        end
    end

endmodule
