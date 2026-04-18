// SPU-13 Chord Receiver (v1.0)
// Role: Receives 16-bit Biometric Chords from RP2040 via UART/Artery Protocol.
// Format: [Type:4][Freq/Prime:6][Amp:6]

module spu_chord_rx (
    input  wire        clk,      // System clock
    input  wire        rst_n,    // Active low reset
    input  wire        uart_rx,  // Serial data from RP2040
    
    output reg [15:0]  chord,    // The received 16-bit chord
    output reg         valid     // Pulse high when a new chord is manifested
);

    parameter CLK_FREQ = 25_000_000;
    parameter BAUD      = 115_200;
    localparam BIT_PERIOD = CLK_FREQ / BAUD;

    // --- UART State Machine ---
    reg [3:0] state;
    localparam STATE_IDLE  = 4'd0;
    localparam STATE_START = 4'd1;
    localparam STATE_DATA  = 4'd2;
    localparam STATE_STOP  = 4'd3;

    reg [15:0] timer;
    reg [3:0]  bit_idx;
    reg [7:0]  rx_byte;
    reg        byte_ready;

    // Byte Receiver Logic
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= STATE_IDLE;
            timer <= 0;
            bit_idx <= 0;
            rx_byte <= 0;
            byte_ready <= 0;
        end else begin
            byte_ready <= 0;
            case (state)
                STATE_IDLE: begin
                    if (!uart_rx) begin // Start bit detected
                        state <= STATE_START;
                        timer <= BIT_PERIOD / 2;
                    end
                end
                STATE_START: begin
                    if (timer == 0) begin
                        state <= STATE_DATA;
                        timer <= BIT_PERIOD;
                        bit_idx <= 0;
                    end else timer <= timer - 1;
                end
                STATE_DATA: begin
                    if (timer == 0) begin
                        rx_byte[bit_idx] <= uart_rx;
                        if (bit_idx == 7) begin
                            state <= STATE_STOP;
                        end else bit_idx <= bit_idx + 1;
                        timer <= BIT_PERIOD;
                    end else timer <= timer - 1;
                end
                STATE_STOP: begin
                    if (timer == 0) begin
                        state <= STATE_IDLE;
                        byte_ready <= 1;
                    end else timer <= timer - 1;
                end
            endcase
        end
    end

    // --- Chord Manifestation ---
    // The RP2040 sends the 16-bit chord as 2 bytes (Big Endian)
    reg [7:0] high_byte;
    reg       waiting_for_low;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            chord <= 16'h0;
            valid <= 0;
            high_byte <= 0;
            waiting_for_low <= 0;
        end else begin
            valid <= 0;
            if (byte_ready) begin
                if (!waiting_for_low) begin
                    high_byte <= rx_byte;
                    waiting_for_low <= 1;
                end else begin
                    chord <= {high_byte, rx_byte};
                    valid <= 1;
                    waiting_for_low <= 0;
                end
            end
        end
    end

endmodule
