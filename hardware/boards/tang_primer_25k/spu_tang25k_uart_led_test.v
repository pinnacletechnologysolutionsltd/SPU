module spu_tang25k_uart_led_test(
    input  wire sys_clk,
    output wire [2:0] led,
    output wire uart_tx,
    output wire uart_tx_telemetry,
    
    // SPI Flash Interface
    output reg  flash_cs,
    output wire flash_sck,
    output reg  flash_mosi,
    input  wire flash_miso
);
    // 50 MHz clock
    reg [25:0] counter = 0;
    always @(posedge sys_clk) counter <= counter + 1;
    
    assign led[0] = counter[24];
    assign led[1] = counter[23];
    assign led[2] = counter[22];
    
    // SPI Flash Reader State Machine
    // Read 4 bytes from address 0x100100 (Golden Primes)
    reg [5:0] spi_state = 0;
    reg [7:0] spi_bit_cnt = 0;
    reg [31:0] spi_shift_out = {8'h03, 24'h100106}; // Command 0x03, Addr 0x100106 (Skip zeros)
    reg [31:0] spi_shift_in = 0;
    reg [31:0] read_data = 32'hDEADBEEF; // Default if not read
    reg spi_done = 0;
    
    // Generate ~780 kHz SPI Clock from 50 MHz
    reg [5:0] sck_div = 0;
    reg sck_en = 0;
    assign flash_sck = (sck_en) ? sck_div[5] : 1'b0; // SPI Mode 0: idle low, rise in middle
    
    wire sck_rise = (sck_div == 6'd31);
    wire sck_fall = (sck_div == 6'd63);
    
    initial flash_cs = 1'b1;
    initial flash_mosi = 1'b0;
    
    always @(posedge sys_clk) begin
        if (!spi_done) begin
            sck_div <= sck_div + 1;
            
            if (sck_fall) begin
                if (spi_state == 0) begin
                    flash_cs <= 0;
                    spi_state <= 1;
                    spi_bit_cnt <= 0;
                    sck_en <= 1;
                    flash_mosi <= spi_shift_out[31];
                end else if (spi_state == 1) begin
                    // Transmit Command + Addr (32 bits)
                    spi_shift_out <= {spi_shift_out[30:0], 1'b0};
                    if (spi_bit_cnt == 31) begin
                        spi_state <= 2;
                        spi_bit_cnt <= 0;
                        flash_mosi <= 0;
                    end else begin
                        spi_bit_cnt <= spi_bit_cnt + 1;
                        flash_mosi <= spi_shift_out[30];
                    end
                end else if (spi_state == 2) begin
                    // Receive Data (32 bits)
                    if (spi_bit_cnt == 31) begin
                        spi_state <= 3;
                        sck_en <= 0;
                    end else begin
                        spi_bit_cnt <= spi_bit_cnt + 1;
                    end
                end else if (spi_state == 3) begin
                    flash_cs <= 1;
                    spi_done <= 1;
                    read_data <= spi_shift_in;
                end
            end else if (sck_rise) begin
                if (spi_state == 2) begin
                    spi_shift_in <= {spi_shift_in[30:0], flash_miso};
                end
            end
        end
    end
    
    // Simple UART TX (115200 baud)
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
    
    // Convert read_data to Hex String
    function [7:0] to_hex;
        input [3:0] val;
        begin
            to_hex = (val < 10) ? (8'h30 + val) : (8'h41 + val - 10);
        end
    endfunction
    
    // Message: "SPI: XXXXXXXX\r\n"
    reg [7:0] message [0:14];
    reg [3:0] msg_idx = 0;
    reg [24:0] send_timer = 0;
    
    always @(posedge sys_clk) begin
        // Update message dynamically
        message[0] = "S"; message[1] = "P"; message[2] = "I"; message[3] = ":"; message[4] = " ";
        message[5] = to_hex(read_data[31:28]);
        message[6] = to_hex(read_data[27:24]);
        message[7] = to_hex(read_data[23:20]);
        message[8] = to_hex(read_data[19:16]);
        message[9] = to_hex(read_data[15:12]);
        message[10] = to_hex(read_data[11:8]);
        message[11] = to_hex(read_data[7:4]);
        message[12] = to_hex(read_data[3:0]);
        message[13] = 8'h0D; message[14] = 8'h0A;
        
        if (!tx_busy && spi_done) begin
            send_timer <= send_timer + 1;
            if (send_timer == 25'd10000000) begin
                send_timer <= 0;
                tx_data <= {1'b1, message[msg_idx]};
                tx_busy <= 1;
                tx_bit_cnt <= 0;
                tx_clk_cnt <= 0;
                tx_out <= 0;
                
                if (msg_idx == 14) msg_idx <= 0;
                else msg_idx <= msg_idx + 1;
            end else begin
                tx_out <= 1;
            end
        end else if (tx_busy) begin
            if (tx_clk_cnt < CLKS_PER_BIT - 1) begin
                tx_clk_cnt <= tx_clk_cnt + 1;
            end else begin
                tx_clk_cnt <= 0;
                if (tx_bit_cnt < 9) begin
                    tx_out <= tx_data[0];
                    tx_data <= {1'b1, tx_data[8:1]};
                    tx_bit_cnt <= tx_bit_cnt + 1;
                end else begin
                    tx_busy <= 0;
                    tx_out <= 1;
                end
            end
        end
    end
endmodule
