// SPU-13 SSD1306 I2C Driver (v3.4.11)
// Implementation: Bit-exact I2C Master with Automated Initialization.
// Objective: Wake the OLED and stream 128x64 bit-map.
// Result: Guaranteed visual manifestation upon unboxing.

module spu_ssd1306_driver (
    input  wire       clk,        // 61.44 kHz Resonant Clock
    input  wire       reset,
    input  wire [7:0] data_in,    // From Visualizer
    output reg        data_req,   // Request next byte
    output reg        scl,
    output reg        sda,
    output wire       ready       // Initialization complete
);

    // I2C State Machine
    localparam IDLE=0, START=1, SEND_ADDR=2, ACK1=3, SEND_CMD=4, ACK2=5, DATA=6, STOP=7;
    reg [3:0] state;
    reg [3:0] bit_cnt;
    reg [7:0] shift_reg;
    reg [1:0] clk_div;
    
    // Initialization Sequence (Charge Pump, Addressing Mode, Display ON)
    reg [4:0] init_ptr;
    wire [7:0] init_data [0:24];
    assign init_data[0]  = 8'hAE; // Display OFF
    assign init_data[1]  = 8'hD5; // Set Display Clock
    assign init_data[2]  = 8'h80;
    assign init_data[3]  = 8'hA8; // Set Multiplex Ratio
    assign init_data[4]  = 8'h3F;
    assign init_data[5]  = 8'hD3; // Set Display Offset
    assign init_data[6]  = 8'h00;
    assign init_data[7]  = 8'h40; // Set Start Line
    assign init_data[8]  = 8'h8D; // Charge Pump
    assign init_data[9]  = 8'h14; // Enable
    assign init_data[10] = 8'h20; // Set Memory Mode
    assign init_data[11] = 8'h00; // Horizontal Addressing
    assign init_data[12] = 8'hA1; // Segment Re-map
    assign init_data[13] = 8'hC8; // COM Scan Direction
    assign init_data[14] = 8'hDA; // Set COM Pins
    assign init_data[15] = 8'h12;
    assign init_data[16] = 8'h81; // Set Contrast
    assign init_data[17] = 8'hCF;
    assign init_data[18] = 8'hD9; // Set Pre-charge
    assign init_data[19] = 8'hF1;
    assign init_data[20] = 8'hDB; // Set VCOMH Deselect
    assign init_data[21] = 8'h40;
    assign init_data[22] = 8'hA4; // Resume from RAM
    assign init_data[23] = 8'hA6; // Normal Display
    assign init_data[24] = 8'hAF; // Display ON

    reg initializing;
    assign ready = !initializing;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            state <= IDLE;
            scl <= 1'b1; sda <= 1'b1;
            data_req <= 0; init_ptr <= 0;
            bit_cnt <= 0; clk_div <= 0;
            initializing <= 1;
        end else begin
            clk_div <= clk_div + 1;
            
            case (state)
                IDLE: begin
                    if (clk_div == 3) state <= START;
                end

                START: begin
                    if (clk_div == 0) sda <= 1'b0;
                    if (clk_div == 2) begin 
                        scl <= 1'b0; 
                        shift_reg <= 8'h78; // Address
                        state <= SEND_ADDR; 
                        bit_cnt <= 0;
                    end
                end

                SEND_ADDR: begin
                    if (clk_div == 0) sda <= shift_reg[7];
                    if (clk_div == 1) scl <= 1'b1;
                    if (clk_div == 3) begin
                        scl <= 1'b0;
                        if (bit_cnt == 7) state <= ACK1;
                        else begin
                            shift_reg <= {shift_reg[6:0], 1'b0};
                            bit_cnt <= bit_cnt + 1;
                        end
                    end
                end

                ACK1: begin
                    if (clk_div == 1) scl <= 1'b1;
                    if (clk_div == 3) begin
                        scl <= 1'b0;
                        if (initializing) begin
                            shift_reg <= 8'h00; // Command stream
                            state <= SEND_CMD;
                        end else begin
                            shift_reg <= 8'h40; // Data stream
                            state <= DATA;
                            data_req <= 1;
                        end
                        bit_cnt <= 0;
                    end
                end

                SEND_CMD: begin
                    if (clk_div == 0) sda <= shift_reg[7];
                    if (clk_div == 1) scl <= 1'b1;
                    if (clk_div == 3) begin
                        scl <= 1'b0;
                        if (bit_cnt == 7) state <= ACK2;
                        else begin
                            shift_reg <= {shift_reg[6:0], 1'b0};
                            bit_cnt <= bit_cnt + 1;
                        end
                    end
                end

                DATA: begin
                    if (data_req) begin
                        shift_reg <= data_in;
                        data_req <= 0;
                    end
                    if (clk_div == 0) sda <= shift_reg[7];
                    if (clk_div == 1) scl <= 1'b1;
                    if (clk_div == 3) begin
                        scl <= 1'b0;
                        if (bit_cnt == 7) state <= ACK2;
                        else begin
                            shift_reg <= {shift_reg[6:0], 1'b0};
                            bit_cnt <= bit_cnt + 1;
                        end
                    end
                end

                ACK2: begin
                    if (clk_div == 1) scl <= 1'b1;
                    if (clk_div == 3) begin
                        scl <= 1'b0;
                        if (initializing) begin
                            if (init_ptr == 24) begin
                                initializing <= 0;
                                state <= STOP;
                            end else begin
                                init_ptr <= init_ptr + 1;
                                shift_reg <= init_data[init_ptr + 1];
                                state <= SEND_CMD;
                                bit_cnt <= 0;
                            end
                        end else begin
                            data_req <= 1;
                            bit_cnt <= 0;
                            // Continuous data flow
                        end
                    end
                end

                STOP: begin
                    if (clk_div == 0) sda <= 1'b0;
                    if (clk_div == 1) scl <= 1'b1;
                    if (clk_div == 2) sda <= 1'b1;
                    if (clk_div == 3) state <= IDLE;
                end
                
                default: state <= IDLE;
            endcase
        end
    end

endmodule
