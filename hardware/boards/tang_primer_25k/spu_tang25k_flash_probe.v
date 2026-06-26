// spu_tang25k_flash_probe.v — Minimal SPI flash JEDEC probe
// Reads the flash JEDEC ID and prints over UART at 115200 baud.
// Assumes 50 MHz sys_clk — divides down for SPI ~1 MHz and UART.
module spu_tang25k_flash_probe (
    input  wire clk,
    output reg  led,
    output reg  flash_cs,
    output reg  flash_sck,
    output reg  flash_mosi,
    input  wire flash_miso,
    output reg  uart_tx
);

reg rst_n;
reg [31:0] counter;
reg [7:0]  state;
reg [5:0]  bit_count;
reg [31:0] shift_reg;

localparam UART_BIT = 434; // 50 MHz / 115200

reg [7:0]  tx_byte;
reg [3:0]  tx_bit;
reg        tx_active;
reg [31:0] jedec_id;

always @(posedge clk) begin
    if (counter < 50) rst_n <= 0; else rst_n <= 1;
end

always @(posedge clk) begin
    if (!rst_n) begin
        counter <= 0;
        state <= 0;
        flash_cs <= 1;
        flash_sck <= 0;
        flash_mosi <= 0;
        uart_tx <= 1;
        tx_active <= 0;
        jedec_id <= 0;
        led <= 0;
    end else begin
        counter <= counter + 1;

        case (state)
            0: begin
                if (counter > 5000) begin
                    flash_cs <= 0;
                    state <= 1;
                    counter <= 0;
                    bit_count <= 0;
                    shift_reg <= {8'h9F, 24'd0}; // JEDEC ID command
                end
            end
            1: begin // SPI transaction: 8 cmd + 24 dummy + 24 response
                if (counter[5:0] == 0) begin // SCK toggle
                    flash_sck <= ~flash_sck;
                    if (flash_sck) begin
                        shift_reg <= {shift_reg[30:0], flash_miso};
                        bit_count <= bit_count + 1;
                        if (bit_count >= 55) begin // 8+24+24-1
                            flash_sck <= 0;
                            flash_cs <= 1;
                            jedec_id <= shift_reg[23:0];
                            state <= 2;
                            counter <= 0;
                        end
                    end else begin
                        flash_mosi <= shift_reg[31];
                    end
                end
            end
            2: begin // Print JEDEC over UART
                if (!tx_active) begin
                    tx_byte <= jedec_id[23:16];
                    tx_bit <= 0;
                    tx_active <= 1;
                    uart_tx <= 0;
                    counter <= 0;
                end else begin
                    if (counter >= UART_BIT) begin
                        counter <= 0;
                        if (tx_bit < 8) begin
                            uart_tx <= tx_byte[tx_bit];
                            tx_bit <= tx_bit + 1;
                        end else if (tx_bit == 8) begin
                            uart_tx <= 1;
                            tx_bit <= tx_bit + 1;
                        end else begin
                            tx_active <= 0;
                            if (jedec_id[7:0] == 0) begin
                                led <= ~led;
                                state <= 0;
                                counter <= 0;
                            end else begin
                                // Print next byte
                                jedec_id <= {jedec_id[15:0], 8'd0};
                            end
                        end
                    end
                end
            end
        endcase
    end
end
endmodule
