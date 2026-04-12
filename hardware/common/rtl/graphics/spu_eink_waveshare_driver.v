// SPU-13 Waveshare E-Ink SPI Driver (v1.0)
// Target: Unified SPU-13 Fleet
// Objective: Persistent Lithic Display via 4-wire SPI.
// Interface: CS, DC, RST, BUSY, MOSI, SCK.

module spu_eink_waveshare_driver #(
    parameter CLK_HZ = 12000000
)(
    input  wire        clk,
    input  wire        reset,
    input  wire [7:0]  data_in,
    input  wire        start_refresh, // Pulse to begin a new 'Carving'
    output reg         busy,
    output reg         spi_cs,
    output reg         spi_dc,
    output reg         spi_rst,
    input  wire        spi_busy_in,   // From E-Ink hardware
    output reg         spi_mosi,
    output reg         spi_sck
);

    // --- 1. SPI State Machine ---
    localparam IDLE=0, RESET=1, INIT=2, DATA=3, WAIT=4;
    reg [3:0] state;
    reg [7:0] shift_reg;
    reg [3:0] bit_cnt;
    reg [15:0] delay_cnt;

    // We use a slow SPI clock (~1MHz) derived from the Artery
    reg [3:0] clk_div;
    wire sck_pulse;
    assign sck_pulse = (clk_div == 4'd10);

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            state <= RESET;
            busy <= 1;
            spi_cs <= 1; spi_dc <= 0; spi_rst <= 0;
            spi_mosi <= 0; spi_sck <= 0;
            bit_cnt <= 0; delay_cnt <= 0; clk_div <= 0;
        end else begin
            clk_div <= clk_div + 1;
            
            case (state)
                RESET: begin
                    if (delay_cnt < 16'hFFFF) delay_cnt <= delay_cnt + 1;
                    else begin
                        spi_rst <= 1;
                        state <= IDLE;
                        busy <= 0;
                    end
                end

                IDLE: begin
                    if (start_refresh) begin
                        busy <= 1;
                        spi_cs <= 0;
                        state <= DATA;
                        shift_reg <= data_in;
                        bit_cnt <= 0;
                    end
                end

                DATA: begin
                    if (sck_pulse) begin
                        spi_sck <= ~spi_sck;
                        if (spi_sck) begin // Falling edge
                            if (bit_cnt == 7) begin
                                state <= WAIT;
                                spi_cs <= 1;
                            end else begin
                                shift_reg <= {shift_reg[6:0], 1'b0};
                                bit_cnt <= bit_cnt + 1;
                            end
                        end else begin // Rising edge
                            spi_mosi <= shift_reg[7];
                        end
                        clk_div <= 0;
                    end
                end

                WAIT: begin
                    if (!spi_busy_in) begin
                        busy <= 0;
                        state <= IDLE;
                    end
                end
            endcase
        end
    end

endmodule
